# Test Agent V2 决策引擎使用指南

## 🎯 V2 核心特性

Test Agent V2 将分析结果升级为**可执行决策指令**，可直接驱动：
- Strategy Engine（测试策略）
- Orchestrator（测试编排）
- CI/CD Pipeline（自动化触发）

## 📊 V2 输出结构

### 完整输出示例
```json
{
  // ===== V1 基础字段（保持兼容）=====
  "need_test": true,
  "modules": ["支付模块", "订单模块"],
  "priority": "P0",
  "reason": "核心支付逻辑变更，涉及订单处理",
  "test_types": ["功能测试", "接口测试"],
  "estimated_effort": "2小时",
  "risk_level": "高",
  
  // ===== V2 增强字段（新增）=====
  "action": "run_tests",
  "confidence": 0.9,
  "test_scope": {
    "types": ["api", "ui"],
    "estimated_cases": 30
  },
  "execution_hint": {
    "parallel": true,
    "retry": 1
  },
  "timestamp": "2026-03-23T14:49:44.341713",
  
  // ===== 元数据 =====
  "analyzed_at": "2026-03-23T14:49:44.341713",
  "duration": "7.15s",
  "provider": "ollama",
  "model": "qwen2.5:1.5b"
}
```

## 🔧 V2 字段详解

### 1. action - 可执行指令
```python
"run_tests"  # 执行测试
"skip"       # 跳过测试
```

**生成规则**:
- `need_test == true` → `action = "run_tests"`
- `need_test == false` → `action = "skip"`

**使用场景**:
```python
# Strategy Engine
if decision['action'] == 'run_tests':
    strategy = create_test_strategy(decision)
    execute_strategy(strategy)
```

### 2. confidence - 决策置信度
```python
0.9  # 高置信度（高风险场景）
0.8  # 标准置信度（默认）
0.6  # 低置信度（低优先级场景）
```

**生成规则**:
- 默认: `0.8`
- `risk_level == "高"` → `0.9`
- `priority == "P2"` → `0.6`

**使用场景**:
```python
# 人工审核阈值
if decision['confidence'] < 0.7:
    await notify_human_review(decision)
else:
    auto_execute(decision)
```

### 3. test_scope - 测试范围
```json
{
  "types": ["api", "ui"],      // 测试类型列表
  "estimated_cases": 30        // 预估用例数量
}
```

**types 映射规则**:
- `test_types` 包含 "接口测试" → `["api"]`
- `test_types` 包含 "功能测试" → `["ui"]`
- 默认 → `["api"]`

**estimated_cases 规则**:
- `priority == "P0"` → `30`
- `priority == "P1"` → `20`
- `priority == "P2"` → `10`

**使用场景**:
```python
# Orchestrator 选择执行器
scope = decision['test_scope']

executors = []
if 'api' in scope['types']:
    executors.append(ApiTestExecutor())
if 'ui' in scope['types']:
    executors.append(UiTestExecutor())

# 资源规划
cases = scope['estimated_cases']
allocate_resources(cases)
```

### 4. execution_hint - 执行建议
```json
{
  "parallel": true,   // 是否并行执行
  "retry": 1          // 重试次数
}
```

**parallel 规则**:
- `priority == "P0"` → `true`
- `priority == "P2"` → `false`
- 其他 → `true`

**使用场景**:
```python
# CI/CD 配置
hint = decision['execution_hint']

pytest_args = []
if hint['parallel']:
    pytest_args.append('-n auto')
if hint['retry'] > 0:
    pytest_args.append(f'--reruns {hint["retry"]}')
```

### 5. timestamp - 时间戳
```
"2026-03-23T14:49:44.341713"  // ISO 8601格式
```

**使用场景**:
```python
# 决策追溯
decisions = get_decisions_after(timestamp)

# 审计日志
audit_log.record(decision['timestamp'], decision)
```

## 💡 集成示例

### 示例1: Strategy Engine 集成
```python
from agent.test_agent_service import get_test_agent_service

# 获取决策
agent = get_test_agent_service()
decision = agent.analyze(requirement, git_diff)

# 根据V2字段制定策略
if decision['action'] == 'run_tests':
    # 检查置信度
    if decision['confidence'] < 0.7:
        print("⚠️  低置信度，建议人工审核")
        await notify_reviewer(decision)
        return
    
    # 创建测试策略
    strategy = {
        'priority': decision['priority'],
        'test_types': decision['test_scope']['types'],
        'case_count': decision['test_scope']['estimated_cases'],
        'parallel': decision['execution_hint']['parallel'],
        'retry': decision['execution_hint']['retry']
    }
    
    # 执行策略
    await execute_test_strategy(strategy)
```

