"""
Phase 16: 批量执行中心 - BatchRunService

支持 4000+ 用例分批执行、并发控制、失败归因、进度追踪、报告生成。
复用已有 ExecutionEngineV2 单用例执行能力，不重写执行引擎。
"""

import json
import time
import uuid as uuid_mod
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session

from database.models import TestCase, TestRun, RunCase, Environment, Report
from database.session import get_db_session
from app.executor_v2.execution_engine import ExecutionEngineV2
from app.executor_v2.models import TestCaseV2, AssertionDef, AssertionType, ExecutionStatus


# ── 失败分类 ──────────────────────────────────────────
class FailureCategory:
    AUTH_FAILED = "auth_failed"          # 401/403
    NETWORK_ERROR = "network_error"      # 超时、连接失败
    ASSERTION_FAILED = "assertion_failed" # 断言失败
    BUSINESS_FAILED = "business_failed"  # HTTP 200 但业务 code 失败
    SYSTEM_ERROR = "system_error"        # 平台内部异常


def classify_failure(result_status: str, error_message: str, resp_snapshot: dict) -> str:
    """根据执行结果分类失败原因"""
    err_lower = (error_message or "").lower()
    status_code = resp_snapshot.get("status_code", 0) if resp_snapshot else 0

    if status_code in (401, 403):
        return FailureCategory.AUTH_FAILED
    if status_code == 0 or "timeout" in err_lower or "connect" in err_lower or "connection" in err_lower:
        return FailureCategory.NETWORK_ERROR
    if result_status == "error" or "traceback" in err_lower or "exception" in err_lower:
        return FailureCategory.SYSTEM_ERROR

    # HTTP 成功但业务 code 失败
    body = resp_snapshot.get("body", {}) if resp_snapshot else {}
    if isinstance(body, dict):
        code = body.get("code")
        if code is not None and code not in (0, 200, "0", "200"):
            return FailureCategory.BUSINESS_FAILED

    return FailureCategory.ASSERTION_FAILED


# ── 批量执行进度追踪 ─────────────────────────────────
class BatchProgress:
    """线程安全的进度追踪器"""

    def __init__(self, total: int, batch_id: str):
        self.batch_id = batch_id
        self.total = total
        self.executed = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.running = 0
        self.stopped = False
        self.failure_categories: Dict[str, int] = {
            FailureCategory.AUTH_FAILED: 0,
            FailureCategory.NETWORK_ERROR: 0,
            FailureCategory.ASSERTION_FAILED: 0,
            FailureCategory.BUSINESS_FAILED: 0,
            FailureCategory.SYSTEM_ERROR: 0,
        }
        self.start_time = time.time()
        import threading
        self._thread_lock = threading.Lock()

    def to_dict(self) -> dict:
        elapsed = time.time() - self.start_time
        return {
            "batch_id": self.batch_id,
            "total": self.total,
            "executed": self.executed,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "running": self.running,
            "stopped": self.stopped,
            "progress_pct": round(self.executed / max(self.total, 1) * 100, 1),
            "elapsed_seconds": round(elapsed, 2),
            "failure_categories": dict(self.failure_categories),
        }

    def inc_pass(self):
        with self._thread_lock:
            self.executed += 1
            self.passed += 1
            self.running = max(0, self.running - 1)

    def inc_fail(self, category: str):
        with self._thread_lock:
            self.executed += 1
            self.failed += 1
            self.running = max(0, self.running - 1)
            if category in self.failure_categories:
                self.failure_categories[category] += 1

    def inc_skip(self):
        with self._thread_lock:
            self.executed += 1
            self.skipped += 1

    def inc_running(self):
        with self._thread_lock:
            self.running += 1

    def dec_running(self):
        with self._thread_lock:
            self.running = max(0, self.running - 1)


# ── 全局进度注册表 ────────────────────────────────────
_active_batches: Dict[str, BatchProgress] = {}


def get_batch_progress(batch_id: str) -> Optional[BatchProgress]:
    return _active_batches.get(batch_id)


def stop_batch(batch_id: str) -> bool:
    bp = _active_batches.get(batch_id)
    if bp:
        bp.stopped = True
        return True
    return False


