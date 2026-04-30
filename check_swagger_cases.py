from pathlib import Path
import json

json_file = Path('ai-test-platform/data/platform_data.json')

if json_file.exists():
    data = json.loads(json_file.read_text(encoding='utf-8'))
    test_cases = data.get('test_cases', [])
    swagger_cases = [tc for tc in test_cases if tc.get('source') == 'swagger']
    print(f'数据库中共有 {len(test_cases)} 个测试用例')
    print(f'其中 Swagger 来源的有 {len(swagger_cases)} 个')
    if swagger_cases:
        print(f'\n前5个 Swagger 用例:')
        for tc in swagger_cases[:5]:
            print(f'  - ID: {tc.get("id")}, Title: {tc.get("title")}')
else:
    print('数据文件不存在')
