#!/usr/bin/env python3
"""
P2-6B API 性能测试 MVP

使用 requests + ThreadPoolExecutor 并发执行 API 用例，统计 QPS / 响应时间 / 错误率等指标。
"""
import os
import time
import logging
import statistics
import threading
import concurrent.futures
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests as req_lib

logger = logging.getLogger(__name__)

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
MAX_CONCURRENCY = 50
MAX_DURATION = 300
MAX_FAILURE_SAMPLES = 20


@dataclass
class PerformanceConfig:
    """性能测试配置"""
    project_id: int = 1
    case_ids: List[str] = field(default_factory=list)
    concurrency: int = 5
    duration_seconds: int = 30
    ramp_up_seconds: int = 0
    think_time_ms: int = 0
    thresholds: Dict[str, float] = field(default_factory=dict)
    allow_unsafe_methods: bool = False

    def validate(self) -> List[str]:
        errors = []
        if not self.case_ids:
            errors.append("case_ids 不能为空")
        if self.concurrency < 1:
            errors.append("concurrency 最小为 1")
        if self.concurrency > MAX_CONCURRENCY:
            errors.append(f"concurrency 最大为 {MAX_CONCURRENCY}")
        if self.duration_seconds < 1:
            errors.append("duration_seconds 最小为 1")
        if self.duration_seconds > MAX_DURATION:
            errors.append(f"duration_seconds 最大为 {MAX_DURATION}")
        if self.ramp_up_seconds > self.duration_seconds:
            errors.append("ramp_up_seconds 不能大于 duration_seconds")
        return errors


@dataclass
class RequestRecord:
    """单次请求记录"""
    case_id: str
    method: str
    url: str
    status_code: int
    duration_ms: float
    success: bool
    error: str = ""
    timestamp: float = 0.0


