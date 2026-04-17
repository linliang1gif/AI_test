# Pipeline V2 使用指南

## 架构升级

从传统模块架构升级为智能 Agent 架构。

### V1 vs V2 对比

| 组件 | V1（传统模块） | V2（Agent 架构） |
|------|---------------|-----------------|
| 测试发现 | TestDiscoveryAgent | TestDiscoveryAgent（保持） |
| 测试设计 | SwaggerTestCaseGenerator | **DesignAgent**（新） |
| 测试执行 | ExecutionEngine | **ExecutionAgent**（新） |
| 自动修复 | HealingEngine（规则引擎） | **HealingAgent**（决策型） |
| 报告生成 | ReportGenerator | ReportGenerator（保持） |

---

## Pipeline 流程

```
Discovery Agent（发现测试点）
    ↓
Design Agent（设计测试用例）
    ↓
Execution Agent（执行测试）
    ↓
Healing Agent（智能自愈）
    ↓
Report Generator（生成报告）
```

---

## 各阶段说明

### 阶段 1: Discovery Agent

**功能**: 发现高风险测试点

**输入**:
- `old_swagger`: 旧版 Swagger 文件
- `new_swagger`: 新版 Swagger 文件

**输出**: `List[TestPoint]`

**调用示例**:
```python
from modules.discovery import TestDiscoveryAgent

discovery_agent = TestDiscoveryAgent()
test_points = discovery_agent.discover_from_swagger_changes(
    old_swagger="old.json",
    new_swagger="new.json"
)
```

**特点**:
- 自动识别 API 变更
- 按风险等级排序
- 支持新增/修改/删除检测

---

### 阶段 2: Design Agent

**功能**: 设计测试用例（具备决策能力）

**输入**:
- Discovery 结果 或
- Swagger 文件 或
- 需求文档

**输出**: `List[TestCase]`

**调用示例**:
```python
from modules.agents import DesignAgent

design_agent = DesignAgent(config={
    'max_testcases_per_api': 5,
    'include_edge_cases': True,
    'include_error_cases': True
})

# 方式1: 从 Discovery 设计
testcases = design_agent.design_from_discovery(test_points)

# 方式2: 从 Swagger 设计
testcases = design_agent.design_from_swagger(swagger_data)

# 方式3: 从需求设计
testcases = design_agent.design_from_requirement("用户登录功能")
```

**特点**:
- 自动控制测试用例数量
- 智能生成边界/异常用例
- 按优先级排序

---

### 阶段 3: Execution Agent

**功能**: 执行测试用例（具备决策能力）

**输入**: `List[TestCase]`

**输出**: `List[ExecutionResult]`

**调用示例**:
```python
from modules.agents import ExecutionAgent

execution_agent = ExecutionAgent(config={
    'environment': 'test',
    'strategy': 'adaptive',          # 自适应策略
    'base_url_test': 'http://test.example.com',
    'max_workers': 4,                # 最大并发数
    'max_retry_count': 3,            # 最大重试次数
    'timeout': 30
})

# 执行测试（带智能决策）
results = execution_agent.run(testcases, environment='test')

# 获取统计
stats = execution_agent.get_statistics()
```

**特点**:
- 自动决策执行策略（串行/并行/优先级）
- 智能重试（超时/连接失败重试，断言失败不重试）
- P0 优先执行
- 支持 fail-fast

---

### 阶段 4: Healing Agent

**功能**: 智能自愈（具备决策能力）

**输入**: `List[ExecutionResult]`

**输出**: `List[HealingRecord]`

**调用示例**:
```python
from modules.agents import HealingAgent

healing_agent = HealingAgent(config={
    'enable_l1': True,               # L1: 重试
    'enable_l2': True,               # L2: 数据修复
    'enable_l3': True,               # L3: 断言修复
    'enable_l4': True,               # L4: 代码修复建议
    'healing_threshold': 0.3,        # 修复价值阈值
    'auto_upgrade': True             # 失败后自动升级层级
})

# 执行智能修复（带决策）
healing_records = healing_agent.heal(results)

# 获取统计
stats = healing_agent.get_statistics()
report = healing_agent.get_healing_report()
```

**特点**:
- L1-L4 分层修复
- 自动选择修复层级
- 判断修复价值（避免浪费时间）
- 失败后自动升级层级

---

### 阶段 5: Report Generator

**功能**: 生成测试报告

**输入**: `List[ExecutionResult]`

**输出**: 测试报告（JSON/HTML/Text）

**调用示例**:
```python
from modules.report import ReportGenerator

report_generator = ReportGenerator()

# 生成报告
report = report_generator.generate(results)

# 保存报告
report_generator.save_report(results, "report.json", format="json")
report_generator.save_report(results, "report.html", format="html")
```

---

## 使用方式

### 方式 1: 从 Swagger 变更发现测试

```bash
py pipeline_v2.py \
  --old-swagger examples/old_swagger.json \
  --new-swagger examples/new_swagger.json \
  --base-url https://api.example.com \
  --environment test \
  --output output
```

**流程**:
1. Discovery Agent 发现变更的 API
2. Design Agent 为变更的 API 设计测试用例
3. Execution Agent 执行测试
4. Healing Agent 自动修复失败用例
5. Report Generator 生成报告

---

### 方式 2: 从单个 Swagger 生成测试

```bash
py pipeline_v2.py \
  --new-swagger examples/swagger.json \
  --base-url https://api.example.com \
  --environment test \
  --output output
```

