from __future__ import annotations

from typing import List


def split_text(text: str, chunk_size: int) -> List[str]:
    """Split long text into chunks respecting the configured size."""
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


