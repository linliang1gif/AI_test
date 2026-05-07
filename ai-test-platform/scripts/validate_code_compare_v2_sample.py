# -*- coding: utf-8 -*-
"""D1 真实项目验证 - finding 评审表导出 + 评分 + TAPD/看板只读观察

使用：
    python scripts/validate_code_compare_v2_sample.py --export rpt_ebc532452984
    python scripts/validate_code_compare_v2_sample.py --score  rpt_ebc532452984
    python scripts/validate_code_compare_v2_sample.py --observe-tapd      rpt_ebc532452984
    python scripts/validate_code_compare_v2_sample.py --observe-dashboard rpt_ebc532452984

模式：
    --export             读取 report，按抽样规则导出 findings_review.{md,csv} +
                         findings_review_full.csv 至 data/validation_samples/<REPORT_ID>/
    --score              读人工填好 findings_review.csv，计算 Precision / FP_Rate /
                         Manual_Review_Pass_Rate，写 score_summary.json
    --observe-tapd       只读观察：调 GET /api/v2/code-compare/reports/<id>，
                         统计已推 finding 的 tapd_* 字段填充情况，写 tapd_observation.json
                         **不调用** sync 端点、**不创建**新 bug
    --observe-dashboard  只读观察：调 dashboard / analytics / defect-summary 接口，
                         记录看板能力边界，写 dashboard_observation.json

抽样规则（仅 --export）：
    - finding 数 ≤ --sample-size（默认 30）：全量
    - finding 数 >  --sample-size：分层抽样 + 强制纳入所有 tapd_bug_id 非空的 finding
    - 不足 target 时第二轮随机补足

约束：
    - 仅 Python stdlib
    - Windows 控制台兼容（utf-8）
    - 不使用 emoji，统一使用 [OK]/[WARN]/[FAIL]/[SKIP]
    - 不调用 AI、不调用 TAPD 写接口、不创建 / 修改任何业务数据
"""
import argparse
import csv
import io
import json
import os
import random
import sys
from pathlib import Path
from urllib import request as urlreq
from urllib.error import HTTPError, URLError

# ── Windows 控制台 UTF-8 兼容 ─────────────────────────
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "data" / "code_compare" / "reports"
SAMPLES_DIR = ROOT / "data" / "validation_samples"

# 评审表字段（顺序影响 CSV 列序）
REVIEW_COLUMNS = [
    "finding_id",
    "type",
    "severity",
    "title",
    "requirement_text",
    "code_evidence",
    "evidence_snippet",
    "engine_judgement",
    "tapd_bug_id",
    "tapd_url",
    "tapd_status",
    # ↓ 人工填写
    "human_review_result",
    "human_comment",
    "should_convert_to_defect",
    "should_push_tapd",
]

VALID_REVIEW = {"valid", "false_positive", "uncertain"}
VALID_YESNO = {"yes", "no"}

# 抽样类型权重（数值越大占比越大）
TYPE_WEIGHTS = {
    "risk": 3,
    "inconsistent": 3,
    "missing": 2,
    "uncertain": 1,
    "implemented": 1,
    "extra": 1,
}


def log(level: str, msg: str) -> None:
    print(f"[{level}] {msg}", flush=True)


# ──────────────────────────────────────────────────────
# 数据加载
# ──────────────────────────────────────────────────────
def load_report(report_id: str, backend_url: str = None) -> dict:
    """优先从文件读取；如果文件不存在或显式指定 --backend-url 则走 API。"""
    fpath = REPORTS_DIR / f"{report_id}.json"

    if backend_url:
        url = f"{backend_url.rstrip('/')}/api/v2/code-compare/reports/{report_id}"
        log("OK", f"从 API 读取: {url}")
        try:
            with urlreq.urlopen(url, timeout=10) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                return payload.get("report") or payload
        except (URLError, HTTPError) as e:
            log("FAIL", f"API 不可达: {e}")
            sys.exit(2)

    if not fpath.exists():
        log("FAIL", f"报告文件不存在: {fpath}")
        log("WARN", "可加 --backend-url http://127.0.0.1:8001 从 API 拉取")
        sys.exit(2)

    log("OK", f"从文件读取: {fpath}")
    return json.loads(fpath.read_text(encoding="utf-8"))


