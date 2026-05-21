# -*- coding: utf-8 -*-
"""端到端实测：蓝点采购订单 — 需求/代码对比 → finding → 缺陷 → TAPD

跑法:
    D:\\python311\\python.exe scripts\\e2e_purchase_order_compare.py

要求:
    后端 http://127.0.0.1:8001 已起
"""
import io
import json
import os
import sys
import zipfile
from pathlib import Path

import requests

BASE = "http://127.0.0.1:8001"
PROJ = Path(r"D:\360Downloads\蓝点\recycle-applet-feature-1.2.3")
CODE_DIR = PROJ / "subpackages" / "purchaseOrder"
AXURE_FILES = PROJ / "采购订单-企业小程序_v1.2.3_files"

OUT = Path(__file__).parent / "_e2e_purchase_order_out"
OUT.mkdir(exist_ok=True)


def log(stage, **kw):
    print(f"\n=== {stage} ===")
    for k, v in kw.items():
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)[:200]
        print(f"  {k} = {v}")


def step1_zip_code() -> Path:
    """把 purchaseOrder 子包打成 zip"""
    if not CODE_DIR.exists():
        sys.exit(f"代码目录不存在: {CODE_DIR}")
    zip_path = OUT / "purchaseOrder_snapshot.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in CODE_DIR.rglob("*"):
            if p.is_file():
                arcname = p.relative_to(CODE_DIR.parent)  # 保留 purchaseOrder/ 前缀
                zf.write(p, arcname)
    log("STEP 1 打包代码", zip=str(zip_path), size_kb=round(zip_path.stat().st_size / 1024, 1))
    return zip_path


def step2_upload(zip_path: Path) -> str:
    """上传代码 zip"""
    with open(zip_path, "rb") as f:
        r = requests.post(f"{BASE}/api/v2/code-compare/upload", files={"file": (zip_path.name, f, "application/zip")}, timeout=60)
    r.raise_for_status()
    data = r.json()
    snap_id = (
        data.get("snapshot_id")
        or data.get("code_snapshot_id")
        or (data.get("snapshot") or {}).get("snapshot_id")
        or (data.get("data") or {}).get("snapshot_id")
    )
    log("STEP 2 上传代码", snapshot_id=snap_id, raw=data)
    if not snap_id:
        sys.exit(f"未拿到 snapshot_id: {data}")
    return snap_id


def step3_parse_axure() -> dict:
    """解析 Axure 文件夹拿到 features/rules/fields/axure_notes"""
    if not AXURE_FILES.exists():
        sys.exit(f"Axure 目录不存在: {AXURE_FILES}")
    r = requests.post(f"{BASE}/api/ai/folder-preview", json={"folder_path": str(AXURE_FILES)}, timeout=120)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        sys.exit(f"Axure 解析失败: {data}")
    structured = data["structured"]
    log("STEP 3 解析 Axure", stats=structured.get("stats"),
        features_n=len(structured.get("features", [])),
        rules_n=len(structured.get("rules", [])),
        fields_n=len(structured.get("fields", [])),
        notes_n=len(structured.get("axure_notes", [])))
    return structured


def step4_cache_req(structured: dict) -> str:
    """把需求结构 cache 到后端，拿 req_id"""
    payload = {
        "features": structured.get("features", []),
        "rules": structured.get("rules", []),
        "fields": structured.get("fields", []),
        "axure_notes": structured.get("axure_notes", []),
        "modules": structured.get("modules", []),
        "stats": structured.get("stats", {}),
    }
    r = requests.post(f"{BASE}/api/v2/code-compare/cache-requirement", json=payload, timeout=15)
    r.raise_for_status()
    data = r.json()
    req_id = data.get("requirement_id") or data.get("req_id") or (data.get("data") or {}).get("requirement_id")
    log("STEP 4 缓存需求", req_id=req_id)
    if not req_id:
        sys.exit(f"未拿到 req_id: {data}")
    return req_id


def step5_analyze(req_id: str, snap_id: str, use_ai: bool = True) -> dict:
    """触发对比"""
    body = {
        "requirement_id": req_id,
        "code_snapshot_id": snap_id,
        "use_ai": use_ai,
    }
    print(f"\n📡 POST /api/v2/code-compare/analyze (AI={use_ai}) - 可能需要几十秒到几分钟...")
    r = requests.post(f"{BASE}/api/v2/code-compare/analyze", json=body, timeout=600)
    r.raise_for_status()
    data = r.json()
    report = data.get("report") or {}
    log("STEP 5 对比分析",
        report_id=report.get("report_id"),
        ai_mode=report.get("ai_mode"),
        summary=report.get("summary"),
        findings_n=len(report.get("findings", [])))
    return report


