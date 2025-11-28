# AI 测试用例生成器

一个基于 PySide6 的桌面应用，读取需求文档（Word），调用 DeepSeek/OpenAI 兼容模型自动生成测试用例，并导出 Excel。

## 功能概述

- 图形界面，支持批量添加 `.docx` 需求文档。
- 可视化配置 API Key、Base URL、模型、分段长度、输出目录。
- 可选开启 OCR，将 Word 中的截图/图片识别为文字后再交给 AI。
- 支持在 GUI 中设置“项目名称 / 模块名称 / 子模块名称”，并将所有用例写入同一个 Excel（按模块名分 Sheet）或单独生成。
- 实时日志、进度提示，生成完成后自动打开输出路径。
- 自动保存 AI 原始输出（TXT）与结构化测试用例（Excel，缺失字段高亮）。

## 快速开始

1. 安装依赖（如需启用 OCR，会同步安装 `paddleocr`/`paddlepaddle`，首次较慢）：
   ```bash
   pip install -r requirements.txt
   ```
2. 复制 `env.sample` 为 `.env` 或在 GUI 中直接填写 API Key：
   ```
   cp env.sample .env
   ```
   并设置 `DEEPSEEK_API_KEY` 等参数。
3. （可选）在 `.env` 中启用 OCR 或调整导出策略/项目/模块/子模块名称：
   ```
   SINGLE_WORKBOOK=true
   PROJECT_NAME=蓝点新生
   MODULE_NAME=采购管理
   SUBMODULE_NAME=废品回收
   ENABLE_OCR=true
   OCR_LANG=ch
   ```

4. 运行桌面应用：
   ```bash
   python main.py
   ```

## 目录结构

```
app/
  config.py        # 配置加载
  core/            # 文档解析、AI 调用、结果导出
  gui/             # PySide6 界面与工作线程
main.py            # 程序入口
requirements.txt
env.sample
```

## 注意事项

- 本地需安装 Microsoft Word 兼容字体以确保 docx 解析正常。
- AI 调用依赖网络，若失败可重试或降低并发。
- 生成 Excel 时如文件被占用会写入失败，需关闭后重试。
- OCR 功能需额外占用内存/下载模型，如不需要可在界面或 `.env` 中关闭。
- 默认导出的 Excel 列顺序为：序号、项目名称、模块名称、子模块名称、功能点、用例标题、前置条件、输入数据、操作步骤、预期结果。


