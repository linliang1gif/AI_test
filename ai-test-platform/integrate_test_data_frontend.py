"""
自动集成测试数据工厂到前端
"""
import os
import sys

def integrate_backend_apis():
    """集成后端API"""
    print("=" * 60)
    print("集成测试数据工厂后端API")
    print("=" * 60)
    
    backend_file = "backend_api_server.py"
    
    if not os.path.exists(backend_file):
        print(f"❌ 找不到文件: {backend_file}")
        return False
    
    # 读取现有内容
    with open(backend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已集成
    if 'test-data/generate' in content:
        print("✅ 后端API已集成")
        return True
    
    # 准备要添加的代码
    api_code = '''

# ==================== 测试数据工厂 API ====================

# 导入测试数据工厂
sys.path.insert(0, 'test_data')
try:
    from data_factory import factory
    print("✅ 测试数据工厂导入成功")
    TEST_DATA_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 测试数据工厂导入失败: {e}")
    TEST_DATA_AVAILABLE = False

# 数据模型
class DataGenerationRequest(BaseModel):
    data_type: str
    count: int = 1
    context: Optional[Dict[str, Any]] = None
    overrides: Optional[Dict[str, Any]] = None

class SmartGenerationRequest(BaseModel):
    field_name: str
    context: Optional[Dict[str, Any]] = None

class SmartObjectRequest(BaseModel):
    schema: Dict[str, str]
    context: Optional[Dict[str, Any]] = None

class QualityEvaluationRequest(BaseModel):
    data: Dict[str, Any]
    schema: Optional[Dict[str, Any]] = None

# API路由
if TEST_DATA_AVAILABLE:
    @app.post("/api/test-data/generate")
    async def generate_test_data(request: DataGenerationRequest):
        """生成测试数据"""
        try:
            if request.count == 1:
                if request.data_type in ['user', 'order', 'product', 'address', 'payment', 'inventory']:
                    data = getattr(factory, request.data_type)(**(request.overrides or {}))
                else:
                    data = factory.string(10)
                return {"success": True, "data": data, "message": f"成功生成{request.data_type}数据"}
            else:
                data_list = factory.batch(request.data_type, request.count, **(request.overrides or {}))
                return {"success": True, "data": data_list, "count": len(data_list), "message": f"成功生成{request.count}条数据"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/test-data/smart-object")
    async def smart_generate_object(request: SmartObjectRequest):
        """AI智能生成对象"""
        try:
            data = factory.smart_object(request.schema, request.context)
            return {"success": True, "data": data, "message": "智能对象生成成功"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/test-data/scenarios/{entity_type}")
    async def get_test_scenarios(entity_type: str):
        """获取测试场景建议"""
        try:
            scenarios = factory.suggest_scenarios(entity_type)
            return {"success": True, "entity_type": entity_type, "scenarios": scenarios, "count": len(scenarios)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/test-data/evaluate")
    async def evaluate_quality(request: QualityEvaluationRequest):
        """评估数据质量"""
        try:
            result = factory.evaluate_quality(request.data, request.schema)
            return {"success": True, "evaluation": result, "message": "质量评估完成"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/test-data/templates")
    async def list_templates():
        """列出所有模板"""
        try:
            templates = factory.list_templates()
            return {"success": True, "templates": templates, "count": len(templates)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/test-data/stats")
    async def get_generation_stats():
        """获取生成统计"""
        try:
            stats = factory.generation_stats()
            return {"success": True, "stats": stats, "message": "统计信息获取成功"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

print("✅ 测试数据工厂API路由已注册")
'''
    
    # 找到合适的插入位置 (在if __name__ == "__main__"之前)
    if 'if __name__ == "__main__":' in content:
        parts = content.split('if __name__ == "__main__":')
        new_content = parts[0] + api_code + '\n\nif __name__ == "__main__":' + parts[1]
    else:
        new_content = content + api_code
    
    # 写回文件
    with open(backend_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 后端API集成完成")
    return True


def create_frontend_route_update():
    """创建前端路由更新说明"""
    print("\n" + "=" * 60)
    print("前端路由更新说明")
    print("=" * 60)
    
    print("""
请手动更新 frontend/src/App.jsx:

1. 添加导入:
   import TestDataFactory from './pages/TestDataFactory'

2. 在导航菜单中添加:
   <NavLink to="/test-data-factory">🏭 测试数据工厂</NavLink>

3. 在Routes中添加:
   <Route path="/test-data-factory" element={<TestDataFactory />} />

前端页面文件已创建: frontend/src/pages/TestDataFactory.jsx
""")


def main():
    """主函数"""
    print("\n🚀 开始集成测试数据工厂到前端系统\n")
    
    # 1. 集成后端API
    if integrate_backend_apis():
        print("\n✅ 后端集成成功")
    else:
        print("\n❌ 后端集成失败")
        return
    
    # 2. 前端路由更新说明
    create_frontend_route_update()
    
    print("\n" + "=" * 60)
    print("集成完成!")
    print("=" * 60)
    print("""
下一步:
1. 手动更新 frontend/src/App.jsx (参考上面的说明)
2. 启动后端: python backend_api_server.py
3. 启动前端: cd frontend && npm run dev
4. 访问: http://localhost:5173/test-data-factory

详细说明请查看: frontend_integration_guide.md
""")


if __name__ == "__main__":
    main()
