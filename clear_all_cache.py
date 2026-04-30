"""
清理所有缓存 - 一键解决前端显示旧数据问题
"""
import requests
import shutil
from pathlib import Path
import json

def clear_backend_data():
    """清理后端测试用例数据"""
    print("=" * 60)
    print("1. 清理后端数据")
    print("=" * 60)
    
    try:
        # 获取所有测试用例
        response = requests.get('http://localhost:8000/api/test-cases')
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', [])
            
            if items:
                # 提取所有 ID
                ids = [item['id'] for item in items]
                
                # 批量删除
                delete_response = requests.post(
                    'http://localhost:8000/api/testcases/batch-delete',
                    json={'ids': ids}
                )
                
                if delete_response.status_code == 200:
                    result = delete_response.json()
                    print(f"✅ 成功删除 {result.get('deleted_count', 0)} 条测试用例")
                else:
                    print(f"❌ 删除失败: {delete_response.status_code}")
            else:
                print("✅ 后端数据已经是空的")
        else:
            print(f"❌ 无法连接后端: {response.status_code}")
    except Exception as e:
        print(f"❌ 清理后端数据失败: {e}")

def clear_platform_data_file():
    """清理 platform_data.json 文件"""
    print("\n" + "=" * 60)
    print("2. 清理 platform_data.json 文件")
    print("=" * 60)
    
    file_path = Path("ai-test-platform/test_data/platform_data.json")
    
    if file_path.exists():
        try:
            # 备份
            backup_path = file_path.with_suffix('.json.backup')
            shutil.copy(file_path, backup_path)
            print(f"✅ 已备份到: {backup_path}")
            
            # 读取并清空测试用例
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            original_count = len(data.get('test_cases', []))
            data['test_cases'] = []
            
            # 保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 已清空 {original_count} 条测试用例")
        except Exception as e:
            print(f"❌ 清理文件失败: {e}")
    else:
        print("⚠️  文件不存在，跳过")

def clear_frontend_build_cache():
    """清理前端构建缓存"""
    print("\n" + "=" * 60)
    print("3. 清理前端构建缓存")
    print("=" * 60)
    
    paths_to_clear = [
        Path("ai-test-platform/frontend/dist"),
        Path("ai-test-platform/frontend/node_modules/.vite"),
        Path("ai-test-platform/frontend/.vite")
    ]
    
    for path in paths_to_clear:
        if path.exists():
            try:
                shutil.rmtree(path)
                print(f"✅ 已删除: {path}")
            except Exception as e:
                print(f"❌ 删除失败 {path}: {e}")
        else:
            print(f"⚠️  不存在: {path}")

def provide_manual_steps():
    """提供手动清理步骤"""
    print("\n" + "=" * 60)
    print("4. 手动清理步骤（重要！）")
    print("=" * 60)
    
    print("""
    ⚠️  以下步骤需要手动执行:
    
    步骤 A: 重启后端服务
    ----------------------------------------
    1. 在后端服务的终端按 Ctrl+C 停止
    2. 运行: cd ai-test-platform
    3. 运行: py backend_api_server.py
    
    步骤 B: 重启前端服务
    ----------------------------------------
    1. 在前端服务的终端按 Ctrl+C 停止
    2. 运行: cd ai-test-platform/frontend
    3. 运行: npm run dev
    
    步骤 C: 清理浏览器缓存
    ----------------------------------------
    方法 1 (推荐):
      1. 打开浏览器开发者工具 (F12)
      2. 右键点击浏览器刷新按钮
      3. 选择 "清空缓存并硬性重新加载"
    
    方法 2:
      1. 按 Ctrl+Shift+Delete 打开清除浏览器数据
      2. 选择 "缓存的图片和文件"
      3. 点击 "清除数据"
    
    方法 3 (最彻底):
      1. 开发者工具 > Application 标签
      2. 左侧 Storage > Clear site data
      3. 点击 "Clear site data" 按钮
      4. 刷新页面 (F5)
    
    步骤 D: 验证清理结果
    ----------------------------------------
    1. 访问: http://localhost:8000/api/test-cases
       应该看到: {"success": true, "data": [], "count": 0}
    
    2. 访问前端页面: http://localhost:5173
       应该看到: 测试用例列表为空
    
    3. 如果仍有问题，尝试:
       - 使用无痕/隐私模式打开浏览器
       - 或使用不同的浏览器
    """)

def verify_cleanup():
    """验证清理结果"""
    print("\n" + "=" * 60)
    print("5. 验证清理结果")
    print("=" * 60)
    
    try:
        response = requests.get('http://localhost:8000/api/test-cases')
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            
            if count == 0:
                print("✅ 后端数据已清空")
            else:
                print(f"⚠️  后端仍有 {count} 条数据")
                print("   可能需要重启后端服务")
        else:
            print(f"⚠️  无法验证: {response.status_code}")
    except Exception as e:
        print(f"⚠️  无法连接后端: {e}")
        print("   后端服务可能已停止，这是正常的")

def main():
    print("\n🧹 清理所有缓存")
    print("=" * 60)
    print("此脚本将清理:")
    print("  1. 后端测试用例数据")
    print("  2. platform_data.json 文件")
    print("  3. 前端构建缓存")
    print("=" * 60)
    
    input("\n按 Enter 继续...")
    
    # 执行清理
    clear_backend_data()
    clear_platform_data_file()
    clear_frontend_build_cache()
    
    # 提供手动步骤
    provide_manual_steps()
    
    # 验证
    verify_cleanup()
    
    print("\n" + "=" * 60)
    print("✅ 自动清理完成")
    print("=" * 60)
    print("\n⚠️  请按照上面的手动步骤完成剩余操作")

if __name__ == "__main__":
    main()
