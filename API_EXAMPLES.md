# API接口示例

## 1. 执行API

### 请求
```http
POST /api/execute-api
Content-Type: application/json

{
  "method": "GET",
  "url": "https://jsonplaceholder.typicode.com/posts/1",
  "base_url": "https://jsonplaceholder.typicode.com",
  "path": "/posts/1",
  "data": {},
  "timeout": 30
}
```

### 响应
```json
{
  "success": true,
  "status_code": 200,
  "response_time": 245,
  "response_data": {
    "userId": 1,
    "id": 1,
    "title": "sunt aut facere repellat provident",
    "body": "quia et suscipit..."
  },
  "headers": {
    "content-type": "application/json; charset=utf-8"
  }
}
```

---

## 2. 保存为测试用例

### 请求
```http
POST /api/save-api-as-testcase
Content-Type: application/json

{
  "api_info": {
    "name": "获取文章详情",
    "method": "GET",
    "path": "/posts/1",
    "tags": ["文章管理"]
  },
  "execution_result": {
    "success": true,
    "status_code": 200,
    "response_time": 245,
    "response_data": {...}
  },
  "request_data": {}
}
```

### 响应
```json
{
  "success": true,
  "message": "测试用例保存成功",
  "test_case_id": "TC_1713334567_0"
}
```

---

## 3. 获取测试用例

### 请求
```http
GET /api/test-cases
```

### 响应
```json
{
  "success": true,
  "data": [
    {
      "id": "TC_1713334567_0",
      "title": "获取文章详情 - GET /posts/1",
      "module": "文章管理",
      "priority": "medium",
      "status": "passed",
      "lastRun": "2024-04-17 14:22:47",
      "steps": [
        "发送 GET 请求到 /posts/1",
        "请求参数: {}"
      ],
      "expected": "返回状态码 200"
    }
  ],
  "count": 1
}
```

---

## 4. 创建测试用例

### 请求
```http
POST /api/test-cases
Content-Type: application/json

{
  "title": "用户登录测试",
  "module": "用户管理",
  "priority": "high",
  "steps": [
    "输入用户名和密码",
    "点击登录按钮",
    "验证登录成功"
  ],
  "expected": "成功跳转到首页"
}
```

### 响应
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "用户登录测试",
    "module": "用户管理",
    "priority": "high",
    "created_at": "2024-03-21"
  },
  "message": "测试用例创建成功"
}
```

---

## 5. 生成自动化脚本

### 请求
```http
POST /api/automation/scripts/generate
Content-Type: application/json

{
  "test_case_id": "TC_1713334567_0"
}
```

### 响应
```json
{
  "success": true,
  "script_id": 1,
  "script": {
    "id": 1,
    "name": "获取文章详情 - GET /posts/1",
    "type": "python",
    "status": "active",
    "test_case_id": "TC_1713334567_0",
    "content": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n...",
    "created_at": "2024-04-17 14:25:30",
    "language": "python"
  },
  "message": "脚本生成成功"
}
```

---

## 6. 获取脚本列表

### 请求
```http
GET /api/automation/scripts
```

### 响应
```json
{
  "success": true,
  "scripts": [
    {
      "id": 1,
      "name": "获取文章详情 - GET /posts/1",
      "type": "python",
      "status": "active",
      "test_case_id": "TC_1713334567_0",
      "created_at": "2024-04-17 14:25:30"
    }
  ],
  "data": [...],
  "count": 1
}
```

---

## 7. 下载脚本

### 请求
```http
GET /api/automation/scripts/1/download
```

### 响应
```
Content-Type: text/plain
Content-Disposition: attachment; filename=test_script_1.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成的测试脚本
测试用例: 获取文章详情 - GET /posts/1
生成时间: 2024-04-17 14:25:30
"""

import requests
import json

def test_TC_1713334567_0():
    """
    获取文章详情 - GET /posts/1
    """
    print("=" * 60)
    print("测试用例: 获取文章详情 - GET /posts/1")
    print("=" * 60)
    
    # 执行API请求
    method = "GET"
    url = "/posts/1"
    data = {}
    
    print(f"\n发送 {method} 请求到 {url}")
    
    try:
        response = requests.get(url, params=data, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {response.elapsed.total_seconds() * 1000:.0f}ms")
        
        if response.status_code < 400:
            print("✅ 测试通过")
            return True
        else:
            print("❌ 测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False

if __name__ == "__main__":
    result = test_TC_1713334567_0()
    exit(0 if result else 1)
```

---

## 8. 执行脚本

### 请求
```http
POST /api/automation/scripts/1/execute
```

### 响应
```json
{
  "success": true,
  "status": "passed",
  "execution_time": 1234,
  "stdout": "============================================================\n测试用例: 获取文章详情 - GET /posts/1\n============================================================\n\n发送 GET 请求到 /posts/1\n状态码: 200\n响应时间: 245ms\n✅ 测试通过\n",
  "stderr": "",
  "return_code": 0,
  "message": "脚本执行完成"
}
```

---

## 9. 获取测试运行

### 请求
```http
GET /api/test-runs
```

### 响应
```json
{
  "success": true,
  "test_runs": [
    {
      "id": 1,
      "script_id": 1,
      "script_name": "获取文章详情 - GET /posts/1",
      "status": "passed",
      "duration": "1234ms",
      "executed_at": "2024-04-17 14:30:15",
      "stdout": "...",
      "stderr": "",
      "return_code": 0
    }
  ],
  "count": 1
}
```

---

## 错误响应示例

### 404 - 资源不存在
```json
{
  "success": false,
  "error": "测试用例不存在: TC_123456"
}
```

### 500 - 服务器错误
```json
{
  "success": false,
  "error": "Internal server error",
  "message": "脚本执行失败"
}
```

### 连接失败
```json
{
  "success": false,
  "error": "连接失败，请检查URL是否正确",
  "status_code": 0,
  "response_time": 0
}
```

---

## 完整流程示例

```bash
# 1. 执行API测试
curl -X POST http://localhost:8000/api/execute-api \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "url": "https://jsonplaceholder.typicode.com/posts/1",
    "base_url": "https://jsonplaceholder.typicode.com",
    "path": "/posts/1"
  }'

# 2. 保存为测试用例
curl -X POST http://localhost:8000/api/save-api-as-testcase \
  -H "Content-Type: application/json" \
  -d '{
    "api_info": {
      "name": "获取文章",
      "method": "GET",
      "path": "/posts/1",
      "tags": ["文章"]
    },
    "execution_result": {...},
    "request_data": {}
  }'

# 3. 生成脚本
curl -X POST http://localhost:8000/api/automation/scripts/generate \
  -H "Content-Type: application/json" \
  -d '{"test_case_id": "TC_1713334567_0"}'

# 4. 下载脚本
curl http://localhost:8000/api/automation/scripts/1/download \
  -o test_script.py

# 5. 执行脚本
curl -X POST http://localhost:8000/api/automation/scripts/1/execute

# 6. 查看测试运行
curl http://localhost:8000/api/test-runs
```
