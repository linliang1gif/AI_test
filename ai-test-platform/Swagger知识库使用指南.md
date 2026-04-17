# Swagger知识库使用指南

## 📚 概述

通过将Swagger文档导入到知识库,AI测试平台现在可以:
- 🧠 理解你的系统API结构
- 🔍 通过自然语言检索相关API
- 🎯 生成更准确的测试用例
- 📊 自动生成符合实际的测试数据

---

## 🚀 快速开始

### 1. 导入Swagger文件

```bash
cd ai测试/ai-test-platform
py import_swagger_to_knowledge.py
```

**导入结果**:
- ✅ 成功导入814个API
- ✅ 支持语义检索
- ✅ 自动分类和标签

### 2. 查看演示

```bash
py demo_swagger_knowledge_usage.py
```

**演示内容**:
- API语义检索
- 测试用例生成
- 测试数据生成
- API依赖分析

---

## 💡 使用场景

### 场景1: 查找相关API

**需求**: 我想测试用户登录功能

**操作**:
```python
from knowledge.knowledge_manager import KnowledgeManager

km = KnowledgeManager()
collection = km.kb.get_collection("apis")

results = collection.query(
    query_texts=["用户登录 认证 token"],
    n_results=5
)

# 查看结果
for metadata in results['metadatas'][0]:
    print(f"{metadata['method']} {metadata['path']}")
    print(f"摘要: {metadata['summary']}")
```

**结果**:
```
POST /recycle/wechat/getEidToken
摘要: 获取EidToken
相似度: 46.63%
```

---

### 场景2: 生成测试用例

**需求**: 测试币别管理功能

**AI自动流程**:
1. 🔍 检索"币别"相关API
2. 📋 识别CRUD操作
3. 🎯 生成测试用例

**生成的测试用例**:
- TC_CURRENCY_001: 新增币别-正常流程
- TC_CURRENCY_002: 查询币别列表
- TC_CURRENCY_003: 编辑币别信息
- TC_CURRENCY_004: 删除币别
- TC_CURRENCY_005: 启用/禁用币别

---

### 场景3: 生成测试数据

**需求**: 为"新增币别"API生成测试数据

**AI自动流程**:
1. 📖 读取API参数定义
2. 🎲 生成正常数据
3. 🔬 生成边界数据
4. ⚠️ 生成异常数据

**生成的数据**:

**正常数据**:
```json
{
  "currencyName": "美元",
  "currencySymbol": "USD",
  "currencyNameEn": "US Dollar",
  "baseCurrency": 0,
  "unitPriceDecimalPlace": 2,
  "totalPriceDecimalPlace": 2
}
```

**边界数据**:
```json
{
  "currencyName": "AAAA...AAA",  // 最大长度
  "currencySymbol": "XXX",
  "unitPriceDecimalPlace": 8,    // 最大小数位
  "totalPriceDecimalPlace": 8
}
```

**异常数据**:
```json
{
  "currencyName": "",            // 空值
  "currencySymbol": "",          // 空值
  "unitPriceDecimalPlace": -1,   // 负数
  "totalPriceDecimalPlace": 100  // 超大值
}
```

---

### 场景4: 分析业务流程

**需求**: 理解采购订单完整流程

**AI分析结果**:

```
步骤1: 创建采购订单
  - POST /purchase/order/add
  - POST /purchase/order/save

步骤2: 审核采购订单 (依赖: 创建采购订单)
  - POST /purchase/order/audit
  - POST /purchase/order/approve

步骤3: 采购入库 (依赖: 审核采购订单)
  - POST /purchase/stockin/add
  - POST /purchase/stockin/save

步骤4: 质检 (依赖: 采购入库)
  - POST /quality/inspection/add
  - POST /quality/inspection/check

步骤5: 财务应付 (依赖: 质检)
  - POST /finance/payment/add
  - POST /finance/payment/pay
```

**测试建议**:
1. 按流程顺序执行测试
2. 每个步骤完成后验证数据状态
3. 测试异常场景(跳过某个步骤)
4. 测试并发场景(多个订单同时处理)

---

## 🎯 在AI测试控制台中使用

### 1. 启动平台

```bash
cd ai测试/ai-test-platform
py start_platform.py
```

### 2. 打开AI测试控制台

访问: http://localhost:5174/ai-console

### 3. 输入测试需求

**示例需求**:
```
测试币别管理功能,包括:
1. 新增币别
2. 查询币别列表
3. 编辑币别信息
4. 删除币别
5. 启用/禁用币别
```

