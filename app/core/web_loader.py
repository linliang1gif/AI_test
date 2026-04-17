"""Web page loader for SVN wiki / intranet requirement pages."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)

# Default timeout for HTTP requests (seconds)
_TIMEOUT = 30

# Tags that typically contain navigation / chrome, not content
_STRIP_TAGS = {
    "nav", "header", "footer", "aside", "script", "style", "noscript",
    "iframe", "form", "button", "input", "select", "textarea",
}

# CSS class / id patterns that usually indicate non-content areas
_NOISE_PATTERNS = re.compile(
    r"(sidebar|menu|nav|footer|header|breadcrumb|toolbar|topbar|banner|ads|cookie)",
    re.IGNORECASE,
)


@dataclass
class WebPage:
    """Represents a fetched and cleaned web page."""
    url: str
    title: str
    text: str
    encoding: str = "utf-8"


def fetch_page(
    url: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    cookies: Optional[dict] = None,
    timeout: int = _TIMEOUT,
) -> WebPage:
    """Fetch a URL and return cleaned text content.

    Supports:
    - Basic auth (SVN / intranet)
    - Cookie-based auth
    - Auto-detection of Chinese encodings (gb2312 / gbk / utf-8)
    """
    auth = (username, password) if username else None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    resp = requests.get(
        url, auth=auth, cookies=cookies, headers=headers,
        timeout=timeout, verify=False,
    )
    resp.raise_for_status()

    # Detect encoding
    encoding = _detect_encoding(resp)
    resp.encoding = encoding
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    title = _extract_title(soup, url)
    text = _extract_content(soup)

    if not text.strip():
        # Fallback: just get all visible text
        text = soup.get_text(separator="\n", strip=True)

    return WebPage(url=url, title=title, text=text, encoding=encoding)


def fetch_multiple(
    urls: List[str],
    username: Optional[str] = None,
    password: Optional[str] = None,
    cookies: Optional[dict] = None,
    on_progress: Optional[callable] = None,
) -> List[WebPage]:
    """Fetch multiple URLs, returning results and skipping failures."""
    pages: List[WebPage] = []
    for i, url in enumerate(urls, 1):
        if on_progress:
            on_progress(f"🌐 [{i}/{len(urls)}] 正在获取：{url}")
        try:
            page = fetch_page(url, username, password, cookies)
            if on_progress:
                on_progress(f"   ✅ {page.title} ({len(page.text)} 字符)")
            pages.append(page)
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", url, e)
            if on_progress:
                on_progress(f"   ❌ 获取失败：{e}")
    return pages


def _detect_encoding(resp: requests.Response) -> str:
    """Detect encoding from HTTP headers and HTML meta tags."""
    # Check Content-Type header
    ct = resp.headers.get("Content-Type", "")
    ct_lower = ct.lower()
    for enc in ("gb2312", "gbk", "gb18030", "utf-8", "big5"):
        if enc in ct_lower:
            return enc

    # Check HTML meta charset
    raw = resp.content[:4096]
    raw_str = raw.decode("ascii", errors="replace").lower()

    charset_match = re.search(r'charset=["\']?([a-zA-Z0-9_-]+)', raw_str)
    if charset_match:
        detected = charset_match.group(1).lower()
        # Normalize
        if detected in ("gb2312", "gbk", "gb18030"):
            return "gbk"  # gbk is superset
        return detected

    # Try decoding with common Chinese encodings
    for enc in ("utf-8", "gbk", "gb2312"):
        try:
            resp.content.decode(enc)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue

    return "utf-8"


def _extract_title(soup: BeautifulSoup, url: str) -> str:
    """Extract page title."""
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    # Use last part of URL path
    path = urlparse(url).path.rstrip("/")
    return path.split("/")[-1] if path else url


def _extract_content(soup: BeautifulSoup) -> str:
    """Extract main content from HTML, stripping navigation and noise."""
    # Remove comments
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # Remove noise tags
    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove elements with noisy class/id
    for tag in soup.find_all(True):
        classes = " ".join(tag.get("class", []))
        tag_id = tag.get("id", "")
        if _NOISE_PATTERNS.search(classes) or _NOISE_PATTERNS.search(tag_id):
            tag.decompose()

    # Try to find main content area
    content_area = None
    for selector in ["main", "article", '[role="main"]', "#content", ".content",
                     "#wiki-body", ".wiki-body", "#main-content", ".main-content",
                     "#svn-content", ".svn-content", "#page-content"]:
        content_area = soup.select_one(selector)
        if content_area:
            break

    target = content_area or soup.body or soup

    # Build structured text
    lines: List[str] = []
    _walk(target, lines)

    return "\n".join(lines)


def _walk(element, lines: List[str]) -> None:
    """Recursively walk DOM and build structured text."""
    if element.name in ("table",):
        _extract_table(element, lines)
        return

    for child in element.children:
        if isinstance(child, str):
            text = child.strip()
            if text:
                lines.append(text)
        elif hasattr(child, "name"):
            if child.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                level = int(child.name[1])
                prefix = "#" * level
                lines.append(f"\n{prefix} {child.get_text(strip=True)}\n")
            elif child.name in ("p", "div", "section"):
                _walk(child, lines)
                lines.append("")
            elif child.name in ("ul", "ol"):
                _extract_list(child, lines)
            elif child.name == "table":
                _extract_table(child, lines)
            elif child.name == "br":
                lines.append("")
            elif child.name in ("pre", "code"):
                lines.append(f"```\n{child.get_text()}\n```")
            elif child.name in _STRIP_TAGS:
                continue
            else:
                _walk(child, lines)


def _extract_list(element, lines: List[str], indent: int = 0) -> None:
    """Extract list items."""
    prefix = "  " * indent
    for li in element.find_all("li", recursive=False):
        text = li.get_text(strip=True)
        if text:
            lines.append(f"{prefix}• {text}")
        # Nested lists
        for sub in li.find_all(["ul", "ol"], recursive=False):
            _extract_list(sub, lines, indent + 1)


def _extract_table(table, lines: List[str]) -> None:
    """Extract table as pipe-separated text."""
    lines.append("")
    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all(["th", "td"])
        row_text = " | ".join(cell.get_text(strip=True) for cell in cells)
        if row_text.strip():
            lines.append(f"| {row_text} |")
    lines.append("")
