# 智能执行Pipeline API 完整文档

## 📋 概述

智能执行Pipeline API (`/api/v2/test/run-intelligent`) 是一个完整的端到端测试执行链路,打通了以下核心模块:

```
前端 → Intelligence Agent → Execution Engine → Healing Engine → Report Generator → 前端
```

## 🎯 核心功能

### 1. Intelligence Agent (智能决策)
- 基于历史数据分析测试用例风险
- 智能选择需要执行的测试用例
- 生成优化的执行计划和并发策略

### 2. Execution Engine (执行引擎)
- 真实执行API测试
- 支持多种HTTP方法
- 完整的请求/响应处理

### 3. Healing Engine (自动修复)
- L1: 环境问题自动重试
- L2: 数据问题重建数据
- L3: 不稳定测试容错通过
- L4: 真实Bug标记人工审查

### 4. Report Generator (报告生成)
- 生成详细的测试报告
- 统计通过率、失败率
- 提供可视化数据

## 🔌 API接口

### 请求

**端点**: `POST /api/v2/test/run-intelligent`

**请求体**:
```json
{
  "test_case_ids": ["TC_001", "TC_002", "TC_003"],
  "environment": "test",
  "base_url": "https://jsonplaceholder.typicode.com"
}
```

**参数说明**:
- `test_case_ids` (必填): 测试用例ID列表
- `environment` (可选): 执行环境,默认 "test"
- `base_url` (必填): API基础URL

### 响应

**成功响应** (200):
```json
{
  "success": true,
  "execution_plan": {
    "selected_tests": ["TC_001", "TC_002"],
    "skipped_tests": ["TC_003"],
    "execution_order": ["TC_001", "TC_002"],
    "parallel_groups": {
      "user": ["TC_001", "TC_002"]
    },
    "risk_scores": [
      {
        "test_case_id": "TC_001",
        "total_score": 0.75,
        "failure_rate": 0.1,
        "change_frequency": 0.1,
        "priority_weight": 1.0,
        "coverage_gap": 0.2,
        "decision": "must_run"
      }
    ],
    "statistics": {
      "total_tests": 3,
      "selected_tests": 2,
      "skipped_tests": 1,
      "selection_rate": 66.67
    }
  },
  "results": [
    {
      "test_case_id": "TC_001",
      "status": "passed",
      "duration": 0.523,
      "start_time": 1713456789.123,
      "end_time": 1713456789.646,
      "error": null,
      "healing_applied": false,
      "healing_level": null,
      "healing_details": null
    }
  ],
  "healing": {
    "total_cases": 2,
    "healed_cases": 1,
    "healing_rate": "50.0%",
    "by_level": {
      "L1_RETRY": {
        "count": 1,
        "description": "环境问题（重试）"
      },
      "L2_DATA": {
        "count": 0,
        "description": "数据问题（重建数据）"
      },
      "L3_TOLERANCE": {
        "count": 0,
        "description": "不稳定（容错）"
      },
      "L4_MANUAL": {
        "count": 0,
        "description": "需要人工审查"
      }
    }
  },
  "report": {
    "summary": {
      "total": 2,
      "passed": 2,
      "failed": 0,
      "pass_rate": "100.0%",
      "total_duration": 1.046
    },
    "details": [...]
  },
  "statistics": {
    "total_tests": 3,
    "executed_tests": 2,
    "passed_tests": 2,
    "failed_tests": 0,
    "pass_rate": "100.0%",
    "total_duration": 1.046
  }
}
```

**失败响应** (400/500):
```json
{
  "success": false,
  "message": "Pipeline执行失败: ...",
  "error": "详细错误信息"
}
```

## 🔄 执行流程

```
1. 接收请求
   ↓
2. 查询测试用例
   ↓
3. Intelligence Agent 生成执行计划
   - 计算风险评分
   - 选择测试用例
   - 生成执行顺序
   - 规划并发策略
   ↓
4. Execution Engine 执行测试
   - 按顺序执行
   - 记录结果
   - 捕获错误
   ↓
5. Healing Engine 自动修复
   - 分析错误类型
   - 应用修复策略
   - 更新测试状态
   ↓
6. Report Generator 生成报告
   - 统计数据
   - 生成摘要
   - 格式化输出
   ↓
7. 返回完整结果
```

## 📊 数据结构

### TestCase (测试用例)
```python
{
  "id": "TC_001",
  "title": "获取用户列表",
  "method": "GET",
  "path": "/users",
  "url": "/users",  # 可选,与path二选一
  "headers": {},
  "body": {},
  "request_body": {},  # 可选,与body二选一
  "expected_status": 200,
  "priority": "P0",  # P0/P1/P2/P3
  "module": "user",
  "tags": ["smoke", "api"]
}
```

### ExecutionResult (执行结果)
```python
{
  "test_case_id": "TC_001",
  "status": "passed",  # passed/failed/skipped
  "duration": 0.523,
  "start_time": 1713456789.123,
  "end_time": 1713456789.646,
  "error": null,
  "healing_applied": false,
  "healing_level": null,  # L1/L2/L3/L4
  "healing_details": null
}
```

## 🧪 测试方法

### 方法1: 使用测试脚本

```bash
# 运行测试脚本
python test_intelligent_pipeline.py

# 选择测试模式
# 1. 直接测试 (使用现有测试用例)
# 2. 使用模拟数据测试 (先创建测试用例)
```

### 方法2: 使用curl

