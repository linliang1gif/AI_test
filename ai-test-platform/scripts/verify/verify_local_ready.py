"""
本地环境就绪检查
验证本地开发环境是否配置正确
"""
import os
import sys
import requests
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def check_item(name, check_func):
    """检查单项"""
    try:
        result, message = check_func()
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if result else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{status} {name:40} {message}")
        return result
    except Exception as e:
        print(f"{Colors.RED}❌ FAIL{Colors.END} {name:40} 异常: {str(e)[:50]}")
        return False

def check_venv():
    """检查虚拟环境"""
    venv_python = Path("venv/Scripts/python.exe")
    if venv_python.exists():
        return True, "虚拟环境存在"
    return False, "虚拟环境不存在，请运行: python -m venv venv"

def check_env_file():
    """检查.env文件"""
    if Path(".env").exists():
        return True, ".env文件存在"
    return False, ".env文件不存在，建议: cp .env.example .env"

def check_env_not_tracked():
    """检查.env是否被Git跟踪"""
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if ".env" in content:
            return True, ".env已在.gitignore中"
    return False, ".env可能被Git跟踪，请检查.gitignore"

def check_backend_health():
    """检查后端健康"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            return True, "后端运行正常 (200)"
        return False, f"后端返回 {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "后端未启动，请运行: python backend_api_server.py"
    except Exception as e:
        return False, f"连接失败: {str(e)[:30]}"

def check_backend_docs():
    """检查API文档"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            return True, "API文档可访问"
        return False, f"API文档返回 {response.status_code}"
    except:
        return False, "API文档不可访问"

def check_frontend():
    """检查前端"""
    for port in [5173, 5174]:
        try:
            response = requests.get(f"http://localhost:{port}", timeout=3)
            if response.status_code == 200:
                return True, f"前端运行正常 (端口{port})"
        except:
            continue
    return False, "前端未启动，请运行: cd frontend && npm run dev"

def check_database():
    """检查数据库"""
    db_path = Path("data/test_platform.db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / 1024 / 1024
        return True, f"数据库存在 ({size_mb:.2f}MB)"
    return False, "数据库不存在"

def check_mock_config():
    """检查Mock配置"""
    env_example = Path(".env.example")
    if env_example.exists():
        content = env_example.read_text()
        if "APP_MODE=mock" in content and "MOCK_API_BASE_URL" in content:
            return True, "Mock配置完整"
    return False, "Mock配置缺失"

def main():
    print("="*80)
    print(f"{Colors.BLUE}AI Test Platform - 本地环境就绪检查{Colors.END}")
    print("="*80)
    print()
    
    results = []
    
    print(f"{Colors.YELLOW}【环境配置检查】{Colors.END}")
    print("-"*80)
    results.append(check_item("虚拟环境", check_venv))
    results.append(check_item(".env文件", check_env_file))
    results.append(check_item(".env未被跟踪", check_env_not_tracked))
    results.append(check_item("Mock配置", check_mock_config))
    results.append(check_item("数据库文件", check_database))
    print()
    
    print(f"{Colors.YELLOW}【服务运行检查】{Colors.END}")
    print("-"*80)
    results.append(check_item("后端健康检查", check_backend_health))
    results.append(check_item("API文档", check_backend_docs))
    results.append(check_item("前端服务", check_frontend))
    print()
    
    # 统计
    total = len(results)
    passed = sum(results)
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print("="*80)
    print(f"{Colors.YELLOW}【检查结果】{Colors.END}")
    print("="*80)
    print(f"总计: {total} 项")
    print(f"{Colors.GREEN}✅ 通过: {passed} 项{Colors.END}")
    print(f"{Colors.RED}❌ 失败: {failed} 项{Colors.END}")
    print(f"通过率: {pass_rate:.1f}%")
    print("="*80)
    
    if pass_rate >= 75:
        print(f"\n{Colors.GREEN}✅ 环境就绪，可以开始开发{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}⚠️  环境未就绪，请检查失败项{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
