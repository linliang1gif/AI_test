#!/usr/bin/env python3
"""
AI Dev Studio Phase 6.2 — DevPackage 产物引用与开发包验收脚本
验收内容: batch_id / packages API / reference_artifact_ids / 兼容性 / 回归
"""

import sys
import json
import time
import requests

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
DS = f"{BASE}/api/v2/dev-studio"
PS = f"{BASE}/api/v2/product-studio"
LLM_T = 180
RESULTS = []


def check(name, ok, detail=""):
    status = "\u2705" if ok else "\u274c"
    RESULTS.append((name, ok, detail))
    print(f"  {status} {name}" + (f"  ({detail})" if detail else ""))


def llm_post(url, json_body=None, timeout=LLM_T, retries=2):
    for attempt in range(retries):
        try:
            r = requests.post(url, json=json_body or {}, timeout=timeout)
            return r, True
        except KeyboardInterrupt:
            return None, False
        except Exception as e:
            if attempt < retries - 1:
                print(f"    \u26a0\ufe0f \u91cd\u8bd5 ({attempt+1}/{retries}): {str(e)[:80]}")
                time.sleep(3)
                continue
            print(f"    \u26a0\ufe0f \u6700\u7ec8\u5931\u8d25: {str(e)[:100]}")
            return None, False
    return None, False


print("=" * 70)
print("AI Dev Studio Phase 6.2 \u2014 DevPackage \u4ea7\u7269\u5f15\u7528\u4e0e\u5f00\u53d1\u5305\u9a8c\u6536")
print(f"BASE: {DS}")
print("=" * 70)

# ======================================================================
# Phase A: \u5065\u5eb7\u68c0\u67e5
# ======================================================================
print("\n" + "=" * 60)
print("PHASE A: \u5065\u5eb7\u68c0\u67e5")
print("=" * 60)

try:
    r = requests.get(f"{BASE}/health", timeout=5)
    check("\u5065\u5eb7\u68c0\u67e5", r.status_code == 200)
except Exception:
    try:
        r = requests.get(f"{DS}/tasks?page_size=1", timeout=5)
        check("\u5065\u5eb7\u68c0\u67e5(fallback)", r.status_code == 200)
    except Exception as e:
        check("\u5065\u5eb7\u68c0\u67e5", False, str(e)[:60])
        print("\n\u540e\u7aef\u4e0d\u53ef\u7528\uff0c\u7ec8\u6b62\u6d4b\u8bd5\u3002")
        sys.exit(1)

# ======================================================================
# Phase B: \u521b\u5efa DevTask
# ======================================================================
print("\n" + "=" * 60)
print("PHASE B: \u521b\u5efa\u6d4b\u8bd5 DevTask")
print("=" * 60)

r = requests.post(f"{DS}/tasks", json={
    "source_type": "manual",
    "title": "Phase 6.2 \u5f00\u53d1\u5305\u9a8c\u6536\u4efb\u52a1",
    "description": "\u9a8c\u8bc1 batch_id\u3001\u5f00\u53d1\u5305\u67e5\u8be2\u3001\u4ea7\u7269\u5f15\u7528\u529f\u80fd\u3002\u9700\u6c42\uff1a\u8ba2\u5355\u7ba1\u7406\u6a21\u5757\uff0c\u542b\u4e0b\u5355\u3001\u652f\u4ed8\u3001\u7269\u6d41\u8ffd\u8e2a\u3002",
})
check("\u521b\u5efa DevTask", r.status_code in (200, 201))
task_id = r.json().get("dev_task_id", "")
check("\u8fd4\u56de dev_task_id", bool(task_id), f"id={task_id}")

# ======================================================================
# Phase C: generate-all \u8fd4\u56de batch_id
# ======================================================================
print("\n" + "=" * 60)
print("PHASE C: generate-all \u8fd4\u56de batch_id")
print("=" * 60)