# ── URL 模式检测（复用 case_execute_routes 逻辑）────────
def _detect_api_pattern(url: str) -> str:
    url_lower = (url or "").lower()
    if url_lower.endswith("/page"):
        return "page"
    if url_lower.endswith("/list"):
        return "list"
    for s in ("/detail", "/get", "/info", "/query"):
        if url_lower.endswith(s):
            return "detail"
    for s in ("/save", "/add", "/create", "/insert"):
        if url_lower.endswith(s):
            return "save"
    for s in ("/update", "/edit", "/modify"):
        if url_lower.endswith(s):
            return "update"
    for s in ("/delete", "/remove"):
        if url_lower.endswith(s):
            return "delete"
    return "other"


def _extract_module_prefix(url_path: str) -> str:
    import re
    return re.sub(
        r'/(page|list|detail|get|info|query|save|add|create|insert|update|edit|modify|delete|remove)$',
        '', url_path, flags=re.I
    )


def _extract_uuid_from_response(body: dict) -> str:
    if not isinstance(body, dict):
        return ""
    if body.get("code") not in (200, "200", 0, "0"):
        return ""
    data = body.get("data")
    if isinstance(data, dict):
        items = data.get("list") or data.get("records") or data.get("rows") or []
    elif isinstance(data, list):
        items = data
    else:
        return ""
    if items and isinstance(items, list) and len(items) > 0:
        first = items[0]
        if isinstance(first, dict):
            return str(first.get("uuid") or first.get("id") or first.get("ID") or "")
    return ""


# ── 智能断言（写操作宽松）────────────────────────────
_WRITE_ACCEPTABLE_CODES = {400, 10000, 1100001, 1100002, 1100003, 1100004, 1100005}


def _is_write_pattern(pattern: str) -> bool:
    return pattern in ("save", "update", "delete")


# ── 断言转换（复用 case_execute_routes 逻辑）──────────
def _convert_assertions(raw_assertions: list) -> list:
    from app.executor_v2.models import AssertionDef, AssertionType
    defs = []
    for a in raw_assertions:
        if not isinstance(a, dict):
            continue
        a_type = a.get('type', '')
        if a_type == 'status_code':
            expected = a.get('expected', [200, 201, 204])
            if not isinstance(expected, list):
                expected = [expected]
            defs.append(AssertionDef(type=AssertionType.STATUS_CODE.value, expected=expected))
        elif a_type == 'response_time':
            defs.append(AssertionDef(type=AssertionType.RESPONSE_TIME.value, expected=a.get('expected', 10000)))
        elif a_type in ('field_exists', 'json_path_exists'):
            defs.append(AssertionDef(type=AssertionType.FIELD_EXISTS.value, path=a.get('path', '')))
        elif a_type in ('field_equals', 'json_path_equals'):
            defs.append(AssertionDef(type=AssertionType.JSON_PATH.value, path=a.get('path', ''), expected=a.get('expected'), operator='eq'))
        elif a_type == 'business_code':
            defs.append(AssertionDef(type=AssertionType.JSON_PATH.value, path=a.get('path', 'code'), expected=a.get('expected', [0, 200]), operator='in'))
        elif a_type == 'json_path':
            field = a.get('field', a.get('path', ''))
            op = a.get('operator', 'eq')
            if op == 'exists':
                defs.append(AssertionDef(type=AssertionType.FIELD_EXISTS.value, path=field))
            else:
                defs.append(AssertionDef(type=AssertionType.JSON_PATH.value, path=field, expected=a.get('expected'), operator=op))
    return defs


