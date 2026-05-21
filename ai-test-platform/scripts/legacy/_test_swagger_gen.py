"""验证 Swagger → V2 用例自动生成"""
import sys
sys.path.insert(0, r"G:\AI项目\ai测试\ai-test-platform")

from app.executor_v2.swagger_to_cases import generate_cases_from_swagger

SWAGGER = r"G:\AI项目\ai测试\ai-test-platform\uploads\swagger\014d88e2-4405-4ec7-a921-7064c04857ab_bluedot_openapi.json"

# 1) 只生成 page + list（查询类，安全）
cases, meta = generate_cases_from_swagger(
    SWAGGER,
    include_patterns=["page", "list", "detail"],
    exclude_patterns=["save", "update", "delete"],
    max_cases=20,
)

print(f"Base URL: {meta['base_url']}")
print(f"Stats: {meta['stats']}")
print(f"\n生成 {len(cases)} 个用例:")
for i, c in enumerate(cases):
    print(f"  {i+1}. [{c['method']}] {c['path']}  {c['title']}")
    print(f"     body={c.get('body', 'N/A')}  assertions={len(c.get('assertions', []))}")

print("\n✅ Swagger 用例生成器工作正常")