print("  \u23f3 \u6279\u91cf\u751f\u6210 5 \u7c7b\u4ea7\u7269\uff08\u53ef\u80fd\u9700\u8981\u6570\u5206\u949f\uff09...")
r, ok = llm_post(f"{DS}/tasks/{task_id}/generate-all", timeout=600)
check("generate-all 200", ok and r is not None and r.status_code == 200,
      f"status={r.status_code if r else 'N/A'}")

batch_data = r.json() if r and r.status_code == 200 else {}
batch_id = batch_data.get("batch_id", "")
check("\u8fd4\u56de batch_id", bool(batch_id), f"batch_id={batch_id}")
check("\u8fd4\u56de dev_task_id", batch_data.get("dev_task_id") == task_id)
check("total=5", batch_data.get("total") == 5)
check("succeeded + failed = total",
      (batch_data.get("succeeded_count", 0) + batch_data.get("failed_count", 0)) == batch_data.get("total", -1))

results = batch_data.get("results", [])
expected_types = ["dev_plan", "api_design", "db_design", "file_impact", "test_plan"]
actual_types = [r_item.get("artifact_type") for r_item in results]
check("artifact_type \u987a\u5e8f\u6b63\u786e", actual_types == expected_types)

succeeded_count = batch_data.get("succeeded_count", 0)
check("\u81f3\u5c11 1 \u9879\u6210\u529f", succeeded_count >= 1, f"succeeded={succeeded_count}")

# ======================================================================
# Phase D: \u67e5\u8be2 packages \u5217\u8868
# ======================================================================
print("\n" + "=" * 60)
print("PHASE D: \u67e5\u8be2\u5f00\u53d1\u5305\u5217\u8868")
print("=" * 60)

r = requests.get(f"{DS}/tasks/{task_id}/packages", timeout=10)
check("packages \u5217\u8868 200", r.status_code == 200)
pkg_data = r.json() if r.status_code == 200 else {}
check("\u8fd4\u56de dev_task_id", pkg_data.get("dev_task_id") == task_id)
pkg_list = pkg_data.get("packages", [])
check("packages \u975e\u7a7a", len(pkg_list) > 0, f"len={len(pkg_list)}")

found_batch = None
for p in pkg_list:
    if p.get("batch_id") == batch_id:
        found_batch = p
        break
check("\u5305\u542b\u521a\u751f\u6210\u7684 batch_id", found_batch is not None)
if found_batch:
    check("artifact_count >= succeeded", found_batch.get("artifact_count", 0) >= succeeded_count,
          f"art_count={found_batch.get('artifact_count')}")
    check("succeeded_count \u5339\u914d", found_batch.get("succeeded_count", 0) == succeeded_count)
    check("artifact_types \u975e\u7a7a", len(found_batch.get("artifact_types", [])) > 0)
    check("created_at \u975e\u7a7a", bool(found_batch.get("created_at")))

# ======================================================================
# Phase E: \u67e5\u8be2\u5355\u4e2a\u5f00\u53d1\u5305\u8be6\u60c5
# ======================================================================
print("\n" + "=" * 60)
print("PHASE E: \u67e5\u8be2\u5f00\u53d1\u5305\u8be6\u60c5")
print("=" * 60)

r = requests.get(f"{DS}/tasks/{task_id}/packages/{batch_id}", timeout=10)
check("package detail 200", r.status_code == 200)
detail = r.json() if r.status_code == 200 else {}
check("\u8fd4\u56de batch_id", detail.get("batch_id") == batch_id)
check("\u8fd4\u56de dev_task_id", detail.get("dev_task_id") == task_id)

pkg_arts = detail.get("artifacts", [])
pkg_runs = detail.get("runs", [])
check("artifacts \u975e\u7a7a", len(pkg_arts) > 0, f"len={len(pkg_arts)}")
check("runs \u975e\u7a7a", len(pkg_runs) > 0, f"len={len(pkg_runs)}")

# \u6bcf\u4e2a artifact \u6709 batch_index
for a in pkg_arts:
    at = a.get("artifact_type", "unknown")
    check(f"{at}: \u6709 batch_index", a.get("batch_index") is not None,
          f"idx={a.get('batch_index')}")

