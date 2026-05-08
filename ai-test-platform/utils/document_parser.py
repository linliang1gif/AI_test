#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档解析工具
支持解析多种文档格式: .docx, .txt, .md, .pdf, .html/.htm
"""

from pathlib import Path
from typing import Optional, Dict, List, Any
import os
import re
import json


def parse_document(file_path: str) -> str:
    """
    解析文档内容
    
    Args:
        file_path: 文档文件路径
    
    Returns:
        文档文本内容
    
    Raises:
        ValueError: 不支持的文件类型
        Exception: 解析失败
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    file_ext = file_path.suffix.lower()
    
    # 根据文件类型选择解析方法
    if file_ext == '.txt':
        return _parse_txt(file_path)
    elif file_ext == '.md':
        return _parse_markdown(file_path)
    elif file_ext in ['.docx', '.doc']:
        return _parse_docx(file_path)
    elif file_ext == '.pdf':
        return _parse_pdf(file_path)
    elif file_ext in ['.html', '.htm']:
        return _parse_html(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {file_ext}")


def _parse_txt(file_path: Path) -> str:
    """解析 TXT 文件"""
    try:
        # 尝试多种编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✅ TXT 文件解析成功 (编码: {encoding})")
                return content
            except UnicodeDecodeError:
                continue
        
        raise Exception("无法识别文件编码")
    
    except Exception as e:
        raise Exception(f"TXT 文件解析失败: {e}")


def _parse_markdown(file_path: Path) -> str:
    """解析 Markdown 文件"""
    try:
        # Markdown 文件通常是 UTF-8 编码
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ Markdown 文件解析成功")
        return content
    
    except Exception as e:
        # 尝试其他编码
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
            print(f"✅ Markdown 文件解析成功 (编码: gbk)")
            return content
        except:
            raise Exception(f"Markdown 文件解析失败: {e}")


def _parse_docx(file_path: Path) -> str:
    """解析 DOCX 文件"""
    try:
        from docx import Document
        
        doc = Document(file_path)
        
        # 提取所有段落文本
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        
        # 提取表格内容
        tables_text = []
        for table in doc.tables:
            for row in table.rows:
                row_text = ' | '.join([cell.text.strip() for cell in row.cells])
                if row_text.strip():
                    tables_text.append(row_text)
        
        # 合并所有内容
        content = '\n'.join(paragraphs)
        if tables_text:
            content += '\n\n表格内容:\n' + '\n'.join(tables_text)
        
        print(f"✅ DOCX 文件解析成功 (段落: {len(paragraphs)}, 表格: {len(doc.tables)})")
        return content
    
    except ImportError:
        raise Exception("缺少 python-docx 库，请安装: pip install python-docx")
    except Exception as e:
        raise Exception(f"DOCX 文件解析失败: {e}")


def _parse_pdf(file_path: Path) -> str:
    """解析 PDF 文件"""
    try:
        import PyPDF2
        
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            # 提取所有页面文本
            text_parts = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)
            
            content = '\n'.join(text_parts)
            
            print(f"✅ PDF 文件解析成功 (页数: {len(pdf_reader.pages)})")
            return content
    
    except ImportError:
        raise Exception("缺少 PyPDF2 库，请安装: pip install PyPDF2")
    except Exception as e:
        raise Exception(f"PDF 文件解析失败: {e}")


def get_document_info(file_path: str) -> dict:
    """
    获取文档信息
    
    Args:
        file_path: 文档文件路径
    
    Returns:
        文档信息字典
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {"error": "文件不存在"}
    
    file_stat = file_path.stat()
    
    return {
        "name": file_path.name,
        "extension": file_path.suffix,
        "size_bytes": file_stat.st_size,
        "size_mb": round(file_stat.st_size / 1024 / 1024, 2),
        "modified_time": file_stat.st_mtime,
    }


# ==================== HTML 解析 ====================

def _read_html_content(file_path: Path) -> str:
    """读取 HTML 文件内容，自动检测编码"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    # fallback: 二进制读取
    with open(file_path, 'rb') as f:
        return f.read().decode('utf-8', errors='ignore')


