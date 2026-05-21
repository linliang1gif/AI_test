import sqlite3

conn = sqlite3.connect('data/test_platform.db')
cursor = conn.cursor()

# 检查reports表
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='reports'")
result = cursor.fetchone()

if result:
    print("reports表存在")
    print("="*60)
    print(result[0])
    print("="*60)
    
    # 查询记录数
    cursor.execute("SELECT COUNT(*) FROM reports")
    count = cursor.fetchone()[0]
    print(f"\n当前记录数: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM reports LIMIT 3")
        rows = cursor.fetchall()
        print("\n示例数据:")
        for row in rows:
            print(row)
else:
    print("❌ reports表不存在")

conn.close()
