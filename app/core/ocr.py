from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import List, Optional

from PIL import Image


@dataclass
class OcrService:
    enabled: bool
    lang: str = "ch"

    def __post_init__(self) -> None:
        self._ocr = None

    def ensure_model(self) -> None:
        if self._ocr is None:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                show_log=False,
            )

    def recognize(self, image_bytes: bytes) -> str:
        if not self.enabled:
            return ""
        self.ensure_model()
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        result = self._ocr.ocr(image, cls=True)  # type: ignore[arg-type]
        lines: List[str] = []
        for block in result or []:
            if len(block) >= 2 and isinstance(block[1], list):
                text = block[1][0]
                if text:
                    lines.append(text)
        return "\n".join(lines)


def get_ocr_service(enabled: bool, lang: str) -> Optional[OcrService]:
    if not enabled:
        return None
    return OcrService(enabled=True, lang=lang)


