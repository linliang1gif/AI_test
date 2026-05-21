import sqlite3
conn = sqlite3.connect("data/test_platform.db")
cur = conn.execute("SELECT id, title, source FROM test_cases WHERE id LIKE 'TC_AI_%' ORDER BY created_at DESC LIMIT 5")
for r in cur.fetchall():
    print(r)
conn.close()
