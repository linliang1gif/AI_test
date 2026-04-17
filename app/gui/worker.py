from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QThread, Signal

from app.config import Config
from app.core.workflow import GenerationResult, UrlSource, generate_for_files, generate_for_sources
from app.core.new_workflow import generate_with_new_workflow
from app.automation.api_script_generator import ApiScriptGenerator


class GenerationWorker(QThread):
    progress = Signal(str)
    finished = Signal(list)
    failed = Signal(str)

    def __init__(
        self,
        files: List[Path],
        config: Config,
        url_sources: Optional[List[UrlSource]] = None,
        use_new_workflow: bool = True,  # 默认使用新流程
    ):
        super().__init__()
        self.files = files
        self.config = config
        self.url_sources = url_sources or []
        self.use_new_workflow = use_new_workflow

    def run(self) -> None:  # pragma: no cover - UI thread
        try:
            if self.url_sources:
                # Mixed mode: files + URLs (使用旧流程)
                sources = list(self.files) + list(self.url_sources)
                results = generate_for_sources(sources, self.config, self._emit_progress)
            elif self.use_new_workflow and not self.url_sources:
                # 使用新的两阶段工作流程
                self._emit_progress("🚀 使用新的两阶段工作流程...")
                new_results = generate_with_new_workflow(self.files, self.config, self._emit_progress)
                
                # 生成API自动化测试脚本
                if new_results and not any(r.error for r in new_results):
                    self._emit_progress("🤖 生成API自动化测试脚本...")
                    try:
                        self._generate_api_scripts(new_results)
                    except Exception as e:
                        self._emit_progress(f"⚠️ API脚本生成失败：{e}")
                
                # 转换为旧格式以兼容GUI
                results = self._convert_new_results_to_old(new_results)
            else:
                # File-only mode (backward compatible)
                results = generate_for_files(self.files, self.config, self._emit_progress)
            self.finished.emit(results)
        except Exception as exc:
            self.failed.emit(str(exc))

    def _emit_progress(self, message: str) -> None:
        self.progress.emit(message)
    
    def _generate_api_scripts(self, new_results):
        """生成API自动化测试脚本"""
        try:
            api_generator = ApiScriptGenerator(self.config)
            
            # 收集所有测试用例（从新工作流程结果中提取）
            all_test_cases = []
            for result in new_results:
                if not result.error and result.cases_count > 0:
                    # NewGenerationResult 已包含原始测试用例结构（英文字段）
                    if getattr(result, "test_cases", None):
                        all_test_cases.extend(result.test_cases)
            
            if all_test_cases:
                scripts = api_generator.generate_scripts_by_module(all_test_cases)
                if scripts:
                    saved_files = api_generator.save_scripts_to_files(scripts)
                    self._emit_progress(f"✅ API测试脚本生成成功，共 {len(saved_files)} 个文件")
                    
                    # 生成配置文件
                    from pathlib import Path
                    conftest_content = api_generator.generate_conftest_py()
                    conftest_path = Path("tests") / "conftest.py"
                    conftest_path.parent.mkdir(exist_ok=True)
                    conftest_path.write_text(conftest_content, encoding="utf-8")
                    
                    requirements_content = api_generator.generate_requirements_txt()
                    req_path = Path("tests") / "requirements.txt"
                    req_path.write_text(requirements_content, encoding="utf-8")
                    
                    self._emit_progress(f"📁 API脚本保存到: tests/ 目录")
        except Exception as e:
            self._emit_progress(f"⚠️ API脚本生成失败：{e}")
    
    def _convert_new_results_to_old(self, new_results):
        """将新结果格式转换为旧格式以兼容GUI"""
        old_results = []
        for new_result in new_results:
            # 创建兼容的GenerationResult对象
            old_result = GenerationResult(
                source_file=new_result.source_file,
                output_file=new_result.output_file,
                sheet_name=new_result.sheet_name,
                cases_count=new_result.cases_count,
                raw_count=new_result.raw_count,
                dedup_removed=new_result.dedup_removed,
                quality_score=new_result.quality_score,
                coverage=new_result.coverage,
                error=new_result.error,
                token_summary=new_result.token_summary
            )
            old_results.append(old_result)
        return old_results
