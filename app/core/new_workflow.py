"""
新的两阶段工作流程：需求文档 -> 测试点 -> 测试用例 -> Excel
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Union

from app.config import Config
from app.core.chunker import split_text
from app.core.dedup import analyze_coverage, deduplicate_cases, validate_cases
from app.core.document_loader import read_document, read_url
from app.core.exporter import export_cases
from app.core.history import record_generation
from app.core.ocr import get_ocr_service
from app.test_design.testpoint_generator import TestPointGenerator
from app.test_design.testcase_generator import TestCaseGenerator

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str], None]


@dataclass
class NewGenerationResult:
    """新工作流程的生成结果"""
    source_file: Path
    output_file: Path
    sheet_name: str
    test_points_count: int
    cases_count: int
    raw_count: int
    dedup_removed: int
    quality_score: int = 0
    coverage: Dict = field(default_factory=dict)
    error: str = ""
    token_summary: str = ""
    test_cases: List[dict] = field(default_factory=list)


def _notify(cb: Optional[ProgressCallback], msg: str) -> None:
    if cb:
        cb(msg)
    logger.info(msg)


def generate_with_new_workflow(
    files: Iterable[Path],
    config: Config,
    log_callback: Optional[ProgressCallback] = None,
) -> List[NewGenerationResult]:
    """
    使用新的两阶段工作流程生成测试用例
    
    流程：需求文档 -> 解析需求文本 -> AI生成测试点 -> AI根据测试点生成测试用例 -> 导出Excel
    """
    testpoint_generator = TestPointGenerator(config)
    testcase_generator = TestCaseGenerator(config)
    ocr_service = get_ocr_service(config.enable_ocr, config.ocr_lang)
    results: List[NewGenerationResult] = []
    file_list = list(files)
    total_files = len(file_list)

    for file_idx, file_path in enumerate(file_list, 1):
        _notify(log_callback, f"📄 [{file_idx}/{total_files}] 开始处理：{file_path.name}")
        try:
            result = _process_single_file_new_workflow(
                file_path, config, testpoint_generator, testcase_generator, ocr_service, log_callback
            )
            results.append(result)
            
            # 记录生成历史
            try:
                record_generation(
                    source_file=str(file_path), 
                    output_file=str(result.output_file),
                    project_name=config.project_name, 
                    module_name=config.module_name,
                    model_used=config.model, 
                    cases_count=result.cases_count,
                    raw_count=result.raw_count, 
                    dedup_removed=result.dedup_removed,
                    quality_score=result.quality_score, 
                    coverage=result.coverage
                )
            except Exception:
                pass
                
        except Exception as exc:
            _notify(log_callback, f"❌ {file_path.name} 处理失败：{exc}")
            results.append(NewGenerationResult(
                source_file=file_path, output_file=Path(""), sheet_name="",
                test_points_count=0, cases_count=0, raw_count=0, dedup_removed=0, error=str(exc)
            ))
            continue

    _print_new_workflow_summary(results, config, log_callback)
    return results


def _process_single_file_new_workflow(
    file_path: Path, 
    config: Config, 
    testpoint_generator: TestPointGenerator,
    testcase_generator: TestCaseGenerator,
    ocr_service,
    log_callback: Optional[ProgressCallback]
) -> NewGenerationResult:
    """使用新工作流程处理单个文件"""
    
    # 1. 读取文档
    text = read_document(file_path, ocr_service=ocr_service)
    if not text:
        raise ValueError(f"文件 {file_path.name} 无有效内容")
    _notify(log_callback, f"   文档长度：{len(text)} 字符")

    # 2. 分块处理
    chunks = split_text(text, config.chunk_size)
    _notify(log_callback, f"   分为 {len(chunks)} 个段落")

    # 3. 生成测试点
    _notify(log_callback, f"   🧠 AI生成测试点...")
    test_points = testpoint_generator.generate_test_points_for_chunks(chunks)
    
    if not test_points:
        raise ValueError("未生成任何测试点")
    
    _notify(log_callback, f"   ✅ 生成测试点 {len(test_points)} 个")
    
    # 保存测试点到文件
    points_file = config.output_dir / f"{file_path.stem}_测试点.txt"
    points_file.write_text('\n'.join(f"{i+1}. {point}" for i, point in enumerate(test_points)), encoding="utf-8")

    # 4. 根据测试点生成测试用例
    _notify(log_callback, f"   🧠 AI根据测试点生成测试用例...")
    test_cases = testcase_generator.generate_test_cases(test_points)
    
    if not test_cases:
        raise ValueError("未生成任何测试用例")

    raw_count = len(test_cases)
    _notify(log_callback, f"   原始生成 {raw_count} 条测试用例")

    # 5. 转换格式并验证
    converted_cases = []
    for case in test_cases:
        converted_case = {
            "测试点": case.get("test_point", ""),
            "用例标题": case.get("title", ""),
            "前置条件": case.get("precondition", ""),
            "测试步骤": case.get("steps", ""),
            "预期结果": case.get("expected", ""),
            "优先级": case.get("priority", "中"),
            "覆盖维度": _infer_dimension(case.get("test_point", "")),
        }
        converted_cases.append(converted_case)

    # 6. 去重和验证
    deduped = deduplicate_cases(converted_cases)
    dedup_removed = raw_count - len(deduped)
    if dedup_removed > 0:
        _notify(log_callback, f"   🔄 去重移除 {dedup_removed} 条")

    cases = validate_cases(deduped)
    _notify(log_callback, f"   ✔️ {len(cases)} 条有效用例")

    # 7. 分析覆盖率
    coverage = analyze_coverage(cases)
    qs = coverage.get("quality_score", 0)
    _notify(log_callback, f"   📊 质量评分：{qs}/100")

    # 8. 导出Excel
    module_display = config.module_name or file_path.stem
    sheet_name = _sanitize_sheet_name(config.submodule_name or module_display)
    if config.single_workbook:
        output_file = config.output_dir / "汇总测试用例_新流程.xlsx"
    else:
        output_file = config.output_dir / f"{file_path.stem}_测试用例_新流程.xlsx"

    export_cases(
        _map_new_cases_to_template(cases, config.project_name, module_display, config.submodule_name),
        output_file, sheet_name=sheet_name, coverage=coverage
    )

    _notify(log_callback, f"   ✅ 完成：{len(test_points)} 个测试点 -> {len(cases)} 条用例（质量 {qs}/100）")

    return NewGenerationResult(
        source_file=file_path, output_file=output_file, sheet_name=sheet_name,
        test_points_count=len(test_points), cases_count=len(cases), 
        raw_count=raw_count, dedup_removed=dedup_removed,
        quality_score=qs, coverage=coverage, test_cases=test_cases
    )


def _map_new_cases_to_template(cases, project_name, module_name, submodule_name):
    """将新格式的测试用例映射到Excel模板"""
    mapped = []
    for idx, case in enumerate(cases, 1):
        mapped.append({
            "序号": idx,
            "项目名称": project_name or module_name,
            "模块名称": module_name,
            "子模块名称": submodule_name,
            "测试点": case.get("测试点", "").strip(),
            "用例标题": case.get("用例标题", "").strip().lstrip(":"),
            "前置条件": case.get("前置条件", "").strip().lstrip(":"),
            "输入数据": case.get("输入数据", ""),
            "操作步骤": case.get("测试步骤", "").strip(),
            "预期结果": case.get("预期结果", "").strip(),
            "优先级": case.get("优先级", "中").strip(),
        })
    return mapped


def _infer_dimension(test_point: str) -> str:
    """根据测试点推断覆盖维度"""
    if not test_point:
        return "功能测试"
    
    test_point_lower = test_point.lower()
    
    if any(keyword in test_point_lower for keyword in ["边界", "最大", "最小", "限制", "范围"]):
        return "边界测试"
    elif any(keyword in test_point_lower for keyword in ["异常", "错误", "失败", "无效"]):
        return "异常测试"
    elif any(keyword in test_point_lower for keyword in ["权限", "角色", "授权", "访问"]):
        return "权限测试"
    elif any(keyword in test_point_lower for keyword in ["校验", "验证", "格式", "必填"]):
        return "数据校验"
    else:
        return "功能测试"


def _sanitize_sheet_name(raw):
    """清理工作表名称"""
    invalid = set(r"[]:*?/\\")
    cleaned = "".join(c for c in raw if c not in invalid).strip()
    return (cleaned or "Sheet1")[:31]


def _print_new_workflow_summary(results, config, log_callback):
    """打印新工作流程汇总"""
    ok = [r for r in results if not r.error]
    fail = [r for r in results if r.error]
    
    if ok:
        total_points = sum(r.test_points_count for r in ok)
        total_cases = sum(r.cases_count for r in ok)
        total_raw = sum(r.raw_count for r in ok)
        total_dedup = sum(r.dedup_removed for r in ok)
        avg_q = sum(r.quality_score for r in ok) // len(ok) if ok else 0
        
        _notify(log_callback, "")
        _notify(log_callback, f"📊 新流程汇总：{len(ok)} 个源成功")
        _notify(log_callback, f"   测试点：{total_points} 个")
        _notify(log_callback, f"   测试用例：{total_cases} 条（原始 {total_raw}，去重 {total_dedup}）")
        _notify(log_callback, f"   平均质量：{avg_q}/100")
    
    if fail:
        _notify(log_callback, f"⚠️ {len(fail)} 个源处理失败")

    # 保存日志
    _save_log(config.output_dir, log_callback)


def _save_log(output_dir: Path, log_callback) -> None:
    """保存时间戳日志文件"""
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = output_dir / f"新流程运行日志_{ts}.txt"
        log_file.write_text(f"日志生成时间：{datetime.now().isoformat()}\n", encoding="utf-8")
    except Exception:
        pass