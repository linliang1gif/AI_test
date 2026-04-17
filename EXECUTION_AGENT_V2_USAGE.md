# ExecutionAgent V2 使用指南

## 升级内容

ExecutionAgent 已从"普通执行器"升级为"具备决策能力的智能 Agent"。

---

## 新增能力

### 1. 执行顺序决策
- ✅ P0 优先执行
- ✅ 高风险优先
- ✅ 支持 fail-fast 策略

### 2. 智能重试策略
- ✅ 超时 → 自动重试（最多3次）
- ✅ 连接失败 → 重建连接后重试
- ✅ 断言失败 → 不重试（避免浪费时间）

### 3. 并发控制
- ✅ 使用 ThreadPoolExecutor
- ✅ 支持 max_workers 配置
- ✅ 自动管理线程池

### 4. 自动策略选择
- ✅ 小规模（<5个）→ 串行执行
- ✅ 大规模（≥5个）→ 并行执行
- ✅ 高优先级多（>50%）→ 按优先级执行

### 5. 环境控制
- ✅ 支持 base_url 切换（test/staging/prod）
- ✅ 运行时切换环境

---

## 使用示例

### 基础使用

```python
from modules.agents import ExecutionAgent
from core import create_test_case

# 创建测试用例
testcases = [
    create_test_case(id="tc1", title="登录测试", module="auth", priority="critical"),
    create_test_case(id="tc2", title="注册测试", module="auth", priority="high"),
    create_test_case(id="tc3", title="个人信息", module="user", priority="medium"),
]

# 创建 Agent（自适应策略）
agent = ExecutionAgent(config={
    'strategy': 'adaptive',      # 自动决策
    'max_retry_count': 3,         # 最多重试3次
    'max_workers': 4              # 最大并发数
})

# 执行测试
results = agent.run(testcases)

# 查看统计
stats = agent.get_statistics()
print(f"通过率: {stats['pass_rate']:.1%}")
print(f"重试次数: {stats['retried']}")
```

---

### 场景1: P0 优先执行

```python
# P0 用例会自动排在最前面执行
testcases = [
    create_test_case(id="tc1", title="普通测试", module="user", priority="medium"),
    create_test_case(id="tc2", title="P0核心功能", module="payment", priority="critical"),
    create_test_case(id="tc3", title="低优先级", module="report", priority="low"),
]

agent = ExecutionAgent(config={'strategy': 'priority'})
results = agent.run(testcases)

# 执行顺序: tc2 (P0) → tc1 (medium) → tc3 (low)
```

---

### 场景2: Fail-Fast 快速失败

```python
# 遇到失败立即停止，节省时间
agent = ExecutionAgent(config={
    'strategy': 'fail_fast',
    'fail_fast': True
})

results = agent.run(testcases)

# 如果第一个用例失败，后续用例不会执行
```

---

### 场景3: 智能重试

```python
agent = ExecutionAgent(config={
    'max_retry_count': 3,         # 最多重试3次
    'retry_delay': 1.0            # 重试延迟1秒
})

results = agent.run(testcases)

# 重试规则：
# - 超时错误 → 自动重试
# - 连接失败 → 重建连接后重试
# - 断言失败 → 不重试（避免浪费）

stats = agent.get_statistics()
print(f"超时重试: {stats['timeout_retries']}")
print(f"连接重试: {stats['connection_retries']}")
```

---

### 场景4: 并行执行

```python
# 大规模测试用例并行执行
testcases = [
    create_test_case(id=f"tc{i}", title=f"测试{i}", module="api", priority="low")
    for i in range(1, 51)  # 50个测试用例
]

agent = ExecutionAgent(config={
    'strategy': 'parallel',
    'max_workers': 8              # 8个线程并发
})

results = agent.run(testcases)
# 并行执行，速度快
```

---

### 场景5: 环境切换

```python
# 配置多环境 base_url
agent = ExecutionAgent(config={
    'environment': 'test',
    'base_url_test': 'http://test.example.com',
    'base_url_staging': 'http://staging.example.com',
    'base_url_prod': 'http://api.example.com'
})

# 在 test 环境执行
results_test = agent.run(testcases, environment='test')

# 切换到 staging 环境执行
results_staging = agent.run(testcases, environment='staging')

print(f"当前环境: {agent.environment.value}")
print(f"当前 base_url: {agent.get_current_base_url()}")
```

---

### 场景6: 自适应策略（推荐）

```python
# 让 Agent 自动决策最佳执行策略
agent = ExecutionAgent(config={
    'strategy': 'adaptive',       # 自适应
    'parallel_threshold': 5       # 超过5个用例才并行
})

# 小规模（3个用例）→ 自动选择串行
small_testcases = [...]  # 3个用例
results1 = agent.run(small_testcases)
# 决策: sequential

# 大规模（20个用例）→ 自动选择并行
large_testcases = [...]  # 20个用例
results2 = agent.run(large_testcases)
# 决策: parallel

# 高优先级多（70% P0）→ 自动选择优先级执行
priority_testcases = [...]  # 70% critical
results3 = agent.run(priority_testcases)
# 决策: priority
```

---

## 配置参数

