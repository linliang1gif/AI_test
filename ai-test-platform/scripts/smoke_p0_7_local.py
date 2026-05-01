"""
P0.7 本地验收脚本
验证本地平台主流程是否可用
不依赖公司真实项目，不依赖真实Token
"""
import requests
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def test_endpoint(name, method, path, expected_status=200):
    """测试单个接口"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json={}, timeout=10)
        
        # 只有2xx才算成功
        success = 200 <= response.status_code < 300 and response.status_code == expected_status
        status_color = Colors.GREEN if success else Colors.RED
        status_text = "✅ PASS" if success else "❌ FAIL"
        
        print(f"{status_text} {name:40} {method:6} {path:50} {status_color}{response.status_code}{Colors.END}")
        
        return success
    except Exception as e:
        print(f"❌ FAIL {name:40} {method:6} {path:50} {Colors.RED}ERROR: {str(e)[:30]}{Colors.END}")
        return False

def main():
    print("="*120)
    print(f"{Colors.BLUE}AI Test Platform - P0.7 本地验收{Colors.END}")
    print("="*120)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端地址: {BASE_URL}")
    print(f"模式: Mock (不依赖真实项目)")
    print("="*120)
    print()
    
    results = []
    
    # 核心接口验收
    print(f"{Colors.YELLOW}【核心接口验收】{Colors.END}")
    print("-"*120)
    
    tests = [
        ("健康检查", "GET", "/health", 200),
        ("项目列表", "GET", "/api/v2/projects", 200),
        ("环境列表", "GET", "/api/v2/environments", 200),
        ("API规范列表", "GET", "/api/v2/swagger/api-specs", 200),
        ("测试用例列表", "GET", "/api/v2/test-cases", 200),
        ("执行记录列表", "GET", "/api/v2/test-runs", 200),
        ("Dashboard摘要", "GET", "/api/v2/dashboard/summary", 200),
        ("可观测性-执行列表", "GET", "/api/v2/observability/runs", 200),
    ]
    
    for name, method, path, expected in tests:
        result = test_endpoint(name, method, path, expected)
        results.append(result)
    
    print()
    
    # 统计结果
    total = len(results)
    passed = sum(results)
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print("="*120)
    print(f"{Colors.YELLOW}【验收结果统计】{Colors.END}")
    print("="*120)
    print(f"总计: {total} 个接口")
    print(f"{Colors.GREEN}✅ 通过: {passed} 个{Colors.END}")
    print(f"{Colors.RED}❌ 失败: {failed} 个{Colors.END}")
    print(f"通过率: {pass_rate:.1f}%")
    print("="*120)
    
    # 判断是否通过
    if pass_rate >= 85:
        print(f"\n{Colors.GREEN}🎉 验收通过！平台核心功能正常{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}⚠️  验收未通过，请检查失败的接口{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
