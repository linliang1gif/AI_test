# -*- coding: utf-8 -*-
"""
P3-1: CI/CD 质量门禁服务
接收 test_run / suite_summary / run_cases，计算 gate_status 并生成 gate_failures。
"""
import json
import logging
from typing import Optional
from sqlalchemy.orm import Session

from database.models import TestRun, RunCase, TestCase

logger = logging.getLogger(__name__)

DEFAULT_GATE_CONFIG = {
    "fail_on_any_failed": True,
    "fail_on_p0_failed": True,
    "max_api_failures": 0,
    "max_web_ui_failures": 0,
    "max_visual_failures": 0,
    "performance_must_pass": True,
    "skip_policy": "warn",      # warn | fail
    "xfail_policy": "warn",     # warn | fail
}


class QualityGateService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def evaluate(self, run_id: str, gate_config: dict = None) -> dict:
        """
        Evaluate quality gate for a given test run.
        Returns gate_summary dict with gate_status, gate_failures, etc.
        """
        cfg = {**DEFAULT_GATE_CONFIG, **(gate_config or {})}

        if self.db:
            return self._evaluate_from_db(run_id, cfg)
        else:
            raise ValueError("DB session required for gate evaluation")

    def evaluate_from_summary(self, suite_summary: dict, case_results: list = None, gate_config: dict = None) -> dict:
        """
        Evaluate quality gate from suite_summary + case_results without DB.
        Used by CLI scripts that already have the data.
        """
        cfg = {**DEFAULT_GATE_CONFIG, **(gate_config or {})}
        return self._apply_rules(suite_summary, case_results or [], cfg)

    def _evaluate_from_db(self, run_id: str, cfg: dict) -> dict:
        test_run = self.db.query(TestRun).filter(TestRun.id == run_id).first()
        if not test_run:
            return {
                "gate_status": "error",
                "message": f"TestRun {run_id} not found",
                "gate_failures": [{"rule": "run_not_found", "message": f"TestRun {run_id} 不存在", "severity": "blocker"}],
            }

        # Parse suite_summary from test_run.summary
        suite_summary = {}
        try:
            raw = json.loads(test_run.summary or "{}") if isinstance(test_run.summary, str) else (test_run.summary or {})
            suite_summary = raw.get("suite_summary", {})
        except Exception:
            pass

        # If no suite_summary, build minimal one from test_run fields
        if not suite_summary:
            suite_summary = {
                "total_cases": test_run.total_cases,
                "passed_cases": test_run.passed_cases,
                "failed_cases": test_run.failed_cases,
                "skipped_cases": test_run.skipped_cases,
            }

        # Get case results from DB
        run_cases = self.db.query(RunCase).filter(RunCase.run_id == run_id).all()
        case_results = []
        for rc in run_cases:
            tc = rc.test_case
            case_results.append({
                "case_id": rc.test_case_id,
                "status": rc.status,
                "case_type": getattr(tc, "case_type", "api") if tc else "api",
                "priority": getattr(tc, "priority", "medium") if tc else "medium",
                "error_message": rc.error_message,
                "error_type": rc.error_type,
            })

        result = self._apply_rules(suite_summary, case_results, cfg)
        result["run_id"] = run_id
        result["trigger_type"] = test_run.trigger_type
        return result

    def _apply_rules(self, suite_summary: dict, case_results: list, cfg: dict) -> dict:
        failures = []
        warnings = []

        total = suite_summary.get("total_cases", 0)
        passed = suite_summary.get("passed_cases", 0)
        failed = suite_summary.get("failed_cases", 0)
        skipped = suite_summary.get("skipped_cases", 0)
        xfail = suite_summary.get("xfail_cases", 0)

        # Rule 1: fail_on_any_failed
        if cfg.get("fail_on_any_failed") and failed > 0:
            failures.append({
                "rule": "fail_on_any_failed",
                "message": f"存在 {failed} 条失败用例",
                "severity": "blocker",
            })

        # Rule 2: fail_on_p0_failed — check critical/P0 priority cases
        if cfg.get("fail_on_p0_failed"):
            p0_failed = [c for c in case_results if c.get("status") == "failed" and c.get("priority") in ("critical", "P0")]
            if p0_failed:
                failures.append({
                    "rule": "fail_on_p0_failed",
                    "message": f"存在 {len(p0_failed)} 条 P0/critical 用例失败",
                    "severity": "blocker",
                    "cases": [c.get("case_id") for c in p0_failed],
                })

        # Rule 3: max_api_failures
        max_api = cfg.get("max_api_failures", 0)
        api_failed = [c for c in case_results if c.get("status") == "failed" and c.get("case_type") == "api"]
        if len(api_failed) > max_api:
            failures.append({
                "rule": "max_api_failures",
                "message": f"API 用例失败 {len(api_failed)} 条，超过阈值 {max_api}",
                "severity": "blocker",
            })

        # Rule 4: max_web_ui_failures
        max_webui = cfg.get("max_web_ui_failures", 0)
        webui_failed = [c for c in case_results if c.get("status") == "failed" and c.get("case_type") == "web_ui"]
        if len(webui_failed) > max_webui:
            failures.append({
                "rule": "max_web_ui_failures",
                "message": f"Web UI 用例失败 {len(webui_failed)} 条，超过阈值 {max_webui}",
                "severity": "blocker",
            })

        # Rule 5: max_visual_failures
        max_vis = cfg.get("max_visual_failures", 0)
        vis_failed = [c for c in case_results if c.get("status") == "failed" and c.get("case_type") == "visual"]
        if len(vis_failed) > max_vis:
            failures.append({
                "rule": "max_visual_failures",
                "message": f"Visual 用例失败 {len(vis_failed)} 条，超过阈值 {max_vis}",
                "severity": "blocker",
            })

        # Rule 6: performance_must_pass
        if cfg.get("performance_must_pass"):
            perf_failed = [c for c in case_results if c.get("status") == "failed" and c.get("case_type") == "performance"]
            if perf_failed:
                failures.append({
                    "rule": "performance_must_pass",
                    "message": f"性能用例失败 {len(perf_failed)} 条",
                    "severity": "blocker",
                })

        # Rule 7: skip_policy
        if skipped > 0:
            skip_policy = cfg.get("skip_policy", "warn")
            entry = {
                "rule": "skip_policy",
                "message": f"存在 {skipped} 条跳过用例 (policy={skip_policy})",
                "severity": "warning" if skip_policy == "warn" else "blocker",
            }
            if skip_policy == "fail":
                failures.append(entry)
            else:
                warnings.append(entry)

        # Rule 8: xfail_policy
        if xfail > 0:
            xfail_policy = cfg.get("xfail_policy", "warn")
            entry = {
                "rule": "xfail_policy",
                "message": f"存在 {xfail} 条预期失败用例 (policy={xfail_policy})",
                "severity": "warning" if xfail_policy == "warn" else "blocker",
            }
            if xfail_policy == "fail":
                failures.append(entry)
            else:
                warnings.append(entry)

        # Rule 9 (P3-2): data_missing — check data_summary for missing variables
        data_summary = suite_summary.get("data_summary", {})
        missing_vars = data_summary.get("missing_variables", 0)
        binding_errors = data_summary.get("data_binding_errors", 0)
        if missing_vars > 0 or binding_errors > 0:
            entry = {
                "rule": "data_missing",
                "message": f"数据缺失: {missing_vars} 个变量未解析, {binding_errors} 个绑定错误",
                "severity": "warning",
                "missing_variable_names": data_summary.get("missing_variable_names", []),
            }
            warnings.append(entry)

        # Rule 10 (P3-3A): data_validation_failed
        validation_errors = data_summary.get("data_validation_errors", 0)
        if validation_errors > 0:
            dv_policy = cfg.get("data_validation_policy", "fail")
            entry = {
                "rule": "data_validation_failed",
                "message": f"数据校验失败: {validation_errors} 个错误",
                "severity": "blocker" if dv_policy == "fail" else "warning",
                "details": data_summary.get("data_validation_messages", []),
            }
            if dv_policy == "fail":
                failures.append(entry)
            else:
                warnings.append(entry)

        # Rule 11 (P3-3A): cleanup_failed
        cleanup_failed = data_summary.get("cleanup_failed", 0)
        if cleanup_failed > 0:
            cf_policy = cfg.get("cleanup_failure_policy", "warn")
            entry = {
                "rule": "cleanup_failed",
                "message": f"清理失败: {cleanup_failed} 个清理操作失败",
                "severity": "blocker" if cf_policy == "fail" else "warning",
            }
            if cf_policy == "fail":
                failures.append(entry)
            else:
                warnings.append(entry)

        gate_status = "failed" if failures else "passed"

        return {
            "gate_status": gate_status,
            "total_cases": total,
            "passed_cases": passed,
            "failed_cases": failed,
            "skipped_cases": skipped,
            "xfail_cases": xfail,
            "gate_failures": failures,
            "gate_warnings": warnings,
            "gate_config": cfg,
        }
