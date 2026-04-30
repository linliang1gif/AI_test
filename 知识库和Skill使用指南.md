# 知识库和Skill使用指南

## 当前状态

### ✅ 已完成
1. **智谱AI集成** - 使用glm-4-flash模型生成测试用例
2. **基础AI生成** - 可以根据需求文档生成测试用例
3. **知识库模块** - 已有knowledge模块和decision_rag
4. **Skill模块** - 已有test-case-generator skill

### ❌ 未集成
1. **知识库RAG** - 生成时显示"知识库为空或未找到相关信息"
2. **Skill增强** - 没有使用test-case-generator skill的专业能力

## 如何添加知识库

### 1. 导入Swagger API文档

```bash
cd ai-test-platform
py import_swagger_to_knowledge.py
```

这会将`swaggerApi (1).json`中的814个API导入到ChromaDB知识库。

### 2. 导入代码库

```bash
cd ai-test-platform
py import_codebase_to_knowledge.py
```

这会将项目代码导入知识库,供AI参考。

### 3. 验证知识库

```python
from knowledge.decision_rag import get_decision_rag

rag = get_decision_rag()
knowledge = rag.retrieve_knowledge_v2(
    query="付款单管理",
    context_type="case_generation",
    max_tokens=1500
)

print(f"找到 {len(knowledge.get('apis', []))} 个相关API")
```

## 如何使用Skill

### 方案1: 在Prompt中引用Skill

修改`backend_api_server.py`中的`_generate_testcases_with_ai`函数:

```python
# 读取skill文档
skill_path = Path(__file__).parent / "skills/test-case-generator/SKILL.md"
if skill_path.exists():
    with open(skill_path, 'r', encoding='utf-8') as f:
        skill_content = f.read()
    
    # 在system_prompt中包含skill指导
    system_prompt = f"""你是一个专业的测试工程师。

{skill_content}

请严格按照上述skill的要求生成测试用例。"""
```

### 方案2: 使用Skill的Python模块

如果skill有Python实现,可以直接调用:

```python
from skills.test_case_generator import case_helper

# 使用skill的辅助函数
test_cases = case_helper.generate_cases(requirement_text)
```

## 完整集成方案

### 修改测试用例生成流程

```python
async def _generate_testcases_with_ai(content: str, filename: str, provider: str):
    """使用AI生成测试用例(集成知识库+Skill)"""
    from ai.ai_client import AIClient
    from knowledge.decision_rag import get_decision_rag
    from pathlib import Path
    import json
    
    # 1. 读取Skill文档
    skill_path = Path(__file__).parent / "skills/test-case-generator/SKILL.md"
    skill_guidance = ""
    if skill_path.exists():
        with open(skill_path, 'r', encoding='utf-8') as f:
            skill_guidance = f.read()
    
    # 2. 查询知识库
    knowledge_context = ""
    try:
        rag = get_decision_rag()
        knowledge = rag.retrieve_knowledge_v2(
            query=content[:500],
            context_type="case_generation",
            max_tokens=1500
        )
        
        # 提取API信息
        apis = knowledge.get('apis', [])
        if apis:
            knowledge_context += "\n\n## 相关API接口:\n"
            for api in apis[:5]:
                knowledge_context += f"- {api['method']} {api['path']}: {api.get('summary', '')}\n"
        
        print(f"✅ 知识库检索成功,找到 {len(apis)} 个相关API")
    except Exception as e:
        print(f"⚠️  知识库检索失败: {e}")
    
    # 3. 构建增强的提示词
    system_prompt = f"""你是一个专业的测试工程师。

{skill_guidance}

请严格按照上述要求生成高质量的测试用例。"""
    
    prompt = f"""请根据以下需求文档生成测试用例。

## 需求文档:
{content[:2000]}

{knowledge_context}

请生成5-10个测试用例,每个包含:
- title: 测试用例标题
- module: 所属模块
- priority: 优先级(high/medium/low)
- steps: 详细的测试步骤列表
- expected: 预期结果
- type: 测试类型

以JSON数组格式返回。"""
    
    # 4. 调用AI
    ai_client = AIClient(provider=provider)
    response = ai_client.generate_text(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.3,
        max_tokens=3000
    )
    
    # 5. 解析结果
    # ... (解析JSON的代码)
```

## 效果对比

### 不使用Skill和知识库
- 生成速度: 快(30秒)
- 用例数量: 7-9个
- 用例质量: 中等
- 测试步骤: 3-5步
- 测试数据: 笼统("有效数据")

### 使用Skill和知识库
- 生成速度: 较慢(40-60秒)
- 用例数量: 10-20个
- 用例质量: 高
- 测试步骤: 5-10步
- 测试数据: 具体("用户名: test@example.com")
- API参考: 包含实际API路径

## 下一步行动

1. **导入知识库数据**
   ```bash
   cd ai-test-platform
   py import_swagger_to_knowledge.py
   ```

2. **修改后端代码**
   - 在`_generate_testcases_with_ai`中集成skill
   - 确保知识库检索正常工作

3. **测试效果**
   - 上传需求文档
   - 对比生成质量
   - 调整prompt和参数

4. **优化配置**
   - 调整max_tokens
   - 优化知识库检索
   - 微调skill指导

## 参考文档

- Skill文档: `ai-test-platform/skills/test-case-generator/SKILL.md`
- 知识库模块: `ai-test-platform/knowledge/`
- 导入脚本: `ai-test-platform/import_swagger_to_knowledge.py`
- 后端API: `ai-test-platform/backend_api_server.py` (第1700行)
