# GitLab CI 配置指南

## 📋 当前状态

✅ `.gitlab-ci.yml` 文件已创建在你的recycle-server项目中
❌ 文件还未提交到GitLab
⚠️  需要修改API URL配置

## 🔧 配置步骤

### 步骤1: 确定API访问地址

GitLab CI运行在GitLab服务器上,需要能访问你的AI测试平台后端。

**选项A: 使用公网IP (推荐)**
如果你的电脑有公网IP或使用内网穿透:
```yaml
http://你的公网IP:8000/api/trigger/git-push
```

**选项B: 部署到服务器**
将AI测试平台部署到与GitLab同网络的服务器:
```yaml
http://服务器IP:8000/api/trigger/git-push
```

**选项C: 使用GitLab Runner (本地)**
如果GitLab Runner运行在本地,可以使用:
```yaml
http://host.docker.internal:8000/api/trigger/git-push
```

### 步骤2: 修改.gitlab-ci.yml

打开文件:
```
d:\360Downloads\蓝点\recycle-server-feature-1.2.2 (1)\recycle-server-feature-1.2.2\.gitlab-ci.yml
```

找到这一行:
```yaml
- RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:8000/api/trigger/git-push" \
```

修改为你的实际地址:
```yaml
- RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "http://你的IP:8000/api/trigger/git-push" \
```

### 步骤3: 提交到GitLab

```bash
cd "d:\360Downloads\蓝点\recycle-server-feature-1.2.2 (1)\recycle-server-feature-1.2.2"

# 添加文件
git add .gitlab-ci.yml

# 提交
git commit -m "feat: 添加GitLab CI自动测试触发"

# 推送到GitLab
git push origin master
```

### 步骤4: 验证

1. 访问GitLab项目页面
2. 进入 **CI/CD > Pipelines**
3. 查看最新的Pipeline执行情况
4. 点击查看日志,确认触发成功

## 🎯 工作流程

提交代码后:
1. GitLab检测到push事件
2. 自动运行`.gitlab-ci.yml`中的任务
3. 任务调用AI测试平台的触发API
4. 触发系统分析变更并生成测试
5. 在GitLab Pipeline中查看结果

## 🔍 当前配置内容

文件位置: `recycle-server-feature-1.2.2/.gitlab-ci.yml`

配置会在每次push时:
- ✅ 自动触发AI测试
- ✅ 传递项目、分支、提交信息
- ✅ 允许失败(不阻塞其他任务)
- ✅ 显示触发结果

## ⚠️  重要提示

1. **URL必须可访问**: GitLab CI环境必须能访问你的API地址
2. **后端必须运行**: 确保AI测试平台后端在运行
3. **防火墙设置**: 如果使用公网IP,需要开放8000端口
4. **测试连接**: 提交前先测试URL是否可访问

## 🧪 测试API连接

在GitLab CI环境中测试(或本地模拟):
```bash
curl -X POST "http://你的IP:8000/api/trigger/git-push" \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "test",
    "branch": "main",
    "commit_id": "test123",
    "commit_message": "test",
    "author": "test"
  }'
```

如果返回200和trigger_id,说明配置正确!

## 📞 需要帮助?

如果不确定如何配置URL,可以:
1. 先不提交,继续使用手动触发API
2. 或者告诉我你的网络环境,我帮你配置