### 4. AI自动工作

AI会自动:
1. 🔍 从知识库检索相关API
2. 📋 生成测试用例
3. 🎲 生成测试数据
4. ✅ 生成断言规则
5. 🚀 执行测试
6. 📊 生成报告

---

## 📊 知识库统计

### 当前状态
- **API总数**: 814个
- **系统名称**: 蓝点新生租户端
- **版本**: last
- **格式**: Swagger 2.0

### 标签分类
- 币别: 8个API
- 汇率: 9个API
- 仓库分类: 5个API
- 仓库: 7个API
- 客户信息: 21个API
- 采购订单: 多个API
- 财务应收: 多个API
- 库存管理: 多个API
- ...等等

### HTTP方法分布
- POST: 812个
- GET: 2个

---

## 🔄 更新知识库

### 当API有变更时

```bash
# 1. 获取最新的Swagger文件
# 2. 替换 swaggerApi (1).json
# 3. 重新导入
py import_swagger_to_knowledge.py
```

### 导入多个系统

```python
# 修改脚本支持多个文件
import_swagger_to_knowledge("system1_swagger.json")
import_swagger_to_knowledge("system2_swagger.json")
import_swagger_to_knowledge("system3_swagger.json")
```

---

## 🧪 测试验证

### 验证导入结果

```bash
py demo_swagger_knowledge_usage.py
```

### 手动测试查询

```python
from knowledge.knowledge_manager import KnowledgeManager

km = KnowledgeManager()
collection = km.kb.get_collection("apis")

# 测试查询
queries = [
    "用户登录",
    "采购订单",
    "库存查询",
    "财务应收"
]

for query in queries:
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    print(f"\n查询: {query}")
    for metadata in results['metadatas'][0]:
        print(f"  {metadata['method']} {metadata['path']}")
```

---

## 💡 最佳实践

### 1. 定期更新
- 每次API变更后重新导入
- 保持知识库与实际系统同步

### 2. 添加自定义标签
```python
metadata = {
    "system": "蓝点新生",
    "environment": "production",
    "version": "1.2.1",
    "team": "测试团队"
}
```

### 3. 结合代码库
- Swagger提供API接口信息
- 代码库提供实现细节
- 两者结合,AI理解更全面

### 4. 持续优化
- 收集AI生成的测试用例质量反馈
- 优化API描述和标签
- 补充业务规则说明

---

## 🎉 效果对比

### 导入前
- ❌ AI不了解系统API
- ❌ 测试用例需要手动配置
- ❌ 测试数据随机生成
- ❌ 无法理解业务流程

### 导入后
- ✅ AI理解814个API
- ✅ 自动生成准确的测试用例
- ✅ 测试数据符合实际参数
- ✅ 理解业务流程和依赖

---

## 📞 常见问题

### Q1: 导入失败怎么办?
**A**: 检查:
1. Swagger文件格式是否正确
2. ChromaDB是否已安装
3. 文件路径是否正确

### Q2: 查询结果不准确?
**A**: 优化:
1. 使用更具体的查询词
2. 补充API描述信息
3. 添加更多标签

### Q3: 如何导入多个系统?
**A**: 修改脚本:
```python
systems = [
    "system1_swagger.json",
    "system2_swagger.json"
]

for swagger_file in systems:
    import_swagger_to_knowledge(swagger_file)
```

### Q4: 知识库占用空间大吗?
**A**: 
- 814个API约占用10-20MB
- ChromaDB使用向量压缩
- 可以定期清理旧数据

---

## ✨ 总结

通过Swagger知识库集成:

1. ✅ **AI更智能** - 理解你的系统结构
2. ✅ **效率更高** - 自动生成测试用例和数据
3. ✅ **质量更好** - 测试更准确,覆盖更全面
4. ✅ **维护更简单** - 一次导入,持续使用

**下一步**: 在AI测试控制台中体验智能测试生成!

---

## 📁 相关文件

- `swaggerApi (1).json` - Swagger文档
- `import_swagger_to_knowledge.py` - 导入脚本
- `demo_swagger_knowledge_usage.py` - 演示脚本
- `Swagger知识库集成完成报告.md` - 完成报告
- `parser/swagger_parser.py` - 解析器
- `knowledge/knowledge_manager.py` - 知识库管理器

---

**最后更新**: 2026-03-24  
**版本**: 1.0  
**状态**: ✅ 已完成并可用
