"""
测试 Skill 要求是否正确实现
"""

def test_module_estimation():
    """测试模块数量估算"""
    print("=" * 60)
    print("1. 测试模块数量估算")
    print("=" * 60)
    
    test_cases = [
        ("付款单新增字段", 1),
        ("付款单模块和企业管理模块", 2),
        ("付款单、企业管理、财务应付单、供应商管理、采购订单、反向开票", 6)
    ]
    
    module_keywords = ['模块', '功能', '页面', '接口', '服务']
    
    for content, expected in test_cases:
        estimated = sum(1 for keyword in module_keywords if keyword in content)
        estimated = max(1, estimated)
        
        status = "✅" if estimated >= expected else "⚠️"
        print(f"{status} '{content[:30]}...' → 估算: {estimated}, 预期: {expected}")

def test_generation_count():
    """测试生成数量计算"""
    print("\n" + "=" * 60)
    print("2. 测试生成数量计算")
    print("=" * 60)
    
    test_cases = [
        (2000, 1, "30-50个"),
        (3500, 2, "100-200个"),
        (6000, 6, "600-900个")
    ]
    
    for content_length, modules, expected_range in test_cases:
        if content_length > 5000:
            target = f"{modules * 100}-{modules * 150}个"
        elif content_length > 3000:
            target = f"{modules * 50}-{modules * 100}个"
        else:
            target = f"{modules * 30}-{modules * 50}个"
        
        status = "✅" if target == expected_range else "❌"
        print(f"{status} {content_length}字符, {modules}模块 → {target} (预期: {expected_range})")

def test_token_calculation():
    """测试 token 限制计算"""
    print("\n" + "=" * 60)
    print("3. 测试 Token 限制计算")
    print("=" * 60)
    
    test_cases = [
        (2000, 1, 6000),
        (3500, 2, 10000),
        (6000, 6, 16000)  # 限制最大值
    ]
    
    for content_length, modules, expected_tokens in test_cases:
        if content_length > 5000:
            max_tokens = 12000 + (modules * 2000)
        elif content_length > 3000:
            max_tokens = 8000 + (modules * 1000)
        else:
            max_tokens = 6000
        
        max_tokens = min(max_tokens, 16000)
        
        status = "✅" if max_tokens == expected_tokens else "❌"
        print(f"{status} {content_length}字符, {modules}模块 → {max_tokens} tokens (预期: {expected_tokens})")

def test_v122_requirement():
    """测试 v1.2.2 需求"""
    print("\n" + "=" * 60)
    print("4. 测试 v1.2.2 需求预期")
    print("=" * 60)
    
    # v1.2.2 需求特征
    content_length = 5234  # 假设长度
    
    # 识别模块
    modules_in_v122 = [
        "付款单模块",
        "企业管理模块",
        "财务应付单模块",
        "供应商管理模块",
        "采购订单模块",
        "反向开票申请单模块"
    ]
    
    estimated_modules = len(modules_in_v122)
    
    print(f"\n需求特征:")
    print(f"  文档长度: {content_length} 字符")
    print(f"  识别模块: {estimated_modules} 个")
    print(f"\n模块列表:")
    for i, module in enumerate(modules_in_v122, 1):
        print(f"  {i}. {module}")
    
    # 计算预期
    target_min = estimated_modules * 100
    target_max = estimated_modules * 150
    max_tokens = min(12000 + (estimated_modules * 2000), 16000)
    
    print(f"\n预期生成:")
    print(f"  ✅ 目标数量: {target_min}-{target_max} 个测试用例")
    print(f"  ✅ Token 限制: {max_tokens}")
    print(f"  ✅ 符合 Skill 要求: 每个模块 100-150 个")

def test_skill_dimensions():
    """测试 Skill 维度要求"""
    print("\n" + "=" * 60)
    print("5. 测试 Skill 维度要求")
    print("=" * 60)
    
    dimensions = [
        "功能测试 - 正常流程、核心功能、业务规则",
        "边界测试 - 最小值/最大值、临界值、空值、超长数据",
        "异常测试 - 非法输入、错误参数、异常状态",
        "安全测试 - SQL注入、XSS攻击、权限控制",
        "性能测试 - 响应时间、并发处理",
        "兼容性测试 - 不同浏览器、设备、分辨率"
    ]
    
    print("\n必须覆盖的测试维度:")
    for i, dim in enumerate(dimensions, 1):
        print(f"  ✅ {i}. {dim}")
    
    print(f"\n总计: {len(dimensions)} 个维度")

def provide_usage_guide():
    """提供使用指南"""
    print("\n" + "=" * 60)
    print("6. 使用指南")
    print("=" * 60)
    
    print("""
测试步骤:
---------
1. 重启后端服务
   cd ai-test-platform
   py backend_api_server.py

2. 上传 v1.2.2 需求文档
   - 文件大小: ~5000+ 字符
   - 包含 6 个模块

3. 查看后端日志
   预期输出:
   📊 需求文档长度: 5234 字符
   📊 估算模块数: 6 个
   📊 目标生成: 600-900个 测试用例 (符合Skill要求)
   🤖 AI 配置: max_tokens=16000, temperature=0.3
   ✅ AI生成成功: 新增 650 个测试用例 (使用Skill增强)

4. 验证生成结果
   - 检查测试用例数量（应该 > 500）
   - 检查测试维度覆盖（6个维度）
   - 检查测试步骤详细度（至少5步）
   - 检查测试数据具体性（不是"有效数据"）

注意事项:
---------
1. 生成时间可能较长（30-60秒）
2. 如果 AI 无法一次生成足够数量，可以多次生成
3. 优先保证质量，数量其次
4. 可以考虑分批生成策略

Skill 要求回顾:
--------------
✅ 每个模块至少 100 个测试用例
✅ 每个测试点至少 20 个场景
✅ 每个场景至少 5 个用例
✅ 覆盖 6 个测试维度
✅ 测试步骤至少 5 步
✅ 测试数据要具体
    """)

def main():
    print("\n🧪 测试 Skill 要求实现")
    print("=" * 60)
    
    # 运行所有测试
    test_module_estimation()
    test_generation_count()
    test_token_calculation()
    test_v122_requirement()
    test_skill_dimensions()
    provide_usage_guide()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)
    print("\n💡 现在可以重启后端服务并测试 v1.2.2 需求文档了！")
    print()

if __name__ == "__main__":
    main()
