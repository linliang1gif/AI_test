"""
API契约检查
验证前端api.js中的核心路径是否与后端openapi.json匹配
"""
import requests
import re
import sys

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

BASE_URL = "http://localhost:8000"

# 前端核心API路径（从api.js提取）
FRONTEND_CORE_APIS = {
    "/api/v2/projects": ["GET", "POST"],
    "/api/v2/projects/{id}": ["GET", "PUT", "DELETE"],
    "/api/v2/environments": ["GET", "POST"],
    "/api/v2/environments/{id}": ["GET", "PUT", "DELETE"],
    "/api/v2/swagger/api-specs": ["GET"],
    "/api/v2/swagger/import-url": ["POST"],
    "/api/v2/swagger/import-file": ["POST"],
    "/api/v2/test-cases": ["GET"],
    "/api/v2/test-cases/{id}": ["GET"],
    "/api/v2/test-cases/{id}/execute": ["POST"],
    "/api/v2/test-cases/batch-execute": ["POST"],
    "/api/v2/test-runs": ["GET", "POST"],
    "/api/v2/test-runs/{id}": ["GET"],
    "/api/v2/test-runs/{id}/cases": ["GET"],
    "/api/v2/observability/runs/{id}/cases": ["GET"],
    "/api/v2/dashboard/summary": ["GET"],
}

def normalize_path(path):
    """标准化路径，将{id}、{project_id}等统一为{id}"""
    return re.sub(r'\{[^}]+\}', '{id}', path)

def check_contract():
    """检查API契约"""
    print("="*100)
    print(f"{Colors.BLUE}API契约检查{Colors.END}")
    print("="*100)
    print(f"后端地址: {BASE_URL}")
    print("="*100)
    print()
    
    # 获取后端OpenAPI规范
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        if response.status_code != 200:
            print(f"{Colors.RED}❌ 无法获取后端OpenAPI规范 (状态码: {response.status_code}){Colors.END}")
            return 1
        
        openapi_spec = response.json()
        backend_paths = set(openapi_spec["paths"].keys())
        
        # 标准化后端路径
        normalized_backend = {normalize_path(p): p for p in backend_paths}
        
    except Exception as e:
        print(f"{Colors.RED}❌ 获取OpenAPI规范失败: {str(e)}{Colors.END}")
        print(f"{Colors.YELLOW}提示: 请确保后端服务已启动 (python backend_api_server.py){Colors.END}")
        return 1
    
    print(f"{Colors.YELLOW}【前端API契约检查】{Colors.END}")
    print("-"*100)
    print(f"{'前端路径':<50} {'方法':<15} {'后端匹配':<15} {'状态'}")
    print("-"*100)
    
    results = []
    mismatches = []
    
    for fe_path, methods in sorted(FRONTEND_CORE_APIS.items()):
        normalized_fe = normalize_path(fe_path)
        
        # 检查路径是否存在
        if normalized_fe in normalized_backend:
            backend_path = normalized_backend[normalized_fe]
            backend_methods = set(openapi_spec["paths"][backend_path].keys())
            backend_methods.discard('parameters')  # 移除parameters
            
            # 检查方法是否匹配
            for method in methods:
                method_lower = method.lower()
                if method_lower in backend_methods:
                    print(f"{Colors.GREEN}✅{Colors.END} {fe_path:<48} {method:<15} {backend_path:<15} 匹配")
                    results.append(True)
                else:
                    print(f"{Colors.RED}❌{Colors.END} {fe_path:<48} {method:<15} {backend_path:<15} 方法不存在")
                    results.append(False)
                    mismatches.append(f"{fe_path} {method} - 后端不支持此方法")
        else:
            # 路径不存在
            for method in methods:
                print(f"{Colors.RED}❌{Colors.END} {fe_path:<48} {method:<15} {'N/A':<15} 路径不存在")
                results.append(False)
                mismatches.append(f"{fe_path} {method} - 后端路径不存在")
    
    print()
    
    # 统计
    total = len(results)
    passed = sum(results)
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print("="*100)
    print(f"{Colors.YELLOW}【检查结果】{Colors.END}")
    print("="*100)
    print(f"总计: {total} 个API方法")
    print(f"{Colors.GREEN}✅ 匹配: {passed} 个{Colors.END}")
    print(f"{Colors.RED}❌ 不匹配: {failed} 个{Colors.END}")
    print(f"匹配率: {pass_rate:.1f}%")
    
    if mismatches:
        print()
        print(f"{Colors.YELLOW}【不匹配详情】{Colors.END}")
        print("-"*100)
        for i, mismatch in enumerate(mismatches, 1):
            print(f"{i}. {mismatch}")
    
    print("="*100)
    
    if pass_rate >= 90:
        print(f"\n{Colors.GREEN}✅ API契约检查通过{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}⚠️  API契约存在不匹配，请修复{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(check_contract())
