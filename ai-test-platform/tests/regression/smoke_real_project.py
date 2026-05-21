#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实项目接入验收脚本

验证真实项目模式下的连接、Swagger检测和安全冒烟测试
"""

import sys
import os
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# 配置
BACKEND_URL = "http://localhost:8000"


class RealProjectSmokeTest:
    def __init__(self):
        self.results = []
        self.app_mode = os.getenv("APP_MODE", "mock")
        self.target_url = os.getenv("TARGET_API_BASE_URL", "")
        self.target_token = os.getenv("TARGET_API_TOKEN", "")
        
    def print_header(self):
        print("=" * 100)
        print("真实项目接入验收")
        print("=" * 100)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"后端地址: {BACKEND_URL}")
        print(f"运行模式: {self.app_mode}")
        print(f"目标地址: {self.target_url or '未配置'}")
        print(f"Token配置: {'已配置' if self.target_token else '未配置'}")
        print("=" * 100)
        print()
    
    def check_backend_health(self) -> bool:
        """检查后端是否运行"""
        try:
            resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if resp.status_code == 200:
                print("✅ 后端服务正常")
                return True
            else:
                print(f"❌ 后端服务异常: {resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ 后端服务无法连接: {e}")
            return False
    
    def check_env_config(self) -> bool:
        """检查环境配置"""
        print("\n【环境配置检查】")
        print("─" * 100)
        
        checks = {
            "APP_MODE": self.app_mode,
            "TARGET_API_BASE_URL": self.target_url,
            "TARGET_API_TOKEN": "已配置" if self.target_token else "未配置"
        }
        
        for key, value in checks.items():
            print(f"{key}: {value}")
        
        if self.app_mode != "real":
            print("\n⚠️  当前模式不是 'real'，建议修改 .env 文件中的 APP_MODE=real")
            print("   本次验收将使用配置的 TARGET_API_BASE_URL 进行测试")
        
        if not self.target_url:
            print("\n❌ TARGET_API_BASE_URL 未配置")
            print("   请在 .env 文件中配置真实项目地址")
            return False
        
        print("\n✅ 环境配置检查通过")
        return True
    
    def test_connection_check_api(self) -> bool:
        """测试连接检测接口"""
        print("\n【连接检测接口测试】")
        print("─" * 100)
        
        try:
            # 使用httpbin作为测试目标（不使用真实项目）
            test_url = "https://httpbin.org"
            
            resp = requests.post(
                f"{BACKEND_URL}/api/v2/real-project/check-connection",
                json={
                    "base_url": test_url,
                    "health_path": "/get",
                    "auth_type": "none",
                    "timeout": 10
                },
                timeout=15
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ 连接检测接口正常")
                print(f"   目标: {test_url}")
                print(f"   状态: {data.get('message')}")
                print(f"   耗时: {data.get('duration_ms')}ms")
                return data.get("success", False)
            else:
                print(f"❌ 连接检测接口异常: {resp.status_code}")
                return False
        
        except Exception as e:
            print(f"❌ 连接检测接口测试失败: {e}")
            return False
    
    def test_swagger_check_api(self) -> bool:
        """测试Swagger检测接口"""
        print("\n【Swagger检测接口测试】")
        print("─" * 100)
        
        try:
            # 使用公开的Swagger示例
            test_swagger_url = "https://petstore.swagger.io/v2/swagger.json"
            
            resp = requests.post(
                f"{BACKEND_URL}/api/v2/real-project/check-swagger",
                json={
                    "swagger_url": test_swagger_url,
                    "auth_type": "none",
                    "timeout": 10
                },
                timeout=15
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    swagger_info = data.get("swagger_info", {})
                    print(f"✅ Swagger检测接口正常")
                    print(f"   标题: {swagger_info.get('title')}")
                    print(f"   版本: {swagger_info.get('version')}")
                    print(f"   路径数: {swagger_info.get('total_paths')}")
                    print(f"   操作数: {swagger_info.get('total_operations')}")
                    print(f"   安全操作: {swagger_info.get('safe_operations')} (GET)")
                    print(f"   写操作: {swagger_info.get('write_operations')} (POST/PUT/DELETE)")
                    return True
                else:
                    print(f"⚠️  Swagger检测失败: {data.get('message')}")
                    return False
            else:
                print(f"❌ Swagger检测接口异常: {resp.status_code}")
                return False
        
        except Exception as e:
            print(f"❌ Swagger检测接口测试失败: {e}")
            return False
    
    def test_safe_methods_api(self) -> bool:
        """测试安全方法列表接口"""
        print("\n【安全方法列表接口测试】")
        print("─" * 100)
        
        try:
            resp = requests.get(
                f"{BACKEND_URL}/api/v2/real-project/safe-methods",
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ 安全方法列表接口正常")
                print(f"   安全方法: {', '.join(data.get('safe_methods', []))}")
                print(f"   危险方法: {', '.join(data.get('unsafe_methods', []))}")
                print(f"   提示: {data.get('message')}")
                return True
            else:
                print(f"❌ 安全方法列表接口异常: {resp.status_code}")
                return False
        
        except Exception as e:
            print(f"❌ 安全方法列表接口测试失败: {e}")
            return False
    
    def test_real_project_connection(self) -> bool:
        """测试真实项目连接（如果配置了）"""
        if not self.target_url:
            print("\n⚠️  跳过真实项目连接测试（未配置TARGET_API_BASE_URL）")
            return True
        
        print("\n【真实项目连接测试】")
        print("─" * 100)
        print(f"目标地址: {self.target_url}")
        print(f"Token: {'已配置' if self.target_token else '未配置'}")
        
        try:
            resp = requests.post(
                f"{BACKEND_URL}/api/v2/real-project/check-connection",
                json={
                    "base_url": self.target_url,
                    "token": self.target_token if self.target_token else None,
                    "health_path": "/health",
                    "auth_type": "bearer" if self.target_token else "none",
                    "timeout": 10
                },
                timeout=15
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    print(f"✅ 真实项目连接成功")
                    print(f"   状态码: {data.get('status_code')}")
                    print(f"   耗时: {data.get('duration_ms')}ms")
                    return True
                else:
                    print(f"⚠️  真实项目连接失败: {data.get('message')}")
                    print(f"   错误: {data.get('error', '未知')}")
                    return False
            else:
                print(f"❌ 连接检测接口异常: {resp.status_code}")
                return False
        
        except Exception as e:
            print(f"❌ 真实项目连接测试失败: {e}")
            return False
    
    def print_summary(self):
        """输出测试总结"""
        print("\n" + "=" * 100)
        print("【验收结果统计】")
        print("=" * 100)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"总计: {total} 项测试")
        print(f"✅ 通过: {passed} 项")
        print(f"❌ 失败: {failed} 项")
        print(f"通过率: {pass_rate:.1f}%")
        print("=" * 100)
        
        if pass_rate >= 80:
            print("\n🎉 真实项目接入验收通过！")
        else:
            print("\n⚠️  真实项目接入验收未通过，请检查失败项")
        
        print()
    
    def run(self):
        """运行所有测试"""
        self.print_header()
        
        # 前置检查
        if not self.check_backend_health():
            print("\n❌ 后端服务未运行，请先启动后端")
            return
        
        # 环境配置检查
        env_ok = self.check_env_config()
        self.results.append(env_ok)
        
        # 接口测试
        self.results.append(self.test_connection_check_api())
        self.results.append(self.test_swagger_check_api())
        self.results.append(self.test_safe_methods_api())
        
        # 真实项目连接测试（可选）
        if self.target_url:
            self.results.append(self.test_real_project_connection())
        
        # 输出总结
        self.print_summary()


if __name__ == "__main__":
    tester = RealProjectSmokeTest()
    tester.run()
