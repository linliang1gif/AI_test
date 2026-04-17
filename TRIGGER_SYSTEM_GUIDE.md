# CI/CD自动测试触发系统使用指南

## 概述

TestTriggerSystem 是一个完整的CI/CD自动测试触发系统，支持Git push、API手动触发和定时任务触发，自动调用Pipeline执行测试。

## 核心功能

### 1. Git Push 触发
当代码推送到Git仓库时自动触发测试
- 自动分析代码变更
- 智能生成测试策略
- 根据提交信息调整优先级

### 2. API 手动触发
通过API手动触发测试执行
- 支持自定义测试需求
- 可配置优先级
- 支持Swagger文件

### 3. 定时任务触发
定时执行测试（如每日回归测试）
- Cron表达式支持
- 灵活的调度配置
- 任务启用/禁用管理

## 快速开始

### 基本使用

```python
from modules.trigger.test_trigger_system import TestTriggerSystem
from pipeline_v2 import PipelineService

# 创建Pipeline服务
pipeline_service = PipelineService()

# 创建触发系统
trigger_system = TestTriggerSystem(pipeline_service=pipeline_service)

# Git Push 触发
result = trigger_system.on_git_push(
    repo="my-project",
    branch="main",
    commit_id="abc123",
    commit_message="feat: 新功能",
    changed_files=["src/api/user.py"],
    author="张三"
)

print(f"Trigger ID: {result['trigger_id']}")
print(f"Status: {result['status']}")
```

### 手动触发

```python
result = trigger_system.manual_trigger(
    requirement="测试用户登录功能",
    priority="P0",
    user="测试工程师"
)
```

### 定时触发

```python
# 每天凌晨2点执行回归测试
result = trigger_system.schedule_trigger(
    cron_expression="0 2 * * *",
    requirement="每日回归测试",
    job_name="daily_regression",
    priority="P2"
)
```

## API接口

### 1. Git Push 触发

```bash
POST /api/trigger/git-push
Content-Type: application/json

{
  "repo": "my-project",
  "branch": "main",
  "commit_id": "abc123def456",
  "commit_message": "feat: 添加新功能",
  "changed_files": ["src/api/user.py", "tests/test_user.py"],
  "author": "张三"
}
```

响应:
```json
{
  "trigger_id": "git_1234567890",
  "status": "pending",
  "message": "Git触发已提交，正在分析变更..."
}
```

### 2. 手动触发

```bash
POST /api/trigger/manual
Content-Type: application/json

{
  "requirement": "测试用户登录功能",
  "priority": "P0",
  "user": "测试工程师"
}
```

### 3. 创建定时任务

```bash
POST /api/trigger/scheduled
Content-Type: application/json

{
  "cron_expression": "0 2 * * *",
  "requirement": "每日回归测试",
  "job_name": "daily_regression",
  "priority": "P2",
  "enabled": true
}
```

### 4. 查询触发状态

```bash
GET /api/trigger/status/{trigger_id}
```

响应:
```json
{
  "trigger_id": "git_1234567890",
  "trigger_type": "git_push",
  "status": "success",
  "created_at": "2024-01-01T10:00:00",
  "started_at": "2024-01-01T10:00:01",
  "completed_at": "2024-01-01T10:05:30",
  "trace_id": "trace_abc123",
  "pipeline_result": {
    "test_cases_generated": 10,
    "test_cases_executed": 10,
    "test_cases_passed": 9,
    "test_cases_failed": 1
  }
}
```

### 5. 列出触发记录

```bash
GET /api/trigger/list?trigger_type=git_push&status=success&limit=50
```

### 6. 管理定时任务

```bash
# 列出所有定时任务
GET /api/trigger/scheduled

# 更新定时任务
PUT /api/trigger/scheduled/{job_id}
{
  "enabled": false
}

# 删除定时任务
DELETE /api/trigger/scheduled/{job_id}
```

## Git Hook 集成

### 方式1: Git Post-Receive Hook

1. 复制hook脚本到仓库:
```bash
cp examples/git_hooks/post-receive .git/hooks/
chmod +x .git/hooks/post-receive
```

2. 配置API地址:
```bash
# 编辑 .git/hooks/post-receive
TRIGGER_API_URL="http://your-server:8000/api/trigger/git-push"
```

3. 推送代码时自动触发:
```bash
git push origin main
# 输出:
# =========================================
# Git Push Detected
# =========================================
# Repo: my-project
# Branch: main
# Commit: abc123
# ✅ Test triggered successfully!
# Trigger ID: git_1234567890
```

### 方式2: GitHub Webhook

1. 启动webhook处理器:
```bash
python examples/git_hooks/github_webhook.py
```

