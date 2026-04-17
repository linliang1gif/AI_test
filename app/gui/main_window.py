from __future__ import annotations

import os
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QCheckBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import Config, MODEL_PRESETS, load_config, save_settings
from app.core.document_loader import get_file_filter, is_supported
from app.core.workflow import GenerationResult, UrlSource
from app.gui.worker import GenerationWorker


# ── URL Import Dialog ────────────────────────────────────────────────────────

class UrlImportDialog(QDialog):
    """Dialog for importing requirements from web URLs (SVN / intranet)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("从 URL 导入需求")
        self.setMinimumWidth(550)
        self.setMinimumHeight(400)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("输入需求页面 URL（每行一个）："))
        self.url_input = QPlainTextEdit()
        self.url_input.setPlaceholderText(
            "http://subvs.szibu.com/svn/wiki/requirements/page1.html\n"
            "http://subvs.szibu.com/svn/wiki/requirements/page2.html"
        )
        layout.addWidget(self.url_input)

        auth_label = QLabel("🔐 认证信息（SVN / 内网需要时填写）：")
        layout.addWidget(auth_label)

        auth_form = QFormLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("SVN 用户名（可选）")
        auth_form.addRow("用户名", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("SVN 密码（可选）")
        auth_form.addRow("密码", self.password_input)
        layout.addLayout(auth_form)

        hint = QLabel(
            "💡 提示：支持 SVN Web 界面、Wiki 页面、内网 HTML 页面。\n"
            "系统会自动提取页面正文内容，过滤导航栏等无关元素。\n"
            "如果页面需要登录，请填写用户名和密码。"
        )
        hint.setStyleSheet("color: #666; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_urls(self) -> List[str]:
        """Return list of non-empty URLs."""
        text = self.url_input.toPlainText()
        urls = []
        for line in text.splitlines():
            line = line.strip()
            if line and (line.startswith("http://") or line.startswith("https://")):
                urls.append(line)
        return urls

    def get_username(self) -> str:
        return self.username_input.text().strip()

    def get_password(self) -> str:
        return self.password_input.text().strip()


# ── Drop-enabled List Widget ────────────────────────────────────────────────

class DropListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self._on_drop = None

    def set_drop_callback(self, callback):
        self._on_drop = callback

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        paths = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file() and is_supported(path):
                paths.append(path)
            elif path.is_dir():
                for f in path.rglob("*"):
                    if f.is_file() and is_supported(f):
                        paths.append(f)
        if paths and self._on_drop:
            self._on_drop(paths)
        event.acceptProposedAction()


# ── Main Window ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI 测试用例生成器 v3.2 Enterprise")
        self.resize(1100, 750)
        self.file_paths: List[Path] = []
        self.url_sources: List[UrlSource] = []  # NEW: URL sources
        self.worker: GenerationWorker | None = None
        self._file_count = 0
        self._files_done = 0
        self._last_results: List[GenerationResult] = []
        self._build_ui()
        self._load_defaults()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs)

        # Tab 1: Generate
        gen_widget = QWidget()
        gen_layout = QHBoxLayout(gen_widget)

        file_panel = QVBoxLayout()
        file_panel.addWidget(QLabel("📁 需求来源（支持文件拖拽 + URL 导入）"))
        self.file_list = DropListWidget()
        self.file_list.set_drop_callback(self._on_files_dropped)
        file_panel.addWidget(self.file_list)

        file_btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加文件")
        add_btn.clicked.connect(self.add_files)
        add_dir_btn = QPushButton("添加目录")
        add_dir_btn.clicked.connect(self.add_directory)
        add_url_btn = QPushButton("🌐 从 URL 导入")
        add_url_btn.clicked.connect(self.add_urls)
        remove_btn = QPushButton("移除选中")
        remove_btn.clicked.connect(self.remove_selected)
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.clear_files)
        file_btn_layout.addWidget(add_btn)
        file_btn_layout.addWidget(add_dir_btn)
        file_btn_layout.addWidget(add_url_btn)
        file_btn_layout.addWidget(remove_btn)
        file_btn_layout.addWidget(clear_btn)
        file_panel.addLayout(file_btn_layout)

        config_panel = QVBoxLayout()
        config_panel.addWidget(QLabel("⚙️ 运行配置"))
        form = QFormLayout()

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(MODEL_PRESETS.keys())
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        form.addRow("模型预设", self.preset_combo)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        form.addRow("API Key", self.api_key_input)

        self.base_url_input = QLineEdit()
        form.addRow("Base URL", self.base_url_input)

        self.model_input = QLineEdit()
        form.addRow("模型名称", self.model_input)

        self.project_name_input = QLineEdit()
        form.addRow("项目名称", self.project_name_input)

        self.module_name_input = QLineEdit()
        form.addRow("模块名称", self.module_name_input)

        self.submodule_name_input = QLineEdit()
        form.addRow("子模块名称", self.submodule_name_input)

        self.chunk_input = QSpinBox()
        self.chunk_input.setRange(500, 8000)
        form.addRow("分段大小", self.chunk_input)

        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(0.0, 1.0)
        self.temperature_input.setSingleStep(0.05)
        self.temperature_input.setDecimals(2)
        form.addRow("AI 温度", self.temperature_input)

        self.ocr_checkbox = QCheckBox("启用 OCR")
        form.addRow("图像识别", self.ocr_checkbox)

        self.single_workbook_checkbox = QCheckBox("合并到一个 Excel")
        self.single_workbook_checkbox.setChecked(True)
        form.addRow("导出策略", self.single_workbook_checkbox)

        output_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.choose_output_dir)
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(browse_btn)
        form.addRow("输出目录", output_layout)
        config_panel.addLayout(form)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("就绪")
        config_panel.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("🚀 开始生成")
        self.start_btn.setMinimumHeight(38)
        self.start_btn.clicked.connect(self.start_generation)
        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setMinimumHeight(38)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_generation)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        config_panel.addLayout(btn_layout)

        # 说明当前版本的内部流程
        hint_label = QLabel(
            "说明：在仅使用文件作为需求来源时，将自动使用“测试点→测试用例”的两阶段新流程，"
            "并在生成成功后自动尝试生成对应的 API 自动化测试脚本（输出在项目根目录 tests/ 下）。"
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #666666; font-size: 11px;")
        config_panel.addWidget(hint_label)

        config_panel.addWidget(QLabel("📋 实时日志"))
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        config_panel.addWidget(self.log_view)

        gen_layout.addLayout(file_panel, 2)
        gen_layout.addLayout(config_panel, 3)
        self.tabs.addTab(gen_widget, "生成")

        # Tab 2: Preview
        self._build_preview_tab()
        # Tab 3: History
        self._build_history_tab()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _build_preview_tab(self) -> None:
        pw = QWidget()
        pl = QVBoxLayout(pw)
        pl.addWidget(QLabel("📋 用例预览（生成后可查看、编辑、删除再导出）"))
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(7)
        self.preview_table.setHorizontalHeaderLabels([
            "序号", "功能点", "用例标题", "前置条件", "操作步骤", "预期结果", "优先级"])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setColumnWidth(0, 50)
        self.preview_table.setColumnWidth(1, 120)
        self.preview_table.setColumnWidth(2, 200)
        self.preview_table.setColumnWidth(3, 150)
        self.preview_table.setColumnWidth(4, 200)
        self.preview_table.setColumnWidth(5, 200)
        self.preview_table.setColumnWidth(6, 60)
        pl.addWidget(self.preview_table)
        pbl = QHBoxLayout()
        del_btn = QPushButton("删除选中行")
        del_btn.clicked.connect(self._delete_selected_preview)
        self.export_btn = QPushButton("📥 重新导出（含编辑）")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._re_export)
        pbl.addWidget(del_btn)
        pbl.addStretch()
        pbl.addWidget(self.export_btn)
        pl.addLayout(pbl)
        self.tabs.addTab(pw, "预览")

    def _build_history_tab(self) -> None:
        hw = QWidget()
        hl = QVBoxLayout(hw)
        ht = QHBoxLayout()
        ht.addWidget(QLabel("📜 生成历史"))
        rb = QPushButton("刷新")
        rb.clicked.connect(self._load_history)
        ht.addStretch()
        ht.addWidget(rb)
        hl.addLayout(ht)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "时间", "文件", "项目", "模型", "用例数", "质量分", "状态"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        hl.addWidget(self.history_table)
        self.stats_label = QLabel("")
        hl.addWidget(self.stats_label)
        self.tabs.addTab(hw, "历史")

    def _load_defaults(self) -> None:
        try:
            config = load_config(Path("."))
            self.api_key_input.setText(config.api_key)
            self.base_url_input.setText(config.base_url)
            self.model_input.setText(config.model)
            self.project_name_input.setText(config.project_name)
            self.module_name_input.setText(config.module_name)
            self.submodule_name_input.setText(config.submodule_name)
            self.chunk_input.setValue(config.chunk_size)
            self.temperature_input.setValue(config.temperature)
            self.output_input.setText(str(config.output_dir))
            self.ocr_checkbox.setChecked(config.enable_ocr)
            self.single_workbook_checkbox.setChecked(config.single_workbook)
            if config.model_preset and config.model_preset in MODEL_PRESETS:
                self.preset_combo.setCurrentText(config.model_preset)
        except Exception:
            self.chunk_input.setValue(3000)
            self.temperature_input.setValue(0.2)
            self.output_input.setText(str((Path.cwd() / "output").resolve()))
            self.single_workbook_checkbox.setChecked(True)

    def _on_preset_changed(self, name: str) -> None:
        p = MODEL_PRESETS.get(name, {})
        if p.get("base_url"):
            self.base_url_input.setText(p["base_url"])
        if p.get("model"):
            self.model_input.setText(p["model"])
        ek = p.get("env_key", "")
        if ek:
            k = os.environ.get(ek, "")
            if k and not self.api_key_input.text().strip():
                self.api_key_input.setText(k)

    def _on_files_dropped(self, paths: List[Path]) -> None:
        for p in paths:
            if p not in self.file_paths:
                self.file_paths.append(p)
                QListWidgetItem(f"📄 {p.name}  ({p.suffix})", self.file_list)

    def add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择需求文档", str(Path.cwd()), get_file_filter())
        for f in files:
            p = Path(f)
            if p not in self.file_paths:
                self.file_paths.append(p)
                QListWidgetItem(f"📄 {p.name}  ({p.suffix})", self.file_list)

    def add_directory(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择文档目录", str(Path.cwd()))
        if folder:
            c = 0
            for f in Path(folder).rglob("*"):
                if f.is_file() and is_supported(f) and f not in self.file_paths:
                    self.file_paths.append(f)
                    QListWidgetItem(f"📄 {f.name}  ({f.suffix})", self.file_list)
                    c += 1
            if c:
                self.status_bar.showMessage(f"从目录导入 {c} 个文件")

    def add_urls(self) -> None:
        """Open URL import dialog."""
        dialog = UrlImportDialog(self)
        if dialog.exec() == QDialog.Accepted:
            urls = dialog.get_urls()
            username = dialog.get_username()
            password = dialog.get_password()
            if not urls:
                QMessageBox.warning(self, "提示", "未输入有效的 URL")
                return
            added = 0
            for url in urls:
                # Check for duplicates
                if any(s.url == url for s in self.url_sources):
                    continue
                source = UrlSource(
                    url=url,
                    username=username or None,
                    password=password or None,
                )
                self.url_sources.append(source)
                # Show in list with globe icon
                display = url.split("/")[-1] or url
                if len(display) > 60:
                    display = display[:57] + "..."
                QListWidgetItem(f"🌐 {display}", self.file_list)
                added += 1
            if added:
                self.status_bar.showMessage(f"已添加 {added} 个 URL 来源")

    def remove_selected(self) -> None:
        for item in reversed(self.file_list.selectedItems()):
            row = self.file_list.row(item)
            text = item.text()
            self.file_list.takeItem(row)
            if text.startswith("🌐"):
                # Remove from url_sources by index offset
                url_idx = self._get_url_index(row)
                if 0 <= url_idx < len(self.url_sources):
                    self.url_sources.pop(url_idx)
            else:
                file_idx = self._get_file_index(row)
                if 0 <= file_idx < len(self.file_paths):
                    self.file_paths.pop(file_idx)

    def _get_file_index(self, list_row: int) -> int:
        """Map list widget row to file_paths index (counting only file items before this row)."""
        idx = 0
        for r in range(list_row):
            item = self.file_list.item(r)
            if item and not item.text().startswith("🌐"):
                idx += 1
        return idx

    def _get_url_index(self, list_row: int) -> int:
        """Map list widget row to url_sources index (counting only URL items before this row)."""
        idx = 0
        for r in range(list_row):
            item = self.file_list.item(r)
            if item and item.text().startswith("🌐"):
                idx += 1
        return idx

    def clear_files(self) -> None:
        self.file_paths.clear()
        self.url_sources.clear()
        self.file_list.clear()

    def choose_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_input.text())
        if folder:
            self.output_input.setText(folder)

    def _build_config(self) -> Config:
        return Config(
            api_key=self.api_key_input.text().strip(),
            base_url=self.base_url_input.text().strip() or "https://api.deepseek.com",
            model=self.model_input.text().strip() or "deepseek-chat",
            chunk_size=int(self.chunk_input.value()),
            temperature=self.temperature_input.value(),
            output_dir=Path(self.output_input.text().strip()).resolve(),
            enable_ocr=self.ocr_checkbox.isChecked(),
            ocr_lang="ch",
            single_workbook=self.single_workbook_checkbox.isChecked(),
            project_name=self.project_name_input.text().strip(),
            module_name=self.module_name_input.text().strip(),
            submodule_name=self.submodule_name_input.text().strip(),
            model_preset=self.preset_combo.currentText(),
        )

    def start_generation(self) -> None:
        if not self.file_paths and not self.url_sources:
            QMessageBox.warning(self, "提示", "请先添加至少一个需求来源（文件或 URL）")
            return
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请填写 API Key")
            return
        config = self._build_config()
        config.ensure_output_dir()
        try:
            save_settings(config)
        except Exception:
            pass
        self.log_view.clear()
        self._file_count = len(self.file_paths) + len(self.url_sources)
        self._files_done = 0
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("生成中... 0%")
        self.toggle_controls(False)
        self.status_bar.showMessage("正在生成...")
        self.worker = GenerationWorker(
            self.file_paths.copy(), config,
            url_sources=[s for s in self.url_sources],
        )
        self.worker.progress.connect(self.append_log)
        self.worker.finished.connect(self.handle_finished)
        self.worker.failed.connect(self.handle_failed)
        self.worker.start()

    def stop_generation(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(3000)
            self.append_log("⏹ 已手动停止")
            self.toggle_controls(True)
            self.worker = None

    def append_log(self, msg: str) -> None:
        self.log_view.appendPlainText(msg)
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum())
        if "✅" in msg:
            self._files_done += 1
            pct = int(self._files_done / max(self._file_count, 1) * 100)
            self.progress_bar.setValue(pct)
            self.progress_bar.setFormat(f"生成中... {pct}%")

    def handle_finished(self, results: List[GenerationResult]) -> None:
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("完成 ✅")
        self._last_results = results
        ok = [r for r in results if not r.error]
        fail = [r for r in results if r.error]
        self.append_log("")
        self.append_log("🎉 处理完成")
        for r in ok:
            name = r.source_file.name if r.source_file.name else str(r.source_file)
            self.append_log(f"  ✅ {name} → {r.output_file.name} "
                            f"({r.cases_count} 条，质量 {r.quality_score}/100)")
        for r in fail:
            name = r.source_file.name if r.source_file.name else str(r.source_file)
            self.append_log(f"  ❌ {name}：{r.error}")
        total = sum(r.cases_count for r in ok)
        self.status_bar.showMessage(
            f"完成：{len(ok)} 成功 / {len(fail)} 失败，共 {total} 条用例")
        self._populate_preview(ok)
        self.toggle_controls(True)
        self.worker = None

    def handle_failed(self, message: str) -> None:
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("失败 ❌")
        self.status_bar.showMessage("生成失败")
        QMessageBox.critical(self, "运行失败", message)
        self.toggle_controls(True)
        self.worker = None

    def toggle_controls(self, enabled: bool) -> None:
        self.start_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(not enabled)
        self.file_list.setEnabled(enabled)
        self.preset_combo.setEnabled(enabled)

    def _populate_preview(self, results: List[GenerationResult]) -> None:
        self.preview_table.setRowCount(0)
        row = 0
        for r in results:
            raw_file = r.output_file.parent / f"{r.source_file.stem}_AI原始输出.txt"
            if not raw_file.exists():
                continue
            try:
                from app.core.parser import parse_cases
                from app.core.dedup import deduplicate_cases, validate_cases
                raw_text = raw_file.read_text(encoding="utf-8")
                chunks = raw_text.split("---CHUNK_SEPARATOR---")
                all_cases = []
                for chunk in chunks:
                    chunk = chunk.strip()
                    if chunk:
                        all_cases.extend(parse_cases(chunk))
                cases = validate_cases(deduplicate_cases(all_cases))
                for case in cases:
                    self.preview_table.insertRow(row)
                    self.preview_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                    self.preview_table.setItem(row, 1, QTableWidgetItem(case.get("功能点", "")))
                    self.preview_table.setItem(row, 2, QTableWidgetItem(case.get("用例标题", "")))
                    self.preview_table.setItem(row, 3, QTableWidgetItem(case.get("前置条件", "")))
                    self.preview_table.setItem(row, 4, QTableWidgetItem(case.get("测试步骤", "")))
                    self.preview_table.setItem(row, 5, QTableWidgetItem(case.get("预期结果", "")))
                    self.preview_table.setItem(row, 6, QTableWidgetItem(case.get("优先级", "中")))
                    row += 1
            except Exception:
                continue
        self.export_btn.setEnabled(row > 0)
        if row > 0:
            self.tabs.setCurrentIndex(1)

    def _delete_selected_preview(self) -> None:
        rows = sorted(set(i.row() for i in self.preview_table.selectedItems()), reverse=True)
        for r in rows:
            self.preview_table.removeRow(r)
        for i in range(self.preview_table.rowCount()):
            self.preview_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

    def _re_export(self) -> None:
        cases = []
        config = self._build_config()
        for row in range(self.preview_table.rowCount()):
            def _txt(col):
                item = self.preview_table.item(row, col)
                return item.text() if item else ""
            case = {
                "序号": row + 1,
                "项目名称": config.project_name or config.module_name,
                "模块名称": config.module_name,
                "子模块名称": config.submodule_name,
                "功能点": _txt(1), "用例标题": _txt(2),
                "前置条件": _txt(3), "输入数据": "",
                "操作步骤": _txt(4), "预期结果": _txt(5), "优先级": _txt(6) or "中",
            }
            if case["用例标题"]:
                cases.append(case)
        if not cases:
            QMessageBox.warning(self, "提示", "没有可导出的用例")
            return
        config.ensure_output_dir()
        try:
            from app.core.exporter import export_cases
            out = config.output_dir / "编辑后_测试用例.xlsx"
            export_cases(cases, out, sheet_name="Sheet1")
            QMessageBox.information(self, "导出成功", f"已导出 {len(cases)} 条到：\n{out}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _load_history(self) -> None:
        try:
            from app.core.history import get_recent_history, get_stats
            records = get_recent_history(100)
            self.history_table.setRowCount(len(records))
            for i, rec in enumerate(records):
                ts = rec.get("timestamp", "")[:19].replace("T", " ")
                src = Path(rec.get("source_file", "")).name
                self.history_table.setItem(i, 0, QTableWidgetItem(ts))
                self.history_table.setItem(i, 1, QTableWidgetItem(src))
                self.history_table.setItem(i, 2, QTableWidgetItem(rec.get("project_name", "")))
                self.history_table.setItem(i, 3, QTableWidgetItem(rec.get("model_used", "")))
                self.history_table.setItem(i, 4, QTableWidgetItem(str(rec.get("cases_count", 0))))
                self.history_table.setItem(i, 5, QTableWidgetItem(str(rec.get("quality_score", 0))))
                self.history_table.setItem(i, 6, QTableWidgetItem(rec.get("status", "")))
            stats = get_stats()
            if stats.get("total_runs"):
                self.stats_label.setText(
                    f"累计：{stats['total_runs']} 次，{stats.get('total_cases', 0)} 条用例，"
                    f"平均质量 {stats.get('avg_quality', 0):.0f}/100")
        except Exception as e:
            self.stats_label.setText(f"加载历史失败：{e}")