# ──────────────────────────────────────────────────────
# 字段抽取（兼容 dict / list / None）
# ──────────────────────────────────────────────────────
def _truncate(s, n: int) -> str:
    if not s:
        return ""
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def _flatten_code_evidence(ev) -> str:
    if not ev:
        return ""
    if isinstance(ev, dict):
        ev = [ev]
    if not isinstance(ev, list):
        return _truncate(str(ev), 200)
    parts = []
    for item in ev:
        if not isinstance(item, dict):
            parts.append(_truncate(str(item), 80))
            continue
        f = item.get("file") or ""
        line = item.get("line") or ""
        ci = item.get("code_item") or ""
        seg = f
        if line:
            seg = f"{seg}:{line}"
        if ci:
            seg = f"{seg}#{ci}"
        if seg:
            parts.append(seg)
    return _truncate(" | ".join(parts), 200)


def _extract_snippet(finding: dict) -> str:
    snip = finding.get("evidence_snippet")
    if snip:
        return _truncate(snip, 240)
    ev = finding.get("code_evidence")
    if isinstance(ev, dict):
        snip = ev.get("snippet") or ev.get("evidence")
        if snip:
            return _truncate(snip, 240)
    elif isinstance(ev, list) and ev:
        first = ev[0] if isinstance(ev[0], dict) else {}
        snip = first.get("snippet") or first.get("evidence")
        if snip:
            return _truncate(snip, 240)
    return ""


def _engine_judgement(f: dict) -> str:
    parts = [
        f"type={f.get('type', '?')}",
        f"risk={f.get('risk_level', '?')}",
        f"conf={f.get('confidence', '?')}",
    ]
    analysis = f.get("analysis") or ""
    if analysis:
        parts.append(f"analysis: {_truncate(analysis, 120)}")
    return "; ".join(parts)


def _row_for_finding(f: dict) -> dict:
    return {
        "finding_id": f.get("finding_id", "") or "",
        "type": f.get("type", "") or "",
        "severity": f.get("risk_level", "") or "",
        "title": _truncate(f.get("requirement", ""), 60),
        "requirement_text": _truncate(f.get("requirement", ""), 500),
        "code_evidence": _flatten_code_evidence(f.get("code_evidence")),
        "evidence_snippet": _extract_snippet(f),
        "engine_judgement": _engine_judgement(f),
        "tapd_bug_id": f.get("tapd_bug_id", "") or "",
        "tapd_url": f.get("tapd_url", "") or "",
        "tapd_status": f.get("tapd_status_name") or f.get("tapd_status") or "",
        "human_review_result": "",
        "human_comment": "",
        "should_convert_to_defect": "",
        "should_push_tapd": "",
    }


# ──────────────────────────────────────────────────────
# 抽样
# ──────────────────────────────────────────────────────
def stratified_sample(findings: list, target: int = 30, seed: int = 42) -> tuple:
    """分层抽样 + 强制纳入所有 tapd_bug_id 非空的 finding。

    返回 (sampled_list, strategy_str)
    """
    rng = random.Random(seed)

    forced = [f for f in findings if f.get("tapd_bug_id")]
    forced_ids = {f.get("finding_id") for f in forced}
    rest = [f for f in findings if f.get("finding_id") not in forced_ids]

    by_type = {}
    for f in rest:
        by_type.setdefault(f.get("type", "unknown"), []).append(f)

    remain = max(0, target - len(forced))
    total_w = sum(
        TYPE_WEIGHTS.get(t, 1) for t, items in by_type.items() if items
    )

    sampled = list(forced)
    sampled_ids = set(forced_ids)

    # 第一轮：按 type 分层抽，share 受 type 实际可用数量限制
    if remain > 0 and total_w > 0:
        for t, items in by_type.items():
            if not items:
                continue
            w = TYPE_WEIGHTS.get(t, 1)
            share = max(1, round(remain * w / total_w))
            share = min(share, len(items))
            if share > 0:
                picked = rng.sample(items, share)
                sampled.extend(picked)
                sampled_ids.update(p.get("finding_id") for p in picked)

    # 第二轮：若总数仍 < target，从剩余 rest 中随机补足
    short = target - len(sampled)
    if short > 0:
        leftover = [f for f in rest if f.get("finding_id") not in sampled_ids]
        topup = min(short, len(leftover))
        if topup > 0:
            sampled.extend(rng.sample(leftover, topup))

    strategy = (
        f"分层抽样 target={target}, "
        f"forced(tapd_bug_id非空)={len(forced)}, "
        f"rest={len(rest)}, sampled={len(sampled)}, seed={seed}"
    )
    return sampled, strategy