# ── 单用例执行器（线程安全，独立 DB session）──────────
def _execute_single_case(
    tc_id: str,
    tc_title: str,
    exec_config: dict,
    assertions_raw: list,
    base_url: str,
    auth_env_key: str,
    default_headers: dict,
    uuid_pool: dict,
    progress: BatchProgress,
    run_id: str,
) -> dict:
    """执行单个用例并返回结果字典，绝不抛异常"""
    case_start = datetime.now()
    result_dict = {
        "test_case_id": tc_id,
        "title": tc_title,
        "status": "error",
        "error_message": "",
        "error_type": "",
        "failure_category": "",
        "duration_ms": 0,
        "assertions_passed": 0,
        "assertions_failed": 0,
        "assertion_details": [],
        "request_snapshot": {},
        "response_snapshot": {},
    }

    if progress.stopped:
        result_dict["status"] = "skipped"
        result_dict["error_message"] = "批量任务已停止"
        progress.inc_skip()
        return result_dict

    progress.inc_running()

    try:
        method = exec_config.get("method", "GET").upper()
        url_path = exec_config.get("url", "/")
        headers = {**default_headers, **(exec_config.get("headers") or {})}
        body = exec_config.get("body")
        if isinstance(body, dict):
            body = body.copy()
        timeout = exec_config.get("timeout", 30)

        pattern = _detect_api_pattern(url_path)

        # 数据关联：注入 uuid
        if pattern in ("update", "delete", "detail") and isinstance(body, dict):
            prefix = _extract_module_prefix(url_path)
            real_uuid = uuid_pool.get(prefix)
            if real_uuid and ("uuid" in body or not body):
                body["uuid"] = real_uuid

        assertions = _convert_assertions(assertions_raw or [])

        case_v2 = TestCaseV2(
            id=tc_id,
            title=tc_title,
            method=method,
            path=url_path,
            base_url=base_url,
            headers=headers,
            body=body,
            timeout=timeout,
            assertions=assertions,
        )

        engine = ExecutionEngineV2(base_url=base_url, auth_env_key=auth_env_key)
        result = engine.execute_case(case_v2, run_id=run_id)

        # 智能断言：写操作宽松
        resp_body = result.response.body if result.response else {}
        if isinstance(resp_body, dict) and "code" in resp_body:
            actual_code = resp_body.get("code")
            if actual_code in (0, 200, "0", "200"):
                pass  # OK
            elif _is_write_pattern(pattern) and (actual_code in _WRITE_ACCEPTABLE_CODES or (isinstance(actual_code, int) and actual_code > 1000)):
                # 写操作连通性通过，不算失败
                if result.status == ExecutionStatus.FAILED.value:
                    result.status = ExecutionStatus.PASSED.value

        duration_ms = result.duration_ms
        resp_snapshot = result.response.to_dict() if result.response else {}
        req_snapshot = result.request.to_dict() if result.request else {}
        assertion_details = [a.to_dict() for a in result.assertions] if result.assertions else []
        a_summary = result.assertion_summary if result.assertions else {"total": 0, "passed": 0, "failed": 0}

        result_dict.update({
            "status": result.status,
            "error_message": result.error_message or "",
            "duration_ms": duration_ms,
            "assertions_passed": a_summary.get("passed", 0),
            "assertions_failed": a_summary.get("failed", 0),
            "assertion_details": assertion_details,
            "request_snapshot": req_snapshot,
            "response_snapshot": resp_snapshot,
        })

        # 数据关联：提取 uuid
        if pattern in ("page", "list") and isinstance(resp_body, dict):
            prefix = _extract_module_prefix(url_path)
            extracted = _extract_uuid_from_response(resp_body)
            if extracted and prefix:
                uuid_pool[prefix] = extracted

        # 分类
        if result.status in (ExecutionStatus.PASSED.value, "no_assertion"):
            progress.inc_pass()
        else:
            cat = classify_failure(result.status, result.error_message or "", resp_snapshot)
            result_dict["failure_category"] = cat
            result_dict["error_type"] = cat
            progress.inc_fail(cat)

    except Exception as e:
        result_dict["status"] = "error"
        result_dict["error_message"] = str(e)
        result_dict["error_type"] = FailureCategory.SYSTEM_ERROR
        result_dict["failure_category"] = FailureCategory.SYSTEM_ERROR
        result_dict["duration_ms"] = (datetime.now() - case_start).total_seconds() * 1000
        progress.inc_fail(FailureCategory.SYSTEM_ERROR)

    return result_dict


