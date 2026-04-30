"""
前端缓存问题诊断脚本
检查后端清理后前端仍显示旧数据的原因
"""
import requests
import json
from pathlib import Path

def check_backend_data():
    """检查后端当前数据"""
    print("=" * 60)
    print("1. 检查后端 API 数据")
    print("=" * 60)
    
    try:
        response = requests.get('http://localhost:8000/api/test-cases')
        if response.status_code == 200:
            data = response.json()
            # 后端返回格式: {"success": True, "data": [...], "count": N}
            count = data.get('count', 0)
            items = data.get('data', [])  # 注意：是 'data' 不是 'items'
            
            print(f"✅ 后端响应成功")
            print(f"   测试用例总数: {count}")
            print(f"   返回的用例数: {len(items)}")
            
            if items:
                print(f"\n   前3个用例:")
                for i, item in enumerate(items[:3], 1):
                    print(f"   {i}. ID: {item.get('id')}, Title: {item.get('title')}")
            else:
                print(f"   ⚠️  后端返回空数据")
            
            return {'count': count, 'items': items}
        else:
            print(f"❌ 后端响应失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 连接后端失败: {e}")
        return None

def check_platform_data_file():
    """检查 platform_data.json 文件"""
    print("\n" + "=" * 60)
    print("2. 检查 platform_data.json 文件")
    print("=" * 60)
    
    file_path = Path("ai-test-platform/test_data/platform_data.json")
    
    if file_path.exists():
        print(f"✅ 文件存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            test_cases = data.get('test_cases', [])
            print(f"   文件中的测试用例数: {len(test_cases)}")
            
            if test_cases:
                print(f"\n   前3个用例:")
                for i, tc in enumerate(test_cases[:3], 1):
                    print(f"   {i}. ID: {tc.get('id')}, Title: {tc.get('title')}")
            else:
                print(f"   ⚠️  文件中无测试用例数据")
            
            return data
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return None
    else:
        print(f"❌ 文件不存在: {file_path}")
        return None

def check_frontend_cache():
    """检查前端可能的缓存位置"""
    print("\n" + "=" * 60)
    print("3. 检查前端缓存机制")
    print("=" * 60)
    
    # 检查前端构建目录
    frontend_dist = Path("ai-test-platform/frontend/dist")
    if frontend_dist.exists():
        print(f"✅ 前端构建目录存在: {frontend_dist}")
        print(f"   建议: 清理构建缓存")
    else:
        print(f"⚠️  前端构建目录不存在")
    
    # 检查 node_modules
    node_modules = Path("ai-test-platform/frontend/node_modules")
    if node_modules.exists():
        print(f"✅ node_modules 存在")
    else:
        print(f"⚠️  node_modules 不存在，需要运行 npm install")

def check_browser_cache():
    """提供浏览器缓存检查建议"""
    print("\n" + "=" * 60)
    print("4. 浏览器缓存检查建议")
    print("=" * 60)
    
    print("""
    浏览器可能缓存了以下内容:
    
    1. HTTP 响应缓存
       - 解决方法: 硬刷新 (Ctrl+Shift+R 或 Ctrl+F5)
    
    2. Service Worker 缓存
       - 解决方法: 开发者工具 > Application > Service Workers > Unregister
    
    3. LocalStorage/SessionStorage
       - 解决方法: 开发者工具 > Application > Storage > Clear site data
    
    4. React 组件状态缓存
       - 解决方法: 完全重启前端开发服务器
    """)

def analyze_caching_issue(backend_data, file_data):
    """分析缓存问题"""
    print("\n" + "=" * 60)
    print("5. 缓存问题分析")
    print("=" * 60)
    
    if backend_data:
        backend_count = backend_data.get('count', 0)
        backend_items = backend_data.get('items', [])
        
        if backend_count > 0:
            print(f"✅ 后端有 {backend_count} 条测试用例数据")
            
            if file_data:
                file_count = len(file_data.get('test_cases', []))
                print(f"   文件有 {file_count} 条数据")
            else:
                print(f"   ⚠️  platform_data.json 文件不存在")
                print(f"   说明: 后端使用内存存储，数据未持久化到文件")
            
            print("\n   如果前端显示旧数据或不同数据，问题可能是:")
            print("   1. 🌐 浏览器 HTTP 缓存 (最常见)")
            print("   2. 💾 浏览器 LocalStorage/SessionStorage")
            print("   3. ⚛️  React 组件状态未更新")
            print("   4. 🔄 前端开发服务器缓存")
        else:
            print(f"✅ 后端数据已清空 (0 条)")
            
            if file_data and len(file_data.get('test_cases', [])) > 0:
                print(f"   ⚠️  但文件中仍有 {len(file_data.get('test_cases', []))} 条数据")
                print(f"   说明: 后端可能在启动时从文件加载数据")
            
            print("\n   如果前端仍显示数据，问题是:")
            print("   1. 🌐 浏览器缓存了旧的 API 响应")
            print("   2. 💾 前端 LocalStorage 保存了旧数据")
            print("   3. ⚛️  React 组件状态未刷新")
    else:
        print("❌ 无法连接到后端服务")
        print("   请确保后端服务正在运行: py backend_api_server.py")

def provide_solutions():
    """提供解决方案"""
    print("\n" + "=" * 60)
    print("6. 推荐解决方案")
    print("=" * 60)
    
    print("""
    按优先级执行以下步骤:
    
    步骤 1: 清理后端数据文件
    ----------------------------------------
    cd ai-test-platform/test_data
    # 备份现有文件
    copy platform_data.json platform_data.json.backup
    # 清空测试用例
    # 手动编辑或运行清理脚本
    
    步骤 2: 重启后端服务
    ----------------------------------------
    # 停止当前后端服务 (Ctrl+C)
    cd ai-test-platform
    py backend_api_server.py
    
    步骤 3: 清理前端缓存
    ----------------------------------------
    cd ai-test-platform/frontend
    # 删除构建缓存
    rm -rf dist
    rm -rf node_modules/.vite
    # 重启开发服务器
    npm run dev
    
    步骤 4: 清理浏览器缓存
    ----------------------------------------
    1. 打开开发者工具 (F12)
    2. 右键点击刷新按钮
    3. 选择 "清空缓存并硬性重新加载"
    或
    1. 开发者工具 > Application
    2. Storage > Clear site data
    3. 刷新页面
    
    步骤 5: 验证修复
    ----------------------------------------
    1. 访问 http://localhost:8000/api/test-cases
    2. 检查返回的数据量
    3. 访问前端页面
    4. 检查显示的数据是否一致
    """)

def main():
    print("\n🔍 前端缓存问题诊断工具")
    print("=" * 60)
    
    # 检查后端数据
    backend_data = check_backend_data()
    
    # 检查文件数据
    file_data = check_platform_data_file()
    
    # 检查前端缓存
    check_frontend_cache()
    
    # 浏览器缓存建议
    check_browser_cache()
    
    # 分析问题
    analyze_caching_issue(backend_data, file_data)
    
    # 提供解决方案
    provide_solutions()
    
    print("\n" + "=" * 60)
    print("✅ 诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
