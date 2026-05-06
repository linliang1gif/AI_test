#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码对比质量验证脚本 (B1)

目的：
1. 用现有报告作为 baseline，记录当前 AI 对比的找出率/分布
2. 重新跑一次同样的 (需求, 代码) 组合，对比新引擎与旧引擎的结果差异
3. 输出 baseline_report.md，作为后续优化的对照基准

用法：
    python scripts/test_diff_quality.py                    # 用最新报告做基线
    python scripts/test_diff_quality.py --report rpt_xxx   # 指定报告
    python scripts/test_diff_quality.py --rerun            # 重新跑一遍对比
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

# 让脚本能 import 项目模块
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


REPORTS_DIR = ROOT / "data" / "code_compare" / "reports"
SNAPSHOTS_DIR = ROOT / "data" / "code_snapshots"
REQ_CACHE_DIR = ROOT / "data" / "code_compare" / "req_cache"


def list_reports():
    """列出所有报告，按时间倒序"""
    items = []
    for p in REPORTS_DIR.glob("rpt_*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            items.append({
                "report_id": data.get("report_id"),
                "path": p,
                "created_at": data.get("created_at", ""),
                "summary": data.get("summary", {}),
                "findings_count": len(data.get("findings", [])),
                "snapshot_id": data.get("code_snapshot_id"),
                "snapshot_name": data.get("code_snapshot_name", ""),
                "ai_mode": data.get("ai_mode", "?"),
            })
        except Exception as e:
            print(f"  ⚠️ 无法读取 {p.name}: {e}")
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return items


def analyze_report(report_path: Path) -> dict:
    """统计单个报告的质量指标"""
    data = json.loads(report_path.read_text(encoding="utf-8"))
    findings = data.get("findings", [])
    summary = data.get("summary", {})

    # ── 1. 类型分布 ──
    type_counter = Counter(f.get("type", "unknown") for f in findings)

    # ── 2. 风险等级分布 ──
    risk_counter = Counter(f.get("risk_level", "unknown") for f in findings)

    # ── 3. 置信度分布 ──
    confidences = [f.get("confidence", 0) for f in findings if f.get("confidence")]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0
    low_conf = sum(1 for c in confidences if c < 0.6)
    high_conf = sum(1 for c in confidences if c >= 0.8)

    # ── 4. 问题密度（每条需求平均产出多少 finding） ──
    total_req = summary.get("total_req_points", 0)
    finding_per_req = len(findings) / max(total_req, 1)

    # ── 5. 有代码证据的比例 ──
    with_evidence = sum(
        1 for f in findings
        if f.get("code_evidence") and (
            f["code_evidence"].get("file") or f["code_evidence"].get("file_path")
        )
    )
    evidence_rate = with_evidence / max(len(findings), 1)

    # ── 6. 关键问题（缺失/风险）统计 ──
    critical_findings = [
        f for f in findings
        if f.get("type") in ("missing", "risk")
        and f.get("risk_level") in ("high", "medium")
    ]

    # ── 7. 可能的重复 finding（按 requirement 文本聚合） ──
    req_groups = defaultdict(list)
    for f in findings:
        req = f.get("requirement", "").strip()
        if req:
            req_groups[req].append(f)
    duplicates = {req: items for req, items in req_groups.items() if len(items) > 1}

    return {
        "report_id": data.get("report_id"),
        "snapshot_name": data.get("code_snapshot_name", ""),
        "created_at": data.get("created_at", ""),
        "ai_mode": data.get("ai_mode", "?"),
        "summary": summary,
        "metrics": {
            "total_findings": len(findings),
            "type_distribution": dict(type_counter),
            "risk_distribution": dict(risk_counter),
            "avg_confidence": round(avg_conf, 3),
            "low_confidence_count": low_conf,
            "high_confidence_count": high_conf,
            "finding_per_requirement": round(finding_per_req, 2),
            "with_code_evidence_rate": round(evidence_rate, 3),
            "critical_findings_count": len(critical_findings),
            "potential_duplicates": len(duplicates),
            "duplicate_groups": {k: len(v) for k, v in list(duplicates.items())[:5]},
        },
        "samples": {
            "missing_3": [
                {"requirement": f.get("requirement"), "analysis": f.get("analysis", "")[:120]}
                for f in findings if f.get("type") == "missing"
            ][:3],
            "risk_3": [
                {"requirement": f.get("requirement"), "analysis": f.get("analysis", "")[:120]}
                for f in findings if f.get("type") == "risk"
            ][:3],
        },
    }


