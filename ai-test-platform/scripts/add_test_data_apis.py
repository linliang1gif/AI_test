"""
添加测试数据工厂API接口到后端服务器
"""

# 在backend_api_server.py中添加以下API接口

TEST_DATA_APIS = """
# ==================== 测试数据工厂 API ====================

# 导入测试数据工厂
sys.path.insert(0, 'test_data')
from data_factory import factory

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

class BatchEvaluationRequest(BaseModel):
    data_list: List[Dict[str, Any]]

# API路由

@app.post("/api/test-data/generate")
async def generate_test_data(request: DataGenerationRequest):
    '''生成测试数据'''
    try:
        if request.count == 1:
            # 生成单个数据
            if request.data_type in ['user', 'order', 'product', 'address', 'payment', 'inventory']:
                data = getattr(factory, request.data_type)(**(request.overrides or {}))
            else:
                data = factory.generate(request.data_type, **(request.overrides or {}))
            
            return {
                "success": True,
                "data": data,
                "message": f"成功生成{request.data_type}数据"
            }
        else:
            # 批量生成
            data_list = factory.batch(request.data_type, request.count, **(request.overrides or {}))
            return {
                "success": True,
                "data": data_list,
                "count": len(data_list),
                "message": f"成功生成{request.count}条{request.data_type}数据"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/smart-generate")
async def smart_generate_field(request: SmartGenerationRequest):
    '''AI智能生成字段'''
    try:
        value = factory.smart_generate(request.field_name, request.context)
        return {
            "success": True,
            "field_name": request.field_name,
            "value": value,
            "message": "智能生成成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/smart-object")
async def smart_generate_object(request: SmartObjectRequest):
    '''AI智能生成对象'''
    try:
        data = factory.smart_object(request.schema, request.context)
        return {
            "success": True,
            "data": data,
            "message": "智能对象生成成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/analyze-field")
async def analyze_field(field_name: str):
    '''分析字段'''
    try:
        analysis = factory.analyze_field(field_name)
        return {
            "success": True,
            "analysis": analysis,
            "message": "字段分析完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/analyze-schema")
async def analyze_schema(schema: Dict[str, str]):
    '''分析Schema'''
    try:
        analysis = factory.analyze_schema(schema)
        return {
            "success": True,
            "analysis": analysis,
            "message": "Schema分析完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/scenarios/{entity_type}")
async def get_test_scenarios(entity_type: str):
    '''获取测试场景建议'''
    try:
        scenarios = factory.suggest_scenarios(entity_type)
        return {
            "success": True,
            "entity_type": entity_type,
            "scenarios": scenarios,
            "count": len(scenarios),
            "message": "场景建议获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/evaluate")
async def evaluate_quality(request: QualityEvaluationRequest):
    '''评估数据质量'''
    try:
        result = factory.evaluate_quality(request.data, request.schema)
        return {
            "success": True,
            "evaluation": result,
            "message": "质量评估完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/batch-evaluate")
async def batch_evaluate_quality(request: BatchEvaluationRequest):
    '''批量评估数据质量'''
    try:
        result = factory.batch_evaluate(request.data_list)
        return {
            "success": True,
            "evaluation": result,
            "message": "批量评估完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/templates")
async def list_templates():
    '''列出所有模板'''
    try:
        templates = factory.list_templates()
        return {
            "success": True,
            "templates": templates,
            "count": len(templates),
            "message": "模板列表获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-data/from-template")
async def generate_from_template(template_name: str, overrides: Optional[Dict[str, Any]] = None):
    '''从模板生成数据'''
    try:
        data = factory.from_template(template_name, **(overrides or {}))
        return {
            "success": True,
            "template_name": template_name,
            "data": data,
            "message": "模板数据生成成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/stats")
async def get_generation_stats():
    '''获取生成统计'''
    try:
        stats = factory.generation_stats()
        return {
            "success": True,
            "stats": stats,
            "message": "统计信息获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/boundary-values/{data_type}")
async def get_boundary_values(data_type: str, min_val: Optional[int] = None, max_val: Optional[int] = None):
    '''获取边界值'''
    try:
        kwargs = {}
        if min_val is not None:
            kwargs['min_val'] = min_val
        if max_val is not None:
            kwargs['max_val'] = max_val
        
        values = factory.boundary_values(data_type, **kwargs)
        return {
            "success": True,
            "data_type": data_type,
            "values": values,
            "count": len(values),
            "message": "边界值获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-data/invalid-values/{data_type}")
async def get_invalid_values(data_type: str):
    '''获取非法值'''
    try:
        values = factory.invalid_values(data_type)
        return {
            "success": True,
            "data_type": data_type,
            "values": values,
            "count": len(values),
            "message": "非法值获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""

print("测试数据工厂API接口代码已生成")
print("\n请将以上代码添加到 backend_api_server.py 文件中")
print("\n添加位置: 在现有API路由之后,app.run()之前")