def _is_axure_html(html_content: str) -> bool:
    """检测是否为 Axure 导出的 HTML"""
    axure_markers = [
        'data-label=', 'axure', 'sitemap.htm', 'Axure',
        'document.axure', 'axureData', '$axure',
    ]
    return any(marker in html_content for marker in axure_markers)


def _parse_axure_datajs(file_path: Path) -> List[Dict[str, Any]]:
    """解析 Axure data.js 文件，提取页面注释和标签（支持混淆变量格式）"""
    results = []
    parent = file_path.parent if file_path.is_file() else file_path
    datajs_candidates = list(parent.rglob('data.js')) + list(parent.rglob('data.js.*'))

    for datajs_path in datajs_candidates:
        try:
            content = _read_html_content(datajs_path)
            results.extend(_extract_axure_annotations(content, datajs_path.name))
        except Exception as e:
            print(f"  Axure data.js 解析警告: {e}")
            continue

    return results


# ══════════════════════════════════════════════════════════════════
#  Axure type='label' 文本启发式分类（避免演示数据进入需求点）
#  带来的问题：Axure 原型中的“¥12303.33”、“待审核”、“(下拉列表)”会被需求-代码对比
#  误判为 missing。本分类器在解析阶段就把他们从 features 中过滤掉。
# ══════════════════════════════════════════════════════════════════

# 常见控件类型（noise）
_AXURE_WIDGET_TYPES = (
    '下拉列表', '文本框', '矩形', '矩形按钮', '按钮', '复选框', '单选框',
    '图片', '图标', '形状', '圆形', '椭圆', '链接', '图像', '文本',
    '占位符', '热区', '动态面板', '中继器', '内联框架', '表格', '面板',
)

# 演示用人名占位
_DEMO_PERSONS = {
    '张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十',
    'test', 'demo', 'sample', 'example',
}

# 演示状态/选项短词（精确匹配）
_DEMO_STATUS_WORDS = {
    '待审核', '已审核', '审核中', '审核通过', '审核拒绝', '审核不通过',
    '草稿', '已提交', '已驳回', '已过期', '已完成', '已取消', '处理中',
    '待处理', '待开票', '已开票', '已支付', '待支付', '已收款', '待收款',
    '是', '否',  # 单个布尔短词
}

# 业务规则关键词（与 parse_axure_folder_structured 中一致）
_RULE_KEYWORDS_RE = re.compile(
    r'(必须|不能|不得|限制|校验|验证|范围|最大|最小|不超过|至少|'
    r'当.*时|如果.*则|若.*则|规则|约束|条件|支持|默认)',
    re.IGNORECASE,
)

# 金额：¥ / $ / ￥ + 数字（含小数）；或纯数字带单位后缀
_DEMO_AMOUNT_RE = re.compile(
    r'^\s*[¥$￥]\s*[\d,]+(\.\d+)?\s*$|'
    r'^\s*[\d,]+(\.\d+)?\s*(KG|kg|元|件|个|岁|%)\s*$'
)

# 日期：YYYY-MM-DD / YYYY/MM/DD / YYYY年MM月DD日（可带时间）
_DEMO_DATE_RE = re.compile(
    r'^\s*\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?'
    r'(\s+\d{1,2}[:：]\d{1,2}([:：]\d{1,2})?)?\s*$'
)

# 时间：HH:MM 或 HH:MM:SS
_DEMO_TIME_RE = re.compile(r'^\s*\d{1,2}[:：]\d{1,2}([:：]\d{1,2})?\s*$')

# 订单号格式：2-5 个大写字母 + 6-20 位数字
_DEMO_ORDER_NO_RE = re.compile(r'^\s*[A-Z]{2,5}\d{6,20}\s*$')

# 纯数字串：整数 ≥4 位 OR 整数 ≥1 位 + 小数 ≥2 位（典型金额演示值如 123.03 / 5.50）
_DEMO_PURE_NUMBER_RE = re.compile(
    r'^\s*[\d,]{4,}(\.\d+)?\s*$|'
    r'^\s*\d+\.\d{2,}\s*$'
)

