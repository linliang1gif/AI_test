from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import QThread, Signal

from app.config import Config
from app.core.workflow import GenerationResult, generate_for_files


class GenerationWorker(QThread):
    progress = Signal(str)
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, files: List[Path], config: Config):
        super().__init__()
        self.files = files
        self.config = config

    def run(self) -> None:  # pragma: no cover - UI thread
        try:
            results = generate_for_files(self.files, self.config, self._emit_progress)
            self.finished.emit(results)
        except Exception as exc:
            self.failed.emit(str(exc))

    def _emit_progress(self, message: str) -> None:
        self.progress.emit(message)


