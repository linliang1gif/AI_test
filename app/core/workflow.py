from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Union

from app.config import Config
from app.core.ai_client import AIClient
from app.core.chunker import split_text
from app.core.dedup import analyze_coverage, deduplicate_cases, validate_cases
from app.core.document_loader import read_document, read_url
from app.core.exporter import export_cases
from app.core.history import record_generation
from app.core.ocr import get_ocr_service
from app.core.parser import parse_cases

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str], None]


@dataclass
class GenerationResult:
    source_file: Path
    output_file: Path
    sheet_name: str
    cases_count: int
    raw_count: int
    dedup_removed: int
    quality_score: int = 0
    coverage: Dict = field(default_factory=dict)
    error: str = ""
    token_summary: str = ""


# ── URL source wrapper ───────────────────────────────────────────────────────

@dataclass
class UrlSource:
    """Represents a URL-based requirement source."""
    url: str
    title: str = ""
    username: Optional[str] = None
    password: Optional[str] = None

    @property
    def name(self) -> str:
        return self.title or self.url.split("/")[-1] or "web_page"

    @property
    def stem(self) -> str:
        import re
        clean = re.sub(r'[^\w\u4e00-\u9fff-]', '_', self.name)
        return clean[:60] or "web_page"


# Type alias for sources
Source = Union[Path, UrlSource]


def _notify(cb: Optional[ProgressCallback], msg: str) -> None:
    if cb:
        cb(msg)
    logger.info(msg)


def generate_for_files(
    files: Iterable[Path],
    config: Config,
    log_callback: Optional[ProgressCallback] = None,
) -> List[GenerationResult]:
    """Generate test cases with per-file error isolation, token tracking, and history."""
    ai_client = AIClient(config)
    ocr_service = get_ocr_service(config.enable_ocr, config.ocr_lang)
    results: List[GenerationResult] = []
    file_list = list(files)
    total_files = len(file_list)

    for file_idx, file_path in enumerate(file_list, 1):
        _notify(log_callback, f"\u00f0\u009f\u0093\u0084 [{file_idx}/{total_files}] 开始处理：{file_path.name}")
        try:
            result = _process_single_file(file_path, config, ai_client, ocr_service, log_callback)
            results.append(result)
            try:
                record_generation(
                    source_file=str(file_path), output_file=str(result.output_file),
                    project_name=config.project_name, module_name=config.module_name,
                    model_used=config.model, cases_count=result.cases_count,
                    raw_count=result.raw_count, dedup_removed=result.dedup_removed,
                    quality_score=result.quality_score, coverage=result.coverage)
            except Exception:
                pass
        except Exception as exc:
            _notify(log_callback, f"❌ {file_path.name} 处理失败：{exc}")
            try:
                record_generation(
                    source_file=str(file_path), output_file="",
                    project_name=config.project_name, module_name=config.module_name,
                    model_used=config.model, cases_count=0, raw_count=0,
                    dedup_removed=0, quality_score=0, status="failed")
            except Exception:
                pass
            results.append(GenerationResult(
                source_file=file_path, output_file=Path(""), sheet_name="",
                cases_count=0, raw_count=0, dedup_removed=0, error=str(exc)))
            continue

    _print_summary(results, ai_client, config, log_callback)
    return results