# 控件类型整体匹配：(下拉列表) / （矩形）
_AXURE_WIDGET_BRACKET_RE = re.compile(
    r'^\s*[\(（]\s*(' + '|'.join(_AXURE_WIDGET_TYPES) + r')\s*[\)）]\s*$'
)

# 纯标点 / 单字符
_PUNCT_ONLY_RE = re.compile(r'^[\s\W_]{1,3}$')


def _classify_axure_label_text(content: str) -> str:
    """对 Axure type='label' 元件文本做四分类。

    Returns:
        "noise"      : 纯标点 / 控件类型标记 / 长度 <= 1
        "demo_value" : 金额 / 日期 / 时间 / 订单号 / 演示状态 / 演示人名 / 纯数字
        "rule"       : 含业务规则关键词
        "field_name" : 其他（默认；保守保留作为字段名候选）
    """
    if not content:
        return "noise"
    s = content.strip()
    if not s:
        return "noise"
    # ── 1) noise ──
    if len(s) <= 1:
        return "noise"
    if _PUNCT_ONLY_RE.match(s):
        return "noise"
    if _AXURE_WIDGET_BRACKET_RE.match(s):
        return "noise"
    # ── 2) demo_value ──
    if _DEMO_AMOUNT_RE.match(s):
        return "demo_value"
    if _DEMO_DATE_RE.match(s):
        return "demo_value"
    if _DEMO_TIME_RE.match(s):
        return "demo_value"
    if _DEMO_ORDER_NO_RE.match(s):
        return "demo_value"
    if _DEMO_PURE_NUMBER_RE.match(s):
        return "demo_value"
    if s in _DEMO_PERSONS:
        return "demo_value"
    if s in _DEMO_STATUS_WORDS:
        return "demo_value"
    # ── 3) rule ──
    if _RULE_KEYWORDS_RE.search(s):
        return "rule"
    # ── 4) field_name (default) ──
    return "field_name"


