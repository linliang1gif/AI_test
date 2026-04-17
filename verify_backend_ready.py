#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证后端服务准备情况

检查：
1. 依赖模块是否可用
2. 配置是否正确
3. 端口是否可用
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ai-test-platform"))


def check_dependencies():
    """检查依赖"""
    print("=" * 80)
    print("🔍 检查依赖模块")
    print("=" * 80)
    
    dependencies = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "pydantic": "Pydantic",
        "requests": "Requests"
    }
    
    missing = []
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} (未安装)")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  缺少依赖: {', '.join(missing)}")
        print(f"\n安装命令:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    print(f"\n✅ 所有依赖已安装")
    return True


def check_modules():
    """检查项目模块"""
    print("\n" + "=" * 80)
    print("🔍 检查项目模块")
    print("=" * 80)
    
    modules = {
        "modules.resilience": "ResilienceEngine",
        "modules.agents": "Agents",
        "modules.executor": "ExecutionEngine",
        "core": "Core Models"
    }
    
    all_ok = True
    
    for module, name in modules.items():
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError as e:
            print(f"  ❌ {name}: {e}")
            all_ok = False
    
    if all_ok:
        print(f"\n✅ 所有项目模块可用")
    else:
        print(f"\n⚠️  部分模块不可用")
    
    return all_ok


def check_port():
    """检查端口是否可用"""
    print("\n" + "=" * 80)
    print("🔍 检查端口")
    print("=" * 80)
    
    import socket
    
    ports = {
        8000: "后端服务",
        5173: "前端服务"
    }
    
    for port, name in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"  ⚠️  端口 {port} ({name}) 已被占用")
        else:
            print(f"  ✅ 端口 {port} ({name}) 可用")


def check_config():
    """检查配置"""
    print("\n" + "=" * 80)
    print("🔍 检查配置")
    print("=" * 80)
    
    # 检查 .env 文件
    env_file = Path("ai-test-platform/.env")
    
    if env_file.exists():
        print(f"  ✅ .env 文件存在")
        
        # 读取配置
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键配置
        if 'AI_PROVIDER' in content:
            print(f"  ✅ AI_PROVIDER 已配置")
        else:
            print(f"  ⚠️  AI_PROVIDER 未配置")
        
        if 'ollama' in content.lower():
            print(f"  ✅ 使用 Ollama (本地)")
        
    else:
        print(f"  ⚠️  .env 文件不存在")
        print(f"     位置: {env_file}")


def main():
    """主函数"""
    print("=" * 80)
    print("🚀 后端服务准备情况检查")
    print("=" * 80)
    
    results = []
    
    # 检查依赖
    results.append(("依赖模块", check_dependencies()))
    
    # 检查项目模块
    results.append(("项目模块", check_modules()))
    
    # 检查端口
    check_port()
    
    # 检查配置
    check_config()
    
    # 汇总
    print("\n" + "=" * 80)
    print("📊 检查结果")
    print("=" * 80)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name:20s} {status}")
    
    all_passed = all(p for _, p in results)
    
    if all_passed:
        print("\n✅ 后端服务准备就绪！")
        print("\n启动命令:")
        print("  cd ai-test-platform")
        print("  py backend_api_server.py")
        return 0
    else:
        print("\n⚠️  后端服务未准备就绪")
        print("  请先解决上述问题")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