def generate_for_sources(
    sources: List[Source],
    config: Config,
    log_callback: Optional[ProgressCallback] = None,
) -> List[GenerationResult]:
    """Generate test cases from mixed sources (files + URLs)."""
    ai_client = AIClient(config)
    ocr_service = get_ocr_service(config.enable_ocr, config.ocr_lang)
    results: List[GenerationResult] = []
    total = len(sources)

    for idx, source in enumerate(sources, 1):
        if isinstance(source, UrlSource):
            _notify(log_callback, f"🌐 [{idx}/{total}] 获取网页：{source.name}")
            try:
                result = _process_url_source(source, config, ai_client, log_callback)
                results.append(result)
                try:
                    record_generation(
                        source_file=source.url, output_file=str(result.output_file),
                        project_name=config.project_name, module_name=config.module_name,
                        model_used=config.model, cases_count=result.cases_count,
                        raw_count=result.raw_count, dedup_removed=result.dedup_removed,
                        quality_score=result.quality_score, coverage=result.coverage)
                except Exception:
                    pass
            except Exception as exc:
                _notify(log_callback, f"❌ {source.name} 处理失败：{exc}")
                results.append(GenerationResult(
                    source_file=Path(source.url), output_file=Path(""), sheet_name="",
                    cases_count=0, raw_count=0, dedup_removed=0, error=str(exc)))
        else:
            _notify(log_callback, f"📄 [{idx}/{total}] 开始处理：{source.name}")
            try:
                result = _process_single_file(source, config, ai_client, ocr_service, log_callback)
                results.append(result)
                try:
                    record_generation(
                        source_file=str(source), output_file=str(result.output_file),
                        project_name=config.project_name, module_name=config.module_name,
                        model_used=config.model, cases_count=result.cases_count,
                        raw_count=result.raw_count, dedup_removed=result.dedup_removed,
                        quality_score=result.quality_score, coverage=result.coverage)
                except Exception:
                    pass
            except Exception as exc:
                _notify(log_callback, f"❌ {source.name} 处理失败：{exc}")
                results.append(GenerationResult(
                    source_file=source, output_file=Path(""), sheet_name="",
                    cases_count=0, raw_count=0, dedup_removed=0, error=str(exc)))

    _print_summary(results, ai_client, config, log_callback)
    return results


def _process_url_source(source: UrlSource, config, ai_client, log_callback):
    """Process a single URL source."""
    text = read_url(source.url, username=source.username, password=source.password)
    if not text or not text.strip():
        raise ValueError(f"网页 {source.url} 无有效内容")
    _notify(log_callback, f"   文档长度：{len(text)} 字符")

    return _generate_cases_from_text(
        text=text,
        source_name=source.stem,
        source_display=source.name,
        source_path=Path(source.url),
        config=config,
        ai_client=ai_client,
        log_callback=log_callback,
    )


def _process_single_file(file_path, config, ai_client, ocr_service, log_callback):
    text = read_document(file_path, ocr_service=ocr_service)
    if not text:
        raise ValueError(f"文件 {file_path.name} 无有效内容")
    _notify(log_callback, f"   文档长度：{len(text)} 字符")

    return _generate_cases_from_text(
        text=text,
        source_name=file_path.stem,
        source_display=file_path.name,
        source_path=file_path,
        config=config,
        ai_client=ai_client,
        log_callback=log_callback,
    )


def _generate_cases_from_text(
    text: str,
    source_name: str,
    source_display: str,
    source_path: Path,
    config: Config,
    ai_client: AIClient,
    log_callback: Optional[ProgressCallback],
) -> GenerationResult:
    """Core generation logic shared by file and URL sources."""
    chunks = split_text(text, config.chunk_size)
    _notify(log_callback, f"   分为 {len(chunks)} 个段落")

    # AI generation with per-chunk error recovery
    chunk_outputs: List[str] = []
    failed_chunks: List[int] = []
    for idx, chunk in enumerate(chunks, 1):
        _notify(log_callback, f"   🧠 AI 生成段落 {idx}/{len(chunks)}...")
        try:
            if len(chunks) == 1:
                output = ai_client.generate(chunk)
            else:
                prev_titles, prev_dims = [], []
                for prev_out in chunk_outputs:
                    try:
                        from app.core.ai_client import _extract_context
                        t, d = _extract_context(prev_out)
                        prev_titles.extend(t)
                        prev_dims.extend(d)
                    except Exception:
                        pass
                output = ai_client.generate_with_context(
                    chunk, idx, len(chunks), prev_titles, prev_dims)
            chunk_outputs.append(output)
        except Exception as e:
            _notify(log_callback, f"   ⚠️ 段落 {idx} 失败：{e}，跳过")
            failed_chunks.append(idx)

    if not chunk_outputs:
        raise RuntimeError("所有段落生成均失败")

    # Save raw output
    raw = "\n\n---CHUNK_SEPARATOR---\n\n".join(chunk_outputs)
    raw_file = config.output_dir / f"{source_name}_AI原始输出.txt"
    raw_file.write_text(raw, encoding="utf-8")
    if failed_chunks:
        _notify(log_callback, f"   ⚠️ 段落 {failed_chunks} 失败已跳过")

    # Parse
    all_cases: List[dict] = []
    for idx, output in enumerate(chunk_outputs, 1):
        cc = parse_cases(output)
        _notify(log_callback, f"   段落 {idx}: {len(cc)} 条")
        all_cases.extend(cc)
    if not all_cases:
        raise ValueError("未解析出任何测试用例")

    raw_count = len(all_cases)
    deduped = deduplicate_cases(all_cases)
    dedup_removed = raw_count - len(deduped)
    if dedup_removed > 0:
        _notify(log_callback, f"   🔄 去重移除 {dedup_removed} 条")

    cases = validate_cases(deduped)
    _notify(log_callback, f"   ✔️ {len(cases)} 条有效用例")

    coverage = analyze_coverage(cases)
    qs = coverage.get("quality_score", 0)
    _notify(log_callback, f"   📊 质量评分：{qs}/100")
    if coverage.get("dimensions"):
        _notify(log_callback, f"   覆盖维度：{'、'.join(f'{k}({v})' for k, v in coverage['dimensions'].items())}")
    if coverage.get("missing_dimensions"):
        _notify(log_callback, f"   ⚠️ 未覆盖：{'、'.join(coverage['missing_dimensions'])}")

    # Export
    module_display = config.module_name or source_name
    sheet_name = _sanitize_sheet_name(config.submodule_name or module_display)
    if config.single_workbook:
        output_file = config.output_dir / "汇总测试用例.xlsx"
    else:
        output_file = config.output_dir / f"{source_name}_测试用例.xlsx"

    export_cases(
        _map_cases_to_template(cases, config.project_name, module_display, config.submodule_name),
        output_file, sheet_name=sheet_name, coverage=coverage)

    _notify(log_callback, f"   ✅ 完成：{len(cases)} 条（原始 {raw_count}，去重 {dedup_removed}，质量 {qs}/100）")

    return GenerationResult(
        source_file=source_path, output_file=output_file, sheet_name=sheet_name,
        cases_count=len(cases), raw_count=raw_count, dedup_removed=dedup_removed,
        quality_score=qs, coverage=coverage, token_summary=ai_client.usage.summary())


