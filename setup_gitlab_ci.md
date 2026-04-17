# GitLab CI 快速设置指南

## 已完成的步骤

✅ `.gitlab-ci.yml` 文件已创建在你的 recycle-server 项目中

## 接下来的步骤

### 1. 修改API地址（重要！）

打开文件：
```
d:\360Downloads\蓝点\recycle-server-feature-1.2.2\.gitlab-ci.yml
```

找到这一行（第35行左右）：
```yaml
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:8000/api/trigger/git-push" \
```

修改为你的实际地址：
- 如果AI测试平台在本机：保持 `http://localhost:8000/api/trigger/git-push`
- 如果在其他机器：改为 `http://你的IP:8000/api/trigger/git-push`

### 2. 提交并推送

```bash
# 进入项目目录
cd d:\360Downloads\蓝点\recycle-server-feature-1.2.2

# 查看文件
git status

# 添加CI配置
git add .gitlab-ci.yml

# 提交
git commit -m "添加GitLab CI自动测试触发"

# 推送
git push
```

### 3. 查看CI执行

推送后，在GitLab项目页面：
1. 点击左侧菜单 **构建** → **流水线**
2. 或者点击 **CI/CD** → **Pipelines**
3. 查看最新的Pipeline执行情况

### 4. 查看执行日志

点击Pipeline中的 `trigger-ai-test` 任务，可以看到：
```
=========================================
触发AI测试平台
=========================================
项目: recycle/recycle-server
分支: feature-1.2.2
提交: abc123...
✅ AI测试触发成功!
```

## 测试流程

### 完整测试步骤

1. **启动AI测试平台后端**
   ```bash
   cd G:\AI项目\ai测试\ai-test-platform
   python backend_api_server.py
   ```
   
   看到这个说明启动成功：
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

2. **修改代码并推送**
   ```bash
   cd d:\360Downloads\蓝点\recycle-server-feature-1.2.2
   
   # 修改任意文件
   echo "// test" >> src/main/java/com/example/Test.java
   
   # 提交推送
   git add .
   git commit -m "test: 测试CI触发"
   git push
   ```

3. **查看GitLab CI执行**
   - 打开GitLab项目
   - 点击 **构建** → **流水线**
   - 查看最新Pipeline

4. **查看AI测试结果**
   - 在CI日志中找到 `trigger_id`
   - 访问: `http://localhost:8000/api/trigger/status/{trigger_id}`
   - 或在AI测试平台查看结果

## 故障排查

### 问题1: CI任务失败

**检查步骤**:
1. 查看CI日志中的错误信息
2. 确认AI测试平台后端是否运行
3. 测试API是否可访问：
   ```bash
   curl http://localhost:8000/api/trigger/git-push
   ```

### 问题2: 无法连接到AI测试平台

**解决方案**:
1. 确认后端服务正在运行
2. 检查防火墙设置
3. 如果GitLab在其他机器，修改URL为实际IP地址

### 问题3: Pipeline不执行

**检查步骤**:
1. 确认 `.gitlab-ci.yml` 文件在项目根目录
2. 检查文件格式是否正确（YAML格式）
3. 查看GitLab项目设置中CI/CD是否启用

## 配置说明

### allow_failure: true

这个配置表示即使AI测试触发失败，也不会阻塞GitLab Pipeline。这样可以确保：
- 代码推送不会因为测试平台问题而失败
- 其他CI任务可以正常执行
- 测试触发是辅助功能，不影响主流程

### only: branches

只在分支推送时触发，不在tag推送时触发。

## 下一步优化

1. **添加测试结果等待**
   - 等待AI测试完成
   - 显示测试结果
   - 失败时发送通知

2. **配置不同分支策略**
   - 主分支：完整测试
   - 功能分支：增量测试

3. **添加测试报告**
   - 生成测试报告
   - 上传到GitLab
   - 在MR中显示

## 快速命令

```bash
# 1. 启动后端
cd G:\AI项目\ai测试\ai-test-platform && python backend_api_server.py

# 2. 推送代码（新窗口）
cd d:\360Downloads\蓝点\recycle-server-feature-1.2.2
git add .
git commit -m "test: CI触发测试"
git push

# 3. 查看IP（如果需要）
cd G:\AI项目\ai测试 && python get_my_ip.py
```

## 完成！

现在每次推送代码到GitLab，都会自动触发AI测试平台执行测试！