# ──────────────────────────────────────────────────────
# 命令：--export
# ──────────────────────────────────────────────────────
def cmd_export(report_id: str, target_sample: int, backend_url: str) -> int:
    log("OK", f"开始导出 report={report_id}")
    report = load_report(report_id, backend_url=backend_url)
    findings = report.get("findings") or []
    if not findings:
        log("FAIL", "report.findings 为空")
        return 2

    total = len(findings)
    log("OK", f"原始 finding 总数 = {total}")

    out_dir = SAMPLES_DIR / report_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── 全量 CSV（参考与可追溯）──
    full_csv = out_dir / "findings_review_full.csv"
    rows_full = [_row_for_finding(f) for f in findings]
    _write_csv(full_csv, rows_full)
    log("OK", f"全量 CSV: {full_csv} ({len(rows_full)} 行)")

    # ── 抽样 ──
    if total <= target_sample:
        sampled = findings
        strategy = f"全量 ({total} <= {target_sample})"
    else:
        sampled, strategy = stratified_sample(findings, target=target_sample)
    log("OK", f"抽样策略: {strategy}")

    rows = [_row_for_finding(f) for f in sampled]

    # ── 评审 CSV（人工填写）──
    csv_path = out_dir / "findings_review.csv"
    _write_csv(csv_path, rows)
    log("OK", f"评审 CSV: {csv_path} ({len(rows)} 行)")

    # ── 评审说明 MD ──
    md_path = out_dir / "findings_review.md"
    md_text = _build_review_md(report_id, total, rows, strategy)
    md_path.write_text(md_text, encoding="utf-8")
    log("OK", f"评审说明 MD: {md_path}")

    # ── 摘要 ──
    by_type = {}
    for r in rows:
        by_type[r["type"]] = by_type.get(r["type"], 0) + 1

    summary = {
        "report_id": report_id,
        "total_findings": total,
        "sampled_findings": len(rows),
        "sample_strategy": strategy,
        "sample_by_type": by_type,
        "tapd_pushed_in_sample": sum(1 for r in rows if r["tapd_bug_id"]),
        "csv_path": str(csv_path),
        "md_path": str(md_path),
        "full_csv_path": str(full_csv),
    }

    print()
    print("=" * 70)
    print("EXPORT SUMMARY")
    print("=" * 70)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _write_csv(path: Path, rows: list) -> None:
    # utf-8-sig 让 Excel 正确识别中文
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _build_review_md(report_id: str, total: int, rows: list, strategy: str) -> str:
    lines = []
    lines.append(f"# Finding 评审表 — {report_id}")
    lines.append("")
    lines.append(f"- 原始 finding 总数：**{total}**")
    lines.append(f"- 抽样数量：**{len(rows)}**")
    lines.append(f"- 抽样策略：{strategy}")
    lines.append(f"- 全量 CSV（仅参考，**不要在此填写**）：`findings_review_full.csv`")
    lines.append(f"- 评审 CSV（**实际填写在这里**）：`findings_review.csv`")
    lines.append("")
    lines.append("## 人工填写说明")
    lines.append("")
    lines.append("打开 `findings_review.csv`（建议 Excel / Numbers 打开，或 VSCode CSV Edit 插件），逐行填以下 4 列：")
    lines.append("")
    lines.append("| 列 | 取值 | 说明 |")
    lines.append("|---|---|---|")
    lines.append("| `human_review_result` | `valid` / `false_positive` / `uncertain` | 必填 |")
    lines.append("| `human_comment` | 1-2 句话（即使不写理由也填 `-`） | 必填 |")
    lines.append("| `should_convert_to_defect` | `yes` / `no` | 必填 |")
    lines.append("| `should_push_tapd` | `yes` / `no` | 必填 |")
    lines.append("")
    lines.append("填完后跑：")
    lines.append("")
    lines.append("```")
    lines.append(f"python scripts/validate_code_compare_v2_sample.py --score {report_id}")
    lines.append("```")
    lines.append("")
    lines.append("将自动计算 Precision / False_Positive_Rate / Manual_Review_Pass_Rate，")
    lines.append("写到 `score_summary.json`。**Recall 当前无法可靠计算，需要完整人工标注的需求-代码映射基准集**。")
    lines.append("")
    lines.append("## 抽样 finding 速览")
    lines.append("")
    lines.append("| # | finding_id | type | severity | title | tapd_bug_id |")
    lines.append("|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        title_md = (r["title"] or "").replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {i} | `{r['finding_id']}` | {r['type']} | {r['severity']} | "
            f"{title_md} | {r['tapd_bug_id'] or '-'} |"
        )
    lines.append("")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────
