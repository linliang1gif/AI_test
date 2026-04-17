#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 Agent 重构完成情况
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def check_design_agent():
    """检查 DesignAgent"""
    print("=" * 80)
    print("检查 DesignAgent")
    print("=" * 80)
    
    try:
        from modules.agents.design_agent import DesignAgent
        print("✅ DesignAgent 导入成功")
        
        # 创建实例
        agent = DesignAgent()
        print("✅ DesignAgent 实例化成功")
        
        # 检查方法
        methods = [
            'design_from_swagger',
            'design_from_requirement',
            'design_from_discovery',
            'optimize_testcases',
            'get_design_statistics'
        ]
        
        for method in methods:
            if hasattr(agent, method):
                print(f"✅ 方法存在: {method}")
            else:
                print(f"❌ 方法缺失: {method}")
        
        return True
        
    except Exception as e:
        print(f"❌ DesignAgent 检查失败: {e}")
        return False


def check_execution_agent():
    """检查 ExecutionAgent"""
    print("\n" + "=" * 80)
    print("检查 ExecutionAgent")
    print("=" * 80)
    
    try:
        # 检查文件是否存在且有内容
        exec_file = Path("modules/agents/execution_agent.py")
        if not exec_file.exists():
            print("❌ execution_agent.py 文件不存在")
            return False
        
        with open(exec_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        if len(lines) < 10:
            print(f"⚠️  execution_agent.py 文件内容不完整（只有 {len(lines)} 行）")
            print("   请在编辑器中保存文件")
            return False
        
        print(f"✅ execution_agent.py 文件存在（{len(lines)} 行）")
        
        # 尝试导入
        try:
            from modules.agents.execution_agent import ExecutionAgent, ExecutionEnvironment, ExecutionStrategy
            print("✅ ExecutionAgent 导入成功")
            
            # 创建实例
            agent = ExecutionAgent()
            print("✅ ExecutionAgent 实例化成功")
            
            # 检查方法
            methods = [
                'execute',
                'execute_single',
                'get_statistics'
            ]
            
            for method in methods:
                if hasattr(agent, method):
                    print(f"✅ 方法存在: {method}")
                else:
                    print(f"❌ 方法缺失: {method}")
            
            # 检查枚举
            print(f"✅ ExecutionEnvironment 枚举: {list(ExecutionEnvironment)}")
            print(f"✅ ExecutionStrategy 枚举: {list(ExecutionStrategy)}")
            
            return True
            
        except ImportError as e:
            print(f"⚠️  ExecutionAgent 导入失败: {e}")
            print("   可能是 __init__.py 中的导入被注释了")
            return False
        
    except Exception as e:
        print(f"❌ ExecutionAgent 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_integration():
    """检查集成"""
    print("\n" + "=" * 80)
    print("检查模块集成")
    print("=" * 80)
    
    try:
        # 检查 __init__.py
        init_file = Path("modules/agents/__init__.py")
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'ExecutionAgent' in content and not content.count('# from .execution_agent'):
            print("✅ __init__.py 已启用 ExecutionAgent 导入")
        else:
            print("⚠️  __init__.py 中 ExecutionAgent 导入被注释")
            print("   需要取消注释以启用")
        
        # 尝试从 modules.agents 导入
        try:
            from modules.agents import DesignAgent
            print("✅ 可以从 modules.agents 导入 DesignAgent")
        except:
            print("❌ 无法从 modules.agents 导入 DesignAgent")
        
        try:
            from modules.agents import ExecutionAgent
            print("✅ 可以从 modules.agents 导入 ExecutionAgent")
            return True
        except:
            print("⚠️  无法从 modules.agents 导入 ExecutionAgent")
            return False
        
    except Exception as e:
        print(f"❌ 集成检查失败: {e}")
        return False


def check_documentation():
    """检查文档"""
    print("\n" + "=" * 80)
    print("检查文档")
    print("=" * 80)
    
    docs = [
        "AGENT_REFACTORING_COMPLETE.md",
        "AGENT_REFACTORING_GUIDE.md",
        "REFACTORING_STATUS.md"
    ]
    
    for doc in docs:
        if Path(doc).exists():
            print(f"✅ {doc} 存在")
        else:
            print(f"❌ {doc} 不存在")
    
    # 检查示例
    examples = [
        "examples/demo_agents.py",
        "test_design_agent.py"
    ]
    
    for example in examples:
        if Path(example).exists():
            print(f"✅ {example} 存在")
        else:
            print(f"❌ {example} 不存在")
    
    return True


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🔍 Agent 重构验证")
    print("=" * 80)
    
    results = {
        "DesignAgent": check_design_agent(),
        "ExecutionAgent": check_execution_agent(),
        "集成": check_integration(),
        "文档": check_documentation()
    }
    
    print("\n" + "=" * 80)
    print("验证结果汇总")
    print("=" * 80)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print("=" * 80)
    print(f"总计: {passed}/{total} 通过")
    print("=" * 80)
    
    if passed == total:
        print("\n🎉 所有检查通过！重构完成！")
        print("\n下一步:")
        print("  1. 运行演示: py examples/demo_agents.py")
        print("  2. 集成到系统中")
    else:
        print(f"\n⚠️  {total - passed} 项检查失败")
        print("\n待完成:")
        if not results["ExecutionAgent"]:
            print("  1. 在编辑器中保存 modules/agents/execution_agent.py")
        if not results["集成"]:
            print("  2. 取消 modules/agents/__init__.py 中的注释")
        print("  3. 重新运行此验证脚本")


if __name__ == "__main__":
    main()
