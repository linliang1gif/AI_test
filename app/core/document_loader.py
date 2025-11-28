from __future__ import annotations

import zipfile
from pathlib import Path
from typing import List, Optional

from docx import Document

from app.core.ocr import OcrService


def read_docx(file_path: Path, ocr_service: Optional[OcrService] = None) -> str:
    """Return concatenated text from a Word document, with optional OCR."""
    document = Document(file_path)
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    text_parts = ["\n".join(paragraphs)]

    if ocr_service:
        image_texts = _extract_images_text(file_path, ocr_service)
        if image_texts:
            text_parts.append("\n".join(image_texts))

    return "\n\n".join([part for part in text_parts if part])


def _extract_images_text(file_path: Path, ocr_service: OcrService) -> List[str]:
    texts: List[str] = []
    with zipfile.ZipFile(file_path) as docx_zip:
        image_files = [f for f in docx_zip.namelist() if f.startswith("word/media/")]
        for index, image_name in enumerate(image_files, 1):
            image_bytes = docx_zip.read(image_name)
            ocr_text = ocr_service.recognize(image_bytes)
            if ocr_text:
                texts.append(f"[图片{index}] {ocr_text}")
    return texts


def load_documents(paths: List[Path], ocr_service: Optional[OcrService] = None) -> List[tuple[Path, str]]:
    """Load multiple documents and return pairs of (path, text)."""
    results: List[tuple[Path, str]] = []
    for path in paths:
        if not path.exists() or path.suffix.lower() != ".docx":
            continue
        text = read_docx(path, ocr_service=ocr_service)
        if text:
            results.append((path, text))
    return results


