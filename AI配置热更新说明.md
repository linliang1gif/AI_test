# AI 配置热更新功能说明

## 功能说明

AI 配置现在支持热更新，修改配置后**立即生效，无需重启后端服务**。

## 实现原理

### 1. 配置更新流程

```
用户修改配置 → 保存到 .env 文件 → 调用 reload_config() → 重新加载配置 → 立即生效
```

### 2. 关键代码

**后端 API (`routes/ai_routes.py`)**:
```python
@router.post("/ai/config/update")
async def update_ai_config(request: dict):
    # 1. 更新 .env 文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    # 2. 重新加载配置（关键！）
    from config.config import reload_config
    reload_config()
    
    return {
        "success": True,
        "message": "配置已更新并立即生效"
    }
```

**配置管理 (`config/config.py`)**:
```python
def reload_config():
    """重新加载配置"""
    global config
    load_dotenv(override=True)  # 重新加载 .env
    config = Config()            # 重新创建配置对象
    return config
```

### 3. 前端体验

- 保存配置后显示：**"配置已保存并立即生效"**
- 自动重新加载配置，显示最新状态
- 无需手动刷新页面

## 使用方式

### 1. 修改配置

1. 访问 `/ai-config` 页面
2. 选择模块和模型
3. 点击"保存配置"
4. 看到成功提示：**"配置已保存并立即生效"**

### 2. 验证生效

配置保存后，立即生效：
- 新的 AI 请求会使用新配置
- 无需等待
- 无需重启

### 3. 测试验证

运行测试脚本验证热更新：
```bash
py test_hot_reload.py
```

预期输出：
```
1. 获取当前配置
   测试用例生成: {'provider': 'deepseek', 'model': 'deepseek-chat'}

2. 更新配置（切换到 ollama）
   结果: 配置已更新并立即生效

3. 验证配置是否立即生效
   测试用例生成: {'provider': 'ollama', 'model': 'qwen2.5-coder:latest'}

4. 对比结果
   ✅ 配置热更新成功！无需重启服务
```

## 技术细节

### 1. 为什么需要 reload_config()？

Python 的 `os.getenv()` 和 `load_dotenv()` 在启动时加载环境变量到内存：
- 修改 `.env` 文件不会自动更新内存中的变量
- 需要调用 `load_dotenv(override=True)` 重新加载
- 需要重新创建 `Config` 对象以读取新值

### 2. 全局配置对象

```python
# 全局配置实例
config = Config()

def get_config() -> Config:
    """获取全局配置实例"""
    return config
```

所有模块通过 `get_config()` 获取同一个配置对象，因此：
- `reload_config()` 更新全局对象
- 所有模块立即看到新配置
- 无需重启服务

### 3. AI 客户端缓存

注意：`get_ai_client()` 有缓存机制：
```python
_ai_client = None

def get_ai_client(provider=None, module=None):
    global _ai_client
    if _ai_client is None or ...:
        _ai_client = AIClient(provider, module)
    return _ai_client
```

配置更新后，下次调用 `get_ai_client()` 时：
- 如果 provider 或 module 改变，会创建新客户端
- 新客户端会读取新配置
- 因此配置立即生效

## 优势

### 1. 用户体验
- ✅ 无需重启服务
- ✅ 配置立即生效
- ✅ 操作流畅

### 2. 开发效率
- ✅ 快速测试不同模型
- ✅ 快速切换提供商
- ✅ 无需等待重启

### 3. 生产环境
- ✅ 零停机时间
- ✅ 动态调整配置
- ✅ 快速响应需求

## 注意事项

### 1. 首次使用

如果是首次添加热更新功能，需要重启一次后端服务以加载新代码：
```bash
# 停止当前后端（Ctrl+C）
cd ai-test-platform
py backend_api_server.py
```

之后所有配置修改都无需重启。

### 2. 配置文件权限

确保后端进程有权限写入 `.env` 文件。

### 3. 并发安全

当前实现是单进程安全的。如果使用多进程部署（如 Gunicorn），需要考虑：
- 配置同步机制
- 或使用数据库存储配置

## 测试清单

- [ ] 修改测试用例生成模块配置
- [ ] 保存后立即调用测试用例生成 API
- [ ] 验证使用了新配置的模型
- [ ] 修改其他模块配置
- [ ] 验证各模块独立配置生效
- [ ] 切换提供商（deepseek → ollama）
- [ ] 验证提供商切换生效
- [ ] 运行 `test_hot_reload.py` 自动化测试

## 总结

AI 配置热更新功能让配置管理更加灵活和高效：
- ✅ 保存即生效
- ✅ 无需重启
- ✅ 用户体验好
- ✅ 开发效率高

这是一个生产级的配置管理方案。
