#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Agent V3 测试脚本
验证接入文档解析能力后的功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from agent.test_agent_service import get_test_agent_service


def test_agent_v3_with_parsing():
    """测试 Agent V3 的文档解析能力"""
    print("=" * 70)
    print("Test Agent V3 - 文档解析能力测试")
    print("=" * 70)
    
    # 准备测试需求
    requirement = """
# 用户管理系统需求

## 功能模块

### 用户注册模块
- 支持邮箱注册
- 支持手机号注册
- 密码强度验证

### 用户登录模块
- 支持多种登录方式
- 记住登录状态
- 登录失败锁定

### 用户信息管理模块
- 查看个人信息
- 编辑个人信息
- 头像上传

### 权限管理模块
- 角色分配
- 权限控制
- 访问验证
"""
    
    git_diff = """
+ def register_user(email, password):
+     # 新增用户注册功能
+     user = User(email=email)
+     user.set_password(password)
+     db.session.add(user)
+     db.session.commit()
"""
    
    # 获取 Agent 服务
    agent_service = get_test_agent_service()
    
    # 测试1: 解析需求
    print("\n【测试1】解析需求文档")
    print("-" * 70)
    parsed_data = agent_service.parse_requirement(requirement)
    
    print(f"✅ 解析结果:")
    print(f"   - 模块数量: {len(parsed_data['modules'])}")
    for module in parsed_data['modules']:
        print(f"   - {module['name']}: {module.get('description', '无描述')}")
    
    # 测试2: 完整分析（V3增强）
    print("\n【测试2】完整分析（V3增强版）")
    print("-" * 70)
    decision = agent_service.analyze(requirement, git_diff)
    
    print(f"\n✅ 决策结果:")
    print(f"   - 版本: {decision.get('version', 'unknown')}")
    print(f"   - 需要测试: {decision['need_test']}")
    print(f"   - 影响模块: {decision['modules']}")
    print(f"   - 优先级: {decision['priority']}")
    print(f"   - 风险等级: {decision['risk_level']}")
    print(f"   - 置信度: {decision['confidence']}")
    print(f"   - 执行建议: {decision['execution_hint']}")
    
    # 测试3: 验证 parsed_modules 字段
    print("\n【测试3】验证解析的模块详情")
    print("-" * 70)
    if 'parsed_modules' in decision:
        print(f"✅ parsed_modules 字段存在")
        print(f"   - 详细模块数: {len(decision['parsed_modules'])}")
        for module in decision['parsed_modules'][:3]:  # 只显示前3个
            print(f"   - {module['name']}: {len(module.get('functions', []))} 个功能")
    else:
        print(f"❌ parsed_modules 字段缺失")
    
    # 测试4: 验证向后兼容性
    print("\n【测试4】验证向后兼容性")
    print("-" * 70)
    required_fields = ['need_test', 'modules', 'priority', 'action', 'confidence', 'test_scope', 'execution_hint', 'timestamp']
    
    missing_fields = [field for field in required_fields if field not in decision]
    
    if not missing_fields:
        print(f"✅ 所有必需字段都存在")
    else:
        print(f"❌ 缺少字段: {missing_fields}")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
    
    return decision


if __name__ == "__main__":
    try:
        result = test_agent_v3_with_parsing()
        
        # 输出完整结果（用于调试）
        print("\n【完整决策结果】")
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