```bash
curl -X POST http://localhost:8000/api/v2/test/run-intelligent \
  -H "Content-Type: application/json" \
  -d '{
    "test_case_ids": ["TC_001", "TC_002"],
    "environment": "test",
    "base_url": "https://jsonplaceholder.typicode.com"
  }'
```

### 方法3: 使用前端

```javascript
import api from '../services/api'

// 调用智能执行Pipeline
const result = await api.pipeline.runIntelligent({
  test_case_ids: ['TC_001', 'TC_002'],
  environment: 'test',
  base_url: 'https://jsonplaceholder.typicode.com'
})

console.log('执行计划:', result.execution_plan)
console.log('执行结果:', result.results)
console.log('修复报告:', result.healing)
console.log('测试报告:', result.report)
```

## 🎨 前端集成示例

### 创建执行页面

```jsx
import { useState } from 'react'
import api from '../services/api'
import { useToast } from '../components/ui/Toast'

export default function IntelligentTestRunner() {
  const toast = useToast()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  
  const handleRun = async () => {
    setLoading(true)
    try {
      const result = await api.pipeline.runIntelligent({
        test_case_ids: ['TC_001', 'TC_002'],
        environment: 'test',
        base_url: 'https://jsonplaceholder.typicode.com'
      })
      
      setResult(result)
      toast.success(`测试完成! 通过率: ${result.statistics.pass_rate}`)
    } catch (error) {
      toast.error('执行失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div>
      <button onClick={handleRun} disabled={loading}>
        {loading ? '执行中...' : '运行智能测试'}
      </button>
      
      {result && (
        <div>
          <h3>执行结果</h3>
          <p>通过率: {result.statistics.pass_rate}</p>
          <p>通过: {result.statistics.passed_tests}</p>
          <p>失败: {result.statistics.failed_tests}</p>
          <p>总耗时: {result.statistics.total_duration}s</p>
        </div>
      )}
    </div>
  )
}
```

## 🔧 配置选项

### Intelligence Agent 配置

```python
# 在backend_api_server.py中配置
intelligence_agent = TestIntelligenceAgent(
    learning_agent=learning_agent  # 可选,提供历史数据
)

# 自定义风险阈值
intelligence_agent.risk_thresholds = {
    'must_run': 0.6,    # > 0.6 必须执行
    'optional': 0.3     # 0.3~0.6 可选, < 0.3 跳过
}

# 自定义优先级权重
intelligence_agent.priority_weights = {
    'P0': 1.0,
    'P1': 0.7,
    'P2': 0.4,
    'P3': 0.2
}
```

### Healing Engine 配置

```python
healing_engine = HealingEngine(config={
    'enable_l1': True,   # 启用L1修复
    'enable_l2': True,   # 启用L2修复
    'enable_l3': True,   # 启用L3修复
    'enable_l4': True,   # 启用L4修复
    'max_retry': 3       # 最大重试次数
})
```

### Execution Engine 配置

```python
execution_engine = ExecutionEngine(
    default_timeout=30  # 默认超时时间(秒)
)
```

## 📈 性能优化

### 1. 并发执行
Intelligence Agent 会自动生成并发分组,按module分组执行:

```python
parallel_groups = {
    'user': ['TC_001', 'TC_002'],
    'order': ['TC_003', 'TC_004']
}
```

### 2. 智能跳过
低风险测试用例会被自动跳过,节省执行时间:

```python
skipped_tests = ['TC_005', 'TC_006']  # 风险评分 < 0.3
```

### 3. 优先级排序
高风险测试用例优先执行,快速发现问题:

```python
execution_order = ['TC_001', 'TC_002', 'TC_003']  # 按风险评分降序
```

## 🐛 错误处理

### 常见错误

1. **测试用例未找到**
```json
{
  "success": false,
  "message": "未找到任何有效的测试用例"
}
```
解决: 确保test_case_ids中的ID存在于系统中

2. **Modules SDK 不可用**
```json
{
  "detail": "Modules SDK 不可用"
}
```
解决: 检查modules目录是否正确安装

3. **执行超时**
```json
{
  "error": "Execution timeout"
}
```
解决: 增加timeout配置或优化测试用例

## 📝 最佳实践

### 1. 测试用例设计
- 使用清晰的ID命名: `TC_模块_功能_序号`
- 设置合理的优先级: P0(核心) > P1(重要) > P2(一般) > P3(次要)
- 添加module分组,便于并发执行

### 2. 执行策略
- 首次执行: 执行所有测试用例,建立基线
- 日常执行: 使用智能选择,只执行高风险用例
- 发布前: 执行所有P0和P1用例

### 3. 修复策略
- L1错误: 自动重试3次
- L2错误: 重新生成测试数据
- L3错误: 标记为flaky,暂时容错
- L4错误: 立即通知开发人员

## 🔗 相关文档

- [Intelligence Agent 文档](./INTELLIGENCE_ARCHITECTURE_SUMMARY.md)
- [Execution Engine 文档](./EXECUTION_ENGINE_COMPLETE.md)
- [Healing Engine 文档](./RESILIENCE_ENGINE_COMPLETE.md)
- [Report Generator 文档](./PROJECT_COMPLETE_SUMMARY.md)

## 📞 支持

如有问题,请查看:
1. 后端日志: 查看详细执行过程
2. 测试脚本: `test_intelligent_pipeline.py`
3. API文档: http://localhost:8000/docs

---

**版本**: v2.0
**更新时间**: 2026-04-18
**状态**: ✅ 已完成并测试
