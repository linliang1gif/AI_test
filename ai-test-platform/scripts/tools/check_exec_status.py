import sqlite3, os
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "test_platform.db")
conn = sqlite3.connect(DB)
c = conn.cursor()

# 执行集
c.execute("SELECT id, name, type, status, case_count, run_id FROM iteration_execution_sets WHERE iteration_id=1")
es = c.fetchall()
print(f"=== 执行集 ({len(es)}) ===")
for r in es:
    print(f"  [{r[0]}] name={r[1]} type={r[2]} status={r[3]} cases={r[4]} run={r[5]}")

# 测试用例
c.execute("SELECT id, title, iteration_id FROM test_cases WHERE iteration_id=1 LIMIT 10")
tc = c.fetchall()
print(f"\n=== 迭代1的测试用例 ({len(tc)}) ===")
for r in tc:
    print(f"  [{r[0]}] {r[1]}")

# 环境
c.execute("SELECT id, name, base_url FROM environments LIMIT 5")
env = c.fetchall()
print(f"\n=== 环境 ({len(env)}) ===")
for r in env:
    print(f"  [{r[0]}] {r[1]}  url={r[2]}")

# 执行集关联的用例
if es:
    es_id = es[0][0]
    c.execute("SELECT id, test_case_id FROM iteration_execution_set_cases WHERE execution_set_id=?", (es_id,))
    links = c.fetchall()
    print(f"\n=== 执行集[{es_id}]关联用例 ({len(links)}) ===")
    for r in links:
        print(f"  [{r[0]}] case_id={r[1]}")

# 执行结果详情
c.execute("SELECT test_case_id, status, error_message, duration FROM run_cases WHERE run_id='RUN_20260511181814_0dbc39b9'")
rows = c.fetchall()
print(f"\n=== 执行结果 ({len(rows)}) ===")
for r in rows:
    cid = r[0][:25] if r[0] else "?"
    err = (r[2] or "-")[:100]
    print(f"  {cid}  status={r[1]}  dur={r[3]}s")
    print(f"    error: {err}")

# 查用例的 execution_config
c.execute("SELECT id, title, execution_config FROM test_cases WHERE iteration_id=1")
tcs = c.fetchall()
print(f"\n=== 用例执行配置 ===")
for t in tcs:
    cfg = t[2] if t[2] else "NULL"
    if isinstance(cfg, str) and len(cfg) > 120:
        cfg = cfg[:120] + "..."
    print(f"  [{t[0][:20]}] {t[1][:40]}")
    print(f"    config: {cfg}")

conn.close()
