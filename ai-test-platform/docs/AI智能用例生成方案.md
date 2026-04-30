# AI 智能用例生成方案

## 核心思路

```
Swagger 接口定义 + 字段 Schema + 业务上下文
              ↓
         AI 大模型分析
              ↓
   每个接口生成 5~10 个场景用例
              ↓
   正向 + 反向 + 边界值 + 权限 + 幂等
```

## 整体架构

```
┌─────────────────────────────────────────────┐
│              前端：AI 用例生成页面             │
│  选接口 → 预览AI生成结果 → 确认导入           │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│         后端：AITestCaseGenerator            │
│                                              │
│  1. 从 Swagger 提取接口定义                    │
│  2. 构造 Prompt（定义+规则+示例）              │
│  3. 调 AI 模型（支持多provider）               │
│  4. 解析 AI 返回的 JSON 用例                   │
│  5. 校验 → 去重 → 入库                        │
└──────────────────────────────────────────────┘
```

## Phase 分步实施

### Phase A：Prompt 工程 + 单接口生成（核心，2天）

**目标：** 给 AI 一个接口定义，让它返回多场景用例

**Prompt 模板设计：**

```
你是 API 测试专家。根据以下接口定义生成测试用例。

## 接口信息
- 路径: POST /basic/basicWarehouse/save
- 功能: 新增仓库
- 字段:
  - name (string, 必填) - 仓库名称
  - code (string, 必填) - 仓库编号
  - type (string, 枚举: NORMAL/COLD/DANGER) - 仓库类型
  - address (string, 非必填) - 地址
  - capacity (integer) - 容量

## 要求
为每个场景生成 请求body + 期望结果，返回 JSON 数组：

1. 正向-完整参数: 所有字段合法
2. 正向-最小参数: 只传必填字段
3. 反向-缺必填: name 不传
4. 反向-空字符串: name=""
5. 反向-类型错误: capacity="abc"
6. 边界-超长: name=500个字符
7. 边界-特殊字符: name含<script>
8. 边界-数字极值: capacity=0, capacity=-1
9. 枚举-非法值: type="INVALID"
```

**AI 输出格式：**

```json
[
  {
    "title": "新增仓库-正向-完整参数",
    "scenario": "positive",
    "body": {"name":"测试仓库A","code":"WH-001","type":"NORMAL","address":"广州","capacity":1000},
    "expected_code": 200,
    "expected_behavior": "success",
    "description": "所有字段合法，期望创建成功"
  },
  {
    "title": "新增仓库-反向-缺少必填name",
    "scenario": "negative",
    "body": {"code":"WH-002","type":"NORMAL"},
    "expected_code": 400,
    "expected_behavior": "client_error",
    "description": "缺少必填字段name，期望返回参数校验错误"
  }
]
```

**后端实现：**
- `services/ai_case_generator.py` — Prompt 构建 + AI 调用 + 结果解析
- 复用现有 AI 模型配置（`/ai-config` 页面已有）
- 支持 OpenAI / 智谱 / 本地 Ollama

---

### Phase B：批量生成 + 前端交互（1天）

**目标：** 选多个接口 → 批量调 AI → 预览 → 确认导入

**API 设计：**

```
POST /api/v2/ai-generate-cases
  body: {
    case_ids: ["TC_001","TC_002"],     // 已有用例，基于它们增强
    generate_count: 8,                  // 每个接口生成几个场景
    scenarios: ["positive","negative","boundary"],  // 场景类型
  }
  response: {
    generated: [
      { source_case_id: "TC_001", new_cases: [...] },
    ]
  }

POST /api/v2/ai-generate-cases/confirm
  body: { case_ids: [...] }            // 确认导入选中的
```

**前端：**
- 在用例列表加"AI 增强"按钮
- 弹窗选择生成选项
- 预览 AI 生成结果，可勾选/反选
- 确认导入到用例库

---

### Phase C：业务上下文增强（1天）

**目标：** 让 AI 生成的数据更贴合蓝点业务

**方式：**
1. 从 list 接口拿真实数据样本 → 作为 Prompt 上下文
2. 枚举值字典 → 告诉 AI 合法的 type、status 值
3. 业务规则注入 → "编号格式: WH-yyyyMMdd-xxx"

```
Prompt 增强:
## 业务上下文
- 该系统是蓝点回收系统（仓储管理）
- 仓库编号规则: WH-日期-序号
- 真实数据样本: {"name":"佛山主仓","code":"WH-20250101-001","type":"NORMAL"}
- 已存在的仓库名: 佛山主仓、广州中转仓
```

---

### Phase D：场景链/流程编排（后续）

**目标：** 多接口串联成业务流程

```
AI 输入: 采购入库流程涉及的接口列表
AI 输出:
  Step 1: save 采购单 → 提取 orderNo
  Step 2: approve 采购单(orderNo)
  Step 3: save 入库单(关联 orderNo)
  Step 4: confirm 入库
  Step 5: query 库存 → 断言数量增加
```

---

## 技术选型

| 组件 | 方案 |
|---|---|
| AI 模型 | 优先智谱GLM / OpenAI，回退本地 Ollama |
| Prompt | 结构化模板，按接口模式(save/list/page)分不同策略 |
| 输出解析 | JSON 格式约束 + 容错解析（AI 有时返回不规范JSON） |
| 存储 | 复用 TestCase 表，source 标记为 `ai_generated` |
| 去重 | 按 path + scenario 组合去重 |
| 限流 | 批量生成时控制 AI 调用频率（避免超 token 限制） |

## 预估效果

| 指标 | 当前 | AI 增强后 |
|---|---|---|
| 每接口用例数 | 1 | 5~10 |
| 场景覆盖 | 连通性 | 正向+反向+边界+枚举 |
| 总用例数 | 4000 | 20000~40000 |
| 发现 bug 能力 | 低（只发现接口挂了）| 中（能发现参数校验缺失、类型不严格）|

## 优先级

```
Phase A（Prompt + 单接口） ← 先做，见效最快
Phase B（批量 + 前端）     ← A 验证后做
Phase C（业务上下文）      ← 提升质量
Phase D（流程编排）        ← 高级能力
```
