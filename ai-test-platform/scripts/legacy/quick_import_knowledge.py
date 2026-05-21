#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速导入知识库 - 简化版
用于快速测试决策级RAG功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🚀 快速导入知识库")
print("=" * 70)

# 1. 检查Swagger文件
print("\n1️⃣ 检查Swagger文件...")
swagger_files = list(Path("data/swagger").glob("*.json")) if Path("data/swagger").exists() else []
print(f"   找到 {len(swagger_files)} 个Swagger文件")

if swagger_files:
    print("\n   开始导入Swagger API...")
    try:
        import subprocess
        result = subprocess.run(
            ["py", "import_swagger_to_knowledge.py"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            print("   ✅ Swagger导入完成")
            # 显示部分输出
            lines = result.stdout.split('\n')
            for line in lines[-10:]:
                if line.strip():
                    print(f"      {line}")
        else:
            print(f"   ⚠️  Swagger导入失败: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("   ⚠️  Swagger导入超时(5分钟)")
    except Exception as e:
        print(f"   ⚠️  Swagger导入出错: {e}")
else:
    print("   ⚠️  未找到Swagger文件,跳过")

# 2. 检查代码库
print("\n2️⃣ 检查代码库...")
backend_path = Path("../后端1.2.1")
frontend_path = Path("../前端-1.2.1")

backend_exists = backend_path.exists()
frontend_exists = frontend_path.exists()

print(f"   后端代码: {'✅ 存在' if backend_exists else '❌ 不存在'}")
print(f"   前端代码: {'✅ 存在' if frontend_exists else '❌ 不存在'}")

if backend_exists or frontend_exists:
    print("\n   开始导入代码库...")
    print("   ⚠️  注意: 代码库导入可能需要较长时间(10-30分钟)")
    print("   建议: 在后台运行,或者先测试基础功能")
    
    response = input("\n   是否现在导入代码库? (y/n): ")
    
    if response.lower() == 'y':
        try:
            import subprocess
            result = subprocess.run(
                ["py", "import_codebase_to_knowledge.py"],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                timeout=1800  # 30分钟超时
            )
            
            if result.returncode == 0:
                print("   ✅ 代码库导入完成")
            else:
                print(f"   ⚠️  代码库导入失败: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print("   ⚠️  代码库导入超时(30分钟)")
        except Exception as e:
            print(f"   ⚠️  代码库导入出错: {e}")
    else:
        print("   ⏭️  跳过代码库导入")
else:
    print("   ⚠️  未找到代码库,跳过")

# 3. 检查最终状态
print("\n3️⃣ 检查知识库状态...")
try:
    from knowledge.knowledge_manager import get_knowledge_manager
    
    km = get_knowledge_manager()
    stats = km.get_knowledge_stats()
    
    api_count = stats.get('apis', {}).get('total', 0)
    backend_count = stats.get('code', {}).get('backend', 0)
    frontend_count = stats.get('code', {}).get('frontend', 0)
    
    print(f"\n📊 知识库最终状态:")
    print(f"   - APIs: {api_count}")
    print(f"   - Backend代码: {backend_count}")
    print(f"   - Frontend代码: {frontend_count}")
    
    if api_count > 0 or backend_count > 0 or frontend_count > 0:
        print("\n✅ 知识库已有数据,可以测试决策级RAG!")
        print("\n💡 运行测试:")
        print("   py test_complete_rag_integration.py")
    else:
        print("\n⚠️  知识库仍为空")
        print("\n💡 手动导入:")
        print("   py import_swagger_to_knowledge.py")
        print("   py import_codebase_to_knowledge.py")
        
except Exception as e:
    print(f"❌ 检查失败: {e}")

print("\n" + "=" * 70)
