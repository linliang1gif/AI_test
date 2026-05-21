"""Phase 10B 综合验收脚本

覆盖 6 项关键能力：
  T1  危险接口扫描   — scan_dangerous_routes.py NEEDS_PROTECTION == 0
  T2  危险接口实跑   — visual_routes 5 个 P0 接口 confirm_text 错误时返回 400
  T3  silent except — 业务目录无 `except Exception:\\n  pass`
  T4  print 使用     — scan_print_usage.py FORBIDDEN == 0
  T5  archive 安全   — 业务代码不引用 archive、不在 sys.path
  T6  前端 confirm   — DangerConfirmDialog.jsx 存在、VisualTesting.jsx 接入、api.js 导出常量

运行：
  python scripts/test_phase10b_acceptance.py
"""
from __future__ import annotations
import os
import re
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, msg: str = ""):
    results.append((name, ok, msg))
    flag = "PASS" if ok else "FAIL"
    print(f"  [{flag}] {name}  {msg}")


# ---------------- T1 ----------------
def t1_dangerous_routes():
    print("\n[T1] 危险接口扫描 — scan_dangerous_routes.py")
    r = subprocess.run([PY, "scripts/scan_dangerous_routes.py"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"\u5f85\u4fdd\u62a4\(NEEDS_PROTECTION\):\s*(\d+)", out)
    needs = int(m.group(1)) if m else -1
    record("T1.1 NEEDS_PROTECTION == 0", needs == 0, f"needs={needs}")
    record("T1.2 退出码 0", r.returncode == 0, f"rc={r.returncode}")


# ---------------- T2 ----------------
def t2_visual_confirm_runtime():
    print("\n[T2] visual 路由 confirm_text 运行时校验")
    try:
        from fastapi.testclient import TestClient
        sys.path.insert(0, str(ROOT))
        # 只导入 visual_routes，避免拉起整套应用
        from fastapi import FastAPI
        from routes import visual_routes
        app = FastAPI()
        app.include_router(visual_routes.router)
        client = TestClient(app)

        # 5 个 P0 接口（visual_routes router 自带 prefix=/api/v2/visual）
        prefix = "/api/v2/visual"
        cases = [
            ("DELETE", f"{prefix}/baselines/__nonexistent__", None),
            ("POST",   f"{prefix}/bulk/delete",                {"baseline_ids": ["x"]}),
            ("POST",   f"{prefix}/baselines/x/rollback",       {"version_id": "v1"}),
            ("DELETE", f"{prefix}/webhook/dead-letters/1",     None),
            ("POST",   f"{prefix}/webhook/test",               {"event": "visual.diff.failed"}),
        ]
        ok_count = 0
        for method, path, body in cases:
            kwargs = {"json": body} if body is not None else {}
            resp = client.request(method, path, **kwargs)
            # 期望 400（confirm_text 缺失/错误），而不是 404/500
            is_confirm_block = (
                resp.status_code == 400
                and "confirm" in resp.text.lower()
            )
            if is_confirm_block:
                ok_count += 1
            else:
                print(f"      [-] {method} {path} status={resp.status_code} body={resp.text[:120]}")
        record("T2 visual P0 接口全部被 confirm_text 拦截",
               ok_count == len(cases),
               f"{ok_count}/{len(cases)}")
    except Exception as e:
        record("T2 visual confirm runtime", False, f"EXC: {e}")


# ---------------- T3 ----------------
def t3_silent_excepts():
    print("\n[T3] silent except 清理")
    pat = re.compile(r"except Exception:\s*\n\s*pass")
    found = []
    for d in ["routes", "services", "backend", "app"]:
        for p, dirs, fs in os.walk(ROOT / d):
            dirs[:] = [x for x in dirs if x not in ("__pycache__", "archive")]
            for f in fs:
                if not f.endswith(".py"):
                    continue
                fp = Path(p) / f
                src = fp.read_bytes().decode("utf-8", errors="replace")
                if pat.search(src):
                    found.append(str(fp.relative_to(ROOT)))
    record("T3 业务目录 silent except == 0",
           len(found) == 0,
           f"残留={len(found)} {found[:3]}")


# ---------------- T4 ----------------
def t4_print_usage():
    print("\n[T4] print 使用扫描")
    r = subprocess.run([PY, "scripts/scan_print_usage.py"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    rep_path = ROOT / "data" / "reports" / "print_usage.json"
    forbid = -1
    if rep_path.exists():
        rep = json.loads(rep_path.read_text(encoding="utf-8"))
        forbid = rep["summary"]["forbidden_count"]
    record("T4.1 业务目录 print 违规 == 0", forbid == 0, f"forbidden={forbid}")
    record("T4.2 退出码 0", r.returncode == 0, f"rc={r.returncode}")


# ---------------- T5 ----------------
def t5_archive_safety():
    print("\n[T5] archive 安全")
    arc = ROOT / "archive"
    record("T5.1 archive 目录存在", arc.is_dir(), str(arc.relative_to(ROOT)))
    readme = arc / "legacy_backup" / "README.md"
    record("T5.2 README 存在", readme.is_file(), str(readme.relative_to(ROOT)))

    # 业务代码不得 import / from archive...
    pat = re.compile(r"(?:^|\W)(?:from\s+archive(?:\.|\s+import)|import\s+archive(?:\.|\s|$))")
    bad = []
    for d in ["routes", "services", "backend", "app"]:
        for p, dirs, fs in os.walk(ROOT / d):
            dirs[:] = [x for x in dirs if x not in ("__pycache__",)]
            for f in fs:
                if not f.endswith(".py"):
                    continue
                fp = Path(p) / f
                src = fp.read_bytes().decode("utf-8", errors="replace")
                if pat.search(src):
                    bad.append(str(fp.relative_to(ROOT)))
    record("T5.3 业务代码无 archive 引用", len(bad) == 0, f"violators={bad}")

    # archive/legacy_backup 下的 .bak 文件不得参与 ast 扫描或被 import
    bad_py = list((arc / "legacy_backup").glob("*.py"))
    record("T5.4 archive 不存在可加载 .py（仅 .bak 容许）",
           len(bad_py) == 0, f"py_files={bad_py}")


# ---------------- T6 ----------------
def t6_frontend_confirm():
    print("\n[T6] 前端 confirm 集成")
    fe = ROOT / "frontend" / "src"
    dlg = fe / "components" / "common" / "DangerConfirmDialog.jsx"
    record("T6.1 DangerConfirmDialog.jsx 存在", dlg.is_file(), str(dlg.relative_to(ROOT)))

    api = fe / "services" / "api.js"
    if api.is_file():
        api_src = api.read_text(encoding="utf-8", errors="replace")
        record("T6.2 api.js 导出 VISUAL_DANGER 常量",
               "VISUAL_DANGER" in api_src, "")
        # api.js 通过 data 透传，调用方负责传 confirm_text；这里只校验 5 个 P0 常量定义齐全
        keys = ["DELETE_BASELINE", "BULK_DELETE_BASELINES", "ROLLBACK_BASELINE",
                "DELETE_DEAD_LETTER", "TEST_WEBHOOK"]
        present = sum(1 for k in keys if k in api_src)
        record("T6.3 api.js VISUAL_DANGER 5 个常量齐全",
               present == 5, f"{present}/5")
    else:
        record("T6.2/3 api.js 缺失", False, "")

    page = fe / "pages" / "VisualTesting.jsx"
    if page.is_file():
        page_src = page.read_text(encoding="utf-8", errors="replace")
        record("T6.4 VisualTesting.jsx 接入 DangerConfirmDialog",
               "DangerConfirmDialog" in page_src, "")
        record("T6.5 VisualTesting.jsx 5 处 confirm_text 调用",
               page_src.count("confirm_text") >= 5,
               f"count={page_src.count('confirm_text')}")
    else:
        record("T6.4 VisualTesting.jsx 缺失", False, "")


def main():
    print("=" * 86)
    print("  Phase 10B 综合验收")
    print("=" * 86)
    t1_dangerous_routes()
    t2_visual_confirm_runtime()
    t3_silent_excepts()
    t4_print_usage()
    t5_archive_safety()
    t6_frontend_confirm()

    print("\n" + "=" * 86)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"  汇总: {passed}/{total} 通过")
    fails = [n for n, ok, _ in results if not ok]
    if fails:
        print("  失败项:", fails)
        return 1
    print("  Phase 10B 全量验收通过 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
