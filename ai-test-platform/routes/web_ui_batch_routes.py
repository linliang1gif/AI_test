"""
P2-7: Web UI 批量执行路由
P2-8: AI UI 失败归因

POST /api/v2/web-ui/batch-run  批量执行 Web UI 用例
GET  /api/v2/web-ui/traces/{filename}  下载 trace 文件
POST /api/v2/web-ui/runs/{run_id}/failure-analysis  执行失败归因
GET  /api/v2/web-ui/runs/{run_id}/failure-analysis  查询归因结果
"""
import json
import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import TestCase, TestRun, RunCase, RunStep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/web-ui", tags=["WebUI"])

TRACE_DIR = os.path.join("data", "artifacts", "ui", "traces")


# ---------- Request / Response Models ----------

class WebUIBatchRunRequest(BaseModel):
    project_id: int = Field(1, description="项目 ID")
    case_ids: List[str] = Field(..., min_items=1, description="Web UI 用例 ID 列表")
    environment_id: Optional[int] = Field(None, description="环境 ID")
    execution_config: Dict[str, Any] = Field(default_factory=lambda: {
        "browser": "chromium", "headless": True,
    }, description="执行配置")


class WebUIBatchRunResponse(BaseModel):
    success: bool
    run_id: str = ""
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    skipped_cases: int = 0
    trace_count: int = 0
    console_error_count: int = 0
    network_error_count: int = 0
    error_message: str = ""
    case_results: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {}


# ---------- 路由 ----------