def _extract_axure_annotations(content: str, source_name: str = 'data.js') -> List[Dict[str, Any]]:
    """从 Axure data.js 内容中提取注释，支持两种格式：
    1. 标准 JSON 格式: "label": "xxx", "说明": "xxx"
    2. 混淆变量格式: var G="label", H="(下拉列表)", I="说明", J="<p>..."
    """
    results = []
    seen = set()

    # === 方法1: 混淆变量格式（Axure 9+ 导出）===
    # 解析 var 声明，建立变量名→值映射
    # Axure data.js 通常把所有 var 声明压缩在一行，直接全文扫描赋值
    var_map = {}
    pair_pattern = re.compile(r'(?:^|,|\s)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"((?:[^"\\]|\\.)*)"')
    for pm in pair_pattern.finditer(content):
        var_map[pm.group(1)] = pm.group(2)

    # 查找 annotations 数组中的 label+说明 配对
    # 格式: _(C,"1",E,"ownerId",G,"(下拉列表)",I,"支持筛选...")
    # 其中 C=fn, G=label, I=说明
    label_var = None
    desc_var = None
    fn_var = None
    for k, v in var_map.items():
        if v == 'label':
            label_var = k
        elif v == '说明' or v == 'description':
            desc_var = k
        elif v == 'fn':
            fn_var = k

    # 从 annotations 数组结构推断 label 和 desc 的位置变量
    # 格式: B,[_(C,D,E,F,G,H,I,J), ...] 即 _(fn, fn_val, key1, val1, key2, val2, key3, val3)
    # 找到第一个 annotation 块，用 var_map 解析每个 key 的含义
    anno_fn = fn_var or 'C'
    anno_pattern = re.compile(
        r'_\(' + re.escape(anno_fn) + r',([^)]+)\)',
        re.DOTALL
    )

    # 从第一个 annotation 推断 label_pos 和 desc_pos（基于 token 位置）
    label_pos = None  # index in tokens where label value is
    desc_pos = None   # index in tokens where desc value is
    first_match = anno_pattern.search(content)
    if first_match:
        tokens = [t.strip() for t in first_match.group(1).split(',')]
        # tokens: [fn_val, key1, val1, key2, val2, key3, val3]
        for idx in range(1, len(tokens) - 1, 2):
            key_name = tokens[idx].strip()
            resolved = var_map.get(key_name, key_name)
            if resolved == 'label':
                label_pos = idx + 1  # value is next token
            elif resolved in ('说明', 'description'):
                desc_pos = idx + 1

    if label_pos is not None:
        for m in anno_pattern.finditer(content):
            block = m.group(1)
            tokens = [t.strip() for t in block.split(',')]

            def _resolve(tok):
                if tok.startswith('"') and tok.endswith('"'):
                    return tok[1:-1]
                return var_map.get(tok, tok)

            label_text = _resolve(tokens[label_pos]).strip() if label_pos < len(tokens) else ''
            desc_text = _resolve(tokens[desc_pos]).strip() if desc_pos is not None and desc_pos < len(tokens) else ''

            # 清理 HTML 标签
            if desc_text:
                desc_text = re.sub(r'<[^>]+>', '', desc_text).strip()
            if label_text:
                label_text = re.sub(r'<[^>]+>', '', label_text).strip()

            if label_text and desc_text and desc_text not in seen:
                seen.add(desc_text)
                results.append({
                    'type': 'annotation',
                    'label': label_text,
                    'content': desc_text,
                    'source': source_name
                })
            elif label_text and label_text not in seen:
                seen.add(label_text)
                results.append({
                    'type': 'label',
                    'content': label_text,
                    'source': source_name
                })

    # === 方法2: 标准 JSON 格式 ===
    note_pattern = re.compile(r'"note"\s*:\s*"((?:[^"\\]|\\.)*)"', re.DOTALL)
    for m in note_pattern.finditer(content):
        note_text = m.group(1).replace('\\n', '\n').replace('\\"', '"').strip()
        note_text = re.sub(r'<[^>]+>', '', note_text).strip()
        if note_text and len(note_text) > 2 and note_text not in seen:
            seen.add(note_text)
            results.append({'type': 'note', 'content': note_text, 'source': source_name})

    label_pattern = re.compile(r'"label"\s*:\s*"((?:[^"\\]|\\.)*)"', re.DOTALL)
    for m in label_pattern.finditer(content):
        label_text = m.group(1).strip()
        if label_text and len(label_text) > 1 and label_text not in seen:
            seen.add(label_text)
            results.append({'type': 'label', 'content': label_text, 'source': source_name})

    return results