**流程**:
1. 跳过 Discovery（没有变更对比）
2. Design Agent 从 Swagger 设计测试用例
3. Execution Agent 执行测试
4. Healing Agent 自动修复失败用例
5. Report Generator 生成报告

---

### 方式 3: 从需求文档生成测试

```bash
py pipeline_v2.py \
  --requirement "用户登录功能：支持用户名密码登录" \
  --base-url https://api.example.com \
  --environment test \
  --output output
```

**流程**:
1. 跳过 Discovery
2. Design Agent 从需求设计测试用例
3. Execution Agent 执行测试
4. Healing Agent 自动修复失败用例
5. Report Generator 生成报告

---

### 方式 4: 代码调用

```python
from pipeline_v2 import run_pipeline_v2

# 从需求生成测试
results = run_pipeline_v2(
    requirement="用户登录功能",
    base_url="https://api.example.com",
    environment="test",
    output_dir="output"
)

# 从 Swagger 变更生成测试
results = run_pipeline_v2(
    old_swagger="old.json",
    new_swagger="new.json",
    base_url="https://api.example.com",
    environment="staging",
    output_dir="output"
)
```

---

## 输出文件

Pipeline V2 会在输出目录生成以下文件：

```
output/
├── testcases_v2.json           # 测试用例列表
├── report_v2.json              # JSON 格式报告
├── report_v2.html              # HTML 格式报告
├── healing_records_v2.json     # 修复记录
└── pipeline_summary_v2.json    # Pipeline 摘要
```

---

## 配置说明

### Design Agent 配置

```python
{
    'max_testcases_per_api': 5,      # 每个 API 最大测试用例数
    'include_edge_cases': True,       # 包含边界测试
    'include_error_cases': True,      # 包含异常测试
    'priority_threshold': 'medium'    # 优先级阈值
}
```

### Execution Agent 配置

```python
{
    'environment': 'test',            # 执行环境
    'strategy': 'adaptive',           # 执行策略（adaptive/sequential/parallel/priority）
    'base_url_test': 'http://...',    # 测试环境 URL
    'base_url_staging': 'http://...',  # 预发环境 URL
    'base_url_prod': 'http://...',    # 生产环境 URL
    'max_workers': 4,                 # 最大并发数
    'max_retry_count': 3,             # 最大重试次数
    'retry_delay': 1.0,               # 重试延迟（秒）
    'timeout': 30,                    # 超时时间（秒）
    'fail_fast': False                # 是否快速失败
}
```

### Healing Agent 配置

```python
{
    'enable_l1': True,                # 启用 L1 重试修复
    'enable_l2': True,                # 启用 L2 数据修复
    'enable_l3': True,                # 启用 L3 断言修复
    'enable_l4': True,                # 启用 L4 代码修复建议
    'healing_threshold': 0.3,         # 修复价值阈值
    'max_retry_count': 3,             # 最大重试次数
    'auto_upgrade': True              # 失败后自动升级层级
}
```

---

## Agent 决策能力

### Design Agent 决策

- 自动控制测试用例数量（避免过多）
- 智能选择测试类型（正常/边界/异常）
- 按优先级排序

### Execution Agent 决策

- 自动选择执行策略：
  - 小规模（<5个）→ 串行
  - 大规模（≥5个）→ 并行
  - 高优先级多（>50%）→ 按优先级
- P0 优先执行
- 智能重试：
  - 超时 → 重试
  - 连接失败 → 重试
  - 断言失败 → 不重试

### Healing Agent 决策

- 自动选择修复层级：
  - 超时/网络 → L1 重试
  - 数据无效 → L2 数据修复
  - 断言失败（低严重度）→ L3 断言修复
  - 断言失败（高严重度）→ L4 人工审查
- 判断修复价值（跳过低价值修复）
- 失败后自动升级层级（L1→L2→L3→L4）

---

## 与 V1 的区别

| 特性 | V1 | V2 |
|------|----|----|
| 架构 | 传统模块 | Agent 架构 |
| 决策能力 | 无 | 有 |
| 测试设计 | 固定规则 | 智能决策 |
| 执行策略 | 固定 | 自适应 |
| 重试机制 | 简单重试 | 智能重试 |
| 自愈能力 | 规则匹配 | 策略决策 |
| 修复层级 | 固定 | 自动选择 |
| 可扩展性 | 低 | 高 |

---

## 最佳实践

1. **使用自适应策略**: `strategy='adaptive'` 让 Agent 自动决策
2. **合理配置重试**: 生产环境多重试，开发环境少重试
3. **启用自动升级**: `auto_upgrade=True` 让修复更智能
4. **设置修复阈值**: 避免浪费时间在低价值修复上
5. **P0 用例优先**: 确保关键功能优先测试

---

## 示例运行

```bash
# 示例1: 从需求生成测试
py pipeline_v2.py --requirement "用户登录功能"

# 示例2: 从 Swagger 生成测试
py pipeline_v2.py --new-swagger examples/sample_swagger.json

# 示例3: 从变更发现测试
py pipeline_v2.py \
  --old-swagger examples/old.json \
  --new-swagger examples/new.json \
  --environment staging

# 示例4: 无参数运行（使用默认示例）
py pipeline_v2.py
```

---

## 总结

Pipeline V2 使用新的 Agent 架构，每个 Agent 都具备决策能力：

- **DesignAgent**: 智能设计测试用例
- **ExecutionAgent**: 智能执行测试
- **HealingAgent**: 智能自愈修复

相比 V1，V2 更智能、更自动化、更易扩展！
