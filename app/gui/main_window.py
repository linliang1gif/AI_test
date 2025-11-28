from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import Config, load_config
from app.core.workflow import GenerationResult
from app.gui.worker import GenerationWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI 测试用例生成器")
        self.resize(960, 640)

        self.file_paths: List[Path] = []
        self.worker: GenerationWorker | None = None

        self._build_ui()
        self._load_defaults()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)

        # Left: file panel
        file_layout = QVBoxLayoutWithTitle("需求文档")
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        file_layout.addWidget(self.file_list)

        file_btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加文件")
        add_btn.clicked.connect(self.add_files)
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.clear_files)
        file_btn_layout.addWidget(add_btn)
        file_btn_layout.addWidget(clear_btn)
        file_layout.addLayout(file_btn_layout)

        # Right: config + log
        right_layout = QVBoxLayoutWithTitle("运行配置")
        form = QFormLayout()

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        form.addRow("API Key", self.api_key_input)

        self.base_url_input = QLineEdit()
        form.addRow("Base URL", self.base_url_input)

        self.model_input = QLineEdit()
        form.addRow("模型", self.model_input)

        self.project_name_input = QLineEdit()
        form.addRow("项目名称", self.project_name_input)

        self.module_name_input = QLineEdit()
        form.addRow("模块名称", self.module_name_input)

        self.submodule_name_input = QLineEdit()
        form.addRow("子模块名称", self.submodule_name_input)

        self.chunk_input = QSpinBox()
        self.chunk_input.setRange(500, 8000)
        form.addRow("分段大小", self.chunk_input)

        self.ocr_checkbox = QCheckBox("启用 OCR（识别图片文字）")
        form.addRow("图像识别", self.ocr_checkbox)

        self.ocr_lang_input = QLineEdit()
        self.ocr_lang_input.setPlaceholderText("ch / en / ...")
        form.addRow("OCR 语言", self.ocr_lang_input)

        self.single_workbook_checkbox = QCheckBox("所有用例写入一个 Excel（按文件分 Sheet）")
        form.addRow("导出策略", self.single_workbook_checkbox)

        output_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.choose_output_dir)
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(browse_btn)
        form.addRow("输出目录", output_layout)

        right_layout.addLayout(form)

        self.start_btn = QPushButton("开始生成")
        self.start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_btn.clicked.connect(self.start_generation)
        right_layout.addWidget(self.start_btn)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        right_layout.addWidget(QLabel("实时日志"))
        right_layout.addWidget(self.log_view)

        root_layout.addLayout(file_layout, 1)
        root_layout.addLayout(right_layout, 1)

    def _load_defaults(self) -> None:
        try:
            config = load_config(Path("."))
            self.base_url_input.setText(config.base_url)
            self.model_input.setText(config.model)
            self.project_name_input.setText(config.project_name)
            self.module_name_input.setText(config.module_name)
            self.submodule_name_input.setText(config.submodule_name)
            self.chunk_input.setValue(config.chunk_size)
            self.output_input.setText(str(config.output_dir))
            self.ocr_checkbox.setChecked(config.enable_ocr)
            self.ocr_lang_input.setText(config.ocr_lang)
            self.single_workbook_checkbox.setChecked(config.single_workbook)
        except Exception:
            # 没有 .env 时允许空配置，由用户手动输入
            self.base_url_input.setText("")
            self.model_input.setText("")
            self.project_name_input.setText("")
            self.module_name_input.setText("")
            self.submodule_name_input.setText("")
            self.chunk_input.setValue(3000)
            self.output_input.setText(str((Path.cwd() / "output").resolve()))
            self.ocr_checkbox.setChecked(False)
            self.ocr_lang_input.setText("ch")
            self.single_workbook_checkbox.setChecked(True)

    def add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择需求文档", str(Path.cwd()), "Word 文档 (*.docx)"
        )
        for file in files:
            path = Path(file)
            if path not in self.file_paths:
                self.file_paths.append(path)
                QListWidgetItem(str(path), self.file_list)

    def clear_files(self) -> None:
        self.file_paths.clear()
        self.file_list.clear()

    def choose_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_input.text())
        if folder:
            self.output_input.setText(folder)

    def start_generation(self) -> None:
        if not self.file_paths:
            QMessageBox.warning(self, "提示", "请先添加至少一个需求文档")
            return

        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请填写 API Key")
            return

        config = Config(
            api_key=api_key,
            base_url=self.base_url_input.text().strip() or "https://api.deepseek.com/v1",
            model=self.model_input.text().strip() or "deepseek-chat",
            chunk_size=int(self.chunk_input.value()),
            output_dir=Path(self.output_input.text().strip()).resolve(),
            enable_ocr=self.ocr_checkbox.isChecked(),
            ocr_lang=self.ocr_lang_input.text().strip() or "ch",
            single_workbook=self.single_workbook_checkbox.isChecked(),
            project_name=self.project_name_input.text().strip(),
            module_name=self.module_name_input.text().strip(),
            submodule_name=self.submodule_name_input.text().strip(),
        )
        config.ensure_output_dir()

        self.log_view.clear()
        self.toggle_controls(False)

        self.worker = GenerationWorker(self.file_paths.copy(), config)
        self.worker.progress.connect(self.append_log)
        self.worker.finished.connect(self.handle_finished)
        self.worker.failed.connect(self.handle_failed)
        self.worker.start()

    def append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def handle_finished(self, results: List[GenerationResult]) -> None:
        self.append_log("🎉 全部文件处理完成")
        for result in results:
            self.append_log(
                f"{result.source_file.name} -> {result.output_file} ({result.cases_count} 条)"
            )
        self.toggle_controls(True)
        self.worker = None

    def handle_failed(self, message: str) -> None:
        # 格式化错误消息，使其更易读
        formatted_message = message
        if "Permission denied" in message or "PermissionError" in message or "文件被占用" in message:
            formatted_message = (
                "❌ 文件写入失败\n\n"
                "可能的原因：\n"
                "1. Excel 文件正在被打开，请先关闭所有 Excel 窗口\n"
                "2. 文件被其他程序占用\n"
                "3. 没有写入权限\n\n"
                f"详细信息：\n{message}"
            )
        QMessageBox.critical(self, "运行失败", formatted_message)
        self.toggle_controls(True)
        self.worker = None

    def toggle_controls(self, enabled: bool) -> None:
        self.start_btn.setEnabled(enabled)
        self.file_list.setEnabled(enabled)


class QVBoxLayoutWithTitle(QVBoxLayout):
    def __init__(self, title: str) -> None:
        super().__init__()
        label = QLabel(title)
        label.setAlignment(Qt.AlignLeft)
        self.addWidget(label)