@dataclass
class PerformanceSummary:
    """性能测试结果摘要"""
    total_requests: int = 0
    success_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0
    min_response_time_ms: float = 0
    max_response_time_ms: float = 0
    p50_ms: float = 0
    p95_ms: float = 0
    p99_ms: float = 0
    qps: float = 0
    error_rate: float = 0
    threshold_passed: bool = True
    threshold_failures: List[Dict[str, Any]] = field(default_factory=list)
    failure_samples: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0
    concurrency: int = 0
    case_count: int = 0

    def to_dict(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "success_requests": self.success_requests,
            "failed_requests": self.failed_requests,
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "min_response_time_ms": round(self.min_response_time_ms, 2),
            "max_response_time_ms": round(self.max_response_time_ms, 2),
            "p50_ms": round(self.p50_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "qps": round(self.qps, 2),
            "error_rate": round(self.error_rate, 4),
            "threshold_passed": self.threshold_passed,
            "threshold_failures": self.threshold_failures,
            "failure_samples": self.failure_samples[:MAX_FAILURE_SAMPLES],
            "duration_seconds": round(self.duration_seconds, 2),
            "concurrency": self.concurrency,
            "case_count": self.case_count,
        }


def _percentile(sorted_data: List[float], p: float) -> float:
    """Calculate percentile from sorted data."""
    if not sorted_data:
        return 0
    k = (len(sorted_data) - 1) * (p / 100)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def _build_request_params(case_config: dict, base_url: str) -> dict:
    """Build requests parameters from a test case execution_config."""
    method = (case_config.get("method") or "GET").upper()
    url_path = case_config.get("url", "/")
    if url_path.startswith(("http://", "https://")):
        full_url = url_path
    else:
        full_url = f"{base_url.rstrip('/')}/{url_path.lstrip('/')}"

    headers = case_config.get("headers") or {}
    params = case_config.get("query_params") or {}
    body = case_config.get("body")
    timeout = case_config.get("timeout", 30)

    req = {
        "method": method,
        "url": full_url,
        "headers": headers,
        "params": params,
        "timeout": timeout,
        "verify": False,
    }
    if body and method in ("POST", "PUT", "PATCH"):
        req["json"] = body
    return req


def _worker_loop(
    worker_id: int,
    cases: List[dict],
    base_url: str,
    session: req_lib.Session,
    records: list,
    stop_event: threading.Event,
    think_time_ms: int,
    ramp_delay: float,
):
    """Single worker thread that loops through cases until stop_event is set."""
    if ramp_delay > 0:
        time.sleep(ramp_delay)

    case_idx = 0
    while not stop_event.is_set():
        case = cases[case_idx % len(cases)]
        case_id = case["id"]
        cfg = case.get("execution_config") or {}
        req_params = _build_request_params(cfg, base_url)

        t0 = time.time()
        record = RequestRecord(
            case_id=case_id,
            method=req_params["method"],
            url=req_params["url"],
            status_code=0,
            duration_ms=0,
            success=False,
            timestamp=t0,
        )
        try:
            resp = session.request(**req_params)
            record.status_code = resp.status_code
            record.duration_ms = (time.time() - t0) * 1000
            record.success = 200 <= resp.status_code < 400
            if not record.success:
                record.error = f"HTTP {resp.status_code}"
        except req_lib.exceptions.Timeout:
            record.duration_ms = (time.time() - t0) * 1000
            record.error = "timeout"
        except Exception as e:
            record.duration_ms = (time.time() - t0) * 1000
            record.error = str(e)[:200]

        records.append(record)
        case_idx += 1

        if think_time_ms > 0 and not stop_event.is_set():
            time.sleep(think_time_ms / 1000)


def _run_performance(
    cases: List[dict],
    base_url: str,
    config: PerformanceConfig,
) -> PerformanceSummary:
    """Core performance runner using threads."""
    records: list = []
    stop_event = threading.Event()
    ramp_interval = config.ramp_up_seconds / config.concurrency if config.ramp_up_seconds > 0 else 0

    session = req_lib.Session()
    threads = []
    for i in range(config.concurrency):
        ramp_delay = i * ramp_interval
        t = threading.Thread(
            target=_worker_loop,
            args=(i, cases, base_url, session, records, stop_event,
                  config.think_time_ms, ramp_delay),
            daemon=True,
        )
        threads.append(t)
        t.start()

    time.sleep(config.duration_seconds)
    stop_event.set()

    for t in threads:
        t.join(timeout=5)

    session.close()
    return _compute_summary(records, config)


def _compute_summary(records: List[RequestRecord], config: PerformanceConfig) -> PerformanceSummary:
    """Compute statistics from request records."""
    summary = PerformanceSummary(
        concurrency=config.concurrency,
        case_count=len(config.case_ids),
    )

    if not records:
        return summary

    summary.total_requests = len(records)
    summary.success_requests = sum(1 for r in records if r.success)
    summary.failed_requests = summary.total_requests - summary.success_requests

    durations = sorted([r.duration_ms for r in records])
    summary.avg_response_time_ms = statistics.mean(durations)
    summary.min_response_time_ms = durations[0]
    summary.max_response_time_ms = durations[-1]
    summary.p50_ms = _percentile(durations, 50)
    summary.p95_ms = _percentile(durations, 95)
    summary.p99_ms = _percentile(durations, 99)

    # QPS
    if records:
        time_span = max(r.timestamp for r in records) - min(r.timestamp for r in records)
        summary.duration_seconds = max(time_span, 0.001)
        summary.qps = summary.total_requests / summary.duration_seconds

    summary.error_rate = summary.failed_requests / summary.total_requests if summary.total_requests > 0 else 0

    # Failure samples
    failures = [r for r in records if not r.success]
    summary.failure_samples = [
        {"case_id": r.case_id, "method": r.method, "url": r.url,
         "status_code": r.status_code, "error": r.error,
         "duration_ms": round(r.duration_ms, 2)}
        for r in failures[:MAX_FAILURE_SAMPLES]
    ]

    # Threshold checks
    _check_thresholds(summary, config.thresholds)

    return summary


def _check_thresholds(summary: PerformanceSummary, thresholds: Dict[str, float]):
    """Check performance thresholds."""
    if not thresholds:
        return

    metric_map = {
        "p95_ms": summary.p95_ms,
        "p99_ms": summary.p99_ms,
        "avg_ms": summary.avg_response_time_ms,
        "error_rate": summary.error_rate,
        "max_ms": summary.max_response_time_ms,
    }

    for metric, expected in thresholds.items():
        actual = metric_map.get(metric)
        if actual is None:
            continue
        passed = actual <= expected
        if not passed:
            summary.threshold_passed = False
            summary.threshold_failures.append({
                "metric": metric,
                "actual": round(actual, 4),
                "expected": expected,
                "status": "failed",
            })


def run_performance_test(
    cases: List[dict],
    base_url: str,
    config: PerformanceConfig,
) -> PerformanceSummary:
    """
    Synchronous entry point for running performance tests.
    Uses threads for concurrency with requests library.
    """
    logger.info(f"P2-6B: Starting performance test — {len(cases)} cases, "
                f"concurrency={config.concurrency}, duration={config.duration_seconds}s, "
                f"base_url={base_url}")

    return _run_performance(cases, base_url, config)