def parse_axure_folder(folder_path: str) -> str:
    """解析 Axure 导出的文件夹（_files 目录），提取所有需求注释

    Args:
        folder_path: Axure 导出文件夹路径，如 G:\\需求\\付款单-企业小程序_v1.2.3_files

    Returns:
        结构化纯文本
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        raise ValueError(f"路径不是目录: {folder_path}")

    sections = []
    page_name = folder.name.replace('_files', '').replace('_', ' ')
    sections.append(f"# {page_name}\n")

    # 1. 解析 data.js
    annotations = _parse_axure_datajs(folder)
    notes = [a for a in annotations if a['type'] in ('note', 'annotation')]
    labels = [a for a in annotations if a['type'] == 'label']

    if notes:
        sections.append("## 需求注释/说明")
        for n in notes:
            if n['type'] == 'annotation':
                sections.append(f"- 【{n.get('label', '')}】{n['content']}")
            else:
                sections.append(f"- {n['content']}")

    if labels:
        sections.append("\n## 控件标签")
        for lb in labels:
            sections.append(f"- {lb['content']}")

    # 2. 解析 HTML 文件中的可见文本
    html_files = list(folder.glob('*.html')) + list(folder.glob('*.htm'))
    for hf in html_files:
        try:
            from bs4 import BeautifulSoup
            html_content = _read_html_content(hf)
            soup = BeautifulSoup(html_content, 'html.parser')
            # 提取可见文本
            for script in soup(['script', 'style']):
                script.decompose()
            text = soup.get_text(separator='\n', strip=True)
            lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 2]
            if lines:
                sections.append(f"\n## 页面文本 ({hf.name})")
                seen_lines = set()
                for line in lines[:200]:  # 限制行数
                    if line not in seen_lines:
                        seen_lines.add(line)
                        sections.append(f"- {line}")
        except Exception:
            continue

    content = '\n'.join(sections)
    stats = {
        'annotations': len(notes),
        'labels': len(labels),
        'html_files': len(html_files),
        'total_chars': len(content),
    }
    print(f"  Axure 文件夹解析成功: {stats}")
    return content


def parse_axure_folder_structured(folder_path: str) -> Dict[str, Any]:
    """结构化解析 Axure 文件夹，返回分层结果"""
    folder = Path(folder_path)
    if not folder.is_dir():
        raise ValueError(f"路径不是目录: {folder_path}")

    raw_text = parse_axure_folder(folder_path)
    annotations = _parse_axure_datajs(folder)

    result = {
        "raw_text": raw_text,
        "modules": [{"name": folder.name.replace('_files', ''), "level": 1}],
        "features": [],
        "rules": [],
        "fields": [],
        "axure_notes": [],
        "demo_values": [],   # D2-2: type='label' 中被识别为演示数据/噪声的项不下游
        "stats": {
            "total_chars": len(raw_text),
            "file_type": "axure_folder",
            "is_axure": True,
        }
    }

    rule_keywords = re.compile(
        r'(必须|不能|不得|限制|校验|验证|范围|最大|最小|不超过|至少|'
        r'当.*时|如果.*则|若.*则|规则|约束|条件|支持|默认)',
        re.IGNORECASE
    )

    for a in annotations:
        content = a['content']
        if a['type'] == 'annotation':
            label = a.get('label', '')
            label_kind = _classify_axure_label_text(label)
            # D2-3: annotation 不再进 axure_notes（避免与 features 内容重复 +
            # 避免 【演示值】content 形式污染需求点拆点链）。axure_notes 留给
            # type='note'（用户在 Axure 里手写的真正需求注释）。raw_text 仍由
            # parse_axure_folder() 单独生成 【label】content 拼接供 AI 上下文。
            #
            # D2-2: 对 annotation.label 做四分类：
            #   field_name/rule → label 进 features
            #   demo_value/noise → content 进 features，原 label 进 demo_values
            if label_kind in ("field_name", "rule"):
                if rule_keywords.search(content):
                    # 字段名/规则：rules 保留 【label】content 标准格式
                    result["rules"].append(f"【{label}】{content}")
                src = "axure_annotation" if label_kind == "field_name" else "axure_annotation_rule"
                result["features"].append({"name": label, "source": src})
            else:
                if rule_keywords.search(content):
                    # demo/noise：rules 不带 【演示值】 前缀，仅用 content
                    result["rules"].append(content)
                if content and content.strip():
                    result["features"].append({
                        "name": content.strip()[:80],
                        "source": "axure_annotation_desc",
                        "_demo_label": label,
                    })
                if label:
                    result["demo_values"].append(label)
            # 识别字段（行为不变；只看 label 是否含表单元件类型词）
            field_markers = ['文本框', '下拉列表', '输入', '选择', '日期']
            if any(m in label for m in field_markers):
                result["fields"].append({"name": label, "type": "input", "required": False})
        elif a['type'] == 'note':
            result["axure_notes"].append(content)
            if rule_keywords.search(content):
                result["rules"].append(content)
        elif a['type'] == 'label':
            # D2-2: 对 type='label' 做四分类，演示值/噪声不进 features
            kind = _classify_axure_label_text(content)
            if kind == "field_name":
                result["features"].append({"name": content, "source": "axure_label"})
            elif kind == "rule":
                result["rules"].append(content)
                # rule 同时以 axure_label_rule 身份进 features，保证 AI prompt 也能看到
                result["features"].append({"name": content, "source": "axure_label_rule"})
            else:
                # demo_value / noise → 仅记在 demo_values，不作为需求点下游
                result["demo_values"].append(content)

    result["stats"]["modules"] = len(result["modules"])
    result["stats"]["features"] = len(result["features"])
    result["stats"]["rules"] = len(result["rules"])
    result["stats"]["fields"] = len(result["fields"])
    result["stats"]["axure_notes"] = len(result["axure_notes"])
    result["stats"]["demo_values"] = len(result["demo_values"])

    return result


def _parse_html(file_path: Path) -> str:
    """解析 HTML 文件，支持普通 HTML 和 Axure 导出"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise Exception("缺少 beautifulsoup4 库，请安装: pip install beautifulsoup4")

    try:
        raw_html = _read_html_content(file_path)
        is_axure = _is_axure_html(raw_html)
        soup = BeautifulSoup(raw_html, 'html.parser')

        sections = []

        # --- 第1层: 标题 (页面/模块) ---
        headings = []
        for tag in soup.find_all(re.compile(r'^h[1-6]$')):
            text = tag.get_text(strip=True)
            if text:
                level = int(tag.name[1])
                headings.append((level, text))
        if headings:
            sections.append("## 页面/模块结构")
            for level, text in headings:
                indent = "  " * (level - 1)
                sections.append(f"{indent}- {text}")

        # --- 第2层: 段落和列表 (功能描述) ---
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text and len(text) > 3:
                paragraphs.append(text)
        lists = []
        for li in soup.find_all('li'):
            text = li.get_text(strip=True)
            if text and len(text) > 2:
                lists.append(text)
        if paragraphs:
            sections.append("\n## 功能描述")
            for p_text in paragraphs:
                sections.append(f"- {p_text}")
        if lists:
            sections.append("\n## 列表项")
            for li_text in lists:
                sections.append(f"- {li_text}")

        # --- 第3层: 表格 (字段/规则) ---
        tables_data = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if any(c for c in cells):
                    rows.append(cells)
            if rows:
                tables_data.append(rows)
        if tables_data:
            sections.append("\n## 表格内容")
            for table_rows in tables_data:
                for row in table_rows:
                    sections.append(" | ".join(row))
                sections.append("")

        # --- 第4层: 表单字段 ---
        form_fields = []
        for inp in soup.find_all(['input', 'select', 'textarea']):
            name = inp.get('name') or inp.get('placeholder') or inp.get('id') or ''
            inp_type = inp.get('type', 'text')
            required = 'required' if inp.get('required') is not None else 'optional'
            if name:
                form_fields.append(f"{name} (type={inp_type}, {required})")
        for label in soup.find_all('label'):
            text = label.get_text(strip=True)
            if text and text not in [f.split(' ')[0] for f in form_fields]:
                form_fields.append(f"{text} (label)")
        if form_fields:
            sections.append("\n## 表单字段")
            for f in form_fields:
                sections.append(f"- {f}")

        # --- 第5层: Axure 专用提取 ---
        axure_items = []
        if is_axure:
            axure_items = _parse_axure_datajs(file_path)

            # 也提取页面内的 Axure 注释面板
            for div in soup.find_all(['div', 'span'], attrs={'data-label': True}):
                label = div.get('data-label', '').strip()
                if label:
                    axure_items.append({'type': 'label', 'content': label, 'source': 'html'})
            for div in soup.find_all(['div', 'span'], class_=re.compile(r'note|annotation|comment', re.I)):
                text = div.get_text(strip=True)
                if text and len(text) > 3:
                    axure_items.append({'type': 'note', 'content': text, 'source': 'html'})

        if axure_items:
            notes = [it for it in axure_items if it['type'] == 'note']
            labels = [it for it in axure_items if it['type'] == 'label']
            if notes:
                sections.append("\n## Axure 注释 (需求说明)")
                seen = set()
                for n in notes:
                    if n['content'] not in seen:
                        seen.add(n['content'])
                        sections.append(f"- {n['content']}")
            if labels:
                sections.append("\n## Axure 控件标签")
                seen = set()
                for lb in labels:
                    if lb['content'] not in seen:
                        seen.add(lb['content'])
                        sections.append(f"- {lb['content']}")

        content = '\n'.join(sections)

        # 统计
        stats = {
            'headings': len(headings),
            'paragraphs': len(paragraphs),
            'lists': len(lists),
            'tables': len(tables_data),
            'form_fields': len(form_fields),
            'axure_notes': len([it for it in axure_items if it['type'] == 'note']),
            'axure_labels': len([it for it in axure_items if it['type'] == 'label']),
            'is_axure': is_axure,
        }
        print(f"  HTML 解析成功: {stats}")

        return content

    except Exception as e:
        if 'beautifulsoup4' in str(e) or 'bs4' in str(e):
            raise
        raise Exception(f"HTML 文件解析失败: {e}")