# 命令：--score
# ──────────────────────────────────────────────────────
def cmd_score(report_id: str) -> int:
    out_dir = SAMPLES_DIR / report_id
    csv_path = out_dir / "findings_review.csv"
    if not csv_path.exists():
        log("FAIL", f"评审 CSV 不存在: {csv_path}（先跑 --export）")
        return 2

    log("OK", f"读取 {csv_path}")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    total = len(rows)
    if total == 0:
        log("FAIL", "CSV 为空")
        return 2

    counts = {"valid": 0, "false_positive": 0, "uncertain": 0, "blank": 0, "invalid": 0}
    uncertain_acceptable = 0
    convert_yes = 0
    push_yes = 0
    bad_rows = []

    for i, r in enumerate(rows, 1):
        v = (r.get("human_review_result") or "").strip().lower()
        if not v:
            counts["blank"] += 1
            bad_rows.append((i, r.get("finding_id", "?"), "human_review_result 为空"))
            continue
        if v not in VALID_REVIEW:
            counts["invalid"] += 1
            bad_rows.append(
                (i, r.get("finding_id", "?"), f"human_review_result={v!r} 非法")
            )
            continue
        counts[v] += 1
        if v == "uncertain" and (r.get("should_convert_to_defect") or "").strip().lower() == "yes":
            uncertain_acceptable += 1
        if (r.get("should_convert_to_defect") or "").strip().lower() == "yes":
            convert_yes += 1
        if (r.get("should_push_tapd") or "").strip().lower() == "yes":
            push_yes += 1

    reviewed = counts["valid"] + counts["false_positive"] + counts["uncertain"]

    if reviewed == 0:
        log("FAIL", "没有任何已评审行（human_review_result 全空）")
        for i, fid, msg in bad_rows[:5]:
            print(f"  row {i} ({fid}): {msg}")
        return 2

    if counts["blank"] > 0:
        log("WARN", f"{counts['blank']} 行 human_review_result 为空，已从指标分母排除")
    if counts["invalid"] > 0:
        log("WARN", f"{counts['invalid']} 行取值非法，已排除")

    precision = counts["valid"] / reviewed
    fp_rate = counts["false_positive"] / reviewed
    pass_rate = (counts["valid"] + uncertain_acceptable) / reviewed

    summary = {
        "report_id": report_id,
        "csv_path": str(csv_path),
        "totals": {
            "rows_in_csv": total,
            "reviewed": reviewed,
            "blank": counts["blank"],
            "invalid": counts["invalid"],
        },
        "counts": {
            "valid": counts["valid"],
            "false_positive": counts["false_positive"],
            "uncertain": counts["uncertain"],
            "uncertain_acceptable": uncertain_acceptable,
            "convert_yes": convert_yes,
            "push_yes": push_yes,
        },
        "metrics": {
            "Precision": round(precision, 4),
            "False_Positive_Rate": round(fp_rate, 4),
            "Manual_Review_Pass_Rate": round(pass_rate, 4),
            "Recall": "N/A (need ground-truth requirement-code mapping)",
        },
        "definitions": {
            "Precision": "valid / reviewed",
            "False_Positive_Rate": "false_positive / reviewed",
            "Manual_Review_Pass_Rate": "(valid + uncertain_acceptable) / reviewed",
            "uncertain_acceptable": "uncertain AND should_convert_to_defect=yes",
        },
    }

    out_path = out_dir / "score_summary.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    log("OK", f"score_summary 写入: {out_path}")

    print()
    print("=" * 70)
    print("SCORE SUMMARY")
    print("=" * 70)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


# ──────────────────────────────────────────────────────
# 命令：--observe-tapd
# ──────────────────────────────────────────────────────
TAPD_FIELDS = (
    "tapd_bug_id", "tapd_url", "tapd_pushed_at",
    "tapd_status", "tapd_status_name", "tapd_last_sync_at", "tapd_modified",
)


def _mask_tapd_url(u: str) -> str:
    if not u:
        return ""
    return u.replace("https://www.tapd.cn/", "https://***.tapd.cn/")


