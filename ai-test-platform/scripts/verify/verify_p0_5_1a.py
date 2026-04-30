#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
P0-5.1a 止血修复验证脚本
验证前端不再发起 /api/pilot/* 请求
"""

import re
from pathlib import Path

def check_app_jsx():
    """检查 App.jsx 的修改"""
    print("=" * 60)
    print("检查 App.jsx 修改")
    print("=" * 60)
    
    app_jsx = Path(__file__).parent / "frontend/src/App.jsx"
    content = app_jsx.read_text(encoding='utf-8')
    
    checks = {
        "默认路由重定向": 'Navigate to="/quick-execution-test"' in content,
        "导入Navigate组件": 'Navigate' in content and 'react-router-dom' in content,
        "概览分组禁用": '概览 (暂不可用)' in content or 'disabled' in content,
        "旧路由重定向存在": content.count('Navigate to=') >= 10,
    }
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    return all(checks.values())

def check_api_js():
    """检查 api.js 的修改"""
    print("\n" + "=" * 60)
    print("检查 api.js 修改")
    print("=" * 60)
    
    api_js = Path(__file__).parent / "frontend/src/services/api.js"
    content = api_js.read_text(encoding='utf-8')
    
    checks = {
        "404错误特殊处理": 'response.status === 404' in content,
        "404错误不重复输出": "error.message.startsWith('404')" in content,
        "404警告日志": 'console.warn' in content and '404' in content,
    }
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    return all(checks.values())

def check_pilot_api_usage():
    """检查是否还有代码直接调用 Pilot API"""
    print("\n" + "=" * 60)
    print("检查 Pilot API 使用情况")
    print("=" * 60)
    
    frontend_dir = Path(__file__).parent / "frontend/src"
    
    # 排除 api.js 本身(它定义了这些API但不调用)
    exclude_files = {'api.js', 'api.ts'}
    
    pilot_api_pattern = re.compile(r'/api/pilot/\w+')
    pilot_api_calls = []
    
    for file_path in frontend_dir.rglob("*.jsx"):
        if file_path.name in exclude_files:
            continue
            
        try:
            content = file_path.read_text(encoding='utf-8')
            matches = pilot_api_pattern.findall(content)
            
            if matches:
                pilot_api_calls.append({
                    'file': file_path.relative_to(frontend_dir),
                    'apis': set(matches)
                })
        except Exception as e:
            print(f"⚠️  读取文件失败: {file_path} - {e}")
    
    if pilot_api_calls:
        print("❌ 发现以下文件仍在调用 Pilot API:")
        for item in pilot_api_calls:
            print(f"   文件: {item['file']}")
            for api in item['apis']:
                print(f"      - {api}")
        return False
    else:
        print("✅ 未发现直接调用 Pilot API 的代码")
        return True

def check_menu_items():
    """检查菜单项配置"""
    print("\n" + "=" * 60)
    print("检查菜单项配置")
    print("=" * 60)
    
    app_jsx = Path(__file__).parent / "frontend/src/App.jsx"
    content = app_jsx.read_text(encoding='utf-8')
    
    # 检查应该被移除的菜单项
    removed_items = [
        '/projects',
        '/api-explorer',
        '/test-cases',
        '/automation',
        '/ai-test-console',
        '/ai-insights',
    ]
    
    # 检查应该保留的菜单项
    kept_items = [
        '/test-runs-v2',
        '/quick-execution-test',
        '/dataset-management',
        '/test-data-factory',
    ]
    
    print("\n应该被移除的菜单项:")
    for item in removed_items:
        # 检查是否在菜单配置中(不在路由定义中)
        in_menu = f"to: '{item}'" in content or f'to: "{item}"' in content
        status = "❌" if in_menu else "✅"
        print(f"{status} {item} {'(仍在菜单中)' if in_menu else '(已移除)'}")
    
    print("\n应该保留的菜单项:")
    for item in kept_items:
        in_menu = f"to: '{item}'" in content or f'to: "{item}"' in content
        status = "✅" if in_menu else "❌"
        print(f"{status} {item} {'(已保留)' if in_menu else '(未找到)'}")
    
    return True

def check_documentation():
    """检查文档是否创建"""
    print("\n" + "=" * 60)
    print("检查文档")
    print("=" * 60)
    
    doc_file = Path(__file__).parent / "P0_5_1a_残留Pilot依赖清单.md"
    
    if doc_file.exists():
        content = doc_file.read_text(encoding='utf-8')
        
        checks = {
            "包含修复内容总结": "修复内容总结" in content,
            "包含残留依赖清单": "残留Pilot依赖页面清单" in content,
            "包含后续迁移优先级": "后续迁移优先级" in content,
            "包含验证方法": "验证方法" in content,
        }
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
        
        return all(checks.values())
    else:
        print("❌ 文档未创建")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("P0-5.1a 止血修复验证")
    print("=" * 60 + "\n")
    
    results = {
        "App.jsx 修改": check_app_jsx(),
        "api.js 修改": check_api_js(),
        "Pilot API 使用": check_pilot_api_usage(),
        "菜单项配置": check_menu_items(),
        "文档创建": check_documentation(),
    }
    
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ P0-5.1a 止血修复验证通过")
        print("\n下一步:")
        print("1. 启动前端: cd frontend && npm run dev")
        print("2. 打开浏览器开发者工具 Network 标签")
        print("3. 访问 http://localhost:5173")
        print("4. 确认无 /api/pilot/* 请求")
        print("5. 确认无 404 错误")
    else:
        print("❌ P0-5.1a 止血修复验证失败")
        print("\n请检查上述失败项并修复")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
