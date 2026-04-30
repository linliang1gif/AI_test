#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 健康检查工具
检查系统各组件状态
"""

import sys
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Tuple

class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.results = []
        
    def check_python_version(self) -> Tuple[bool, str]:
        """检查Python版本"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 11:
            return True, f"✅ Python {version.major}.{version.minor}.{version.micro}"
        else:
            return False, f"❌ Python版本过低 ({version.major}.{version.minor}), 需要3.11+"
    
    def check_python_dependencies(self) -> Tuple[bool, str]:
        """检查Python依赖"""
        required_packages = [
            "fastapi",
            "uvicorn",
            "requests",
            "pydantic",
            "pytest"
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if not missing:
            return True, f"✅ Python依赖完整 ({len(required_packages)}个包)"
        else:
            return False, f"❌ 缺少依赖: {', '.join(missing)}"
    
    def check_nodejs(self) -> Tuple[bool, str]:
        """检查Node.js"""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, f"✅ Node.js {version}"
            else:
                return False, "❌ Node.js未正确安装"
        except FileNotFoundError:
            return False, "❌ Node.js未安装"
        except Exception as e:
            return False, f"❌ Node.js检查失败: {e}"
    
    def check_frontend_dependencies(self) -> Tuple[bool, str]:
        """检查前端依赖"""
        frontend_dir = self.root_dir / "frontend"
        node_modules = frontend_dir / "node_modules"
        
        if node_modules.exists():
            return True, "✅ 前端依赖已安装"
        else:
            return False, "❌ 前端依赖未安装 (运行: cd frontend && npm install)"
    
    def check_ollama(self) -> Tuple[bool, str]:
        """检查Ollama服务"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m["name"] for m in models]
                return True, f"✅ Ollama运行中 ({len(models)}个模型: {', '.join(model_names[:3])})"
            else:
                return False, f"❌ Ollama响应异常 (状态码: {response.status_code})"
        except requests.exceptions.ConnectionError:
            return False, "⚠️  Ollama未运行 (可选，如使用云端AI可忽略)"
        except Exception as e:
            return False, f"⚠️  Ollama检查失败: {e}"
    
    def check_backend_api(self) -> Tuple[bool, str]:
        """检查后端API"""
        try:
            response = requests.get("http://127.0.0.1:8081/api/dashboard/stats", timeout=3)
            if response.status_code == 200:
                return True, "✅ 后端API运行中 (http://127.0.0.1:8081)"
            else:
                return False, f"❌ 后端API响应异常 (状态码: {response.status_code})"
        except requests.exceptions.ConnectionError:
            return False, "❌ 后端API未运行 (运行: python backend_api_server.py)"
        except Exception as e:
            return False, f"❌ 后端API检查失败: {e}"
    
    def check_frontend_server(self) -> Tuple[bool, str]:
        """检查前端服务"""
        try:
            response = requests.get("http://localhost:3000", timeout=3)
            if response.status_code == 200:
                return True, "✅ 前端服务运行中 (http://localhost:3000)"
            else:
                return False, f"❌ 前端服务响应异常 (状态码: {response.status_code})"
        except requests.exceptions.ConnectionError:
            return False, "❌ 前端服务未运行 (运行: cd frontend && npm run dev)"
        except Exception as e:
            return False, f"❌ 前端服务检查失败: {e}"
    
    def check_directories(self) -> Tuple[bool, str]:
        """检查目录结构"""
        required_dirs = [
            "data",
            "uploads",
            "output",
            "logs"
        ]
        
        missing = []
        for dir_name in required_dirs:
            dir_path = self.root_dir / dir_name
            if not dir_path.exists():
                missing.append(dir_name)
        
        if not missing:
            return True, f"✅ 目录结构完整 ({len(required_dirs)}个目录)"
        else:
            return False, f"⚠️  缺少目录: {', '.join(missing)} (将自动创建)"
    
    def check_env_file(self) -> Tuple[bool, str]:
        """检查环境配置文件"""
        env_file = self.root_dir / ".env"
        env_example = self.root_dir / ".env.example"
        
        if env_file.exists():
            return True, "✅ 环境配置文件存在 (.env)"
        elif env_example.exists():
            return False, "⚠️  .env文件不存在 (复制.env.example并配置)"
        else:
            return False, "❌ 缺少环境配置文件"
    
    def run_all_checks(self) -> List[Tuple[str, bool, str]]:
        """运行所有检查"""
        checks = [
            ("Python版本", self.check_python_version),
            ("Python依赖", self.check_python_dependencies),
            ("Node.js", self.check_nodejs),
            ("前端依赖", self.check_frontend_dependencies),
            ("目录结构", self.check_directories),
            ("环境配置", self.check_env_file),
            ("Ollama服务", self.check_ollama),
            ("后端API", self.check_backend_api),
            ("前端服务", self.check_frontend_server),
        ]
        
        results = []
        for name, check_func in checks:
            success, message = check_func()
            results.append((name, success, message))
        
        return results
    
    def print_results(self, results: List[Tuple[str, bool, str]]):
        """打印检查结果"""
        print("\n" + "=" * 60)
        print("🏥 AI Test Platform - 健康检查报告")
        print("=" * 60 + "\n")
        
        critical_failures = 0
        warnings = 0
        
        for name, success, message in results:
            print(f"{name:20s} {message}")
            if not success:
                if "❌" in message:
                    critical_failures += 1
                elif "⚠️" in message:
                    warnings += 1
        
        print("\n" + "=" * 60)
        print("📊 检查摘要")
        print("=" * 60)
        print(f"总检查项: {len(results)}")
        print(f"通过: {len([r for r in results if r[1]])}")
        print(f"警告: {warnings}")
        print(f"失败: {critical_failures}")
        
        if critical_failures == 0 and warnings == 0:
            print("\n✅ 系统状态良好，可以正常使用！")
        elif critical_failures == 0:
            print(f"\n⚠️  系统基本正常，但有 {warnings} 个警告项")
        else:
            print(f"\n❌ 发现 {critical_failures} 个关键问题，请先解决")
        
        print("=" * 60 + "\n")
        
        return critical_failures == 0
    
    def suggest_fixes(self, results: List[Tuple[str, bool, str]]):
        """建议修复方案"""
        failures = [r for r in results if not r[1] and "❌" in r[2]]
        
        if not failures:
            return
        
        print("🔧 修复建议:\n")
        
        for name, _, message in failures:
            if "Python依赖" in name:
                print("1. 安装Python依赖:")
                print("   pip install -r requirements.txt\n")
            
            elif "Node.js" in name:
                print("2. 安装Node.js:")
                print("   访问 https://nodejs.org/ 下载安装\n")
            
            elif "前端依赖" in name:
                print("3. 安装前端依赖:")
                print("   cd frontend")
                print("   npm install\n")
            
            elif "后端API" in name:
                print("4. 启动后端服务:")
                print("   python backend_api_server.py\n")
            
            elif "前端服务" in name:
                print("5. 启动前端服务:")
                print("   cd frontend")
                print("   npm run dev\n")
            
            elif "环境配置" in name:
                print("6. 配置环境变量:")
                print("   cp .env.example .env")
                print("   # 编辑.env文件配置AI密钥\n")

def main():
    """主函数"""
    checker = HealthChecker()
    results = checker.run_all_checks()
    is_healthy = checker.print_results(results)
    
    if not is_healthy:
        checker.suggest_fixes(results)
    
    sys.exit(0 if is_healthy else 1)

if __name__ == "__main__":
    main()