```python
config = {
    # 执行策略
    'strategy': 'adaptive',           # sequential/parallel/priority/adaptive/fail_fast
    'fail_fast': False,               # 是否快速失败
    
    # 环境配置
    'environment': 'test',            # local/test/staging/production
    'base_url_local': 'http://localhost:8000',
    'base_url_test': 'http://test.example.com',
    'base_url_staging': 'http://staging.example.com',
    'base_url_prod': 'http://api.example.com',
    
    # 并发控制
    'max_workers': 4,                 # 最大并发线程数
    'parallel_threshold': 5,          # 并行阈值（用例数）
    
    # 重试配置
    'max_retry_count': 3,             # 最大重试次数
    'retry_delay': 1.0,               # 重试延迟（秒）
    'timeout': 30                     # 单个用例超时（秒）
}

agent = ExecutionAgent(config=config)
```

---

## API 参考

### 主要方法

#### `run(testcases, environment=None)`
执行测试用例（主入口）

**参数**:
- `testcases`: 测试用例列表
- `environment`: 可选，运行时切换环境

**返回**: 执行结果列表

---

#### `get_statistics()`
获取执行统计信息

**返回**:
```python
{
    'total_executed': 10,
    'passed': 8,
    'failed': 2,
    'skipped': 0,
    'retried': 3,
    'timeout_retries': 2,
    'connection_retries': 1,
    'pass_rate': 0.8
}
```

---

#### `stop()`
停止当前执行

```python
agent.stop()
```

---

#### `get_current_base_url()`
获取当前环境的 base_url

```python
url = agent.get_current_base_url()
```

---

## 决策逻辑

### 执行计划决策 (`_decide_execution_plan`)

```python
def _decide_execution_plan(testcases):
    """
    决策因素：
    1. 用例数量（小规模串行，大规模并行）
    2. 优先级分布（P0优先）
    3. 风险等级（高风险优先）
    4. fail-fast 配置
    
    返回：
    {
        'strategy': 'priority',
        'testcases': [排序后的用例],
        'max_workers': 1,
        'fail_fast': False
    }
    """
```

**决策规则**:
- 用例数 < 5 → sequential
- 用例数 ≥ 5 且高优先级 > 50% → priority
- 用例数 ≥ 5 且高优先级 ≤ 50% → parallel

---

### 重试逻辑 (`_execute_single_with_retry`)

```python
def _execute_single_with_retry(testcase):
    """
    重试策略：
    1. 超时 → 自动重试（最多3次）
    2. 连接失败 → 重建连接后重试
    3. 断言失败 → 不重试
    4. 未知错误 → 重试
    
    重试延迟：指数退避（1s, 2s, 3s）
    """
```

**失败分类**:
```python
class FailureType(Enum):
    TIMEOUT = "timeout"        # 可重试
    CONNECTION = "connection"  # 可重试
    ASSERTION = "assertion"    # 不重试
    UNKNOWN = "unknown"        # 可重试
```

---

## 性能对比

### 串行 vs 并行

```python
# 20个测试用例

# 串行执行
agent_seq = ExecutionAgent(config={'strategy': 'sequential'})
# 耗时: ~2.0秒

# 并行执行（4线程）
agent_par = ExecutionAgent(config={'strategy': 'parallel', 'max_workers': 4})
# 耗时: ~0.5秒

# 提速: 4倍
```

---

## 最佳实践

### 1. 使用自适应策略
```python
# 推荐：让 Agent 自动决策
agent = ExecutionAgent(config={'strategy': 'adaptive'})
```

### 2. 合理配置重试
```python
# 生产环境：多重试
config = {'max_retry_count': 3, 'retry_delay': 2.0}

# 开发环境：少重试
config = {'max_retry_count': 1, 'retry_delay': 0.5}
```

### 3. P0 用例优先
```python
# 确保 P0 用例有正确的优先级
testcases = [
    create_test_case(..., priority="critical"),  # P0
    create_test_case(..., priority="high"),      # P1
    create_test_case(..., priority="medium"),    # P2
]
```

### 4. 环境隔离
```python
# 不同环境使用不同配置
config_test = {'environment': 'test', 'max_retry_count': 1}
config_prod = {'environment': 'production', 'max_retry_count': 3}
```

---

## 测试验证

运行测试验证所有功能：

```bash
py test_execution_agent_v2.py
```

预期输出：
```
✅ 所有测试通过！ExecutionAgent V2 升级成功！

新增能力:
  ✅ 执行顺序决策（P0优先、高风险优先、fail-fast）
  ✅ 智能重试策略（超时/连接失败重试，断言失败不重试）
  ✅ 并发控制（ThreadPoolExecutor）
  ✅ 自动策略选择（串行/并行自动选择）
  ✅ 环境控制（base_url切换）
```

---

## 升级总结

| 能力 | V1 | V2 |
|------|----|----|
| 执行顺序决策 | ❌ | ✅ P0优先、高风险优先 |
| 智能重试 | ❌ 简单重试 | ✅ 根据失败类型决策 |
| 并发控制 | ✅ 基础 | ✅ 自动调整 |
| 策略选择 | ❌ 手动 | ✅ 自动决策 |
| 环境控制 | ❌ | ✅ base_url切换 |
| Fail-Fast | ❌ | ✅ 支持 |

ExecutionAgent V2 现在是一个真正的"智能 Agent"！
