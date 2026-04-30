"""查看最新生成的测试用例详情"""
import requests
import json

print("=" * 80)
print("📋 查看最新生成的测试用例")
print("=" * 80)
print()

# 获取所有测试用例
response = requests.get("http://localhost:8000/api/test-cases")

if response.status_code == 200:
    result = response.json()
    
    # 尝试不同的数据结构
    if 'data' in result:
        testcases = result.get('data', [])
    elif 'testCases' in result:
        testcases = result.get('testCases', [])
    elif 'test_cases' in result:
        testcases = result.get('test_cases', [])
    elif isinstance(result, list):
        testcases = result
    else:
        testcases = []
    
    print(f"✅ 共有 {len(testcases)} 个测试用例")
    print()
    
    # 获取最新的10个测试用例(按ID倒序)
    latest_cases = sorted(testcases, key=lambda x: x.get('id', ''), reverse=True)[:10]
    
    print("📝 最新的10个测试用例详情:")
    print("=" * 80)
    
    for i, tc in enumerate(latest_cases, 1):
        print(f"\n【测试用例 {i}】")
        print(f"ID: {tc.get('id')}")
        print(f"标题: {tc.get('title')}")
        print(f"模块: {tc.get('module')}")
        print(f"优先级: {tc.get('priority')}")
        print(f"类型: {tc.get('type')}")
        print(f"状态: {tc.get('status')}")
        print(f"来源: {tc.get('source')}")
        
        print(f"\n测试步骤:")
        steps = tc.get('steps', [])
        if isinstance(steps, list):
            for step in steps:
                print(f"  {step}")
        else:
            print(f"  {steps}")
        
        print(f"\n预期结果:")
        expected = tc.get('expected', '')
        print(f"  {expected}")
        
        print("-" * 80)
    
    # 分析最新用例的关键词
    print("\n📊 最新10个用例的关键词分析:")
    print("=" * 80)
    
    keywords_count = {
        '付款单': 0,
        '付款': 0,
        '应付': 0,
        '实付': 0,
        '个税': 0,
        '平台服务费': 0,
        '不含税': 0,
        '购物车': 0,
        '商品': 0,
        '支付': 0,
        '注册': 0,
        '登录': 0
    }
    
    for tc in latest_cases:
        text = json.dumps(tc, ensure_ascii=False)
        for keyword in keywords_count:
            if keyword in text:
                keywords_count[keyword] += 1
    
    print("\n关键词出现次数:")
    for keyword, count in sorted(keywords_count.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {keyword}: {count} 次")
    
    print("\n" + "=" * 80)
    
else:
    print(f"❌ 获取失败: {response.status_code}")
    print(response.text)