def render_markdown(reports_metrics: list[dict]) -> str:
    """把分析结果渲染成 Markdown"""
    lines = ["# 代码对比质量基线报告 (B1)", ""]
    lines.append(f"_生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}_")
    lines.append("")
    lines.append(f"分析了 **{len(reports_metrics)}** 份历史报告：")
    lines.append("")

    # ── 概览表 ──
    lines.append("## 总览")
    lines.append("")
    lines.append("| 报告 ID | 代码快照 | AI模式 | 需求点 | Finding | 缺失 | 风险 | 平均置信度 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in reports_metrics:
        s = r.get("summary", {})
        m = r.get("metrics", {})
        lines.append(
            f"| `{r['report_id']}` | {r['snapshot_name'][:30]} | {r['ai_mode']} | "
            f"{s.get('total_req_points', '?')} | {m.get('total_findings', 0)} | "
            f"{s.get('missing', '?')} | {s.get('risk', '?')} | "
            f"{m.get('avg_confidence', 0)} |"
        )
    lines.append("")

    # ── 每份报告详细 ──
    for r in reports_metrics:
        m = r["metrics"]
        lines.append(f"## 报告 `{r['report_id']}`")
        lines.append("")
        lines.append(f"- **代码快照**: {r['snapshot_name']}")
        lines.append(f"- **AI 模式**: {r['ai_mode']}")
        lines.append(f"- **创建时间**: {r['created_at']}")
        lines.append("")
        lines.append("### 量化指标")
        lines.append("")
        lines.append(f"- Finding 总数: **{m['total_findings']}**")
        lines.append(f"- 类型分布: `{m['type_distribution']}`")
        lines.append(f"- 风险等级分布: `{m['risk_distribution']}`")
        lines.append(f"- 平均置信度: **{m['avg_confidence']}** (高 {m['high_confidence_count']} / 低 {m['low_confidence_count']})")
        lines.append(f"- 每条需求产出 Finding: **{m['finding_per_requirement']}** 个")
        lines.append(f"- 带代码证据的比例: **{m['with_code_evidence_rate'] * 100:.1f}%**")
        lines.append(f"- 关键 Finding (缺失/高风险): **{m['critical_findings_count']}**")
        lines.append(f"- 可能重复的 Finding 组数: **{m['potential_duplicates']}**")
        lines.append("")

        if r["samples"]["missing_3"]:
            lines.append("### 抽样：缺失项（前 3 条）")
            lines.append("")
            for s in r["samples"]["missing_3"]:
                lines.append(f"- **{s['requirement']}**")
                lines.append(f"  > {s['analysis']}")
            lines.append("")

        if r["samples"]["risk_3"]:
            lines.append("### 抽样：风险项（前 3 条）")
            lines.append("")
            for s in r["samples"]["risk_3"]:
                lines.append(f"- **{s['requirement']}**")
                lines.append(f"  > {s['analysis']}")
            lines.append("")

    # ── 结论 ──
    lines.append("## 评估结论")
    lines.append("")
    lines.append("### 当前引擎特征")
    if reports_metrics:
        avg_findings = sum(r["metrics"]["total_findings"] for r in reports_metrics) / len(reports_metrics)
        avg_conf = sum(r["metrics"]["avg_confidence"] for r in reports_metrics) / len(reports_metrics)
        avg_evidence = sum(r["metrics"]["with_code_evidence_rate"] for r in reports_metrics) / len(reports_metrics)
        lines.append(f"- 平均每份报告产出 **{avg_findings:.0f}** 个 Finding")
        lines.append(f"- 平均置信度 **{avg_conf:.2f}**")
        lines.append(f"- 平均代码证据率 **{avg_evidence * 100:.1f}%**")
        lines.append("")

    lines.append("### 改进方向（基于数据）")
    lines.append("")
    lines.append("- [ ] 如果 `with_code_evidence_rate` < 60%，说明 AI 提示需强化代码引用")
    lines.append("- [ ] 如果 `potential_duplicates` > 5，需要去重机制")
    lines.append("- [ ] 如果 `low_confidence_count` 占比 > 30%，需要二次校验")
    lines.append("- [ ] 后续重跑同份样本时，对比 critical_findings 数量是否提升")
    lines.append("")
    lines.append("### 后续验证步骤")
    lines.append("")
    lines.append("1. 选择一份报告作为 **黄金样本**，人工标注真实问题清单")
    lines.append("2. 重跑对比，计算召回率（人工 vs AI）")
    lines.append("3. 调整 prompt 后重跑，观察指标变化")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="代码对比质量验证")
    parser.add_argument("--report", help="指定单个报告 ID 分析")
    parser.add_argument("--top", type=int, default=5, help="分析最新 N 份报告")
    parser.add_argument("--output", default="docs/diff_quality_baseline.md",
                        help="输出 Markdown 路径")
    args = parser.parse_args()

    if not REPORTS_DIR.exists():
        print(f"❌ 报告目录不存在: {REPORTS_DIR}")
        sys.exit(1)

    print(f"📂 报告目录: {REPORTS_DIR}")
    reports = list_reports()
    print(f"📋 共找到 {len(reports)} 份报告\n")

    if args.report:
        target = [r for r in reports if r["report_id"] and args.report in r["report_id"]]
        if not target:
            print(f"❌ 未找到报告: {args.report}")
            sys.exit(1)
        reports = target[:1]
    else:
        reports = reports[:args.top]

    print(f"🔍 将分析 {len(reports)} 份报告...\n")

    metrics_list = []
    for r in reports:
        print(f"  📊 分析 {r['report_id']} ({r['snapshot_name']})...")
        try:
            m = analyze_report(r["path"])
            metrics_list.append(m)
            print(f"     finding={m['metrics']['total_findings']} "
                  f"avg_conf={m['metrics']['avg_confidence']} "
                  f"evidence={m['metrics']['with_code_evidence_rate'] * 100:.0f}%")
        except Exception as e:
            print(f"     ❌ 失败: {e}")

    # ── 输出 ──
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    md = render_markdown(metrics_list)
    output_path.write_text(md, encoding="utf-8")
    print(f"\n✅ 基线报告已生成: {output_path}")
    print(f"   ({len(md)} 字符, {md.count(chr(10)) + 1} 行)")

    # ── 控制台总结 ──
    print("\n" + "=" * 60)
    print("📈 关键指标汇总")
    print("=" * 60)
    if metrics_list:
        all_findings = [m["metrics"]["total_findings"] for m in metrics_list]
        all_conf = [m["metrics"]["avg_confidence"] for m in metrics_list]
        all_evidence = [m["metrics"]["with_code_evidence_rate"] for m in metrics_list]
        all_dup = [m["metrics"]["potential_duplicates"] for m in metrics_list]
        print(f"  分析报告数:     {len(metrics_list)}")
        print(f"  Finding 总数:   {sum(all_findings)} (avg {sum(all_findings)/len(all_findings):.1f})")
        print(f"  平均置信度:     {sum(all_conf)/len(all_conf):.3f}")
        print(f"  代码证据率:     {sum(all_evidence)/len(all_evidence)*100:.1f}%")
        print(f"  重复 Finding 组: {sum(all_dup)}")


if __name__ == "__main__":
    main()