def parse_document_structured(file_path: str) -> Dict[str, Any]:
    """
    结构化解析文档，返回分层结果（用于前端预览确认）

    Returns:
        {
            "raw_text": str,        # 完整纯文本
            "modules": [...],       # 模块列表
            "features": [...],      # 功能点列表
            "rules": [...],         # 业务规则
            "fields": [...],        # 表单字段
            "axure_notes": [...],   # Axure 注释
            "stats": {...},         # 统计信息
        }
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    ext = file_path.suffix.lower()

    # 获取纯文本
    raw_text = parse_document(str(file_path))

    result = {
        "raw_text": raw_text,
        "modules": [],
        "features": [],
        "rules": [],
        "fields": [],
        "axure_notes": [],
        "stats": {
            "total_chars": len(raw_text),
            "file_type": ext,
        }
    }

    # 对 HTML 做额外结构化
    if ext in ['.html', '.htm']:
        try:
            from bs4 import BeautifulSoup
            html_content = _read_html_content(file_path)
            soup = BeautifulSoup(html_content, 'html.parser')

            # 模块 (h1-h3)
            for tag in soup.find_all(re.compile(r'^h[1-3]$')):
                text = tag.get_text(strip=True)
                if text:
                    result["modules"].append({"name": text, "level": int(tag.name[1])})

            # 功能点 (h4-h6, strong, b)
            for tag in soup.find_all(re.compile(r'^h[4-6]$')):
                text = tag.get_text(strip=True)
                if text:
                    result["features"].append({"name": text, "source": "heading"})
            for li in soup.find_all('li'):
                text = li.get_text(strip=True)
                if text and len(text) > 5:
                    result["features"].append({"name": text, "source": "list"})

            # 业务规则 (含关键词的段落)
            rule_keywords = re.compile(
                r'(必须|不能|不得|限制|校验|验证|范围|最大|最小|不超过|至少|'
                r'当.*时|如果.*则|若.*则|规则|约束|条件)',
                re.IGNORECASE
            )
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if text and rule_keywords.search(text):
                    result["rules"].append(text)

            # 表单字段
            for inp in soup.find_all(['input', 'select', 'textarea']):
                name = inp.get('name') or inp.get('placeholder') or inp.get('id') or ''
                if name:
                    result["fields"].append({
                        "name": name,
                        "type": inp.get('type', 'text'),
                        "required": inp.get('required') is not None
                    })

            # Axure 注释
            if _is_axure_html(html_content):
                for item in _parse_axure_datajs(file_path):
                    if item['type'] == 'note':
                        result["axure_notes"].append(item['content'])

        except ImportError:
            pass
    else:
        # 对非 HTML 文件，用正则从纯文本中提取模块和规则
        lines = raw_text.split('\n')
        for line in lines:
            line = line.strip()
            # Markdown 标题 → 模块
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                if title and level <= 3:
                    result["modules"].append({"name": title, "level": level})
                elif title:
                    result["features"].append({"name": title, "source": "heading"})

    result["stats"]["modules"] = len(result["modules"])
    result["stats"]["features"] = len(result["features"])
    result["stats"]["rules"] = len(result["rules"])
    result["stats"]["fields"] = len(result["fields"])
    result["stats"]["axure_notes"] = len(result["axure_notes"])

    return result