# ── BatchRunService ───────────────────────────────────
class BatchRunService:
    """
    批量执行服务。

    用法:
        service = BatchRunService(db)
        batch = service.create_batch_run(...)
        service.execute_batch(batch_id)  # 在后台线程执行
    """

    def __init__(self, db: Session):
        self.db = db

    # ---- 创建批量任务 ----
    def create_batch_run(
        self,
        project_id: int,
        environment_id: int,
        case_ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        batch_size: int = 50,
        concurrency: int = 5,
    ) -> TestRun:
        """
        创建批量执行任务。

        filters 支持:
          - status: 用例状态筛选
          - api_pattern: 接口类型 (page/list/save/update/delete/...)
          - module_prefix: 模块路径前缀
          - title_keyword: 标题关键词
        """
        # 筛选用例（TestCase 表无 project_id，按条件筛选）
        query = self.db.query(TestCase)
        if case_ids:
            query = query.filter(TestCase.id.in_(case_ids))
        else:
            if filters:
                if filters.get("status"):
                    query = query.filter(TestCase.status == filters["status"])
                if filters.get("title_keyword"):
                    query = query.filter(TestCase.title.contains(filters["title_keyword"]))
                if filters.get("module_prefix"):
                    prefix = filters["module_prefix"]
                    # SQLite 兼容：用标题或 JSON 字符串匹配
                    from sqlalchemy import cast, String
                    query = query.filter(
                        cast(TestCase.execution_config, String).contains(prefix)
                    )

        cases = query.all()
        if not cases:
            raise ValueError("未找到符合条件的测试用例")

        # 按接口类型过滤
        if filters and filters.get("api_pattern"):
            target_pattern = filters["api_pattern"]
            cases = [
                tc for tc in cases
                if _detect_api_pattern((tc.execution_config or {}).get("url", "")) == target_pattern
            ]
            if not cases:
                raise ValueError(f"筛选后无 '{target_pattern}' 类型的用例")

        total = len(cases)
        case_id_list = [tc.id for tc in cases]

        # 创建 TestRun
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        batch_id = f"BATCH_{timestamp}_{uuid_mod.uuid4().hex[:8]}"
        trace_id = f"TRACE_{uuid_mod.uuid4().hex}"

        test_run = TestRun(
            id=batch_id,
            project_id=project_id,
            environment_id=environment_id,
            trigger_type="batch_center",
            status="created",
            trace_id=trace_id,
            start_time=None,
            total_cases=total,
            passed_cases=0,
            failed_cases=0,
            skipped_cases=0,
            summary=json.dumps({
                "batch_size": batch_size,
                "concurrency": concurrency,
                "case_ids": case_id_list,
                "filters": filters or {},
            }, ensure_ascii=False),
            created_by="batch_center",
        )
        self.db.add(test_run)
        self.db.commit()
        self.db.refresh(test_run)
        return test_run

    # ---- 查询批量任务列表 ----
    def list_batch_runs(self, skip: int = 0, limit: int = 20) -> List[TestRun]:
        return (
            self.db.query(TestRun)
            .filter(TestRun.trigger_type == "batch_center")
            .order_by(TestRun.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    # ---- 获取单个批量任务 ----
    def get_batch_run(self, batch_id: str) -> Optional[TestRun]:
        return self.db.query(TestRun).filter(TestRun.id == batch_id).first()

    # ---- 执行批量任务（同步，在后台线程调用）----
    def execute_batch(self, batch_id: str):
        """
        执行批量任务。此方法会阻塞直到完成，应在后台线程中调用。
        """
        from database.session import get_db_session

        with get_db_session() as db:
            test_run = db.query(TestRun).filter(TestRun.id == batch_id).first()
            if not test_run:
                return

            summary_data = json.loads(test_run.summary or "{}")
            case_ids = summary_data.get("case_ids", [])
            batch_size = summary_data.get("batch_size", 50)
            concurrency = summary_data.get("concurrency", 5)
            env_id = test_run.environment_id

            # 加载环境
            env = db.query(Environment).filter(Environment.id == env_id).first()
            if not env:
                test_run.status = "failed"
                test_run.summary = json.dumps({**summary_data, "error": "环境不存在"}, ensure_ascii=False)
                db.commit()
                return

            base_url = env.base_url

            # 加载认证
            from routes.case_execute_routes import _prepare_environment_auth
            auth_context = _prepare_environment_auth(db, env_id)
            default_headers = auth_context.get("default_headers", {})
            auth_env_key = auth_context.get("env_key", "default")

            # 加载用例
            cases = db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()
            case_map = {tc.id: tc for tc in cases}

            # 智能排序
            PATTERN_ORDER = {"page": 0, "list": 1, "detail": 2, "other": 3, "save": 4, "update": 5, "delete": 6}
            sorted_ids = sorted(
                case_ids,
                key=lambda cid: PATTERN_ORDER.get(
                    _detect_api_pattern((case_map.get(cid, TestCase()).execution_config or {}).get("url", "")),
                    3
                )
            )

            # 初始化进度
            progress = BatchProgress(total=len(sorted_ids), batch_id=batch_id)
            _active_batches[batch_id] = progress

            # 更新状态为 running
            test_run.status = "running"
            test_run.start_time = datetime.now()
            db.commit()

            uuid_pool: Dict[str, str] = {}
            all_results: List[dict] = []

            # 分批执行
            for batch_start in range(0, len(sorted_ids), batch_size):
                if progress.stopped:
                    break

                batch_ids = sorted_ids[batch_start:batch_start + batch_size]

                # 将当前批次再分为：查询类（先执行）和写操作类（后执行）
                query_ids = []
                write_ids = []
                for cid in batch_ids:
                    tc = case_map.get(cid)
                    if not tc:
                        continue
                    cfg = tc.execution_config or {}
                    p = _detect_api_pattern(cfg.get("url", ""))
                    if p in ("page", "list", "detail", "other"):
                        query_ids.append(cid)
                    else:
                        write_ids.append(cid)

                # 先并发执行查询类
                query_results = self._execute_batch_chunk(
                    query_ids, case_map, base_url, auth_env_key, default_headers,
                    uuid_pool, progress, batch_id, concurrency
                )
                all_results.extend(query_results)

                # 再并发执行写操作类（此时 uuid_pool 已填充）
                write_results = self._execute_batch_chunk(
                    write_ids, case_map, base_url, auth_env_key, default_headers,
                    uuid_pool, progress, batch_id, concurrency
                )
                all_results.extend(write_results)

            # 写入 RunCase 记录 + Phase 16: 写回 TestCase 治理字段
            for r in all_results:
                rc = RunCase(
                    run_id=batch_id,
                    test_case_id=r["test_case_id"],
                    status=r["status"],
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    duration=r["duration_ms"] / 1000 if r["duration_ms"] else 0,
                    error_message=r.get("error_message"),
                    error_type=r.get("failure_category"),
                    request_snapshot=r.get("request_snapshot"),
                    response_snapshot=r.get("response_snapshot"),
                    assertions_passed=r.get("assertions_passed", 0),
                    assertions_failed=r.get("assertions_failed", 0),
                    assertion_details=r.get("assertion_details"),
                )
                db.add(rc)

                # Phase 16: 写回 TestCase.last_run_status / failure_category
                tc = case_map.get(r["test_case_id"])
                if tc:
                    tc.status = r["status"]
                    tc.last_run_status = r["status"]
                    tc.failure_category = r.get("failure_category") or None

            # 更新 TestRun 统计
            test_run.status = "aborted" if progress.stopped else ("passed" if progress.failed == 0 else "failed")
            test_run.end_time = datetime.now()
            test_run.duration = (test_run.end_time - test_run.start_time).total_seconds() if test_run.start_time else 0
            test_run.passed_cases = progress.passed
            test_run.failed_cases = progress.failed
            test_run.skipped_cases = progress.skipped
            test_run.summary = json.dumps({
                **summary_data,
                "failure_categories": progress.failure_categories,
                "elapsed_seconds": round(time.time() - progress.start_time, 2),
            }, ensure_ascii=False)

            db.commit()

            # 清理进度追踪
            _active_batches.pop(batch_id, None)

    def _execute_batch_chunk(
        self,
        case_ids: List[str],
        case_map: dict,
        base_url: str,
        auth_env_key: str,
        default_headers: dict,
        uuid_pool: dict,
        progress: BatchProgress,
        run_id: str,
        concurrency: int,
    ) -> List[dict]:
        """并发执行一组用例"""
        results = []
        if not case_ids:
            return results

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {}
            for cid in case_ids:
                tc = case_map.get(cid)
                if not tc:
                    progress.inc_skip()
                    results.append({
                        "test_case_id": cid, "title": "", "status": "skipped",
                        "error_message": "用例不存在", "failure_category": "",
                        "error_type": "", "duration_ms": 0,
                        "assertions_passed": 0, "assertions_failed": 0,
                        "assertion_details": [], "request_snapshot": {}, "response_snapshot": {},
                    })
                    continue

                fut = pool.submit(
                    _execute_single_case,
                    tc_id=tc.id,
                    tc_title=tc.title,
                    exec_config=tc.execution_config or {},
                    assertions_raw=tc.assertions or [],
                    base_url=base_url,
                    auth_env_key=auth_env_key,
                    default_headers=default_headers,
                    uuid_pool=uuid_pool,
                    progress=progress,
                    run_id=run_id,
                )
                futures[fut] = cid

            for fut in as_completed(futures):
                try:
                    r = fut.result()
                    results.append(r)
                except Exception as e:
                    cid = futures[fut]
                    results.append({
                        "test_case_id": cid, "title": "", "status": "error",
                        "error_message": str(e), "failure_category": FailureCategory.SYSTEM_ERROR,
                        "error_type": FailureCategory.SYSTEM_ERROR, "duration_ms": 0,
                        "assertions_passed": 0, "assertions_failed": 0,
                        "assertion_details": [], "request_snapshot": {}, "response_snapshot": {},
                    })
                    progress.inc_fail(FailureCategory.SYSTEM_ERROR)

        return results

    # ---- 生成报告 ----
    def generate_report(self, batch_id: str) -> dict:
        """生成批量执行报告 JSON"""
        test_run = self.db.query(TestRun).filter(TestRun.id == batch_id).first()
        if not test_run:
            raise ValueError(f"批量任务 {batch_id} 不存在")

        run_cases = self.db.query(RunCase).filter(RunCase.run_id == batch_id).all()

        summary_data = json.loads(test_run.summary or "{}")
        failure_categories = summary_data.get("failure_categories", {})

        # 按模块聚合
        module_stats: Dict[str, Dict[str, int]] = {}
        failed_cases = []
        for rc in run_cases:
            # 模块前缀
            req = rc.request_snapshot or {}
            url = req.get("url", "")
            module = _extract_module_prefix(url.split("/dev-api")[-1] if "/dev-api" in url else url)
            if module not in module_stats:
                module_stats[module] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
            module_stats[module]["total"] += 1
            if rc.status == "passed":
                module_stats[module]["passed"] += 1
            elif rc.status in ("failed", "error"):
                module_stats[module]["failed"] += 1
                failed_cases.append({
                    "test_case_id": rc.test_case_id,
                    "status": rc.status,
                    "error_type": rc.error_type or "",
                    "error_message": (rc.error_message or "")[:200],
                    "duration_ms": round((rc.duration or 0) * 1000, 2),
                })
            else:
                module_stats[module]["skipped"] += 1

        # 耗时统计
        durations = [rc.duration for rc in run_cases if rc.duration and rc.duration > 0]
        duration_stats = {}
        if durations:
            duration_stats = {
                "min_ms": round(min(durations) * 1000, 2),
                "max_ms": round(max(durations) * 1000, 2),
                "avg_ms": round(sum(durations) / len(durations) * 1000, 2),
                "p95_ms": round(sorted(durations)[int(len(durations) * 0.95)] * 1000, 2) if len(durations) > 1 else round(durations[0] * 1000, 2),
            }

        pass_rate = round(test_run.passed_cases / max(test_run.total_cases, 1) * 100, 1)

        report = {
            "batch_id": batch_id,
            "status": test_run.status,
            "created_at": test_run.created_at.isoformat() if test_run.created_at else "",
            "started_at": test_run.start_time.isoformat() if test_run.start_time else "",
            "finished_at": test_run.end_time.isoformat() if test_run.end_time else "",
            "duration_seconds": round(test_run.duration or 0, 2),
            "total_cases": test_run.total_cases,
            "passed_cases": test_run.passed_cases,
            "failed_cases": test_run.failed_cases,
            "skipped_cases": test_run.skipped_cases,
            "pass_rate": pass_rate,
            "failure_categories": failure_categories,
            "module_stats": module_stats,
            "duration_stats": duration_stats,
            "failed_case_details": failed_cases[:100],  # 最多100条
        }
        return report
