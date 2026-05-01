import sqlite3

db_path = 'data/test_platform.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print(f"数据库文件路径: {db_path}")
print("\n当前真实表清单:")
print("=" * 50)

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

for i, (table_name,) in enumerate(tables, 1):
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"{i}. {table_name} (记录数: {count})")

print("\n" + "=" * 50)
print(f"总计: {len(tables)} 个表")

# 检查核心表
required_tables = [
    'projects', 'environments', 'auth_profiles', 'api_specs',
    'test_cases', 'test_runs', 'run_cases', 'run_steps',
    'reports', 'healing_records', 'system_settings',
    'ai_report_analyses', 'run_status_history'
]

existing_table_names = [t[0] for t in tables]
missing_tables = [t for t in required_tables if t not in existing_table_names]

print("\n核心表检查:")
print("=" * 50)
for table in required_tables:
    status = "✅" if table in existing_table_names else "❌"
    print(f"{status} {table}")

if missing_tables:
    print(f"\n⚠️ 缺失的核心表: {', '.join(missing_tables)}")
else:
    print("\n✅ 所有核心表都存在")

conn.close()
