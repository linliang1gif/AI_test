#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 项目诊断工具
检查项目配置和依赖
"""

import sys
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("\n🐍 检查Python版本...")
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ⚠️  建议使用Python 3.8+")
        return False

    print("  ✅ Python版本符合要求")
    return True

def check_dependencies():
    """检查依赖"""
    print("\n📦 检查依赖...")

    required = [
        "fastapi",
        "uvicorn",
        "requests",
        "pytest",
        "openpyxl",
        "python-docx",
        "pydantic",
        "python-dotenv"
    ]

    missing = []

    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} (缺失)")
            missing.append(pkg)

    if missing:
        print(f"\n⚠️  缺少依赖: {', '.join(missing)}")
        print("  运行: pip install -r requirements.txt")
        return False

    print("\n✅ 所有依赖已安装")
    return True

def check_directories():
    """检查目录结构"""
    print("\n📁 检查目录结构...")

    root = Path(__file__).parent
    required_dirs = [
        "ai",
        "ai_core",
        "config",
        "executor",
        "parser",
        "test_design",
        "automation",
        "analysis",
        "report",
        "export"
    ]

    missing = []

    for dir_name in required_dirs:
        dir_path = root / dir_name
        if dir_path.exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ (缺失)")
            missing.append(dir_name)

    if missing:
        print(f"\n⚠️  缺少目录: {', '.join(missing)}")
        return False

    print("\n✅ 目录结构完整")
    return True

def check_config():
    """检查配置文件"""
    print("\n⚙️  检查配置...")

    root = Path(__file__).parent
    env_file = root / ".env"

    if not env_file.exists():
        print("  ⚠️  .env文件不存在")
        print("  提示: 复制.env.example为.env")
        return False

    print("  ✅ .env文件存在")

    # 检查配置内容
    try:
        sys.path.insert(0, str(root))
        from config.config import get_config

        config = get_config()
        print(f"  AI提供商: {config.ai.default_provider}")
        print(f"  输出目录: {config.paths.output_dir}")

        print("\n✅ 配置加载成功")
        return True

    except Exception as e:
        print(f"  ❌ 配置加载失败: {e}")
        return False

def check_pytest():
    """检查pytest"""
    print("\n🧪 检查pytest...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"  ✅ {result.stdout.strip()}")
            return True
        else:
            print("  ❌ pytest不可用")
            return False

    except Exception as e:
        print(f"  ❌ pytest检查失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 AI Test Platform - 项目诊断")
    print("=" * 60)

    checks = [
        ("Python版本", check_python_version),
        ("依赖包", check_dependencies),
        ("目录结构", check_directories),
        ("配置文件", check_config),
        ("Pytest", check_pytest),
    ]

    results = {}

    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ {name}检查异常: {e}")
            results[name] = False

    print("\n" + "=" * 60)
    print("📊 诊断总结")
    print("=" * 60)

    for name, result in results.items():
        status = "✅ 正常" if result else "❌ 异常"
        print(f"  {name}: {status}")

    total = len(results)
    passed = sum(1 for r in results.values() if r)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 项目状态良好，可以开始使用!")
        print("\n💡 快速开始:")
        print("  python quick_test.py      # 快速测试")
        print("  python test_workflow.py   # 完整流程测试")
    else:
        print("\n⚠️  请先解决上述问题")

    print("=" * 60)

if __name__ == "__main__":
    main()