@router.post("/batch-run", response_model=WebUIBatchRunResponse)
def batch_run_web_ui(
    req: WebUIBatchRunRequest,
    db: Session = Depends(get_db),
):
    """P2-7: 批量执行 Web UI 用例"""
    from services.playwright_engine import execute_web_ui, _is_playwright_available

    if not _is_playwright_available():
        raise HTTPException(
            status_code=503,
            detail="Playwright 未安装。请运行: pip install playwright && python -m playwright install chromium"
        )

    # 1. 查询用例
    cases = db.query(TestCase).filter(TestCase.id.in_(req.case_ids)).all()
    if not cases:
        raise HTTPException(status_code=404, detail="未找到任何用例")

    # 2. 过滤非 web_ui 用例
    non_webui = [tc for tc in cases if getattr(tc, "case_type", "") != "web_ui"]
    if non_webui:
        non_ids = [tc.id for tc in non_webui]
        raise HTTPException(
            status_code=400,
            detail=f"以下用例不是 web_ui 类型，不能加入 Web UI 批量执行: {non_ids}"
        )

    webui_cases = cases

    # 3. 合并 execution_config
    base_config = dict(req.execution_config)
    base_config.setdefault("browser", "chromium")
    base_config.setdefault("headless", True)
    base_config.setdefault("enable_trace", True)
    base_config.setdefault("capture_console", True)
    base_config.setdefault("capture_network", True)

    # 4. 创建 TestRun
    run_id = f"RUN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    test_run = TestRun(
        id=run_id,
        project_id=req.project_id,
        environment_id=req.environment_id,
        trigger_type="web_ui_batch",
        status="running",
        trace_id=f"TRACE_{uuid.uuid4().hex}",
        start_time=datetime.now(),
        total_cases=len(webui_cases),
    )
    db.add(test_run)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建 TestRun 失败: {e}")

    # P2-9B: retry config
    retry_enabled = base_config.get("retry_enabled", False)
    retry_count = min(base_config.get("retry_count", 1), 3)  # cap at 3
    retry_on = base_config.get("retry_on", ["page_timeout", "network_error", "selector_not_found"])

    # 5. 逐条执行 (单条失败不中断)
    passed = 0
    failed = 0
    skipped = 0
    trace_count = 0
    total_console_errors = 0
    total_network_errors = 0
    retried_cases = 0
    recovered_cases = 0
    flaky_candidate_count = 0
    total_selector_low_score = 0
    total_wait_warnings = 0
    case_results = []

    from services.web_ui_stability import (
        analyze_selectors, analyze_wait_strategies, preflight_check,
        categorize_failure, should_retry,
    )

    for tc in webui_cases:
        exec_config = dict(base_config)
        tc_exec = tc.execution_config or {}
        # 用例自身的 base_url / timeout 等可覆盖
        for k in ("base_url", "timeout", "viewport", "session_project_id"):
            if k in tc_exec:
                exec_config[k] = tc_exec[k]
        if not exec_config.get("base_url") and tc_exec.get("base_url"):
            exec_config["base_url"] = tc_exec["base_url"]

        steps = tc.steps or []
        assertions = tc.assertions or []

        # P2-9B: selector & wait analysis (pre-execution)
        sel_analysis = analyze_selectors(steps)
        wait_analysis = analyze_wait_strategies(steps)
        total_selector_low_score += sel_analysis["low_score_count"]
        total_wait_warnings += wait_analysis["warning_count"]

        # P2-9B: preflight check
        pf = preflight_check(getattr(tc, 'case_type', 'web_ui'), steps, assertions, exec_config)
        if not pf["ok"]:
            failed += 1
            err_msg = "执行前检查失败: " + "; ".join(pf["errors"])
            _write_run_case(db, run_id, tc, "failed", 0, err_msg, None)
            case_results.append({"case_id": tc.id, "title": tc.title, "status": "failed",
                                 "error": err_msg, "preflight_warnings": pf["warnings"]})
            continue

        # P2-9B: first execution attempt
        first_pw_result = None
        pw_result = None
        retry_attempt = 0
        is_flaky = False

        try:
            pw_result = execute_web_ui(
                steps=steps,
                assertions=assertions,
                execution_config=exec_config,
                case_id=tc.id,
                run_id=run_id,
            )
        except Exception as e:
            logger.error(f"Web UI case {tc.id} execution exception: {e}")
            pw_result = None

        # P2-9B: retry logic
        if pw_result and pw_result.status not in ("passed",) and retry_enabled:
            failure_cat = categorize_failure(pw_result.error_message or "")
            if should_retry(failure_cat, retry_on):
                first_pw_result = pw_result  # preserve first failure evidence
                for attempt in range(1, retry_count + 1):
                    retry_attempt = attempt
                    retried_cases += 1
                    logger.info(f"P2-9B retry {attempt}/{retry_count} for case {tc.id} (category={failure_cat})")
                    try:
                        pw_result = execute_web_ui(
                            steps=steps,
                            assertions=assertions,
                            execution_config=exec_config,
                            case_id=tc.id,
                            run_id=run_id,
                        )
                    except Exception as e:
                        logger.error(f"Web UI case {tc.id} retry {attempt} exception: {e}")
                        pw_result = None
                    if pw_result and pw_result.status == "passed":
                        is_flaky = True
                        recovered_cases += 1
                        flaky_candidate_count += 1
                        break

        if pw_result is None:
            # Treat as failed
            failed += 1
            _write_run_case(db, run_id, tc, "failed", 0, "执行引擎异常", None)
            case_results.append({"case_id": tc.id, "title": tc.title, "status": "failed",
                                 "error": "执行引擎异常"})
            continue

        final_status = pw_result.status if pw_result.status in ("passed", "failed") else "failed"
        if final_status == "passed":
            passed += 1
        else:
            failed += 1

        if pw_result.trace_path:
            trace_count += 1
        total_console_errors += len(pw_result.console_logs)
        total_network_errors += len(pw_result.network_errors)

        # Write RunCase + RunSteps
        _write_run_case_full(db, run_id, tc, pw_result, final_status)

        case_result_entry = {
            "case_id": tc.id,
            "title": tc.title,
            "status": final_status,
            "duration_ms": round(pw_result.duration_ms, 2),
            "error": pw_result.error_message or "",
            "trace_path": pw_result.trace_path,
            "console_error_count": len(pw_result.console_logs),
            "network_error_count": len(pw_result.network_errors),
            "screenshot_count": sum(1 for sr in pw_result.step_results if sr.screenshot_path),
            "selector_score": sel_analysis["selector_score"],
            "unstable_selectors": sel_analysis["unstable_selectors"],
            "wait_warnings": wait_analysis["wait_strategy_warnings"],
        }
        # P2-9B: retry & flaky metadata
        if retry_attempt > 0:
            case_result_entry["retry_attempt"] = retry_attempt
            case_result_entry["flaky_candidate"] = is_flaky
            if first_pw_result:
                case_result_entry["first_failure_category"] = categorize_failure(first_pw_result.error_message or "")
                case_result_entry["first_failure_screenshot"] = first_pw_result.failure_screenshot
            case_result_entry["recovered_by_retry"] = is_flaky

        case_results.append(case_result_entry)

    # 6. 更新 TestRun
    test_run.status = "passed" if failed == 0 else "failed"
    test_run.end_time = datetime.now()
    test_run.duration = (test_run.end_time - test_run.start_time).total_seconds()
    test_run.passed_cases = passed
    test_run.failed_cases = failed
    test_run.skipped_cases = skipped
    test_run.summary = json.dumps({
        "case_type": "web_ui",
        "total_cases": len(webui_cases),
        "passed_cases": passed,
        "failed_cases": failed,
        "skipped_cases": skipped,
        "trace_count": trace_count,
        "console_error_count": total_console_errors,
        "network_error_count": total_network_errors,
        # P2-9B: stability summary
        "retry_enabled": retry_enabled,
        "retry_count": retry_count if retry_enabled else 0,
        "retried_cases": retried_cases,
        "recovered_cases": recovered_cases,
        "flaky_candidate_count": flaky_candidate_count,
        "selector_low_score_count": total_selector_low_score,
        "wait_strategy_warnings": total_wait_warnings,
    }, ensure_ascii=False)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"TestRun 更新失败: {e}")

    return WebUIBatchRunResponse(
        success=True,
        run_id=run_id,
        total_cases=len(webui_cases),
        passed_cases=passed,
        failed_cases=failed,
        skipped_cases=skipped,
        trace_count=trace_count,
        console_error_count=total_console_errors,
        network_error_count=total_network_errors,
        case_results=case_results,
        summary={
            "case_type": "web_ui",
            "total_cases": len(webui_cases),
            "passed_cases": passed,
            "failed_cases": failed,
            "skipped_cases": skipped,
            "trace_count": trace_count,
            "console_error_count": total_console_errors,
            "network_error_count": total_network_errors,
            # P2-9B: stability summary
            "retry_enabled": retry_enabled,
            "retry_count": retry_count if retry_enabled else 0,
            "retried_cases": retried_cases,
            "recovered_cases": recovered_cases,
            "flaky_candidate_count": flaky_candidate_count,
            "selector_low_score_count": total_selector_low_score,
            "wait_strategy_warnings": total_wait_warnings,
        },
    )


