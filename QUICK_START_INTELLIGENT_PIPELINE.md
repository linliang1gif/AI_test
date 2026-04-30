# 智能执行Pipeline 快速启动指南

## 🚀 5分钟快速开始

### 步骤1: 启动后端服务

```bash
cd ai测试/ai-test-platform
py backend_api_server.py
```

等待看到:
```
✅ Modules SDK 已加载
✅ Core Models 已加载
✅ Model Converter 已加载
🚀 AI测试平台后端服务启动
📍 地址: http://0.0.0.0:8000
📖 API文档: http://0.0.0.0:8000/docs
```

### 步骤2: 测试Pipeline API

打开新终端,运行测试脚本:

```bash
cd ai测试
py test_intelligent_pipeline.py
```

选择测试模式:
- 输入 `1`: 直接测试(使用现有测试用例)
- 输入 `2`: 使用模拟数据测试(推荐)

### 步骤3: 查看结果

测试完成后会显示:

```
✅ 测试完成!
═══════════════════════════════════════════════════════════

🧠 执行计划:
   - 选中测试: 3
   - 跳过测试: 0
   - 并发分组: 1

⚙️  执行结果:
   - 总计: 3
   - 通过: 3
   - 失败: 0

🔧 修复报告:
   - 总用例: 3
   - 已修复: 0
   - 修复率: 0%

📊 测试报告:
   - 通过率: 100.0%
   - 通过: 3
   - 失败: 0
   - 总耗时: 1.52秒

💾 完整结果已保存到: intelligent_pipeline_result.json
```

## 📝 使用curl测试

```bash
curl -X POST http://localhost:8000/api/v2/test/run-intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "test_case_ids": ["TC_001", "TC_002"],
    "environment": "test",
    "base_url": "https://jsonplaceholder.typicode.com"
  }'
```

## 🎨 前端集成

### 1. 在React组件中使用

```jsx
import { useState } from 'react'
import api from '../services/api'

function TestRunner() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  
  const runTests = async () => {
    setLoading(true)
    try {
      const result = await api.pipeline.runIntelligent({
        test_case_ids: ['TC_001', 'TC_002'],
        environment: 'test',
        base_url: 'https://jsonplaceholder.typicode.com'
      })
      setResult(result)
      alert(`测试完成! 通过率: ${result.statistics.pass_rate}`)
    } catch (error) {
      alert('执行失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div>
      <button onClick={runTests} disabled={loading}>
        {loading ? '执行中...' : '运行智能测试'}
      </button>
      
      {result && (
        <div>
          <h3>执行结果</h3>
          <p>通过率: {result.statistics.pass_rate}</p>
          <p>通过: {result.statistics.passed_tests}</p>
          <p>失败: {result.statistics.failed_tests}</p>
        </div>
      )}
    </div>
  )
}
```

### 2. API已自动集成

前端的 `api.js` 已经包含了新方法:

```javascript
// 已经可以直接使用
api.pipeline.runIntelligent({
  test_case_ids: ['TC_001', 'TC_002'],
  environment: 'test',
  base_url: 'https://api.example.com'
})
```

## 📊 查看API文档

访问 http://localhost:8000/docs 查看完整的API文档和交互式测试界面。

## 🔍 调试技巧

### 1. 查看详细日志

后端会输出详细的执行日志:

```
═══════════════════════════════════════════════════════════
🚀 开始智能执行Pipeline
═══════════════════════════════════════════════════════════
📋 测试用例数: 3
🌍 环境: test
🔗 Base URL: https://jsonplaceholder.typicode.com

✅ 找到 3 个有效测试用例

═══════════════════════════════════════════════════════════
🧠 步骤1: Intelligence Agent - 生成执行计划
═══════════════════════════════════════════════════════════
✅ 执行计划生成完成
   - 选中测试: 3
   - 跳过测试: 0
   - 并发分组: 1

═══════════════════════════════════════════════════════════
⚙️  步骤2: Execution Engine - 执行测试
═══════════════════════════════════════════════════════════
🔄 执行: TC_001 - 获取用户列表
   ✅ passed - 耗时: 0.52s
...
```

### 2. 检查结果文件

测试脚本会保存完整结果到 `intelligent_pipeline_result.json`:

```bash
# 查看结果
cat intelligent_pipeline_result.json | jq .

# 或在Windows上
type intelligent_pipeline_result.json
```

### 3. 常见问题

**问题1: 连接失败**
```
❌ 连接失败! 请确保后端服务已启动
```
解决: 确保后端服务在 http://localhost:8000 运行

**问题2: 测试用例未找到**
```
⚠️  测试用例 TC_001 未找到，跳过
```
解决: 使用测试脚本的模式2创建测试用例

**问题3: Modules SDK 不可用**
```
⚠️  Modules SDK 导入失败
```
解决: 检查 modules 目录是否存在,路径是否正确

## 📚 完整文档

- **API文档**: [INTELLIGENT_PIPELINE_API.md](./INTELLIGENT_PIPELINE_API.md)
- **完成报告**: [INTELLIGENT_PIPELINE_COMPLETE.md](./INTELLIGENT_PIPELINE_COMPLETE.md)
- **测试脚本**: [test_intelligent_pipeline.py](./test_intelligent_pipeline.py)

## 🎯 下一步

1. **创建前端UI**: 开发可视化的测试执行页面
2. **添加实时监控**: 使用WebSocket推送执行进度
3. **保存历史记录**: 将执行结果保存到数据库
4. **性能优化**: 提升并发执行效率

---

**版本**: v2.0
**更新时间**: 2026-04-18
**状态**: ✅ 可用
