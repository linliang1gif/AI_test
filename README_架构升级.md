# AI测试用例生成工具 - 架构升级完成

## 🎯 升级目标达成

✅ **增加"AI测试点生成模块"** - 让系统先生成测试点，再根据测试点生成测试用例

✅ **新的两阶段流程** - 需求文档 → 解析需求文本 → AI生成测试点 → AI根据测试点生成测试用例 → 导出Excel

## 📁 新增模块结构

```
ai测试/
├── app/
│   ├── test_design/              # 新增：测试设计模块
│   │   ├── __init__.py
│   │   ├── testpoint_generator.py    # 测试点生成器
│   │   └── testcase_generator.py     # 测试用例生成器
│   └── core/
│       └── new_workflow.py           # 新工作流程
├── demo_complete_workflow.py         # 完整演示脚本
├── test_new_workflow.py             # 测试脚本
└── 使用说明_新流程.md                # 详细使用说明
```

## 🔧 核心实现

### 1. TestPointGenerator (测试点生成器)
- **文件**: `app/test_design/testpoint_generator.py`
- **功能**: 根据需求文本生成结构化测试点列表
- **输入**: 需求文档文本
- **输出**: 测试点列表 `["验证订单创建功能", "验证订单金额边界条件", ...]`
- **覆盖维度**: 功能测试、边界测试、异常测试、权限测试、数据校验

### 2. TestCaseGenerator (测试用例生成器)  
- **文件**: `app/test_design/testcase_generator.py`
- **功能**: 根据测试点生成详细测试用例
- **输入**: 测试点列表
- **输出**: 结构化测试用例，包含 test_point, title, precondition, steps, expected, priority

### 3. 新工作流程
- **文件**: `app/core/new_workflow.py`
- **功能**: 整合两阶段生成流程
- **特性**: 支持分块处理、自动去重、质量分析、完整错误处理

## 📊 Excel结构升级

### 新增字段
- **测试点**: 显示对应的测试点描述

### 完整列结构
1. 序号
2. 项目名称  
3. 模块名称
4. 子模块名称
5. **测试点** (新增)
6. 用例标题
7. 前置条件
8. 操作步骤
9. 预期结果
10. 优先级

## 🚀 使用方法

### 方法1: 完整演示
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 逐步演示每个阶段
python demo_complete_workflow.py

# 简化版演示
python demo_complete_workflow.py simple
```

### 方法2: 测试脚本
```bash
python test_new_workflow.py 需求文档.docx
```

### 方法3: 原main.py演示
```bash
python main.py 需求文档.docx
```

### 方法4: 程序化调用
```python
from app.config import load_config
from app.core.new_workflow import generate_with_new_workflow
from pathlib import Path

config = load_config()
results = generate_with_new_workflow(
    files=[Path("需求文档.docx")],
    config=config,
    log_callback=lambda msg: print(msg)
)
```

## 📈 升级优势

### 1. 更好的可控性
- ✅ 可以先审查测试点，再生成用例
- ✅ 便于调整测试覆盖范围
- ✅ 测试设计更加系统化

### 2. 更高的质量
- ✅ 两阶段生成更加全面
- ✅ 测试点设计覆盖5个维度
- ✅ 每个用例都有明确的测试意图

### 3. 更好的可追溯性
- ✅ 每个测试用例对应明确的测试点
- ✅ 便于理解测试目的和范围
- ✅ 生成中间文件便于审查

### 4. 完全向后兼容
- ✅ 保持原有接口不变
- ✅ 支持新旧格式混用
- ✅ 不破坏现有GUI逻辑

## 🔄 工作流程对比

### 原流程
```
需求文档 → AI直接生成测试用例 → 导出Excel
```

### 新流程
```
需求文档 → 解析需求文本 → AI生成测试点 → AI根据测试点生成测试用例 → 导出Excel
```

## 📋 输出文件

### 1. 测试点文件
- **格式**: `{文档名}_测试点.txt`
- **内容**: 编号的测试点列表
- **用途**: 中间结果，便于审查

### 2. Excel测试用例
- **格式**: `{文档名}_测试用例_新流程.xlsx`
- **内容**: 完整测试用例，包含新增的"测试点"列
- **工作表**: 测试用例 + 覆盖率统计

## ⚙️ 配置要求

确保 `.env` 文件包含必要配置：
```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
MODEL_TEMPERATURE=0.2
CHUNK_SIZE=3000
```

## 📝 注意事项

1. **API调用**: 新流程会增加API调用次数（测试点 + 测试用例）
2. **处理时间**: 相比原流程会增加处理时间
3. **文件输出**: 会生成额外的测试点中间文件
4. **兼容性**: 完全兼容现有配置和输出格式

## 🎉 升级完成

所有要求的功能都已实现：

✅ 新增测试点生成模块  
✅ 新增测试用例生成模块  
✅ 修改main.py支持新流程  
✅ Excel结构升级（新增测试点字段）  
✅ 代码模块化且可维护  
✅ 不破坏现有GUI和导出逻辑  
✅ 提供完整的使用示例和文档

代码可以直接运行，支持Python 3.11，完全满足架构升级需求！