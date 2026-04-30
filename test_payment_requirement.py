"""测试付款单需求生成"""
import requests
import io

requirement = """v1.2.2迭代需求说明
【【付款单】新增"不含税应付金额、个税税额、平台服务费、个税承担方"及其他优化】

一、新增字段
1、付款单新增"不含税应付金额、个税承担方、个税税额、平台服务费"，取值及放置位置见原型
2、导出、导入、设置显示字段同步新增（不含税应付金额为隐藏字段，无须新增）

二、其他优化
1、付款单主表的实付/实退金额（付款币别）≤0时，不允许提交审核
2、付款单明细的"应付金额（付款币别）"字段，改为"应付金额（原币）"
3、付款单明细的"实付金额（付款币别）"字段，改为"实付金额（原币）"

三、测试要点
1. 新增字段的显示和取值
2. 导出导入功能
3. 金额校验规则
4. 字段名称修改
"""

files = {
    'file': ('payment_requirement.txt', io.BytesIO(requirement.encode('utf-8')), 'text/plain')
}

print("=" * 70)
print("🧪 测试付款单需求生成")
print("=" * 70)
print()
print("📝 需求内容:")
print(requirement[:300])
print("...")
print()
print("⏳ 发送请求...")

response = requests.post(
    "http://localhost:8000/api/testcases/generate",
    files=files,
    timeout=120
)

if response.status_code == 200:
    result = response.json()
    testcases = result.get('testCases', [])
    
    print(f"✅ 生成成功: {len(testcases)} 个测试用例")
    print()
    
    # 显示所有测试用例标题
    print("📋 生成的测试用例:")
    for i, tc in enumerate(testcases, 1):
        print(f"{i}. {tc.get('title')}")
        print(f"   模块: {tc.get('module')}")
        print(f"   类型: {tc.get('type')}")
        
        # 显示第一个步骤
        steps = tc.get('steps', [])
        if steps:
            print(f"   第一步: {steps[0]}")
        print()
    
    # 检查是否包含付款单相关内容
    payment_keywords = ['付款', '应付', '实付', '个税', '平台服务费', '不含税']
    cart_keywords = ['购物车', '商品', '结算', '支付方式']
    
    payment_count = 0
    cart_count = 0
    
    for tc in testcases:
        title = tc.get('title', '')
        module = tc.get('module', '')
        text = title + module
        
        if any(kw in text for kw in payment_keywords):
            payment_count += 1
        if any(kw in text for kw in cart_keywords):
            cart_count += 1
    
    print("=" * 70)
    print("📊 内容分析:")
    print(f"   包含付款单关键词的用例: {payment_count}/{len(testcases)}")
    print(f"   包含购物车关键词的用例: {cart_count}/{len(testcases)}")
    
    if payment_count > cart_count:
        print("   ✅ 生成内容正确 - 主要是付款单相关")
    elif cart_count > 0:
        print("   ❌ 生成内容错误 - 包含购物车内容")
    else:
        print("   ⚠️  生成内容可能不够准确")
    print("=" * 70)
    
else:
    print(f"❌ 请求失败: {response.status_code}")
    print(response.text)
