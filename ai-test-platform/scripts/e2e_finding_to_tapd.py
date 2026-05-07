# -*- coding: utf-8 -*-
"""端到端: 选一条高质量 finding → 转缺陷 → 推 TAPD → 同步状态联动

用法:
    D:\\python311\\python.exe scripts\\e2e_finding_to_tapd.py [report_id] [finding_id]

默认从最新报告里挑第 1 条 risk/inconsistent finding。
"""
import json
import sys
import time
from pathlib import Path

import requests

BASE = "http://127.0.0.1:8001"


def fail(msg):
    print(f"\n❌ {msg}")
    sys.exit(1)


def step1_pick_finding(report_id: str | None, finding_id: str | None):
    if finding_id and report_id:
        r = requests.get(f"{BASE}/api/v2/code-compare/reports/{report_id}", timeout=30)
        r.raise_for_status()
        rep = (r.json().get("report") or r.json())
        for f in rep.get("findings", []):
            if f.get("finding_id") == finding_id:
                return rep, f
        fail(f"finding_id {finding_id} 不存在于 report {report_id}")

    if not report_id:
        # 取最近一份报告
        r = requests.get(f"{BASE}/api/v2/code-compare/reports", timeout=30)
        r.raise_for_status()
        items = r.json().get("reports") or r.json().get("data") or []
        if not items:
            fail("没有任何报告，先跑 e2e_purchase_order_compare.py")
        report_id = items[0].get("report_id")
        print(f"  自动选取最新报告: {report_id}")

    r = requests.get(f"{BASE}/api/v2/code-compare/reports/{report_id}", timeout=30)
    r.raise_for_status()
    rep = r.json().get("report") or r.json()
    findings = rep.get("findings", [])
    # 优先 risk，再 inconsistent
    for ftype in ("risk", "inconsistent"):
        for f in findings:
            if f.get("type") == ftype and f.get("confidence", 0) >= 0.6:
                return rep, f
    fail("没找到 risk/inconsistent 类型的 finding")


def step2_convert_to_defect(finding_id: str):
    body = {
        "severity": "major",
        "priority": "P2",
        "review_comment": "AI 代码对比发现：实现可能与需求不一致，需复核",
    }
    r = requests.post(
        f"{BASE}/api/v2/code-compare/findings/{finding_id}/convert-to-defect",
        json=body,
        timeout=30,
    )
    if not r.ok:
        fail(f"convert-to-defect 失败: {r.status_code} {r.text[:300]}")
    data = r.json()
    print(f"  defect_id = {data.get('defect_id') or data}")
    return data


def step3_check_tapd_config():
    r = requests.get(f"{BASE}/api/v2/code-compare/tapd/config", timeout=10)
    if not r.ok:
        fail(f"读 TAPD 配置失败: {r.status_code}")
    cfg = (r.json().get("config") or {})
    print(f"  TAPD workspace_id = {cfg.get('workspace_id')}")
    print(f"  TAPD api_user     = {cfg.get('api_user')}")
    if not cfg.get("workspace_id") or not cfg.get("api_user"):
        return False
    # 测试连接
    r2 = requests.post(f"{BASE}/api/v2/code-compare/tapd/test", timeout=15)
    print(f"  TAPD test         = {r2.status_code} {r2.text[:200]}")
    return r2.ok


def step4_push_to_tapd(finding_id: str):
    body = {
        "title": None,  # 用 finding requirement 自动生成
        "severity": "major",
        "priority": "P2",
        "code_location": None,
    }
    r = requests.post(
        f"{BASE}/api/v2/code-compare/findings/{finding_id}/push-to-tapd",
        json=body,
        timeout=60,
    )
    if not r.ok:
        fail(f"push-to-tapd 失败: {r.status_code} {r.text[:500]}")
    data = r.json()
    print(f"  TAPD bug_id = {data.get('tapd_bug_id') or data.get('bug_id') or data}")
    return data


def step5_sync_tapd_status(finding_id: str):
    r = requests.post(
        f"{BASE}/api/v2/code-compare/findings/{finding_id}/sync-tapd-status",
        timeout=30,
    )
    if not r.ok:
        fail(f"sync-tapd-status 失败: {r.status_code} {r.text[:500]}")
    data = r.json()
    inner = data.get("data") or data
    print(f"  TAPD bug_id     = {inner.get('tapd_bug_id')}")
    print(f"  TAPD 状态码     = {inner.get('tapd_status')}")
    print(f"  TAPD 状态名     = {inner.get('tapd_status_name')}")
    print(f"  本地状态        = {inner.get('local_status_after') or inner.get('local_status')}")
    print(f"  最后同步时间    = {inner.get('tapd_last_sync_at')}")
    return data


def main():
    report_id = sys.argv[1] if len(sys.argv) > 1 else None
    finding_id = sys.argv[2] if len(sys.argv) > 2 else None

    # 后端 health
    try:
        requests.get(f"{BASE}/health", timeout=5).raise_for_status()
    except Exception as e:
        fail(f"后端未起: {e}")

    print("\n=== STEP 1: 选取 finding ===")
    rep, f = step1_pick_finding(report_id, finding_id)
    print(f"  report_id  = {rep.get('report_id')}")
    print(f"  finding_id = {f.get('finding_id')}")
    print(f"  type       = {f.get('type')}")
    print(f"  confidence = {f.get('confidence')}")
    print(f"  risk_level = {f.get('risk_level')}")
    print(f"  requirement= {f.get('requirement', '')[:100]}")
    fid = f.get("finding_id")

    print("\n=== STEP 2: convert-to-defect ===")
    step2_convert_to_defect(fid)

    print("\n=== STEP 3: 检查 TAPD 配置 ===")
    if not step3_check_tapd_config():
        print("  ⚠️ TAPD 未配置或测试连接失败，跳过 TAPD 推送步骤")
        print("\n=== 闭环验证: 仅完成本地缺陷流程（TAPD 部分需要先配置） ===")
        return

    print("\n=== STEP 4: push-to-tapd ===")
    step4_push_to_tapd(fid)

    print("\n=== STEP 5: sync-tapd-status ===")
    step5_sync_tapd_status(fid)

    print("\n✅ 闭环全程跑通！")


if __name__ == "__main__":
    main()
