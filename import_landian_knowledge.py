"""
导入蓝点项目知识库数据
将蓝点项目的 API 定义导入到知识库中
"""
import json
from pathlib import Path
import shutil

def import_landian_api():
    """导入蓝点项目的 API 定义"""
    print("=" * 60)
    print("导入蓝点项目 API 知识库")
    print("=" * 60)
    
    # 蓝点项目 API 文件路径
    landian_api_file = Path(r"D:\360Downloads\蓝点\api.json")
    
    # 目标知识库路径
    knowledge_dir = Path("ai-test-platform/knowledge")
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    target_file = knowledge_dir / "landian_apis.json"
    
    if not landian_api_file.exists():
        print(f"❌ 蓝点 API 文件不存在: {landian_api_file}")
        print(f"\n💡 请确认蓝点项目路径是否正确")
        return False
    
    try:
        # 读取蓝点 API 数据
        with open(landian_api_file, 'r', encoding='utf-8') as f:
            api_data = json.load(f)
        
        print(f"✅ 成功读取蓝点 API 文件")
        print(f"   文件大小: {landian_api_file.stat().st_size / 1024:.1f} KB")
        
        # 转换为知识库格式
        knowledge_data = {
            "source": "landian_project",
            "type": "api_definitions",
            "data": api_data,
            "metadata": {
                "project": "蓝点回收系统",
                "version": "v1.2.2",
                "imported_at": "2024-03-24"
            }
        }
        
        # 保存到知识库
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已导入到知识库: {target_file}")
        print(f"   知识库文件大小: {target_file.stat().st_size / 1024:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def import_postman_collections():
    """导入 Postman 测试集合"""
    print("\n" + "=" * 60)
    print("导入 Postman 测试集合")
    print("=" * 60)
    
    landian_root = Path(r"D:\360Downloads\蓝点")
    knowledge_dir = Path("ai-test-platform/knowledge")
    
    # 查找 Postman 集合
    postman_files = list(landian_root.glob("Postman*.json"))
    
    if not postman_files:
        print("⚠️  未找到 Postman 集合文件")
        return False
    
    print(f"找到 {len(postman_files)} 个 Postman 集合:")
    
    imported_count = 0
    for postman_file in postman_files:
        try:
            # 读取 Postman 集合
            with open(postman_file, 'r', encoding='utf-8') as f:
                postman_data = json.load(f)
            
            # 保存到知识库
            target_file = knowledge_dir / f"postman_{postman_file.stem}.json"
            
            knowledge_data = {
                "source": "landian_project",
                "type": "postman_collection",
                "data": postman_data,
                "metadata": {
                    "project": "蓝点回收系统",
                    "collection_name": postman_file.stem,
                    "imported_at": "2024-03-24"
                }
            }
            
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
            
            print(f"  ✅ {postman_file.name} → {target_file.name}")
            imported_count += 1
            
        except Exception as e:
            print(f"  ❌ {postman_file.name}: {e}")
    
    print(f"\n✅ 成功导入 {imported_count} 个 Postman 集合")
    return imported_count > 0

def import_test_scenarios():
    """导入测试场景"""
    print("\n" + "=" * 60)
    print("导入测试场景")
    print("=" * 60)
    
    landian_root = Path(r"D:\360Downloads\蓝点")
    knowledge_dir = Path("ai-test-platform/knowledge")
    
    # 查找测试场景文件
    scenario_files = [
        landian_root / "分账支付测试场景.json",
        landian_root / "多明细测试API.json"
    ]
    
    imported_count = 0
    for scenario_file in scenario_files:
        if not scenario_file.exists():
            continue
        
        try:
            # 读取场景数据
            with open(scenario_file, 'r', encoding='utf-8') as f:
                scenario_data = json.load(f)
            
            # 保存到知识库
            target_file = knowledge_dir / f"scenario_{scenario_file.stem}.json"
            
            knowledge_data = {
                "source": "landian_project",
                "type": "test_scenario",
                "data": scenario_data,
                "metadata": {
                    "project": "蓝点回收系统",
                    "scenario_name": scenario_file.stem,
                    "imported_at": "2024-03-24"
                }
            }
            
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
            
            print(f"  ✅ {scenario_file.name} → {target_file.name}")
            imported_count += 1
            
        except Exception as e:
            print(f"  ❌ {scenario_file.name}: {e}")
    
    if imported_count > 0:
        print(f"\n✅ 成功导入 {imported_count} 个测试场景")
    else:
        print("\n⚠️  未找到测试场景文件")
    
    return imported_count > 0

def create_knowledge_index():
    """创建知识库索引"""
    print("\n" + "=" * 60)
    print("创建知识库索引")
    print("=" * 60)
    
    knowledge_dir = Path("ai-test-platform/knowledge")
    
    # 统计知识库文件
    json_files = list(knowledge_dir.glob("*.json"))
    
    if not json_files:
        print("⚠️  知识库为空")
        return False
    
    # 创建索引
    index = {
        "total_files": len(json_files),
        "files": [],
        "created_at": "2024-03-24"
    }
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            index["files"].append({
                "filename": json_file.name,
                "source": data.get("source", "unknown"),
                "type": data.get("type", "unknown"),
                "size_kb": json_file.stat().st_size / 1024
            })
        except Exception as e:
            print(f"  ⚠️  无法读取 {json_file.name}: {e}")
    
    # 保存索引
    index_file = knowledge_dir / "index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已创建知识库索引: {index_file}")
    print(f"   总文件数: {index['total_files']}")
    
    # 按类型统计
    type_stats = {}
    for file_info in index["files"]:
        file_type = file_info["type"]
        type_stats[file_type] = type_stats.get(file_type, 0) + 1
    
    print(f"\n   文件类型统计:")
    for file_type, count in type_stats.items():
        print(f"   - {file_type}: {count} 个")
    
    return True