def cmd_observe_tapd(report_id: str, backend_url: str) -> int:
    if not backend_url:
        backend_url = "http://127.0.0.1:8001"
    url = f"{backend_url.rstrip('/')}/api/v2/code-compare/reports/{report_id}"
    log("OK", f"GET {url}")
    try:
        with urlreq.urlopen(url, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (URLError, HTTPError) as e:
        log("FAIL", f"API 不可达: {e}")
        return 2
    report = payload.get("report") or payload
    findings = report.get("findings") or []

    pushed = [f for f in findings if f.get("tapd_bug_id")]
    log("OK", f"all_findings={len(findings)}, pushed_to_tapd={len(pushed)}")

    records = []
    for f in pushed:
        rec = {k: f.get(k) for k in TAPD_FIELDS}
        rec["finding_id"] = f.get("finding_id")
        rec["type"] = f.get("type")
        rec["title_preview"] = (f.get("requirement") or "")[:60]
        rec["tapd_url"] = _mask_tapd_url(rec.get("tapd_url") or "")
        rec["field_presence"] = {k: bool(f.get(k)) for k in TAPD_FIELDS}
        records.append(rec)

    field_filled = {
        k: sum(1 for r in records if r["field_presence"][k]) for k in TAPD_FIELDS
    }

    obs = {
        "report_id": report_id,
        "source": "GET /api/v2/code-compare/reports/{report_id}",
        "totals": {
            "all_findings": len(findings),
            "pushed_to_tapd": len(pushed),
        },
        "tapd_field_filled_count": field_filled,
        "note": (
            "本轮只读观察：未调用 sync-tapd-status 端点，未创建新 bug。"
            "tapd_last_sync_at 仅反映历史同步时刻。"
        ),
        "pushed_findings": records,
    }

    out_dir = SAMPLES_DIR / report_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "tapd_observation.json"
    out_path.write_text(json.dumps(obs, ensure_ascii=False, indent=2), encoding="utf-8")
    log("OK", f"已写 {out_path}")

    print()
    print("=" * 70)
    print("TAPD OBSERVATION SUMMARY")
    print("=" * 70)
    print(f"all_findings           : {len(findings)}")
    print(f"pushed_to_tapd         : {len(pushed)}")
    print()
    print("tapd_field_filled_count:")
    for k, v in field_filled.items():
        print(f"  {k:<22}: {v}/{len(pushed)}")
    print()
    print("pushed findings (url 已脱敏):")
    for r in records:
        sn = r.get("tapd_status_name") or r.get("tapd_status") or "-"
        print(f"  - {r['finding_id']}  bug={r['tapd_bug_id']}  status={sn}  "
              f"pushed_at={r['tapd_pushed_at']}  last_sync={r['tapd_last_sync_at']}")
    return 0


# ──────────────────────────────────────────────────────
# 命令：--observe-dashboard
# ──────────────────────────────────────────────────────
DASHBOARD_PROBES = [
    ("dashboard_summary", "/api/v2/dashboard/summary"),
    ("analytics_overview", "/api/v2/analytics/overview"),
    ("dashboard_defect_summary", "/api/v2/dashboard/defect-summary"),
    ("defect_summary_for_gate", "/api/v2/defects/summary/for-gate"),
    ("code_compare_reports_list", "/api/v2/code-compare/reports"),
]


def _safe_get(backend_url: str, path: str, timeout: float = 10.0):
    """返回 (status, payload, err)；任何异常都吃掉"""
    url = backend_url.rstrip("/") + path
    try:
        with urlreq.urlopen(url, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(text), None
            except Exception:
                return resp.status, text, None
    except HTTPError as e:
        try:
            t = e.read().decode("utf-8", errors="replace")
        except Exception:
            t = ""
        try:
            body = json.loads(t) if t else None
        except Exception:
            body = t
        return e.code, body, None
    except URLError as e:
        return None, None, f"URLError: {getattr(e, 'reason', e)}"
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"


def cmd_observe_dashboard(report_id: str, backend_url: str) -> int:
    if not backend_url:
        backend_url = "http://127.0.0.1:8001"

    obs = {
        "report_id": report_id,
        "backend_url": backend_url,
        "probes": [],
        "capabilities": {},
    }

    for name, path in DASHBOARD_PROBES:
        code, payload, err = _safe_get(backend_url, path)
        rec = {"name": name, "path": path, "status": code, "error": err}
        # 抽取关键指标但不保留全部敏感数据
        keys_present = []
        sample_value = None
        if isinstance(payload, dict):
            keys_present = list(payload.keys())[:30]
            # 脱敏：去除任何可能含密码的字段
            sample_value = {k: v for k, v in payload.items() if k not in ("config", "credentials")}
            # 截断 long string
            for k, v in list(sample_value.items()):
                if isinstance(v, str) and len(v) > 200:
                    sample_value[k] = v[:197] + "..."
        rec["keys_present"] = keys_present
        rec["sample"] = sample_value
        obs["probes"].append(rec)

        if code == 200:
            log("OK", f"{name:<30} {path} -> 200, keys={len(keys_present)}")
        elif code in (None,):
            log("WARN", f"{name:<30} {path} -> 不可达: {err}")
        elif code == 404:
            log("WARN", f"{name:<30} {path} -> 404 (能力可能未实现)")
        else:
            log("WARN", f"{name:<30} {path} -> {code}")

    # 能力边界总结
    caps = {}
    for p in obs["probes"]:
        sample = p.get("sample") or {}
        if p["name"] == "dashboard_summary" and isinstance(sample, dict):
            data = sample.get("data") if isinstance(sample.get("data"), dict) else sample
            if isinstance(data, dict):
                caps["shows_total_defect_count"] = "defect_count" in data or "total_defects" in data
                caps["shows_project_count"] = "project_count" in data
                caps["shows_test_case_count"] = "test_case_count" in data
        if p["name"] == "analytics_overview" and isinstance(sample, dict):
            caps["shows_run_pass_rate"] = "run_pass_rate" in sample
            caps["shows_case_pass_rate"] = "case_pass_rate" in sample
        if p["name"] == "dashboard_defect_summary":
            caps["dashboard_defect_summary_endpoint_exists"] = (p["status"] == 200)
        if p["name"] == "defect_summary_for_gate":
            caps["defect_summary_for_gate_endpoint_exists"] = (p["status"] == 200)
    # 默认 false
    for k in (
        "shows_total_defect_count", "shows_project_count", "shows_test_case_count",
        "shows_run_pass_rate", "shows_case_pass_rate",
        "dashboard_defect_summary_endpoint_exists",
        "defect_summary_for_gate_endpoint_exists",
    ):
        caps.setdefault(k, False)

    # finding-derived defect 联动观察（基于 dashboard_summary 现有字段判断）
    caps["shows_finding_derived_defects"] = False  # 当前无该专用字段
    caps["notes"] = [
        "本观察仅基于通用看板/分析端点 200 响应内容；",
        "未发现专门统计 'finding-derived defect' 或 'TAPD-linked defect' 的端点；",
        "若需联动展示，应增加专用端点或在 defect 模型上增加来源标签字段（属于 D2+ 范围）。",
    ]

    obs["capabilities"] = caps

    out_dir = SAMPLES_DIR / report_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "dashboard_observation.json"
    out_path.write_text(json.dumps(obs, ensure_ascii=False, indent=2), encoding="utf-8")
    log("OK", f"已写 {out_path}")

    print()
    print("=" * 70)
    print("DASHBOARD OBSERVATION SUMMARY")
    print("=" * 70)
    for p in obs["probes"]:
        print(f"  {p['name']:<30} {p['status']}  {p['path']}")
    print()
    print("capabilities:")
    for k, v in caps.items():
        if k == "notes":
            continue
        print(f"  {k:<45}: {v}")
    return 0


# ──────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="D1 finding 评审导出+评分+只读观察")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--export", metavar="REPORT_ID", help="导出 finding 评审表")
    g.add_argument("--score", metavar="REPORT_ID", help="读人工填好 CSV 计算指标")
    g.add_argument("--observe-tapd", metavar="REPORT_ID",
                   help="只读观察 TAPD 字段回写（不创建新 bug、不调 sync）")
    g.add_argument("--observe-dashboard", metavar="REPORT_ID",
                   help="只读观察 dashboard / analytics / defect-summary 接口")
    parser.add_argument(
        "--sample-size", type=int, default=30,
        help="抽样目标条数（默认 30；finding<=N 时全量）",
    )
    parser.add_argument(
        "--backend-url", default=None,
        help="API 地址，默认 http://127.0.0.1:8001 (export 模式默认读文件)",
    )
    args = parser.parse_args()

    if args.export:
        sys.exit(cmd_export(args.export, args.sample_size, args.backend_url))
    if args.score:
        sys.exit(cmd_score(args.score))
    if args.observe_tapd:
        sys.exit(cmd_observe_tapd(args.observe_tapd, args.backend_url))
    if args.observe_dashboard:
        sys.exit(cmd_observe_dashboard(args.observe_dashboard, args.backend_url))


if __name__ == "__main__":
    main()