def _print_summary(results, ai_client, config, log_callback):
    """Print generation summary."""
    ok = [r for r in results if not r.error]
    fail = [r for r in results if r.error]
    if ok:
        total = sum(r.cases_count for r in ok)
        total_raw = sum(r.raw_count for r in ok)
        total_dedup = sum(r.dedup_removed for r in ok)
        avg_q = sum(r.quality_score for r in ok) // len(ok)
        _notify(log_callback, "")
        _notify(log_callback, f"📊 汇总：{len(ok)} 个源成功，共 {total} 条用例")
        _notify(log_callback, f"   原始 {total_raw}，去重 {total_dedup}，平均质量 {avg_q}/100")
    if fail:
        _notify(log_callback, f"⚠️ {len(fail)} 个源处理失败")

    # Token usage summary
    _notify(log_callback, f"💰 {ai_client.usage.summary()}")

    # Save log to file
    _save_log(config.output_dir, log_callback)


def _map_cases_to_template(cases, project_name, module_name, submodule_name):
    mapped = []
    for idx, case in enumerate(cases, 1):
        mapped.append({
            "序号": idx,
            "项目名称": project_name or module_name,
            "模块名称": module_name,
            "子模块名称": submodule_name,
            "测试点": case.get("测试点", case.get("test_point", "")),  # 支持新字段
            "功能点": case.get("功能点", "").strip(),  # 保持兼容性
            "用例标题": case.get("用例标题", case.get("title", "")).strip().lstrip(":"),
            "前置条件": case.get("前置条件", case.get("precondition", "")).strip().lstrip(":"),
            "输入数据": case.get("输入数据", ""),
            "操作步骤": case.get("测试步骤", case.get("steps", "")).strip(),
            "预期结果": case.get("预期结果", case.get("expected", "")).strip(),
            "优先级": case.get("优先级", case.get("priority", "中")).strip(),
        })
    return mapped


def _sanitize_sheet_name(raw):
    invalid = set(r"[]:*?/\\")
    cleaned = "".join(c for c in raw if c not in invalid).strip()
    return (cleaned or "Sheet1")[:31]


def _save_log(output_dir: Path, log_callback) -> None:
    """Save a timestamped log file for audit trail."""
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = output_dir / f"运行日志_{ts}.txt"
        log_file.write_text(f"日志生成时间：{datetime.now().isoformat()}\n", encoding="utf-8")
    except Exception:
        pass