def verify_import():
    """验证导入结果"""
    print("\n" + "=" * 60)
    print("验证导入结果")
    print("=" * 60)
    
    knowledge_dir = Path("ai-test-platform/knowledge")
    
    # 检查知识库文件
    json_files = list(knowledge_dir.glob("*.json"))
    
    if not json_files:
        print("❌ 知识库为空,导入失败")
        return False
    
    print(f"✅ 知识库包含 {len(json_files)} 个文件:")
    
    total_size = 0
    for json_file in json_files:
        size = json_file.stat().st_size / 1024
        total_size += size
        print(f"   - {json_file.name:<40} ({size:>6.1f} KB)")
    
    print(f"\n   总大小: {total_size:.1f} KB")
    
    return True

def main():
    print("\n🚀 导入蓝点项目知识库")
    print("=" * 60)
    
    success_count = 0
    
    # 1. 导入 API 定义
    if import_landian_api():
        success_count += 1
    
    # 2. 导入 Postman 集合
    if import_postman_collections():
        success_count += 1
    
    # 3. 导入测试场景
    if import_test_scenarios():
        success_count += 1
    
    # 4. 创建索引
    if create_knowledge_index():
        success_count += 1
    
    # 5. 验证导入
    verify_import()
    
    print("\n" + "=" * 60)
    if success_count > 0:
        print("✅ 知识库导入完成")
        print("=" * 60)
        print(f"\n成功导入 {success_count} 类数据")
        print("\n💡 下一步:")
        print("   1. 重启后端服务")
        print("   2. 测试 AI 生成功能")
        print("   3. 查看后端日志确认知识库被调用")
    else:
        print("❌ 知识库导入失败")
        print("=" * 60)
        print("\n💡 请检查:")
        print("   1. 蓝点项目路径是否正确")
        print("   2. API 文件是否存在")
    print()

if __name__ == "__main__":
    main()