2. 在GitHub仓库设置中添加Webhook:
   - Payload URL: `http://your-server:8001/webhook/github`
   - Content type: `application/json`
   - Events: `Just the push event`
   - Secret: 配置密钥（可选）

3. 推送代码时GitHub自动调用webhook

## 测试策略

### Git变更分析

系统会自动分析Git变更并生成测试策略:

1. **测试范围**:
   - `incremental`: 增量测试（默认）
   - `full`: 全量测试（重构/架构变更时）

2. **优先级**:
   - `P0`: hotfix、critical、urgent
   - `P1`: feature、新功能
   - `P2`: 其他变更

3. **关注领域**:
   - API文件变更 → api_testing
   - Model文件变更 → data_validation
   - Service文件变更 → business_logic

### 示例

```python
# 提交信息: "hotfix: 修复登录bug"
# 变更文件: ["src/auth/login.py"]
# 
# 生成策略:
# {
#   "test_scope": "incremental",
#   "priority": "P0",
#   "focus_areas": ["api_testing"]
# }
```

## Cron表达式

定时任务使用标准Cron表达式:

```
格式: 分 时 日 月 周
     * * * * *
     │ │ │ │ │
     │ │ │ │ └─ 星期 (0-7, 0和7都表示周日)
     │ │ │ └─── 月份 (1-12)
     │ │ └───── 日期 (1-31)
     │ └─────── 小时 (0-23)
     └───────── 分钟 (0-59)
```

### 常用示例

```python
# 每天凌晨2点
"0 2 * * *"

# 每周一早上9点
"0 9 * * 1"

# 每月1号凌晨3点
"0 3 1 * *"

# 每小时执行
"0 * * * *"

# 每15分钟执行
"*/15 * * * *"

# 工作日早上10点
"0 10 * * 1-5"
```

## 与Pipeline集成

触发系统会调用Pipeline服务执行测试:

```python
# Pipeline服务接口
class PipelineService:
    def run_pipeline(
        self,
        requirement: str,
        swagger_file: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        执行测试Pipeline
        
        Returns:
            {
                "trace_id": "...",
                "status": "success",
                "test_cases_generated": 10,
                "test_cases_executed": 10,
                "test_cases_passed": 9
            }
        """
        pass
```

触发系统会在config中传递触发信息:
```python
config = {
    "trigger_type": "git_push",  # 或 "manual", "scheduled"
    "trigger_id": "git_1234567890",
    "test_strategy": {...},  # Git触发时包含
    "priority": "P0"
}
```

## 运行示例

```bash
# 运行测试
python test_trigger_system.py

# 运行演示
python examples/demo_trigger_system.py

# 启动API服务（需要集成到backend_api_server.py）
python ai-test-platform/backend_api_server.py
```

## 最佳实践

### 1. Git触发
- 在CI/CD流程中集成Git hook
- 根据分支配置不同的测试策略
- 使用提交信息关键词控制优先级

### 2. 手动触发
- 用于临时测试需求
- 用于验证特定功能
- 用于回归测试

### 3. 定时触发
- 每日回归测试（凌晨执行）
- 每周全量测试（周末执行）
- 性能测试（低峰期执行）

### 4. 监控和告警
- 定期检查触发记录
- 监控失败率
- 设置告警通知

## 故障排查

### 问题1: 触发失败
```python
# 检查Pipeline服务是否正常
status = trigger_system.get_trigger_status(trigger_id)
print(status.get('error'))
```

### 问题2: 定时任务未执行
```python
# 检查任务是否启用
jobs = trigger_system.list_scheduled_jobs()
for job in jobs:
    print(f"{job['job_name']}: enabled={job['enabled']}")

# 检查调度器是否运行
if not trigger_system.scheduler_running:
    trigger_system.start_scheduler()
```

### 问题3: Git hook不工作
```bash
# 检查hook文件权限
ls -la .git/hooks/post-receive

# 检查API地址是否正确
curl -X POST http://localhost:8000/api/trigger/git-push \
  -H "Content-Type: application/json" \
  -d '{"repo":"test","branch":"main","commit_id":"test"}'
```

## 文件清单

- `modules/trigger/test_trigger_system.py` - 触发系统核心实现
- `modules/trigger/trigger_api.py` - FastAPI接口
- `modules/trigger/__init__.py` - 模块导出
- `examples/git_hooks/post-receive` - Git hook脚本
- `examples/git_hooks/github_webhook.py` - GitHub webhook处理器
- `examples/demo_trigger_system.py` - 使用示例
- `test_trigger_system.py` - 测试脚本
- `TRIGGER_SYSTEM_GUIDE.md` - 使用指南
