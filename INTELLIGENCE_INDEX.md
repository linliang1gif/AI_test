# Intelligence Agent 架构 - 文档索引

## 📚 快速导航

### 🚀 快速开始

1. **[快速开始指南](INTELLIGENCE_QUICK_START.md)** ⭐ 推荐首先阅读
   - 5分钟快速上手
   - 代码示例
   - 常见问题

2. **[测试脚本](test_intelligence_architecture.py)**
   - 验证架构升级
   - 性能测试
   - 功能测试

### 📖 详细文档

3. **[完整升级文档](INTELLIGENCE_ARCHITECTURE_UPGRADE.md)**
   - 升级目标
   - 修改点详解
   - 架构对比
   - 使用示例

4. **[架构对比](ARCHITECTURE_COMPARISON.md)**
   - 旧架构 vs 新架构
   - 性能对比
   - 功能对比
   - 收益分析

5. **[完整总结](INTELLIGENCE_ARCHITECTURE_SUMMARY.md)**
   - 完成情况
   - 修改点清单
   - 代码统计
   - 核心价值

### 💻 核心代码

6. **[ExecutionEngine](modules/executor/execution_engine.py)**
   - execute_plan (新架构)
   - execute_legacy (兼容模式)
   - execute (已废弃)

7. **[Pipeline V2 Intelligence](pipeline_v2_intelligence.py)**
   - 完整 Pipeline
   - Intelligence Agent 集成
   - 7 个阶段

### 📊 示例文件

8. **执行计划示例** (`output/execution_plan.json`)
   - selected_tests
   - execution_order
   - parallel_groups
   - risk_scores

9. **测试报告示例** (`output/report_intelligence.html`)
   - 测试结果
   - 统计信息
   - 失败详情

## 🎯 按需求查找

### 我想快速上手

→ 阅读 [快速开始指南](INTELLIGENCE_QUICK_START.md)
→ 运行 `python test_intelligence_architecture.py`
→ 运行 `python pipeline_v2_intelligence.py`

### 我想了解架构变化

→ 阅读 [架构对比](ARCHITECTURE_COMPARISON.md)
→ 查看修改点清单

### 我想了解性能提升

