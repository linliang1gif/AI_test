import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from database.models import Environment, Project, RunCase, TestCase, TestRun
from services.sanitize import sanitize_exception_message
from services.variable_resolver import resolve_variables

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)


class BatchExecutionService:
    def __init__(self, db: Session):
        self.db = db

    def execute(
        self,
        case_ids: Optional[List[str]] = None,
        preset: Optional[str] = None,
        environment_id: Optional[int] = None,
        base_url: Optional[str] = None,
        dataset_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        allow_unsafe_methods: bool = False,
        allow_write_operations: bool = True,
        skip_destructive: bool = False,
        trigger_type: str = "manual_batch",
        iteration_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        from routes.case_execute_routes import (
            UNSAFE_METHODS,
            _apply_business_code_assertion,
            _classify_failure_category,
            _convert_assertions,
            _detect_api_pattern_from_url,
            _detect_write_api,
            _extract_module_prefix,
            _extract_uuid_from_response,
            _get_app_mode,
            _json_safe,
            _load_dataset_variables,
            _merge_headers,
            _prepare_environment_auth,
        )

        if preset and not case_ids:
            from services.case_governance_service import CaseGovernanceService
            gov_svc = CaseGovernanceService(self.db)
            preset_map = {
                "smoke": gov_svc.recommend_smoke,
                "regression": gov_svc.recommend_regression,
                "query-safe": gov_svc.recommend_query_safe,
                "failed-rerun": gov_svc.recommend_failed_rerun,
                "p0": gov_svc.recommend_p0,
            }
            loader = preset_map.get(preset)
            if not loader:
                raise HTTPException(status_code=400, detail=f"未知推荐集: {preset}，可选: {', '.join(preset_map.keys())}")
            case_ids = [tc.id for tc in loader(limit=2000)]

        if not case_ids:
            raise HTTPException(status_code=400, detail="请选择要执行的测试用例或指定 preset")

        resolved_base_url = base_url or ""
        env_id = environment_id
        if not resolved_base_url and env_id:
            env = self.db.query(Environment).filter(Environment.id == env_id).first()
            if env:
                resolved_base_url = env.base_url
        if not resolved_base_url:
            envs = self.db.query(Environment).all()
            if envs:
                resolved_base_url = envs[0].base_url
                env_id = envs[0].id
        if not resolved_base_url:
            raise HTTPException(status_code=400, detail="未配置测试环境地址。请在请求中传入 base_url 或先在项目中创建环境。")

        auth_context = _prepare_environment_auth(self.db, env_id)
        cases = self.db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()
        found_ids = {tc.id for tc in cases}
        missing_ids = [cid for cid in case_ids if cid not in found_ids]
        if not cases:
            raise HTTPException(status_code=404, detail="未找到可执行的测试用例")

        web_ui_cases = [tc for tc in cases if getattr(tc, "case_type", None) == "web_ui"]
        if web_ui_cases:
            cases = [tc for tc in cases if getattr(tc, "case_type", None) != "web_ui"]
            if not cases:
                raise HTTPException(status_code=400, detail="所选用例均为 Web UI 用例，暂不支持执行。Playwright 执行引擎将在 P2-4 支持。")

        app_mode = _get_app_mode()
        if app_mode == "real" and not allow_unsafe_methods:
            unsafe_cases = []
            for tc in cases:
                cfg = tc.execution_config or {}
                method = (cfg.get("method") or "GET").upper()
                if method in UNSAFE_METHODS:
                    unsafe_cases.append({"case_id": tc.id, "title": tc.title, "method": method, "url": cfg.get("url", "")})
            if unsafe_cases:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "REAL_MODE_UNSAFE_METHOD_BLOCKED",
                        "message": f"真实项目模式下默认禁止执行写操作，批量中包含 {len(unsafe_cases)} 个危险方法用例，请手动确认后再执行",
                        "unsafe_count": len(unsafe_cases),
                        "unsafe_cases": unsafe_cases[:20],
                        "app_mode": app_mode,
                    },
                )

        skipped_write_cases = []
        skipped_destructive_cases = []
        skipped_destructive_info = []
        if skip_destructive:
            safe = []
            for tc in cases:
                if getattr(tc, "destructive", False):
                    skipped_destructive_cases.append(tc.id)
                    skipped_destructive_info.append({
                        "case_id": tc.id,
                        "case_name": tc.title,
                        "module_name": getattr(tc, "module_name", "") or tc.module or "",
                        "risk_level": getattr(tc, "risk_level", "") or "",
                    })
                else:
                    safe.append(tc)
            cases = safe

        if not allow_write_operations:
            safe_cases = []
            for tc in cases:
                exec_config = tc.execution_config or {}
                if _detect_write_api(exec_config.get("method"), exec_config.get("url")):
                    skipped_write_cases.append(tc.id)
                else:
                    safe_cases.append(tc)
            cases = safe_cases

        if not cases:
            raise HTTPException(
                status_code=400,
                detail=f"无可执行用例。跳过写操作: {len(skipped_write_cases)}，跳过破坏性: {len(skipped_destructive_cases)}",
            )

        pattern_order = {"page": 0, "list": 1, "detail": 2, "other": 3, "save": 4, "update": 5, "delete": 6}
        cases.sort(key=lambda tc: pattern_order.get(_detect_api_pattern_from_url((tc.execution_config or {}).get("url", "")), 3))

        uuid_pool: Dict[str, str] = {}
        run_id = f"RUN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        trace_id = f"TRACE_{uuid.uuid4().hex}"
        start_time = datetime.now()
        from app.executor_v2.execution_engine import ExecutionEngineV2
        from app.executor_v2.models import ExecutionStatus, TestCaseV2

        engine = ExecutionEngineV2(base_url=resolved_base_url, auth_env_key=auth_context["env_key"], default_timeout=5.0)
        results = []
        counters = {"passed": 0, "failed": 0, "no_assertion": 0, "error": 0}

        resolved_project_id = project_id
        if not resolved_project_id and env_id:
            env_obj = self.db.query(Environment).filter(Environment.id == env_id).first()
            resolved_project_id = getattr(env_obj, "project_id", None) if env_obj else None
        if not resolved_project_id:
            first_project = self.db.query(Project).first()
            resolved_project_id = first_project.id if first_project else None

        test_run = TestRun(
            id=run_id,
            project_id=resolved_project_id,
            environment_id=env_id,
            trigger_type=trigger_type,
            status="running",
            trace_id=trace_id,
            start_time=start_time,
            total_cases=len(cases) + len(skipped_write_cases) + len(skipped_destructive_cases),
            passed_cases=0,
            failed_cases=0,
            skipped_cases=len(skipped_write_cases) + len(skipped_destructive_cases),
            iteration_id=iteration_id,
        )
        self.db.add(test_run)
        self.db.commit()
        self.db.refresh(test_run)

        for skipped_case_id in skipped_write_cases:
            self.db.add(RunCase(
                run_id=run_id,
                test_case_id=skipped_case_id,
                status="skipped",
                start_time=start_time,
                end_time=start_time,
                duration=0,
                error_message="写操作接口默认阻止执行",
                error_type="write_blocked",
                assertion_details=[],
            ))

        for skipped_case_id in skipped_destructive_cases:
            self.db.add(RunCase(
                run_id=run_id,
                test_case_id=skipped_case_id,
                status="skipped",
                start_time=start_time,
                end_time=start_time,
                duration=0,
                error_message="已跳过破坏性接口，避免修改或删除数据",
                error_type="destructive",
                assertion_details=[],
            ))

        resolved_variables = variables or (_load_dataset_variables(dataset_id, self.db) if dataset_id else {})

        for tc in cases:
            case_start = datetime.now()
            final_status = "error"
            error_message = ""
            req_snapshot = {}
            resp_snapshot = {}
            assertion_detail_list = []
            assertion_summary = {"total": 0, "passed": 0, "failed": 0}
            duration_ms = 0
            failure_category = None

            try:
                exec_config = tc.execution_config or {}
                if not exec_config.get("method") or not exec_config.get("url"):
                    raise ValueError(f"用例 {tc.id} 缺少执行配置(method/url)")

                method = exec_config.get("method", "GET").upper()
                url_path = exec_config.get("url", "/")
                case_base_url = (exec_config.get("base_url") or resolved_base_url).rstrip("/")
                headers = _merge_headers(auth_context["default_headers"], exec_config.get("headers", {}))
                query_params = exec_config.get("query_params", {})
                body = exec_config.get("body")
                if isinstance(body, dict):
                    body = body.copy()
                timeout = exec_config.get("timeout", 30)
                cur_pattern = _detect_api_pattern_from_url(url_path)

                if cur_pattern in ("update", "delete", "detail") and isinstance(body, dict):
                    module_prefix = _extract_module_prefix(url_path)
                    real_uuid = uuid_pool.get(module_prefix)
                    if real_uuid and ("uuid" in body or not body):
                        body["uuid"] = real_uuid

                if resolved_variables:
                    url_path, m1 = resolve_variables(url_path, resolved_variables)
                    headers, m2 = resolve_variables(headers, resolved_variables)
                    query_params, m3 = resolve_variables(query_params, resolved_variables)
                    body, m4 = resolve_variables(body, resolved_variables) if body else (body, [])
                    missing_vars = list(dict.fromkeys(m1 + m2 + m3 + m4))
                    if missing_vars:
                        raise ValueError(f"缺少变量: {', '.join(missing_vars)}")

                assertions = _convert_assertions(tc.assertions or [])
                case_v2 = TestCaseV2(
                    id=tc.id,
                    title=tc.title,
                    method=method,
                    path=url_path,
                    base_url=case_base_url,
                    headers=headers if isinstance(headers, dict) else {},
                    query_params=query_params if isinstance(query_params, dict) else {},
                    body=body,
                    timeout=timeout,
                    assertions=assertions,
                )

                result = engine.execute_case(case_v2, run_id=run_id)
                _apply_business_code_assertion(result, url_path=url_path)
                final_status = result.status
                if not result.assertions and result.status == ExecutionStatus.PASSED.value:
                    final_status = "no_assertion"

                duration_ms = result.duration_ms
                error_message = result.error_message or ""
                resp_snapshot = result.response.to_dict() if result.response else {}
                assertion_detail_list = [a.to_dict() for a in result.assertions] if result.assertions else []
                assertion_summary = result.assertion_summary if result.assertions else assertion_summary

                if cur_pattern in ("page", "list") and result.response and isinstance(result.response.body, dict):
                    module_prefix = _extract_module_prefix(url_path)
                    extracted = _extract_uuid_from_response(result.response.body)
                    if extracted and module_prefix:
                        uuid_pool[module_prefix] = extracted

                req_snapshot = result.request.to_dict() if result.request else {
                    "method": method,
                    "url": f"{case_base_url.rstrip('/')}/{url_path.lstrip('/')}",
                    "headers": headers,
                    "query_params": query_params,
                    "body": body,
                }
            except Exception as e:
                final_status = "error"
                error_message = sanitize_exception_message(str(e))
                duration_ms = (datetime.now() - case_start).total_seconds() * 1000

            counters[final_status if final_status in counters else "error"] += 1
            case_end = datetime.now()
            if final_status in ("failed", "error"):
                failure_category = _classify_failure_category(final_status, error_message, resp_snapshot if isinstance(resp_snapshot, dict) else {})
            self.db.add(RunCase(
                run_id=run_id,
                test_case_id=tc.id,
                status=final_status,
                start_time=case_start,
                end_time=case_end,
                duration=duration_ms / 1000,
                error_message=error_message or None,
                error_type=failure_category,
                request_snapshot=_json_safe(req_snapshot),
                response_snapshot=_json_safe(resp_snapshot),
                assertions_passed=assertion_summary.get("passed", 0),
                assertions_failed=assertion_summary.get("failed", 0),
                assertion_details=_json_safe(assertion_detail_list),
            ))

            tc.status = final_status
            tc.updated_at = datetime.now()
            tc.last_run_status = final_status
            if final_status in ("failed", "error"):
                tc.failure_category = failure_category
            else:
                tc.failure_category = None

            results.append({
                "case_id": tc.id,
                "case_name": tc.title,
                "status": final_status,
                "duration_ms": round(duration_ms, 2),
                "assertion_summary": assertion_summary,
                "error_message": error_message,
                "failure_category": tc.failure_category,
            })

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        overall_status = "passed"
        if counters["error"] > 0:
            overall_status = "error"
        elif counters["failed"] > 0:
            overall_status = "failed"
        elif counters["no_assertion"] > 0 and counters["passed"] == 0:
            overall_status = "no_assertion"
        elif counters["no_assertion"] > 0:
            overall_status = "passed"

        fc_agg = {}
        for item in results:
            cat = item.get("failure_category")
            if cat:
                fc_agg[cat] = fc_agg.get(cat, 0) + 1
        skipped_reasons = {}
        if skipped_destructive_cases:
            skipped_reasons["destructive"] = len(skipped_destructive_cases)
        if skipped_write_cases:
            skipped_reasons["write_blocked"] = len(skipped_write_cases)

        total_all = len(cases) + len(skipped_write_cases) + len(skipped_destructive_cases)
        total_skipped = len(skipped_write_cases) + len(skipped_destructive_cases)
        executed_count = counters["passed"] + counters["failed"] + counters["error"] + counters["no_assertion"]
        pass_rate = round(counters["passed"] / max(executed_count, 1) * 100, 1)

        test_run.status = overall_status
        test_run.end_time = end_time
        test_run.duration = total_duration
        test_run.total_cases = total_all
        test_run.passed_cases = counters["passed"]
        test_run.failed_cases = counters["failed"] + counters["error"]
        test_run.skipped_cases = total_skipped
        test_run.summary = json.dumps({
            "app_mode": app_mode,
            "allow_unsafe_methods": allow_unsafe_methods,
            "missing_case_ids": missing_ids,
            "skipped_write_case_ids": skipped_write_cases,
            "skipped_destructive_case_ids": skipped_destructive_cases,
            "no_assertion_cases": counters["no_assertion"],
            "error_cases": counters["error"],
            "preset": preset or None,
            "failure_categories": fc_agg,
            "skipped_reasons": skipped_reasons,
            "pass_rate": pass_rate,
        }, ensure_ascii=False)

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "RUN_CASE_WRITE_FAILED",
                    "message": "批量执行结果入库失败",
                    "details": {"error": sanitize_exception_message(str(e))},
                },
            )

        for info in skipped_destructive_info:
            results.append({
                "case_id": info["case_id"],
                "case_name": info["case_name"],
                "status": "skipped",
                "duration_ms": 0,
                "assertion_summary": {"total": 0, "passed": 0, "failed": 0},
                "error_message": "已跳过破坏性接口，避免修改或删除数据",
                "failure_category": None,
                "skipped_reason": "destructive",
                "skipped_message": "已跳过破坏性接口，避免修改或删除数据",
            })

        return {
            "success": overall_status in ("passed", "no_assertion"),
            "run_id": run_id,
            "status": overall_status,
            "message": f"批量执行完成：通过 {counters['passed']}，失败 {counters['failed']}，跳过 {total_skipped}，通过率 {pass_rate}%",
            "total_cases": total_all,
            "passed_cases": counters["passed"],
            "failed_cases": counters["failed"] + counters["error"],
            "skipped_cases": total_skipped,
            "no_assertion_cases": counters["no_assertion"],
            "error_cases": counters["error"],
            "duration_ms": round(total_duration * 1000, 2),
            "pass_rate": pass_rate,
            "failure_categories": fc_agg,
            "skipped_reasons": skipped_reasons,
            "results": results,
        }