def step6_dump_findings(report: dict) -> Path:
    """把 finding 列表写到 markdown 方便核对"""
    findings = report.get("findings", [])
    md_path = OUT / "findings_report.md"
    type_emoji = {
        "missing": "❌", "inconsistent": "⚠️", "extra": "➕",
        "uncertain": "❔", "risk": "🔥", "implemented": "✅",
    }
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# 采购订单 需求-代码对比报告\n\n")
        f.write(f"**Report ID**: {report.get('report_id')}\n\n")
        f.write(f"**AI 模式**: {report.get('ai_mode')}\n\n")
        s = report.get("summary", {})
        f.write(f"**统计**: 总需求点 {s.get('total_req_points', 0)} | "
                f"✅实现 {s.get('implemented', 0)} | "
                f"❌缺失 {s.get('missing', 0)} | "
                f"⚠️不一致 {s.get('inconsistent', 0)} | "
                f"➕多余 {s.get('extra', 0)} | "
                f"❔不确定 {s.get('uncertain', 0)} | "
                f"🔥风险 {s.get('risk', 0)}\n\n")
        f.write(f"---\n\n")
        # 按类型分组
        for ftype in ["missing", "inconsistent", "risk", "extra", "uncertain", "implemented"]:
            grp = [x for x in findings if x.get("type") == ftype]
            if not grp:
                continue
            f.write(f"## {type_emoji.get(ftype, '·')} {ftype} ({len(grp)})\n\n")
            for i, fi in enumerate(grp, 1):
                f.write(f"### {i}. {fi.get('requirement', '')[:80]}\n\n")
                f.write(f"- **finding_id**: `{fi.get('finding_id')}`\n")
                f.write(f"- **置信度**: {fi.get('confidence')}\n")
                f.write(f"- **风险**: {fi.get('risk_level')}\n")
                if fi.get("analysis"):
                    f.write(f"- **分析**: {fi['analysis'][:300]}\n")
                if fi.get("inconsistencies"):
                    f.write(f"- **不一致点**:\n")
                    for inc in fi["inconsistencies"]:
                        f.write(f"  - 方面: {inc.get('aspect')} | 期望: {inc.get('requirement_expectation')} | 实际: {inc.get('code_actual')}\n")
                if fi.get("code_evidence"):
                    ce = fi["code_evidence"]
                    if isinstance(ce, list):
                        f.write(f"- **代码位置**: {', '.join(str(x) for x in ce[:5])}\n")
                    else:
                        f.write(f"- **代码位置**: {ce}\n")
                if fi.get("evidence_snippet"):
                    f.write(f"- **代码片段**:\n```\n{fi['evidence_snippet'][:800]}\n```\n")
                if fi.get("test_suggestion"):
                    ts = fi["test_suggestion"]
                    if isinstance(ts, (list, tuple)):
                        ts_text = " | ".join(str(x) for x in ts)
                    elif isinstance(ts, dict):
                        ts_text = json.dumps(ts, ensure_ascii=False)
                    else:
                        ts_text = str(ts)
                    f.write(f"- **测试建议**: {ts_text[:300]}\n")
                f.write("\n")
        f.write("\n")
    log("STEP 6 输出报告", md=str(md_path))
    return md_path


def main():
    print(f"=== 采购订单 端到端实测 ===")
    print(f"代码目录: {CODE_DIR}")
    print(f"Axure 目录: {AXURE_FILES}")

    # 健康检查
    try:
        h = requests.get(f"{BASE}/health", timeout=5)
        h.raise_for_status()
    except Exception as e:
        sys.exit(f"❌ 后端未起: {e}")
    print(f"✅ 后端 health OK")

    zip_path = step1_zip_code()
    snap_id = step2_upload(zip_path)
    structured = step3_parse_axure()

    # dump 结构化需求供检查
    (OUT / "requirement_structured.json").write_text(
        json.dumps(structured, ensure_ascii=False, indent=2), encoding="utf-8")

    req_id = step4_cache_req(structured)
    report = step5_analyze(req_id, snap_id, use_ai=True)

    # dump 完整报告
    (OUT / "report_raw.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = step6_dump_findings(report)

    print(f"\n=== 完成 ===")
    print(f"  结构化需求: {OUT / 'requirement_structured.json'}")
    print(f"  原始报告:   {OUT / 'report_raw.json'}")
    print(f"  可读报告:   {md}")
    print(f"\n下一步: 你打开 findings_report.md 跟手工 14 个 bug 核对")


if __name__ == "__main__":
    main()
