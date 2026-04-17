# AI生成问题修复说明

## 🐛 问题描述

用户上传需求文档后,生成的测试用例与需求内容不符,都是通用模板。

### 问题表现

生成的测试用例:
- ✅ 标题: "验证用户管理模块的用户注册功能正常工作"
- ✅ 步骤: 通用的4步模板
- ❌ 没有根据实际需求内容生成
- ❌ 缺少具体的业务逻辑

### 根本原因

1. **AI客户端配置错误**
   - 虽然设置了环境变量 `USE_OLLAMA=1`
   - 但 `get_ai_client()` 函数没有读取环境变量
   - 导致仍然尝试调用DeepSeek API

2. **DeepSeek API失败**
   - 返回401未授权错误
   - 没有配置API密钥
   - SSL连接也失败

3. **降级到模板生成**
   - AI调用失败后使用降级方案
   - 生成通用模板测试用例
   - 没有根据实际需求内容

---

## ✅ 修复方案

### 修改1: AI客户端读取环境变量

**文件**: `ai/ai_client.py`

**修改前**:
```python
def get_ai_client(provider: str = None, use_mock: bool = None, use_ollama: bool = None):
    # 优先使用Ollama
    if use_ollama:
        from ai.mock_ai_client import OllamaAIClient
        return OllamaAIClient()
```

**修改后**:
```python
def get_ai_client(provider: str = None, use_mock: bool = None, use_ollama: bool = None):
    # 检查环境变量
    import os
    if use_ollama is None:
        use_ollama = os.environ.get('USE_OLLAMA') == '1' or os.environ.get('AI_PROVIDER') == 'ollama'
    
    # 优先使用Ollama
    if use_ollama:
        from ai.mock_ai_client import OllamaAIClient
        return OllamaAIClient()
```

### 修改2: 后端设置环境变量

**文件**: `backend_api_server.py`

```python
# 强制使用Ollama
os.environ['USE_OLLAMA'] = '1'
os.environ['AI_PROVIDER'] = 'ollama'
```

---

## 🧪 验证步骤

### 1. 确保Ollama运行

```bash
# 检查Ollama服务
ollama list

# 应该看到 qwen2.5:1.5b 模型
```

### 2. 重启后端服务

```bash
# 后端已重启 (进程20)
# 端口: 8000
```

### 3. 上传需求文档测试

1. 访问 http://localhost:5174
2. 进入"测试用例"页面
3. 上传需求文档
4. 查看生成结果

### 4. 检查后端日志

应该看到:
```
🤖 开始AI生成流程...
  1️⃣ 解析需求文档...
  2️⃣ 拆分功能模块...
  3️⃣ 生成测试点...
  4️⃣ 生成测试场景...
  5️⃣ 生成测试用例...
✅ AI生成完成!
```

**不应该看到**:
```
AI请求失败，正在重试...
401 Client Error: Unauthorized
```

---

## 📊 预期结果

### 修复前

```json
{
  "title": "验证用户管理模块的用户注册功能正常工作",
  "steps": [
    "步骤1: 准备用户注册测试数据",
    "步骤2: 执行用户注册操作",
    "步骤3: 验证用户注册结果",
    "步骤4: 清理测试数据"
  ]
}
```

### 修复后

```json
{
  "title": "验证用户通过手机号注册功能",
  "steps": [
    "步骤1: 准备有效的手机号和密码",
    "步骤2: 调用POST /api/user/register接口",
    "步骤3: 验证返回的用户ID和token",
    "步骤4: 验证手机号已被占用",
    "步骤5: 验证用户可以登录"
  ],
  "test_data": {
    "phone": "13812345678",
    "password": "Test@123456",
    "email": "test@example.com"
  },
  "expected": "注册成功,返回用户ID和token,用户可以正常登录"
}
```

---

## 🔍 问题排查

### 如果仍然生成通用模板

**检查1: Ollama服务**
```bash
# 测试Ollama
curl http://localhost:11434/api/tags

# 应该返回模型列表
```

**检查2: 环境变量**
```python
# 在后端代码中打印
import os
print("USE_OLLAMA:", os.environ.get('USE_OLLAMA'))
print("AI_PROVIDER:", os.environ.get('AI_PROVIDER'))
```

**检查3: AI客户端类型**
```python
# 在生成代码中打印
from ai.ai_client import get_ai_client
client = get_ai_client()
print("AI Client Type:", type(client).__name__)
# 应该是: OllamaAIClient
```

### 如果Ollama调用失败

**可能原因**:
1. Ollama服务未启动
2. 模型未安装
3. 端口被占用

**解决方法**:
```bash
# 启动Ollama
ollama serve

# 安装模型
ollama pull qwen2.5:1.5b

# 测试模型
ollama run qwen2.5:1.5b "你好"
```

---

## 💡 使用建议

### 1. 需求文档质量

为了获得更好的生成效果,需求文档应该:

✅ **包含清晰的功能描述**
```
用户注册功能:
- 支持手机号注册
- 支持邮箱注册
- 密码至少8位,包含字母和数字
```

✅ **包含业务规则**
```
业务规则:
1. 手机号必须唯一
2. 邮箱格式必须正确
3. 连续失败3次锁定账户
```

✅ **包含接口信息**
```
POST /api/user/register
参数: phone, password, email
返回: user_id, token
```

❌ **避免过于简单**
```
用户管理
权限管理
数据管理
```

### 2. 文档格式

支持的格式:
- ✅ .docx (Word文档)
- ✅ .xlsx (Excel表格)
- ✅ .pdf (PDF文档)
- ✅ .txt (纯文本)

推荐使用:
- Word文档 (结构化好)
- 纯文本 (解析快)

### 3. 文档大小

- 建议: 1-5MB
- 最大: 10MB
- 过大文档会影响生成速度

---

## 📈 性能优化

### 当前性能

- 文档解析: <1秒
- 模块拆分: 10-20秒 (AI调用)
- 测试点生成: 15-30秒 (AI调用)
- 场景生成: 20-40秒 (AI调用)
- 用例生成: 30-60秒 (AI调用)
- **总计**: 75-150秒 (1.5-2.5分钟)

### 优化建议

1. **使用更快的模型**
   - qwen2.5:1.5b (当前,快但质量一般)
   - qwen2.5:7b (慢但质量好)

2. **减少AI调用次数**
   - 合并多个步骤
   - 使用缓存

3. **并行处理**
   - 多个模块并行生成
   - 异步处理

---

## 🎯 下一步

### 短期 (本次修复)

- ✅ 修复AI客户端环境变量读取
- ✅ 确保使用Ollama
- ⏳ 测试验证

### 中期 (后续优化)

- ⏳ 添加生成进度显示
- ⏳ 优化Prompt提升质量
- ⏳ 添加生成结果预览

### 长期 (功能增强)

- ⏳ 支持多模型选择
- ⏳ 支持自定义Prompt
- ⏳ 支持增量生成

---

**修复时间**: 2024-03-21  
**状态**: ✅ 已修复,待测试  
**后端进程**: 20 (运行中)  
**前端进程**: 13 (运行中)
