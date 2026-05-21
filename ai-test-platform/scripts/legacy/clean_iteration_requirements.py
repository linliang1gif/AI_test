#!/usr/bin/env python3
"""
清理迭代中多余的旧需求数据 (纯 sqlite3，无需 SQLAlchemy)
用法:
  python scripts/clean_iteration_requirements.py          # 查看所有迭代的需求
  python scripts/clean_iteration_requirements.py --fix    # 删除不属于 v1.2.5 的旧需求
"""
import sqlite3, os, sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "test_platform.db")

def main():
    fix_mode = "--fix" in sys.argv
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. 列出所有迭代
    c.execute("SELECT id, name, version, status FROM iterations ORDER BY id")
    iters = c.fetchall()
    print(f"=== 所有迭代 ({len(iters)}) ===")
    for it in iters:
        print(f"  ID={it[0]}  name={it[1]}  version={it[2]}  status={it[3]}")

    # 2. 每个迭代的需求
    for it in iters:
        c.execute("SELECT id, title, risk_level, ai_summary FROM iteration_requirements WHERE iteration_id=? ORDER BY id", (it[0],))
        reqs = c.fetchall()
        print(f"\n--- 迭代 [{it[1]}] (ID={it[0]}) 的需求 ({len(reqs)} 条) ---")
        for r in reqs:
            title = (r[1] or "")[:80]
            ai = (r[3] or "")[:100]
            print(f"  [{r[0]}] risk={r[2]}  title={title}")
            if ai:
                print(f"        ai_summary={ai}...")

    # 3. 查测试点
    c.execute("SELECT id, iteration_id, test_point, priority FROM iteration_test_points ORDER BY iteration_id, id")
    tps = c.fetchall()
    if tps:
        print(f"\n=== 测试点 ({len(tps)}) ===")
        for tp in tps:
            print(f"  [{tp[0]}] iter={tp[1]}  priority={tp[3]}  point={tp[2][:80]}")

    # 4. 可选清理
    if fix_mode:
        stale_titles = ["Login", "用户登录功能", "用户信息修改", "用户登录接口"]
        c.execute("SELECT id, iteration_id, title FROM iteration_requirements WHERE title IN ({})".format(
            ",".join("?" * len(stale_titles))
        ), stale_titles)
        stale = c.fetchall()
        if stale:
            print(f"\n  [FIX] 将删除 {len(stale)} 条无关需求:")
            for s in stale:
                print(f"    - [{s[0]}] iter={s[1]} title={s[2]}")
            ids = [s[0] for s in stale]
            c.execute("DELETE FROM iteration_requirements WHERE id IN ({})".format(",".join("?" * len(ids))), ids)
            conn.commit()
            print(f"  Done: deleted {len(stale)} rows")
        else:
            print("\n  [FIX] 未发现无关需求")

    conn.close()

if __name__ == "__main__":
    main()
