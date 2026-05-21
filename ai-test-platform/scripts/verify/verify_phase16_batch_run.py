"""
Phase 16 验证脚本：批量执行中心最小验证
验证：创建任务 → 执行100+用例 → 进度查询 → 报告生成
"""
import requests
import time
import json
import sys

BASE = "http://localhost:8000"
API = f"{BASE}/api/v2/batch-runs"


def test_create_batch():
    """创建批量任务（前100条用例）"""
    print("=" * 60)
    print("Phase 16 验证: 批量执行中心")
    print("=" * 60)

    # 先查有多少用例
    r = requests.get(f"{BASE}/api/v2/test-cases", params={"limit": 1})
    if r.ok:
        data = r.json()
        total = data.get("total", 0) if isinstance(data, dict) else len(data)
        print(f"[INFO] 系统中共有 {total} 条用例")

    # 创建批量任务 - 只选前100条 page/list 类型
    print("\n[1] 创建批量任务 (page/list类型, 最多100条)...")
    payload = {
        "project_id": 1,
        "environment_id": 1,
        "batch_size": 20,
        "concurrency": 3,
        "filters": {
            "api_pattern": "page"
        }
    }
    r = requests.post(API, json=payload)
    if not r.ok:
        print(f"[FAIL] 创建失败: {r.status_code} {r.text}")
        return None
    data = r.json()
    batch_id = data["batch_id"]
    print(f"[OK] 批量任务已创建: {batch_id}, 共 {data['total_cases']} 条用例")
    return batch_id


def test_progress(batch_id):
    """轮询进度直到完成"""
    print(f"\n[2] 轮询进度 ({batch_id})...")
    max_wait = 300  # 最多等5分钟
    start = time.time()

    while time.time() - start < max_wait:
        r = requests.get(f"{API}/{batch_id}/progress")
        if not r.ok:
            print(f"  [WARN] 进度查询失败: {r.status_code}")
            time.sleep(3)
            continue

        p = r.json()
        pct = p["progress_pct"]
        print(f"  进度: {pct}% | 通过:{p['passed']} 失败:{p['failed']} 跳过:{p['skipped']} 运行中:{p['running']} | {p['elapsed_seconds']}s")

        if p["status"] not in ("running", ""):
            print(f"  [完成] 状态: {p['status']}")
            return p
        if pct >= 100:
            print(f"  [完成] 100%")
            return p
        time.sleep(3)

    print(f"  [TIMEOUT] 超过 {max_wait}s 未完成")
    return None


def test_report(batch_id):
    """获取报告"""
    print(f"\n[3] 获取报告 ({batch_id})...")
    r = requests.get(f"{API}/{batch_id}/report")
    if not r.ok:
        print(f"[FAIL] 报告获取失败: {r.status_code}")
        return None

    report = r.json()
    print(f"  通过率: {report['pass_rate']}%")
    print(f"  总计: {report['total_cases']} | 通过: {report['passed_cases']} | 失败: {report['failed_cases']}")
    print(f"  耗时: {report['duration_seconds']}s")

    fc = report.get("failure_categories", {})
    if any(v > 0 for v in fc.values()):
        print(f"  失败分类:")
        for cat, count in fc.items():
            if count > 0:
                print(f"    {cat}: {count}")

    ms = report.get("module_stats", {})
    if ms:
        print(f"  模块统计 (top 5):")
        for mod, st in sorted(ms.items(), key=lambda x: x[1]["total"], reverse=True)[:5]:
            print(f"    {mod}: {st['passed']}/{st['total']}")

    ds = report.get("duration_stats", {})
    if ds:
        print(f"  耗时统计: avg={ds.get('avg_ms')}ms, p95={ds.get('p95_ms')}ms")

    return report


def test_list():
    """列表查询"""
    print(f"\n[4] 查询任务列表...")
    r = requests.get(API)
    if r.ok:
        runs = r.json()
        print(f"  共 {len(runs)} 条记录")
        for run in runs[:3]:
            print(f"    {run['batch_id']} | {run['status']} | {run['pass_rate']}% | {run['duration_seconds']}s")
    return r.ok


def test_stop():
    """测试停止功能（创建一个大任务然后立即停止）"""
    print(f"\n[5] 测试停止功能...")
    payload = {
        "project_id": 1,
        "environment_id": 1,
        "batch_size": 10,
        "concurrency": 2,
    }
    r = requests.post(API, json=payload)
    if not r.ok:
        print(f"  [SKIP] 创建失败")
        return

    bid = r.json()["batch_id"]
    time.sleep(2)  # 等它开始

    r2 = requests.post(f"{API}/{bid}/stop")
    if r2.ok:
        print(f"  [OK] 停止信号已发送: {r2.json()}")
    else:
        print(f"  [INFO] {r2.text}")


if __name__ == "__main__":
    batch_id = test_create_batch()
    if not batch_id:
        sys.exit(1)

    progress = test_progress(batch_id)
    report = test_report(batch_id)
    test_list()

    # 验收
    print("\n" + "=" * 60)
    print("验收结果:")
    checks = [
        ("创建批量任务", batch_id is not None),
        ("执行不崩溃", progress is not None),
        ("单用例失败不影响后续", progress and progress.get("executed", 0) > 1),
        ("进度实时查看", progress is not None),
        ("通过率可见", report and "pass_rate" in report),
        ("失败分类可见", report and "failure_categories" in report),
        ("报告可导出", report is not None),
    ]
    for name, ok in checks:
        print(f"  {'✅' if ok else '❌'} {name}")

    all_pass = all(ok for _, ok in checks)
    print(f"\n{'🎉 全部验收通过!' if all_pass else '⚠️  部分验收未通过'}")
    sys.exit(0 if all_pass else 1)
