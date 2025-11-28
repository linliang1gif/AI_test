from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from app.config import Config
from app.core.ai_client import AIClient
from app.core.chunker import split_text
from app.core.document_loader import read_docx
from app.core.exporter import export_cases
from app.core.ocr import get_ocr_service
from app.core.parser import normalize_output, parse_cases


ProgressCallback = Callable[[str], None]


@dataclass
class GenerationResult:
    source_file: Path
    output_file: Path
    sheet_name: str
    cases_count: int


def _notify(callback: Optional[ProgressCallback], message: str) -> None:
    if callback:
        callback(message)


def generate_for_files(
    files: Iterable[Path],
    config: Config,
    log_callback: Optional[ProgressCallback] = None,
) -> List[GenerationResult]:
    """Generate test cases for each file and export them."""
    ai_client = AIClient(config)
    ocr_service = get_ocr_service(config.enable_ocr, config.ocr_lang)
    results: List[GenerationResult] = []

    for file_path in files:
        _notify(log_callback, f"📄 开始处理：{file_path.name}")
        text = read_docx(file_path, ocr_service=ocr_service)
        if not text:
            _notify(log_callback, f"⚠️ 文件 {file_path.name} 无有效内容，跳过")
            continue

        chunks = split_text(text, config.chunk_size)
        chunk_outputs: List[str] = []
        for idx, chunk in enumerate(chunks, 1):
            _notify(
                log_callback,
                f"🧠 调用 AI 生成（{file_path.name} 分段 {idx}/{len(chunks)}）",
            )
            chunk_outputs.append(ai_client.generate(chunk))

        raw_output = "\n".join(chunk_outputs)
        normalized = normalize_output(raw_output)
        raw_log_file = config.output_dir / f"{file_path.stem}_AI原始输出.txt"
        raw_log_file.write_text(normalized, encoding="utf-8")
        cases = parse_cases(normalized)

        if not cases:
            _notify(log_callback, f"❌ 未解析出测试用例：{file_path.name}")
            continue

        module_display = config.module_name or file_path.stem
        # 优先使用子模块名称作为sheet名称，如果子模块为空则使用模块名称
        sheet_name = _sanitize_sheet_name(config.submodule_name or module_display)
        if config.single_workbook:
            output_file = config.output_dir / "汇总测试用例.xlsx"
            export_cases(
                _map_cases_to_template(
                    cases, config.project_name, module_display, config.submodule_name
                ),
                output_file,
                sheet_name=sheet_name,
            )
        else:
            output_file = config.output_dir / f"{file_path.stem}_测试用例.xlsx"
            export_cases(
                _map_cases_to_template(
                    cases, config.project_name, module_display, config.submodule_name
                ),
                output_file,
                sheet_name="Sheet1",
            )
        _notify(
            log_callback,
            f"✅ {file_path.name} 完成，共 {len(cases)} 条，写入工作表：{sheet_name}",
        )
        results.append(
            GenerationResult(
                source_file=file_path,
                output_file=output_file,
                sheet_name=sheet_name,
                cases_count=len(cases),
            )
        )

    return results


def _extract_function_point(title: str) -> str:
    """Extract function point from test case title."""
    if not title:
        return ""
    title = title.strip().lstrip(":")
    
    # 移除"验证"开头
    if title.startswith("验证"):
        title = title[2:].strip()
    
    # 提取核心功能描述
    # 如果包含"时"、"后"等时间词，提取前面的部分
    for sep in ["时", "后", "，", ","]:
        if sep in title:
            parts = title.split(sep, 1)
            if len(parts) > 1:
                title = parts[0].strip()
                break
    
    # 移除常见的修饰词
    title = title.replace("通过", "").replace("生成", "").replace("创建", "").strip()
    
    # 如果还是太长，取前30个字符
    if len(title) > 30:
        title = title[:30]
    
    # 如果提取后为空，返回一个默认值
    if not title:
        return "功能验证"
    
    return title


def _map_cases_to_template(
    cases: List[dict],
    project_name: str,
    module_name: str,
    submodule_name: str,
) -> List[dict]:
    mapped: List[dict] = []
    for idx, case in enumerate(cases, 1):
        title = case.get("用例标题", "").strip().lstrip(":")
        function_point = case.get("功能点", "").strip()
        if not function_point:
            function_point = _extract_function_point(title)
        mapped.append(
            {
                "序号": idx,
                "项目名称": project_name or module_name,
                "模块名称": module_name,
                "子模块名称": submodule_name,
                "功能点": function_point,
                "用例标题": title,
                "前置条件": case.get("前置条件", "").strip().lstrip(":"),
                "输入数据": case.get("输入数据", ""),
                "操作步骤": case.get("测试步骤", "").strip(),
                "预期结果": case.get("预期结果", "").strip(),
            }
        )
    return mapped


def _sanitize_sheet_name(raw: str) -> str:
    invalid_chars = set(r"[]:*?/\\")
    cleaned = "".join(ch for ch in raw if ch not in invalid_chars)
    cleaned = cleaned.strip()
    if not cleaned:
        cleaned = "Sheet1"
    if len(cleaned) > 31:
        cleaned = cleaned[:31]
    return cleaned


