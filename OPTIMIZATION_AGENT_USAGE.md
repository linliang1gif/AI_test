# TestOptimizationAgent 使用指南

## 📖 概述

TestOptimizationAgent 是一个智能测试优化代理，用于优化测试用例和执行策略。

## 🎯 核心功能

### 1. 测试去重
- 识别相同 API + 相同参数结构的测试
- 保留边界测试、异常测试、高优先级测试
- 移除低优先级的冗余测试

### 2. 优先级排序
- 结合测试用例优先级（critical/high/medium/low）
- 结合 LearningAgent 的风险评分
- 综合分数 = 优先级 × 0.6 + 风险 × 0.4

### 3. 覆盖率分析
- 识别覆盖重复的 API（超过 3 个测试）
- 识别未覆盖的重要路径
- 输出覆盖率报告

### 4. 执行计划
- 优化后的测试用例列表
- 执行顺序（按优先级排序）
- 预计耗时和节省时间

## 🚀 使用方式

### 方式 1: 独立使用

```python
from modules.agents import TestOptimizationAgent, LearningAgent

# 创建 Agent
optimization_agent = TestOptimizationAgent(config={
    'dedup_threshold': 0.9,        # 去重相似度阈值
    'keep_boundary': True,         # 保留边界测试
    'keep_negative': True,         # 保留异常测试
    'keep_high_priority': True     # 保留高优先级测试
})

learning_agent = LearningAgent()

# 执行优化
result = optimization_agent.optimize(testcases, learning_agent)

# 使用优化后的用例
optimized_cases = result['optimized_cases']
dropped_cases = result['dropped_cases']
statistics = result['statistics']
```

### 方式 2: Pipeline 集成

OptimizationAgent 已集成到 Pipeline V2，自动在 Design 和 Execution 之间执行。

```bash
# 运行 Pipeline（自动优化）
py pipeline_v2.py --requirement "用户登录功能" --base-url "https://api.example.com"
```

Pipeline 流程：
```
Discovery → Design → Optimization → Execution → Healing → Report
                         ↑
                    自动优化
```

## 📊 输出结果

### 优化结果字典

```python
{
    "optimized_cases": [TestCase, ...],    # 优化后的用例
    "dropped_cases": [TestCase, ...],      # 被移除的用例
    "execution_plan": {
        "total_cases": 12,
        "optimized_cases": 10,
        "dropped_cases": 2,
        "reduction_rate": "16.7%",
        "execution_order": [...],
        "estimated_time": "20s",
        "estimated_time_saved": "4s"
    },
    "coverage_report": {
        "total_apis": 3,
        "covered_apis": [...],
        "duplicate_coverage": [...],
        "coverage_gaps": [...],
        "avg_tests_per_api": 3.3
    },
    "statistics": {
        "original_count": 12,
        "optimized_count": 10,
        "dropped_count": 2,
        "reduction_rate": 0.167,
        "optimization_duration": 0.001
    }
}
```

## 🔧 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `dedup_threshold` | float | 0.9 | 去重相似度阈值 |
| `keep_boundary` | bool | True | 保留边界测试 |
| `keep_negative` | bool | True | 保留异常测试 |
| `keep_high_priority` | bool | True | 保留高优先级测试 |

## 📈 优化策略

### 去重策略

1. 按 API 分组（相同 API 的测试归为一组）
2. 对每组进行去重：
   - 保留所有边界测试
   - 保留所有异常测试
   - 保留所有高优先级测试（critical/high）
   - 普通测试只保留一个（优先级最高的）

### 排序策略

1. 计算优先级分数：
   - critical: 1.0
   - high: 0.7
   - medium: 0.4
   - low: 0.1

2. 获取风险分数（从 LearningAgent）

3. 综合分数 = 优先级分数 × 0.6 + 风险分数 × 0.4

4. 按综合分数降序排序

## 💡 最佳实践

### 1. 与 LearningAgent 配合使用

```python
# 先让 LearningAgent 学习历史数据
learning_agent.learn(execution_results, healing_records)

# 再使用 OptimizationAgent 优化
result = optimization_agent.optimize(testcases, learning_agent)
```

### 2. 查看优化统计

```python
# 获取优化统计
stats = optimization_agent.get_optimization_statistics()

print(f"总优化次数: {stats['total_optimizations']}")
print(f"平均减少比例: {stats['avg_reduction_rate']:.1%}")
```

### 3. 分析覆盖率报告

```python
coverage = result['coverage_report']

# 识别重复覆盖
if coverage['duplicate_coverage']:
    print("⚠️  以下 API 测试过多:")
    for dup in coverage['duplicate_coverage']:
        print(f"  - {dup['api']}: {dup['test_count']} 个测试")
```

## 🧪 测试示例

运行测试：
```bash
py test_optimization_agent.py
```

运行演示：
```bash
py demo_optimization_agent.py
```

## 📝 示例输出

```
================================================================================
📊 优化结果
================================================================================

统计信息:
  原始用例数: 12
  优化后用例数: 10
  移除用例数: 2
  减少比例: 16.7%
  优化耗时: 0.001s

执行计划:
  总用例: 12
  优化后: 10
  移除: 2
  减少比例: 16.7%
  预计耗时: 20s
  节省时间: 4s

覆盖率报告:
  总 API 数: 3
  平均每个 API 的测试数: 3.3
  ⚠️  重复覆盖 (1 个):
     - POST /payment/create: 4 个测试 - 考虑减少测试数量
```

## ⚠️ 注意事项

1. **去重逻辑**：基于 API 路径和测试类型，不是基于测试数据
2. **风险评分**：需要 LearningAgent 有足够的历史数据
3. **保留策略**：边界测试和异常测试始终保留，即使优先级低
4. **执行顺序**：优化后的用例已按优先级排序，建议按顺序执行

## 🔗 相关文档

- `OPTIMIZATION_AGENT_COMPLETE.md` - 实现完成报告
- `test_optimization_agent.py` - 测试文件
- `demo_optimization_agent.py` - 演示文件
- `pipeline_v2.py` - Pipeline 集成

## 📞 集成点

### 在 Pipeline 中的位置

```
Design Agent (生成测试用例)
    ↓
Optimization Agent (优化测试用例) ← 这里
    ↓
Execution Agent (执行优化后的用例)
```

### 与其他 Agent 的关系

- **Design Agent**: 提供原始测试用例
- **Learning Agent**: 提供风险评分数据
- **Execution Agent**: 使用优化后的用例
- **Healing Agent**: 修复失败用例（不受优化影响）

## ✅ 总结

TestOptimizationAgent 通过智能去重、优先级排序和覆盖率分析，可以：

- 减少 10-30% 的冗余测试
- 提高执行效率（节省时间）
- 优化测试覆盖质量
- 高风险 + 高优先级测试优先执行

已完整集成到 Pipeline V2，开箱即用。
