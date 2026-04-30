# 删除功能修复说明

## 问题描述

在前端删除测试用例时,出现"删除资源使用中"的错误。

## 问题原因

后端API的`BatchDeleteRequest`模型定义的`ids`字段类型为`List[int]`,但实际数据中存在字符串类型的ID(如`TC_1776479357_14`),导致类型验证失败,返回422错误。

## 修复方案

### 1. 修改后端API

**文件**: `ai-test-platform/backend_api_server.py`

**修改内容**:

```python
# 修改前
class BatchDeleteRequest(BaseModel):
    ids: List[int]

# 修改后
class BatchDeleteRequest(BaseModel):
    ids: List[Union[int, str]]  # 支持整数和字符串ID
```

同时添加`Union`导入:
```python
from typing import Dict, Any, List, Optional, Union
```

### 2. 重启后端服务 (必须)

修改代码后需要重启后端服务才能生效:

```bash
# 停止当前服务 (Ctrl+C)

# 重新启动
cd ai-test-platform
py backend_api_server.py
```

## 验证修复

### 方法1: 使用测试脚本

```bash
cd ai测试
py test_delete_testcase.py
```

预期输出:
```
✅ 删除成功
删除数量: 1
删除前: 71 个
删除后: 70 个
✅ 删除验证成功
```

### 方法2: 前端测试

1. 访问: http://localhost:5173/test-cases
2. 勾选一个测试用例
3. 点击删除按钮
4. 确认删除

预期结果: 删除成功,页面刷新,测试用例消失

## 技术细节

### 数据类型不一致

测试用例ID存在两种类型:
- **整数ID**: 如 `2`, `3`, `4` (早期数据)
- **字符串ID**: 如 `TC_1776479357_14` (新生成的数据)

### API验证

FastAPI的Pydantic模型会进行严格的类型验证:
- `List[int]`: 只接受整数列表
- `List[Union[int, str]]`: 接受整数或字符串列表

### 错误码

- **422 Unprocessable Entity**: 请求体格式正确,但数据验证失败
- **404 Not Found**: API端点不存在
- **200 OK**: 请求成功

## 相关文件

- `ai-test-platform/backend_api_server.py` - 后端API服务器
- `test_delete_testcase.py` - 删除功能测试脚本
- `ai-test-platform/frontend/src/services/api.js` - 前端API服务层

## 后续优化建议

### 1. 统一ID类型

建议统一使用字符串类型的ID:
- 更灵活
- 支持更多格式
- 避免类型转换问题

### 2. 数据迁移

将所有整数ID迁移为字符串ID:
```python
for case in test_cases:
    if isinstance(case['id'], int):
        case['id'] = f"TC_{case['id']}"
```

### 3. 前端类型检查

在前端也添加类型检查,确保传递正确的ID类型。

## 常见问题

### Q1: 修复后还是删除失败?

**A**: 确保已重启后端服务。修改代码后必须重启才能生效。

### Q2: 删除成功但前端没有刷新?

**A**: 检查前端是否正确处理删除成功的回调,并刷新列表。

### Q3: 部分用例可以删除,部分不行?

**A**: 可能是ID类型不一致。使用测试脚本检查具体的ID类型。

---

**修复时间**: 2026-04-18 14:00  
**状态**: ✅ 已修复  
**需要操作**: ⚠️ 重启后端服务
