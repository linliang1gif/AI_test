#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档解析工具
支持解析多种文档格式: .docx, .txt, .md, .pdf
"""

from pathlib import Path
from typing import Optional
import os


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
