# GitLab 集成指南

## 概述

本指南介绍如何将AI测试平台与GitLab集成，实现代码推送自动触发测试。

## 集成方式

### 方式1: GitLab Webhook（推荐）

通过GitLab Webhook实时接收push事件并触发测试。

#### 1.1 启动Webhook处理器

```bash
# 启动webhook服务
python examples/git_hooks/gitlab_webhook.py
```

服务将在 `http://0.0.0.0:8001` 启动，提供以下端点：
- Webhook: `http://your-server:8001/webhook/gitlab`
- 健康检查: `http://your-server:8001/webhook/gitlab/health`

#### 1.2 配置GitLab Webhook

1. 进入GitLab项目设置
2. 导航到 `Settings` → `Webhooks`
3. 添加新的Webhook:
   - **URL**: `http://your-server:8001/webhook/gitlab`
   - **Secret Token**: 配置密钥（可选，建议配置）
   - **Trigger**: 勾选 `Push events`
   - **SSL verification**: 根据实际情况选择

4. 点击 `Add webhook`

#### 1.3 测试Webhook

在Webhook列表中点击 `Test` → `Push events`，查看响应：

```json
{
  "message": "Test triggered successfully",
  "trigger_id": "git_1234567890",
  "status": "pending",
  "repo": "group/project",
  "branch": "main",
  "commit": "abc123de"
}
```

#### 1.4 配置密钥验证（推荐）

编辑 `gitlab_webhook.py`:

```python
webhook_router = create_gitlab_webhook_router(
    trigger_api_url="http://localhost:8000/api/trigger/git-push",
    webhook_secret="your-secret-token-here"  # 与GitLab配置一致
)
```

### 方式2: GitLab CI/CD Pipeline

通过GitLab CI/CD在每次push时自动触发测试。

#### 2.1 添加CI配置文件

将 `.gitlab-ci.yml` 复制到项目根目录：

```bash
cp examples/gitlab-ci/.gitlab-ci.yml .gitlab-ci.yml
```

#### 2.2 配置变量

在GitLab项目中配置CI/CD变量：

1. 进入 `Settings` → `CI/CD` → `Variables`
2. 添加变量:
   - `AI_TEST_API`: `http://your-ai-test-server:8000/api/trigger/git-push`
   - `AI_TEST_TOKEN`: 认证Token（如果需要）

#### 2.3 CI Pipeline 流程

```yaml
stages:
  - test              # 基础测试
  - trigger-ai-test   # 触发AI测试
  - report            # 获取测试结果
```

**触发AI测试阶段**:
```yaml
trigger-ai-test:
  stage: trigger-ai-test
  script:
    - # 收集Git信息
    - # 构建JSON请求
    - # 调用触发API
    - # 保存trigger_id
```

**等待结果阶段**（可选）:
```yaml
wait-for-results:
  stage: report
  script:
    - # 轮询检查测试状态
    - # 输出测试结果
```

#### 2.4 查看Pipeline

推送代码后，在GitLab中查看Pipeline执行情况：

```
CI/CD → Pipelines → 选择最新的Pipeline
```

输出示例：
```
=========================================
Triggering AI Test Platform
=========================================
Repo: group/project
Branch: feature/user-auth
Commit: abc123def456
Author: 张三
Message: feat: 添加用户认证功能
=========================================
✅ AI Test triggered successfully!
Trigger ID: git_1234567890
```

## 触发策略

### 自动触发规则

系统会根据提交信息和变更文件自动生成测试策略：

#### 优先级判断

| 关键词 | 优先级 | 说明 |
|--------|--------|------|
| hotfix, critical, urgent | P0 | 紧急修复，立即执行 |
| feature, 新功能 | P1 | 新功能，高优先级 |
| 其他 | P2 | 常规变更 |

#### 测试范围

| 关键词 | 测试范围 | 说明 |
|--------|----------|------|
| refactor, 重构, 架构 | full | 全量测试 |
| 其他 | incremental | 增量测试 |

#### 关注领域

| 变更文件 | 关注领域 |
|----------|----------|
| *api*, *controller* | api_testing |
| *model*, *entity* | data_validation |
| *service* | business_logic |

### 示例

**提交1: 紧急修复**
```bash
git commit -m "hotfix: 修复登录bug"
# 变更: src/auth/login.py

# 生成策略:
# - 优先级: P0
# - 范围: incremental
# - 关注: api_testing
```

**提交2: 架构重构**
```bash
git commit -m "refactor: 重构用户模块"
# 变更: src/user/*.py

# 生成策略:
# - 优先级: P2
# - 范围: full
# - 关注: api_testing, business_logic
```

## 分支策略

### 主分支保护

在主分支上触发完整回归测试：

```yaml
trigger-full-test:
  stage: trigger-ai-test
  script:
    - # 触发完整测试
  only:
    - main
    - master
```

### 功能分支

功能分支触发增量测试：

```yaml
trigger-ai-test:
  stage: trigger-ai-test
  script:
    - # 触发增量测试
  only:
    - branches
  except:
    - main
    - master
```