@router.get("/traces/{filename}")
def download_trace(filename: str):
    """P2-7: 下载 trace.zip 文件 (P2-7.1 安全加固)"""
    import re
    from pathlib import Path

    # 1. 文件名安全校验: 只允许 字母/数字/下划线/连字符/点，禁止 ..
    if not re.match(r'^[A-Za-z0-9_\-\.]+$', filename):
        raise HTTPException(status_code=400, detail="非法文件名")
    if '..' in filename:
        raise HTTPException(status_code=400, detail="非法路径")

    # 2. 只允许 .zip 扩展名
    if not filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="仅允许下载 .zip 文件")

    # 3. 路径穿越防御: resolve 后必须仍在 TRACE_DIR 内
    trace_root = Path(TRACE_DIR).resolve()
    target = (trace_root / filename).resolve()
    if not str(target).startswith(str(trace_root)):
        raise HTTPException(status_code=403, detail="禁止访问目录外文件")

    # 4. 文件存在性
    if not target.is_file():
        raise HTTPException(status_code=404, detail=f"Trace 文件不存在: {filename}")

    return FileResponse(str(target), media_type="application/zip", filename=filename)


# ── P2-8: Failure Analysis ──────────────────────────────────────

@router.post("/runs/{run_id}/failure-analysis", summary="P2-8: 执行失败归因分析")
def run_failure_analysis(run_id: str, db: Session = Depends(get_db)):
    """对指定 Web UI run 执行失败归因。可重复调用，更新已有分析结果。"""
    from services.failure_analysis import analyze_run_failures, build_failure_summary

    # 1. 查找 TestRun
    test_run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not test_run:
        raise HTTPException(status_code=404, detail=f"TestRun {run_id} 不存在")

    # 2. 获取所有 RunCases
    run_cases = db.query(RunCase).filter(RunCase.run_id == run_id).all()
    if not run_cases:
        return {"success": True, "run_id": run_id, "analyses": [], "summary": {}}

    # 3. 序列化 RunCase 数据
    rc_data_list = []
    for rc in run_cases:
        rc_data_list.append({
            "test_case_id": rc.test_case_id,
            "status": rc.status,
            "error_message": rc.error_message,
            "error_type": rc.error_type,
            "request_snapshot": rc.request_snapshot or {},
            "response_snapshot": rc.response_snapshot or {},
            "assertion_details": rc.assertion_details or [],
        })

    # 4. 执行归因
    analyses = analyze_run_failures(rc_data_list, run_id)
    summary = build_failure_summary(analyses)

    # 5. 写入 TestRun.summary (合并，不覆盖原始数据)
    try:
        existing_summary = json.loads(test_run.summary) if test_run.summary else {}
    except (json.JSONDecodeError, TypeError):
        existing_summary = {}
    existing_summary["failure_analysis"] = analyses
    existing_summary["failure_analysis_summary"] = summary
    test_run.summary = json.dumps(existing_summary, ensure_ascii=False, default=str)

    # 6. 也写入每个 RunCase.response_snapshot
    analysis_map = {a["case_id"]: a for a in analyses}
    for rc in run_cases:
        if rc.test_case_id in analysis_map:
            resp = rc.response_snapshot or {}
            resp["failure_analysis"] = analysis_map[rc.test_case_id]
            rc.response_snapshot = resp

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Failure analysis commit failed: {e}")

    return {
        "success": True,
        "run_id": run_id,
        "analyses": analyses,
        "summary": summary,
    }


