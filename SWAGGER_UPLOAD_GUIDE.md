# Swagger文件上传指南

## 问题诊断

如果看到错误 "Spec must be a JSON object (dictionary)"，说明上传的文件格式不正确。

## 文件要求

### 1. 文件格式
- 必须是 **JSON** 或 **YAML** 格式
- 文件编码必须是 **UTF-8**

### 2. 文件结构
文件内容必须是**对象**（以 `{` 开头），不能是数组（以 `[` 开头）

✅ 正确示例:
```json
{
  "swagger": "2.0",
  "info": {...},
  "paths": {...}
}
```

❌ 错误示例:
```json
[
  {"path": "/api/users"},
  {"path": "/api/products"}
]
```

### 3. 必需字段

#### Swagger 2.0
```json
{
  "swagger": "2.0",           // 必需：版本号
  "info": {                   // 必需：API信息
    "title": "My API",
    "version": "1.0.0"
  },
  "paths": {                  // 必需：API路径
    "/users": {
      "get": {...}
    }
  }
}
```

#### OpenAPI 3.0
```json
{
  "openapi": "3.0.0",         // 必需：版本号
  "info": {                   // 必需：API信息
    "title": "My API",
    "version": "1.0.0"
  },
  "paths": {                  // 必需：API路径
    "/users": {
      "get": {...}
    }
  }
}
```

## 验证工具

### 上传前验证
在上传前，使用验证工具检查文件：

```bash
py validate_swagger_file.py your_swagger.json
```

工具会检查：
- ✅ 文件是否存在
- ✅ 文件大小（不能为空）
- ✅ 文件编码（UTF-8）
- ✅ 文件格式（JSON/YAML）
- ✅ 内容类型（必须是对象）
- ✅ 版本字段（swagger/openapi）
- ✅ 必需字段（info, paths）
- ✅ API数量统计

### 示例输出

#### 成功示例
```
============================================================
验证文件: swagger.json
============================================================
✅ 文件大小: 1234 字节
✅ 文件编码: UTF-8
✅ 文件格式: JSON
✅ 文件内容: 对象(字典)

可用的顶级字段: ['swagger', 'info', 'paths', 'basePath']
✅ Swagger版本: 2.0
✅ API标题: 测试API
✅ API版本: 1.0.0
✅ API路径数量: 5
✅ API方法数量: 10

前3个API路径:
  1. /users - GET, POST
  2. /products - GET, POST, PUT
  3. /orders - GET

============================================================
✅ 文件验证通过！可以上传
============================================================
```

#### 失败示例
```
============================================================
验证文件: invalid.json
============================================================
✅ 文件大小: 234 字节
✅ 文件编码: UTF-8
⚠️ 不是有效的JSON: Expecting property name enclosed in double quotes
❌ 也不是有效的YAML: ...

============================================================
❌ 该文件存在问题，请修复后再上传
============================================================
```

## 常见错误及解决方案

### 错误1: "Spec must be a JSON object (dictionary)"
**原因**: 文件内容是数组而不是对象

**解决方案**:
```json
// 错误 ❌
[
  {"path": "/api/users"}
]

// 正确 ✅
{
  "swagger": "2.0",
  "paths": {
    "/api/users": {...}
  }
}
```

### 错误2: "Unknown spec version"
**原因**: 缺少 `swagger` 或 `openapi` 字段

**解决方案**:
```json
// 错误 ❌
{
  "info": {...},
  "paths": {...}
}

// 正确 ✅
{
  "swagger": "2.0",  // 或 "openapi": "3.0.0"
  "info": {...},
  "paths": {...}
}
```

### 错误3: "Spec file is empty"
**原因**: 文件为空或只包含空白字符

**解决方案**: 确保文件包含有效内容

### 错误4: "Invalid spec file format"
**原因**: 文件不是有效的JSON或YAML

**解决方案**:
- 检查JSON语法（括号、引号、逗号）
- 使用JSON验证工具（如 jsonlint.com）
- 确保文件编码是UTF-8

## 测试文件

系统已创建一个测试文件供参考：`test_swagger_valid.json`

可以先上传这个文件测试功能是否正常。

## 获取帮助

如果问题仍然存在：

1. 运行验证工具查看详细错误
2. 检查文件是否符合Swagger/OpenAPI规范
3. 使用在线工具验证（如 editor.swagger.io）
4. 查看后端日志获取更多信息
