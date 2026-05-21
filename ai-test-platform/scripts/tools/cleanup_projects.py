#!/usr/bin/env python3
"""清理项目：只保留蓝点dev (ID=9)"""
import sqlite3

DB = "data/test_platform.db"
KEEP_ID = 9

conn = sqlite3.connect(DB)

# 查找所有含 project_id 列的表
tables_with_pid = []
for (tname,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
    cols = [c[1] for c in conn.execute(f"PRAGMA table_info({tname})").fetchall()]
    if "project_id" in cols:
        tables_with_pid.append(tname)

print(f"含 project_id 的表: {tables_with_pid}")

# 删除非保留项目的关联数据
for t in tables_with_pid:
    if t == "projects":
        continue
    c = conn.execute(f"DELETE FROM {t} WHERE project_id != ?", (KEEP_ID,))
    print(f"  {t}: 删除 {c.rowcount} 行")

# 删除项目本身
c = conn.execute("DELETE FROM projects WHERE id != ?", (KEEP_ID,))
print(f"  projects: 删除 {c.rowcount} 行")

conn.commit()

remaining = conn.execute("SELECT id, name FROM projects").fetchall()
print(f"\n剩余项目: {remaining}")
conn.close()
print("✅ 清理完成")
