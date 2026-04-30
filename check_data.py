from pathlib import Path
import json

data_file = Path('ai-test-platform/data/platform_data.json')
if data_file.exists():
    data = json.loads(data_file.read_text(encoding='utf-8'))
    projects = data.get('projects', [])
    print(f'数据库中有 {len(projects)} 个项目')
    for p in projects[:5]:
        print(f'  - ID: {p.get("id")}, Name: {p.get("name")}')
else:
    print('数据文件不存在')