→ 阅读 [架构对比 - 性能对比](ARCHITECTURE_COMPARISON.md#性能对比)
→ 查看收益分析

### 我想迁移旧代码

→ 阅读 [快速开始指南 - 兼容模式](INTELLIGENCE_QUICK_START.md#示例-2-兼容模式)
→ 使用 `execute_legacy`

### 我想了解完整实现

→ 阅读 [完整升级文档](INTELLIGENCE_ARCHITECTURE_UPGRADE.md)
→ 查看核心代码

## 📋 文档清单

### 核心文档 (必读)

- ✅ [快速开始指南](INTELLIGENCE_QUICK_START.md) - 5分钟上手
- ✅ [完整升级文档](INTELLIGENCE_ARCHITECTURE_UPGRADE.md) - 详细说明
- ✅ [架构对比](ARCHITECTURE_COMPARISON.md) - 对比分析
- ✅ [完整总结](INTELLIGENCE_ARCHITECTURE_SUMMARY.md) - 总结报告
- ✅ [文档索引](INTELLIGENCE_INDEX.md) - 本文档

### 代码文件 (核心)

- ✅ [execution_engine.py](modules/executor/execution_engine.py) - 执行引擎
- ✅ [pipeline_v2_intelligence.py](pipeline_v2_intelligence.py) - Pipeline
- ✅ [test_intelligence_architecture.py](test_intelligence_architecture.py) - 测试脚本

### 示例文件 (参考)

- ✅ `output/execution_plan.json` - 执行计划
- ✅ `output/report_intelligence.html` - 测试报告
- ✅ `output/pipeline_summary_intelligence.json` - Pipeline 摘要

## 🔍 关键概念

### Intelligence Agent

智能决策引擎,负责:
- 计算测试用例风险评分
- 决定哪些用例执行/跳过
- 生成执行顺序 (高风险优先)
- 生成并发分组 (按 module)

**文档:** [完整升级文档 - Intelligence Agent](INTELLIGENCE_ARCHITECTURE_UPGRADE.md#intelligence-agent)

### execution_plan

执行计划,包含:
- `selected_tests`: 选中的测试用例ID列表
- `execution_order`: 执行顺序 (按风险评分排序)
- `parallel_groups`: 并发分组 (按module分组)
- `risk_scores`: 风险评分列表
- `statistics`: 统计信息

**文档:** [快速开始指南 - execution_plan](INTELLIGENCE_QUICK_START.md#execution_plan)

### test_cases_map

测试用例映射,用于 O(1) 查找:
```python
test_cases_map = {tc.id: tc for tc in test_cases}
```

**文档:** [架构对比 - test_cases_map](ARCHITECTURE_COMPARISON.md#test_cases_map)

### execute_plan

新架构核心方法:
```python
def execute_plan(self, execution_plan: Dict, test_cases_map: Dict) -> List[ExecutionResult]
```

**文档:** [完整升级文档 - execute_plan](INTELLIGENCE_ARCHITECTURE_UPGRADE.md#execute_plan)

### execute_legacy

兼容模式方法:
```python
def execute_legacy(self, test_cases: List) -> List[ExecutionResult]
```

**文档:** [快速开始指南 - 兼容模式](INTELLIGENCE_QUICK_START.md#示例-2-兼容模式)

## 📊 数据流

```
TestCase[]
    ↓
IntelligenceTestCase[]
    ↓
Intelligence Agent
    ↓
execution_plan + test_cases_map
    ↓
ExecutionEngine.execute_plan()
    ↓
ExecutionResult[]
```

**文档:** [快速开始指南 - 执行流程](INTELLIGENCE_QUICK_START.md#执行流程)

## 🎯 核心优势

| 优势 | 说明 | 文档 |
|------|------|------|
| 智能决策 | Intelligence Agent 完全接管 | [架构对比](ARCHITECTURE_COMPARISON.md) |
| 性能优化 | O(1) 查找,20-40% 时间节省 | [架构对比 - 性能](ARCHITECTURE_COMPARISON.md#性能对比) |
| 向后兼容 | 旧代码无需修改 | [快速开始 - 兼容](INTELLIGENCE_QUICK_START.md#示例-2-兼容模式) |
| 架构统一 | 所有执行路径统一 | [完整总结](INTELLIGENCE_ARCHITECTURE_SUMMARY.md) |
| 可扩展性 | 支持大规模测试用例 | [架构对比 - 性能](ARCHITECTURE_COMPARISON.md#性能对比) |

## 🚀 快速命令

```bash
# 1. 运行测试验证
python test_intelligence_architecture.py

# 2. 运行 Pipeline
python pipeline_v2_intelligence.py

# 3. 查看执行计划
cat output/execution_plan.json

# 4. 查看测试报告
open output/report_intelligence.html

# 5. 查看 Pipeline 摘要
cat output/pipeline_summary_intelligence.json
```

## 📞 获取帮助

### 常见问题

→ 阅读 [快速开始指南 - 常见问题](INTELLIGENCE_QUICK_START.md#常见问题)

### 详细文档

→ 阅读 [完整升级文档](INTELLIGENCE_ARCHITECTURE_UPGRADE.md)

### 代码示例

→ 查看 [快速开始指南 - 代码示例](INTELLIGENCE_QUICK_START.md#代码示例)

### 测试验证

→ 运行 [测试脚本](test_intelligence_architecture.py)

## 🎉 开始使用

1. **阅读** [快速开始指南](INTELLIGENCE_QUICK_START.md)
2. **运行** `python test_intelligence_architecture.py`
3. **体验** `python pipeline_v2_intelligence.py`
4. **查看** `output/execution_plan.json`

---

**文档索引** | Intelligence Agent 架构 | 2026-04-17
