#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
四阶段系统快速验证脚本
一键验证所有模块是否正常工作
"""

import requests
import sys


BASE_URL = "http://localhost:8000/api"


def check_module(name, endpoint):
    """检查单个模块"""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        data = response.json()
        status = data.get('status', 'unknown')
        
        if status == 'healthy':
            print(f"✅ {name:20s} 正常")
            return True
        else:
            print(f"❌ {name:20s} 异常: {status}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {name:20s} 连接失败")
        return False
    except Exception as e:
        print(f"❌ {name:20s} 错误: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🔍 四阶段系统快速验证")
    print("="*60)
    
    modules = [
        ("Test Agent", "/agent/health"),
        ("Strategy Engine", "/strategy/health"),
        ("Orchestrator", "/orchestrator/health"),
        ("Self-Healing", "/healing/health")
    ]
    
    print("\n检查模块状态:")
    print("-" * 60)
    
    results = []
    for name, endpoint in modules:
        ok = check_module(name, endpoint)
        results.append(ok)
    
    print("-" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n结果: {passed}/{total} 模块正常")
    
    if passed == total:
        print("\n✅ 四阶段系统完全就绪！")
        print("\n可用功能:")
        print("   1. AI 智能决策 (Test Agent)")
        print("   2. 自动策略生成 (Strategy Engine)")
        print("   3. 自动测试执行 (Orchestrator)")
        print("   4. 自动失败修复 (Self-Healing)")
        print("\n访问 API 文档: http://localhost:8000/docs")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个模块异常")
        print("\n请检查:")
        print("   1. 后端服务是否启动: python backend_api_server.py")
        print("   2. 端口是否被占用: 8000")
        print("   3. 依赖是否安装: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
