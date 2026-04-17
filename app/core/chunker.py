from __future__ import annotations

import re
from typing import List, Tuple


def _detect_headings(text: str) -> List[Tuple[int, int, str]]:
    """Detect heading-like lines and their positions.

    Returns list of (line_start_pos, level, heading_text).
    Level 1 = top-level heading, Level 2 = sub-heading, etc.
    """
    headings: List[Tuple[int, int, str]] = []
    pos = 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if not stripped:
            pos += len(line)
            continue

        level = 0
        # Chinese numbered headings: 一、 二、 三、 etc.
        if re.match(r"^[一二三四五六七八九十]+[、.]", stripped):
            level = 1
        # Digit headings: 1. 2. 3. or 1、2、
        elif re.match(r"^\d+[.、]\s*\S", stripped) and len(stripped) < 80:
            level = 2
        # Sub-digit: 1.1 1.2 or (1) (2)
        elif re.match(r"^\d+\.\d+[\s.、]", stripped) and len(stripped) < 80:
            level = 3
        elif re.match(r"^[（(]\d+[)）]", stripped) and len(stripped) < 80:
            level = 3
        # Markdown-style headings
        elif re.match(r"^#{1,4}\s+", stripped):
            hashes = len(re.match(r"^(#+)", stripped).group(1))
            level = min(hashes, 3)

        if level > 0:
            headings.append((pos, level, stripped))

        pos += len(line)

    return headings


def _find_split_point(text: str, start: int, end: int) -> int:
    """Find the best split point near `end` by looking for natural breaks."""
    search_start = max(start, end - 500)
    segment = text[search_start:end]

    # Priority 1: double newline (paragraph break)
    idx = segment.rfind("\n\n")
    if idx != -1:
        return search_start + idx + 2

    # Priority 2: single newline
    idx = segment.rfind("\n")
    if idx != -1:
        return search_start + idx + 1

    # Priority 3: sentence-ending punctuation
    for punct in ["。", "；", ".", ";", "！", "？"]:
        idx = segment.rfind(punct)
        if idx != -1:
            return search_start + idx + 1

    return end


def split_text(text: str, chunk_size: int) -> List[str]:
    """Split text into chunks respecting document structure.

    Strategy:
    1. Detect headings to understand document structure
    2. Try to split at heading boundaries (keep each section together)
    3. If a section exceeds chunk_size, fall back to paragraph/sentence splits
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    headings = _detect_headings(text)

    # If we found top-level headings, try structure-aware splitting
    if headings:
        return _split_by_structure(text, headings, chunk_size)

    # Fallback: split at natural boundaries
    return _split_by_size(text, chunk_size)


def _split_by_structure(
    text: str, headings: List[Tuple[int, int, str]], chunk_size: int
) -> List[str]:
    """Split by document structure, merging small sections, splitting large ones."""
    # Build sections from headings
    sections: List[Tuple[int, int]] = []  # (start, end) pairs
    for i, (pos, level, _) in enumerate(headings):
        if level <= 2:  # Only split on level 1-2 headings
            end = headings[i + 1][0] if i + 1 < len(headings) else len(text)
            # Find next same-or-higher level heading for end
            next_end = len(text)
            for j in range(i + 1, len(headings)):
                if headings[j][1] <= level:
                    next_end = headings[j][0]
                    break
            sections.append((pos, next_end))

    if not sections:
        return _split_by_size(text, chunk_size)

    # Merge small sections, split large ones
    chunks: List[str] = []
    buffer = ""

    for start, end in sections:
        section_text = text[start:end].strip()
        if not section_text:
            continue

        if len(buffer) + len(section_text) + 2 <= chunk_size:
            buffer = (buffer + "\n\n" + section_text).strip()
        else:
            # Flush buffer
            if buffer:
                chunks.append(buffer)
                buffer = ""

            if len(section_text) <= chunk_size:
                buffer = section_text
            else:
                # Section too large, split it by size
                sub_chunks = _split_by_size(section_text, chunk_size)
                chunks.extend(sub_chunks[:-1])
                buffer = sub_chunks[-1] if sub_chunks else ""

    if buffer.strip():
        chunks.append(buffer.strip())

    # Handle any text before the first heading
    if sections and sections[0][0] > 0:
        preamble = text[: sections[0][0]].strip()
        if preamble:
            if chunks and len(chunks[0]) + len(preamble) + 2 <= chunk_size:
                chunks[0] = preamble + "\n\n" + chunks[0]
            else:
                chunks.insert(0, preamble)

    return chunks if chunks else [text]


def _split_by_size(text: str, chunk_size: int) -> List[str]:
    """Fallback: split at natural boundaries by size."""
    chunks: List[str] = []
    pos = 0
    while pos < len(text):
        if pos + chunk_size >= len(text):
            chunk = text[pos:].strip()
            if chunk:
                chunks.append(chunk)
            break
        split_at = _find_split_point(text, pos, pos + chunk_size)
        chunk = text[pos:split_at].strip()
        if chunk:
            chunks.append(chunk)
        pos = split_at

    return chunks