### 示例2: Orchestrator 集成
```python
from agent.test_agent_service import get_test_agent_service

# 获取决策
agent = get_test_agent_service()
decision = agent.analyze(requirement, git_diff)

# 编排测试执行
if decision['action'] == 'run_tests':
    scope = decision['test_scope']
    hint = decision['execution_hint']
    
    # 选择执行器
    executors = []
    if 'api' in scope['types']:
        executors.append(ApiTestExecutor(
            case_count=scope['estimated_cases']
        ))
    if 'ui' in scope['types']:
        executors.append(UiTestExecutor(
            case_count=scope['estimated_cases']
        ))
    
    # 配置执行参数
    config = {
        'parallel': hint['parallel'],
        'retry': hint['retry'],
        'priority': decision['priority']
    }
    
    # 执行测试
    results = await orchestrator.run(executors, config)
```

### 示例3: CI/CD Pipeline 集成
```bash
#!/bin/bash
# ci_test_decision.sh

# 调用Test Agent API
DECISION=$(curl -s -X POST http://localhost:8000/api/agent/analyze \
  -H "Content-Type: application/json" \
  -d "{\"requirement\": \"$REQUIREMENT\", \"git_diff\": \"$GIT_DIFF\"}")

# 提取V2字段
ACTION=$(echo $DECISION | jq -r '.action')
CONFIDENCE=$(echo $DECISION | jq -r '.confidence')
PARALLEL=$(echo $DECISION | jq -r '.execution_hint.parallel')
TYPES=$(echo $DECISION | jq -r '.test_scope.types[]')

# 决策执行
if [ "$ACTION" == "run_tests" ]; then
  echo "✅ 需要执行测试 (置信度: $CONFIDENCE)"
  
  # 根据类型执行
  for TYPE in $TYPES; do
    if [ "$TYPE" == "api" ]; then
      pytest tests/api/ --parallel=$PARALLEL
    elif [ "$TYPE" == "ui" ]; then
      pytest tests/ui/ --parallel=$PARALLEL
    fi
  done
else
  echo "⏭️  跳过测试"
fi
```

## 🔍 API 使用

### 调用方式
```bash
POST /api/agent/analyze
Content-Type: application/json

{
  "requirement": "需求描述",
  "git_diff": "代码变更（可选）"
}
```

### Python 调用
```python
import requests

response = requests.post(
    "http://localhost:8000/api/agent/analyze",
    json={
        "requirement": "修改支付逻辑",
        "git_diff": "diff --git a/payment.py..."
    }
)

decision = response.json()

# 使用V2字段
if decision['action'] == 'run_tests':
    print(f"需要测试，置信度: {decision['confidence']}")
    print(f"测试范围: {decision['test_scope']}")
```

### JavaScript 调用
```javascript
const response = await fetch('/api/agent/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    requirement: '修改支付逻辑',
    git_diff: 'diff --git a/payment.py...'
  })
});

const decision = await response.json();

// 使用V2字段
if (decision.action === 'run_tests') {
  console.log(`需要测试，置信度: ${decision.confidence}`);
  console.log(`测试类型: ${decision.test_scope.types}`);
}
```

## 📋 最佳实践

### 1. 置信度阈值策略
```python
confidence = decision['confidence']

if confidence >= 0.8:
    # 高置信度：自动执行
    auto_execute(decision)
elif confidence >= 0.7:
    # 中等置信度：通知但自动执行
    notify_and_execute(decision)
else:
    # 低置信度：人工审核
    require_human_approval(decision)
```

### 2. 优先级队列
```python
decisions = []
for change in changes:
    decision = agent.analyze(change.requirement, change.diff)
    if decision['action'] == 'run_tests':
        decisions.append(decision)

# 按优先级排序
decisions.sort(key=lambda d: {'P0': 0, 'P1': 1, 'P2': 2}[d['priority']])

# 按优先级执行
for decision in decisions:
    execute_tests(decision)
```

### 3. 资源分配
```python
total_cases = sum(
    d['test_scope']['estimated_cases'] 
    for d in decisions 
    if d['action'] == 'run_tests'
)

# 根据总用例数分配资源
workers = calculate_workers(total_cases)
allocate_test_resources(workers)
```

## 🐛 故障排查

### 问题1: V2字段缺失
**症状**: API返回结果中没有 action、confidence 等字段

**解决**:
1. 检查 `agent/controller.py` 中 `AnalyzeResponse` 是否包含V2字段
2. 清除Python缓存: `rm -rf agent/__pycache__`
3. 重启后端服务器

### 问题2: confidence 值异常
**症状**: confidence 不在 0-1 范围内

**解决**:
检查 `enhance_decision()` 函数中的置信度计算逻辑

### 问题3: test_scope.types 为空
**症状**: types 数组为空

**解决**:
检查 LLM 是否正确输出 test_types 字段，如果为空会默认为 ["api"]

## 📞 技术支持

- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/agent/health
- 测试脚本: `test_agent_v2_quick.py`

---
**版本**: V2.0
**更新时间**: 2026-03-23
