#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试后端500错误诊断脚本
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("后端500错误诊断")
print("=" * 60)

# 1. 测试数据库连接
print("\n1. 测试数据库连接...")
try:
    from database import get_db_session, get_db_info
    
    info = get_db_info()
    print(f"✅ 数据库信息: {info}")
    
    with get_db_session() as db:
        print("✅ 数据库连接成功")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    import traceback
    traceback.print_exc()

# 2. 测试ProjectService
print("\n2. 测试ProjectService...")
try:
    from database import get_db_session
    from services import ProjectService
    
    with get_db_session() as db:
        service = ProjectService(db)
        projects = service.get_all_projects()
        print(f"✅ ProjectService工作正常, 项目数量: {len(projects)}")
        for p in projects:
            print(f"   - {p.id}: {p.name}")
except Exception as e:
    print(f"❌ ProjectService失败: {e}")
    import traceback
    traceback.print_exc()

# 3. 测试路由导入
print("\n3. 测试路由导入...")
try:
    from routes.project_config_routes import router
    print(f"✅ 路由导入成功, 路由数量: {len(router.routes)}")
except Exception as e:
    print(f"❌ 路由导入失败: {e}")
    import traceback
    traceback.print_exc()

# 4. 模拟API调用
print("\n4. 模拟API调用...")
try:
    from fastapi.testclient import TestClient
    from backend_api_server import app
    
    client = TestClient(app)
    response = client.get("/api/v2/projects")
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
    
    if response.status_code == 200:
        print("✅ API调用成功")
    else:
        print(f"❌ API返回错误: {response.status_code}")
except Exception as e:
    print(f"❌ API调用失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