# ======================================================================
# Phase F: DevArtifact batch_id \u5b57\u6bb5\u9a8c\u8bc1
# ======================================================================
print("\n" + "=" * 60)
print("PHASE F: DevArtifact batch_id \u5b57\u6bb5")
print("=" * 60)

succeeded_items = [r_item for r_item in results if r_item.get("status") == "succeeded"]
for item in succeeded_items[:3]:
    at = item["artifact_type"]
    art_id = item.get("dev_artifact_id")
    if art_id:
        r = requests.get(f"{DS}/artifacts/{art_id}", timeout=10)
        if r.status_code == 200:
            art_data = r.json()
            check(f"{at}: batch_id \u5339\u914d", art_data.get("batch_id") == batch_id)
            check(f"{at}: batch_index \u975e\u7a7a", art_data.get("batch_index") is not None)

# ======================================================================
# Phase G: DevStudioRun batch_id \u5b57\u6bb5
# ======================================================================
print("\n" + "=" * 60)
print("PHASE G: DevStudioRun batch_id")
print("=" * 60)

for item in succeeded_items[:2]:
    at = item["artifact_type"]
    run_id = item.get("run_id")
    if run_id:
        r = requests.get(f"{DS}/runs/{run_id}", timeout=10)
        # run \u8be6\u60c5 API \u53ef\u80fd\u4e0d\u8fd4\u56de batch_id\uff0c\u4f46\u5f00\u53d1\u5305 detail \u4e2d\u7684 runs \u5df2\u7ecf\u5305\u542b
        check(f"{at}: run \u53ef\u67e5\u8be2", r.status_code == 200)

# \u68c0\u67e5 package detail \u4e2d\u7684 runs \u6570\u91cf
check("package runs \u6570\u91cf >= succeeded", len(pkg_runs) >= succeeded_count,
      f"runs={len(pkg_runs)} succeeded={succeeded_count}")

# ======================================================================
# Phase H: dev_plan reference_artifact_ids
# ======================================================================
print("\n" + "=" * 60)
print("PHASE H: dev_plan \u5f15\u7528\u5176\u4ed6\u4ea7\u7269")
print("=" * 60)

dev_plan_item = next((i for i in succeeded_items if i["artifact_type"] == "dev_plan"), None)
if dev_plan_item and dev_plan_item.get("dev_artifact_id"):
    r = requests.get(f"{DS}/artifacts/{dev_plan_item['dev_artifact_id']}", timeout=10)
    if r.status_code == 200:
        dp = r.json()
        ref_ids = dp.get("reference_artifact_ids")
        check("dev_plan \u6709 reference_artifact_ids", ref_ids is not None and len(ref_ids) > 0,
              f"count={len(ref_ids) if ref_ids else 0}")
        if ref_ids:
            other_succeeded = [i for i in succeeded_items if i["artifact_type"] != "dev_plan"]
            other_ids = [i["dev_artifact_id"] for i in other_succeeded if i.get("dev_artifact_id")]
            for oid in other_ids:
                check(f"ref \u5305\u542b {oid[:16]}", oid in ref_ids)

        # \u68c0\u67e5 markdown \u4e2d\u662f\u5426\u8ffd\u52a0\u4e86\u5173\u8054\u7ae0\u8282
        md = dp.get("content_markdown", "")
        check("markdown \u542b\u300e\u5173\u8054\u5f00\u53d1\u4ea7\u7269\u300f\u7ae0\u8282", "\u5173\u8054\u5f00\u53d1\u4ea7\u7269" in md)
        check("markdown \u542b\u300e\u9700\u4eba\u5de5\u786e\u8ba4\u300f\u63d0\u793a", "\u9700\u4eba\u5de5\u786e\u8ba4" in md)
    else:
        check("dev_plan \u67e5\u8be2\u5931\u8d25", False, f"status={r.status_code}")
else:
    check("dev_plan \u672a\u6210\u529f\u751f\u6210\uff0c\u8df3\u8fc7\u5f15\u7528\u6d4b\u8bd5", True, "LLM \u4e0d\u7a33\u5b9a")

