# 快速修复指南

## 立即执行（解决连接错误）

### 步骤1：重启后端
```bash
# 在后端窗口按 Ctrl+C 停止
# 然后重新运行
cd "G:\AI项目\ai测试\ai-test-platform"
py backend_api_server.py
```

### 步骤2：等待10秒后测试
```bash
cd "G:\AI项目\ai测试"
py check_all_features.py
```

### 步骤3：如果还有问题，硬刷新浏览器
```
按 Ctrl+Shift+R
```

## 如果重启后还有问题

运行修复脚本：
```bash
cd "G:\AI项目\ai测试"
py fix_critical_issues.py
```

这会自动修复：
1. 自动化脚本404错误
2. 测试用例连接问题
3. API执行问题
4. 创建缺失的前端页面