@router.get("/runs/{run_id}/failure-analysis", summary="P2-8: 查询失败归因结果")
def get_failure_analysis(run_id: str, db: Session = Depends(get_db)):
    """查询已有归因结果。如果没有归因结果，返回空数组。"""
    test_run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not test_run:
        raise HTTPException(status_code=404, detail=f"TestRun {run_id} 不存在")

    try:
        summary_data = json.loads(test_run.summary) if test_run.summary else {}
    except (json.JSONDecodeError, TypeError):
        summary_data = {}

    analyses = summary_data.get("failure_analysis", [])
    fa_summary = summary_data.get("failure_analysis_summary", {})

    return {
        "success": True,
        "run_id": run_id,
        "analyses": analyses,
        "summary": fa_summary,
    }


# ---------- 内部函数 ----------

def _write_run_case(db, run_id, tc, status, duration_ms, error_message, pw_result):
    """Write a minimal RunCase for exception cases."""
    try:
        rc = RunCase(
            run_id=run_id,
            test_case_id=tc.id,
            status=status,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=duration_ms / 1000 if duration_ms else 0,
            error_message=error_message,
            request_snapshot={"engine": "playwright", "batch": True},
            response_snapshot={},
        )
        db.add(rc)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"RunCase 写入失败: {e}")


def _write_run_case_full(db, run_id, tc, pw_result, final_status):
    """Write RunCase + RunSteps with full trace/console/network data."""
    try:
        steps = tc.steps or []
        assertions = tc.assertions or []
        a_passed = sum(1 for a in pw_result.assertion_results if a.passed)
        a_failed = sum(1 for a in pw_result.assertion_results if not a.passed)
        assertion_details = [
            {"type": a.type, "value": a.value, "target": a.target, "passed": a.passed,
             "actual": a.actual, "error_message": a.error_message, "description": a.description}
            for a in pw_result.assertion_results
        ]

        start_time = datetime.fromisoformat(pw_result.started_at) if pw_result.started_at else datetime.now()
        end_time = datetime.fromisoformat(pw_result.finished_at) if pw_result.finished_at else datetime.now()

        rc = RunCase(
            run_id=run_id,
            test_case_id=tc.id,
            status=final_status,
            start_time=start_time,
            end_time=end_time,
            duration=pw_result.duration_ms / 1000,
            error_message=pw_result.error_message or None,
            request_snapshot={"engine": "playwright", "batch": True,
                              "steps_count": len(steps), "assertions_count": len(assertions)},
            response_snapshot={
                "screenshots": [sr.screenshot_path for sr in pw_result.step_results if sr.screenshot_path],
                "failure_screenshot": pw_result.failure_screenshot,
                "visual_results": pw_result.visual_results,
                "trace_path": pw_result.trace_path,
                "console_error_count": len(pw_result.console_logs),
                "console_logs": pw_result.console_logs[:20],
                "network_error_count": len(pw_result.network_errors),
                "network_errors": pw_result.network_errors[:20],
            },
            assertions_passed=a_passed,
            assertions_failed=a_failed,
            assertion_details=assertion_details,
        )
        db.add(rc)
        db.flush()

        # Write RunSteps
        for sr in pw_result.step_results:
            step_target = sr.target
            step_value = sr.value
            if sr.action == "eval_js":
                step_target = (sr.target[:50] + "…") if len(sr.target) > 50 else sr.target
                step_value = "[JS]"
            elif sr.action == "save_cookies":
                step_value = "[cookie_data]"
            run_step = RunStep(
                run_case_id=rc.id,
                step_name=f"{sr.action}: {step_target or step_value or sr.description}",
                step_order=sr.step_index,
                status=sr.status,
                start_time=start_time,
                end_time=end_time,
                duration=sr.duration_ms / 1000,
                input_snapshot={
                    "action": sr.action,
                    "target": step_target,
                    "value": step_value,
                    "description": sr.description,
                },
                output_snapshot={
                    "current_url": sr.current_url,
                    "screenshot_path": sr.screenshot_path,
                },
                error_message=sr.error_message or None,
                error_type="step_error" if sr.status == "failed" else None,
            )
            db.add(run_step)

        # Assertions as steps
        for i, ar in enumerate(pw_result.assertion_results):
            run_step = RunStep(
                run_case_id=rc.id,
                step_name=f"assert:{ar.type} — {ar.description or ar.value}",
                step_order=len(pw_result.step_results) + i,
                status="passed" if ar.passed else "failed",
                start_time=start_time,
                end_time=end_time,
                duration=0,
                input_snapshot={
                    "type": ar.type, "target": ar.target,
                    "value": ar.value, "description": ar.description,
                },
                output_snapshot={"actual": ar.actual, "passed": ar.passed},
                error_message=ar.error_message or None,
                error_type="assertion_error" if not ar.passed else None,
            )
            db.add(run_step)

        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"RunCase/RunSteps 写入失败: {e}")