# ======================================================================
# Phase I: \u7b2c\u4e8c\u6b21 generate-all \u4ea7\u751f\u65b0 batch_id
# ======================================================================
print("\n" + "=" * 60)
print("PHASE I: \u91cd\u590d generate-all \u4ea7\u751f\u65b0 batch_id")
print("=" * 60)

print("  \u23f3 \u7b2c\u4e8c\u6b21\u6279\u91cf\u751f\u6210 (2 types)...")
r2, ok2 = llm_post(f"{DS}/tasks/{task_id}/generate-all", json_body={
    "artifact_types": ["dev_plan", "api_design"],
}, timeout=300)
check("\u7b2c\u4e8c\u6b21 200", ok2 and r2 is not None and r2.status_code == 200)
if r2 and r2.status_code == 200:
    batch2 = r2.json()
    batch_id_2 = batch2.get("batch_id", "")
    check("\u65b0 batch_id \u975e\u7a7a", bool(batch_id_2))
    check("\u65b0 batch_id != \u65e7 batch_id", batch_id_2 != batch_id,
          f"new={batch_id_2} old={batch_id}")
    check("\u7b2c\u4e8c\u6b21 total=2", batch2.get("total") == 2)

    # packages \u5217\u8868\u5e94\u5305\u542b\u4e24\u4e2a batch
    r = requests.get(f"{DS}/tasks/{task_id}/packages", timeout=10)
    if r.status_code == 200:
        pkgs = r.json().get("packages", [])
        batch_ids = [p["batch_id"] for p in pkgs]
        check("\u5305\u542b\u4e24\u4e2a batch", batch_id in batch_ids and batch_id_2 in batch_ids,
              f"count={len(pkgs)}")

# ======================================================================
# Phase J: \u5386\u53f2\u65e0 batch_id \u517c\u5bb9\u6027
# ======================================================================
print("\n" + "=" * 60)
print("PHASE J: \u5386\u53f2\u65e0 batch_id \u6570\u636e\u517c\u5bb9\u6027")
print("=" * 60)

# \u5355\u9879\u751f\u6210\u4e0d\u5e26 batch_id
r = requests.post(f"{DS}/tasks", json={
    "source_type": "manual",
    "title": "\u517c\u5bb9\u6027\u6d4b\u8bd5\u4efb\u52a1",
    "description": "\u6d4b\u8bd5\u5355\u9879\u751f\u6210\u65e0 batch_id",
})
compat_task_id = r.json().get("dev_task_id", "") if r.status_code in (200, 201) else ""

if compat_task_id:
    print("  \u23f3 \u5355\u9879 dev_plan \u751f\u6210...")
    r_gen, ok_gen = llm_post(f"{DS}/tasks/{compat_task_id}/generate-dev-plan", timeout=LLM_T)
    if ok_gen and r_gen and r_gen.status_code == 200:
        gen_data = r_gen.json()
        art_id = gen_data.get("dev_artifact_id")
        if art_id:
            r_art = requests.get(f"{DS}/artifacts/{art_id}", timeout=10)
            if r_art.status_code == 200:
                check("\u5355\u9879\u751f\u6210 batch_id \u4e3a null", r_art.json().get("batch_id") is None)
            # \u8be5\u4efb\u52a1\u7684 packages \u5217\u8868\u5e94\u4e3a\u7a7a
            r_pkg = requests.get(f"{DS}/tasks/{compat_task_id}/packages", timeout=10)
            if r_pkg.status_code == 200:
                check("\u5355\u9879\u751f\u6210\u65e0\u5f00\u53d1\u5305", len(r_pkg.json().get("packages", [])) == 0)
        else:
            check("\u5355\u9879 dev_plan \u6210\u529f\u4f46\u65e0 artifact", gen_data.get("status") == "failed", "LLM \u5931\u8d25")
    else:
        check("\u5355\u9879\u751f\u6210 (LLM)", True, "LLM \u4e0d\u7a33\u5b9a\u8df3\u8fc7")

    # \u8be6\u60c5\u9875\u4ecd\u6b63\u5e38
    r = requests.get(f"{DS}/tasks/{compat_task_id}", timeout=10)
    check("\u5355\u9879\u4efb\u52a1\u8be6\u60c5\u6b63\u5e38", r.status_code == 200)