### Merge Request

在MR时触发测试：

```yaml
trigger-mr-test:
  stage: trigger-ai-test
  script:
    - # 触发MR测试
  only:
    - merge_requests
```

## 监控和告警

### 查看触发历史

```bash
# 通过API查询
curl http://your-server:8000/api/trigger/list?trigger_type=git_push&limit=20
```

### 查看测试状态

```bash
# 查询特定触发的状态
curl http://your-server:8000/api/trigger/status/{trigger_id}
```

响应示例：
```json
{
  "trigger_id": "git_1234567890",
  "trigger_type": "git_push",
  "status": "success",
  "created_at": "2024-01-01T10:00:00",
  "trace_id": "trace_abc123",
  "pipeline_result": {
    "test_cases_generated": 10,
    "test_cases_executed": 10,
    "test_cases_passed": 9,
    "test_cases_failed": 1
  },
  "source": {
    "repo": "group/project",
    "branch": "main",
    "commit_id": "abc123",
    "author": "张三"
  }
}
```

### GitLab通知集成

在 `.gitlab-ci.yml` 中添加通知：

```yaml
notify-results:
  stage: report
  script:
    - |
      if [ "$TEST_STATUS" = "success" ]; then
        curl -X POST "$GITLAB_API/projects/$CI_PROJECT_ID/statuses/$CI_COMMIT_SHA" \
          -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
          -d "state=success&name=AI-Test&description=测试通过"
      else
        curl -X POST "$GITLAB_API/projects/$CI_PROJECT_ID/statuses/$CI_COMMIT_SHA" \
          -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
          -d "state=failed&name=AI-Test&description=测试失败"
      fi
```

## 故障排查

### 问题1: Webhook未触发

**检查步骤**:
1. 确认webhook服务正在运行
   ```bash
   curl http://your-server:8001/webhook/gitlab/health
   ```

2. 检查GitLab webhook日志
   - 进入 `Settings` → `Webhooks`
   - 点击webhook → `Recent Deliveries`
   - 查看请求和响应

3. 检查网络连接
   ```bash
   # 从GitLab服务器测试连接
   curl -X POST http://your-server:8001/webhook/gitlab \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   ```

### 问题2: CI Pipeline失败

**检查步骤**:
1. 查看Pipeline日志
   - 进入 `CI/CD` → `Pipelines`
   - 点击失败的Pipeline
   - 查看具体Job的日志

2. 检查变量配置
   ```bash
   # 在CI脚本中打印变量（注意不要打印敏感信息）
   echo "AI_TEST_API: $AI_TEST_API"
   ```

3. 手动测试API
   ```bash
   curl -X POST "$AI_TEST_API" \
     -H "Content-Type: application/json" \
     -d '{"repo":"test","branch":"main","commit_id":"test"}'
   ```

### 问题3: 测试未执行

**检查步骤**:
1. 查看触发记录
   ```bash
   curl http://your-server:8000/api/trigger/status/{trigger_id}
   ```

2. 检查Pipeline服务
   ```python
   # 确认Pipeline服务已配置
   trigger_system = TestTriggerSystem(pipeline_service=pipeline_service)
   ```

3. 查看日志
   ```bash
   # 查看触发系统日志
   tail -f logs/trigger_system.log
   ```

## 最佳实践

### 1. 使用Webhook（推荐）
- 实时触发，延迟低
- 不占用CI/CD资源
- 独立部署，易于维护

### 2. 使用CI/CD
- 与现有流程集成
- 可以等待测试结果
- 支持复杂的条件判断

### 3. 混合使用
- Webhook用于快速反馈
- CI/CD用于关键分支的完整测试

### 4. 安全建议
- 配置Secret Token验证
- 使用HTTPS传输
- 限制webhook访问IP
- 定期轮换密钥

### 5. 性能优化
- 增量测试用于功能分支
- 完整测试用于主分支
- 定时任务用于夜间回归

## 完整示例

### 项目结构
```
your-project/
├── .gitlab-ci.yml          # CI配置
├── src/
│   ├── api/
│   ├── service/
│   └── model/
└── tests/
```

### 工作流程

1. **开发者推送代码**
   ```bash
   git add .
   git commit -m "feat: 添加用户注册功能"
   git push origin feature/user-register
   ```

2. **GitLab触发Webhook**
   - GitLab检测到push事件
   - 调用webhook: `POST /webhook/gitlab`

3. **Webhook处理器**
   - 接收GitLab事件
   - 提取commit信息
   - 调用触发API: `POST /api/trigger/git-push`

4. **触发系统**
   - 分析代码变更
   - 生成测试策略
   - 调用Pipeline执行测试

5. **Pipeline执行**
   - 生成测试用例
   - 执行测试
   - 生成报告

6. **结果反馈**
   - 更新触发状态
   - 记录trace_id
   - 保存测试结果

## 参考资料

- [GitLab Webhooks文档](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html)
- [GitLab CI/CD文档](https://docs.gitlab.com/ee/ci/)
- [触发系统使用指南](TRIGGER_SYSTEM_GUIDE.md)
