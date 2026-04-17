# 后端重启指南

## 问题
修改了后端代码后，需要重启后端服务才能生效。

## 修复内容
1. 改进了 `modules/swagger/api_spec_loader.py` 的错误处理
   - 更详细的版本检测错误信息
   - 更好的文件格式验证
   - 空文件检测
   - 非字典内容检测

2. 改进了 `ai-test-platform/backend_api_server.py` 的错误处理
   - 区分 ValueError 和其他异常
   - 返回更友好的错误信息给前端
   - 正确的HTTP状态码（400 vs 500）

## 重启步骤

### 方法1: 手动重启
1. 找到运行后端的终端窗口
2. 按 `Ctrl+C` 停止后端服务
3. 重新运行: `cd ai-test-platform && py backend_api_server.py`

### 方法2: 使用进程管理器
如果使用 PM2 或其他进程管理器:
```bash
pm2 restart backend
```

## 验证修复
重启后运行测试:
```bash
py test_swagger_upload_endpoint.py
```

预期结果:
- ✅ 上传有效Swagger 2.0 - PASS
- ✅ 上传无效Swagger - PASS (应该返回400状态码和详细错误信息)
- ✅ 上传OpenAPI 3.0 - PASS
- ✅ 上传空文件 - PASS

## 测试前端
1. 打开浏览器访问 http://localhost:5173
2. 进入 Swagger 上传页面
3. 尝试上传不同类型的文件:
   - 有效的 Swagger 2.0 文件 → 应该成功
   - 有效的 OpenAPI 3.0 文件 → 应该成功
   - 无效的文件（缺少版本键）→ 应该显示友好的错误信息
   - 空文件 → 应该显示"文件内容为空"