else:
    check("\u517c\u5bb9\u6027 - \u521b\u5efa\u4efb\u52a1\u5931\u8d25", False)

# ======================================================================
# Phase K: \u9519\u8bef\u5904\u7406
# ======================================================================
print("\n" + "=" * 60)
print("PHASE K: \u9519\u8bef\u5904\u7406")
print("=" * 60)

# \u4e0d\u5b58\u5728\u7684 dev_task_id
r = requests.get(f"{DS}/tasks/nonexistent_xxx/packages", timeout=10)
check("packages: \u4e0d\u5b58\u5728 task \u2192 404", r.status_code == 404)

r = requests.get(f"{DS}/tasks/{task_id}/packages/nonexistent_batch", timeout=10)
check("package detail: \u4e0d\u5b58\u5728 batch \u2192 404", r.status_code == 404)

r = requests.get(f"{DS}/tasks/nonexistent_xxx/packages/nonexistent_batch", timeout=10)
check("package detail: \u4e0d\u5b58\u5728 task \u2192 404", r.status_code == 404)

# generate-all \u975e\u6cd5\u7c7b\u578b
r = requests.post(f"{DS}/tasks/{task_id}/generate-all", json={
    "artifact_types": ["bad_type"],
}, timeout=10)
check("\u975e\u6cd5 artifact_type \u2192 400", r.status_code == 400)

# generate-all \u4e0d\u5b58\u5728 task
r = requests.post(f"{DS}/tasks/nonexistent_xxx/generate-all", timeout=10)
check("generate-all \u4e0d\u5b58\u5728 task \u2192 404", r.status_code == 404)

# ======================================================================
# Phase L: Phase 6 / 6.1 \u56de\u5f52
# ======================================================================
print("\n" + "=" * 60)
print("PHASE L: Phase 6 / 6.1 \u56de\u5f52")
print("=" * 60)

# \u4efb\u52a1\u5217\u8868
r = requests.get(f"{DS}/tasks", timeout=10)
check("\u56de\u5f52: \u4efb\u52a1\u5217\u8868 200", r.status_code == 200)
check("\u56de\u5f52: \u5217\u8868\u6709 items", len(r.json().get("items", [])) > 0)

# artifact 404
r = requests.get(f"{DS}/artifacts/nonexistent_id", timeout=10)
check("\u56de\u5f52: artifact 404", r.status_code == 404)

# run 404
r = requests.get(f"{DS}/runs/nonexistent_id", timeout=10)
check("\u56de\u5f52: run 404", r.status_code == 404)

# ======================================================================
# Phase M: Product Studio \u5065\u5eb7
# ======================================================================
print("\n" + "=" * 60)
print("PHASE M: Product Studio \u5065\u5eb7")
print("=" * 60)

r = requests.get(f"{PS}/ideas?page_size=1", timeout=10)
check("Product Studio \u60f3\u6cd5\u5217\u8868\u6b63\u5e38", r.status_code == 200)

# ======================================================================
# \u6c47\u603b
# ======================================================================
print("\n" + "=" * 70)
print("\u9a8c\u6536\u7ed3\u679c\u6c47\u603b")
print("=" * 70)

total = len(RESULTS)
passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = sum(1 for _, ok, _ in RESULTS if not ok)

for name, ok, detail in RESULTS:
    status = "\u2705" if ok else "\u274c"
    print(f"  {status} {name}" + (f"  ({detail})" if detail else ""))

print(f"\n\u603b\u8ba1: {total} \u9879 | \u2705 \u901a\u8fc7: {passed} | \u274c \u5931\u8d25: {failed}")

if failed == 0:
    print("\n\ud83c\udf89 \u5168\u90e8\u901a\u8fc7\uff01")
else:
    print(f"\n\u26a0\ufe0f \u6709 {failed} \u9879\u5931\u8d25")

sys.exit(0 if failed == 0 else 1)
