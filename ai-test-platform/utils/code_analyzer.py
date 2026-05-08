#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代码解析器 - 扫描代码仓库，提取组件、函数、路由、条件分支等结构化信息

支持语言: Vue/JS, Python, Java
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


# ======== 通用扫描 ========

def scan_code_directory(directory: str, languages: List[str] = None) -> Dict[str, Any]:
    """
    扫描代码目录，自动识别语言并提取结构化信息

    Args:
        directory: 代码目录路径
        languages: 指定语言列表，None=自动检测

    Returns:
        {
            "directory": str,
            "languages_detected": [str],
            "stats": { "total_files": int, "total_lines": int, ... },
            "components": [{ "name", "file", "type", "methods", "fields", ... }],
            "routes": [{ "path", "method", "handler", "file" }],
            "functions": [{ "name", "file", "line", "params", "conditions" }],
            "api_calls": [{ "url", "method", "file", "line" }],
            "conditions": [{ "expression", "file", "line", "context" }],
        }
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"目录不存在: {directory}")

    result = {
        "directory": str(directory),
        "languages_detected": [],
        "stats": {"total_files": 0, "total_lines": 0},
        "components": [],
        "routes": [],
        "functions": [],
        "api_calls": [],
        "conditions": [],
    }

    # 自动检测语言
    ext_map = {
        ".vue": "vue", ".js": "javascript", ".ts": "typescript", ".jsx": "javascript",
        ".py": "python", ".java": "java",
    }
    detected = set()
    files_by_lang = {}

    for root, dirs, files in os.walk(directory):
        # 跳过常见无用目录
        dirs[:] = [d for d in dirs if d not in (
            "node_modules", ".git", "__pycache__", "dist", "build",
            ".idea", ".vscode", "target", "venv", ".env",
        )]
        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext in ext_map:
                lang = ext_map[ext]
                if languages and lang not in languages and ext_map.get(ext) not in languages:
                    continue
                detected.add(lang)
                fpath = os.path.join(root, fname)
                files_by_lang.setdefault(lang, []).append(fpath)

    result["languages_detected"] = sorted(detected)

    # 逐语言解析
    for lang, fpaths in files_by_lang.items():
        for fpath in fpaths:
            try:
                content = _read_file_safe(fpath)
                if content is None:
                    continue
                lines = content.count('\n') + 1
                result["stats"]["total_files"] += 1
                result["stats"]["total_lines"] += lines

                rel_path = os.path.relpath(fpath, directory)

                if lang == "vue":
                    _parse_vue_file(content, rel_path, result)
                elif lang in ("javascript", "typescript"):
                    _parse_js_file(content, rel_path, result)
                elif lang == "python":
                    _parse_python_file(content, rel_path, result)
                elif lang == "java":
                    _parse_java_file(content, rel_path, result)
            except Exception as e:
                print(f"⚠️ 解析文件失败 {fpath}: {e}")

    return result


def _read_file_safe(fpath: str, max_size: int = 500_000) -> Optional[str]:
    """安全读取文件，跳过过大或二进制文件"""
    try:
        size = os.path.getsize(fpath)
        if size > max_size:
            return None
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


# ======== Vue 解析 ========

def _parse_vue_file(content: str, rel_path: str, result: Dict):
    """解析 Vue 单文件组件"""
    comp = {
        "name": Path(rel_path).stem,
        "file": rel_path,
        "type": "vue_component",
        "methods": [],
        "computed": [],
        "watch": [],
        "props": [],
        "data_fields": [],
        "template_conditions": [],
        "api_calls": [],
    }

    # 提取 <script> 部分
    script_match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    script = script_match.group(1) if script_match else ""

    # 提取 <template> 部分
    template_match = re.search(r'<template>(.*?)</template>', content, re.DOTALL)
    template = template_match.group(1) if template_match else ""

    # methods
    methods_block = re.search(r'methods\s*:\s*\{(.*?)\n\s*\}', script, re.DOTALL)
    if methods_block:
        method_names = re.findall(r'(\w+)\s*\(', methods_block.group(1))
        comp["methods"] = method_names

    # 也匹配 setup() / <script setup> 中的函数
    setup_funcs = re.findall(r'(?:const|function)\s+(\w+)\s*=?\s*(?:async\s*)?\(', script)
    if setup_funcs:
        comp["methods"].extend([f for f in setup_funcs if f not in comp["methods"]])

    # computed
    computed_block = re.search(r'computed\s*:\s*\{(.*?)\n\s*\}', script, re.DOTALL)
    if computed_block:
        comp["computed"] = re.findall(r'(\w+)\s*(?:\(|:)', computed_block.group(1))

    # watch
    watch_block = re.search(r'watch\s*:\s*\{(.*?)\n\s*\}', script, re.DOTALL)
    if watch_block:
        comp["watch"] = re.findall(r'[\'"]?(\w+)[\'"]?\s*(?:\(|:)', watch_block.group(1))

    # props
    props_match = re.findall(r'props\s*:\s*[\[\{](.*?)[\]\}]', script, re.DOTALL)
    if props_match:
        comp["props"] = re.findall(r'[\'"](\w+)[\'"]', props_match[0])

    # data fields
    data_match = re.search(r'data\s*\(\)\s*\{?\s*return\s*\{(.*?)\n\s*\}', script, re.DOTALL)
    if data_match:
        comp["data_fields"] = re.findall(r'(\w+)\s*:', data_match.group(1))

    # ref() in setup
    refs = re.findall(r'const\s+(\w+)\s*=\s*ref\(', script)
    comp["data_fields"].extend(refs)

    # v-if / v-show 条件
    conditions = re.findall(r'v-(?:if|else-if|show)="([^"]+)"', template)
    for cond in conditions:
        comp["template_conditions"].append(cond)
        result["conditions"].append({
            "expression": cond,
            "file": rel_path,
            "line": 0,
            "context": "vue_template",
        })

    # 模板中的中文标签（label, placeholder, title 属性 + 纯文本）
    chinese_labels = []
    # 属性值中的中文
    label_attrs = re.findall(
        r'(?:label|placeholder|title|name|header)\s*=\s*["\']([^"\']*[\u4e00-\u9fff][^"\']*)["\']',
        template
    )
    chinese_labels.extend(label_attrs)
    # 标签内的纯中文文本（如 <text>供应商</text>, <span>付款单号</span>）
    tag_texts = re.findall(r'>([^<]*[\u4e00-\u9fff][^<]*)<', template)
    for txt in tag_texts:
        txt = txt.strip()
        if 2 <= len(txt) <= 30 and not re.match(r'^[\s\d.]+$', txt):
            chinese_labels.append(txt)
    # 去重保序
    seen = set()
    unique_labels = []
    for lb in chinese_labels:
        lb = lb.strip()
        if lb and lb not in seen:
            seen.add(lb)
            unique_labels.append(lb)
    comp["chinese_labels"] = unique_labels[:100]

    # API 调用
    api_patterns = [
        r'(?:this\.)?\$(?:http|axios|api|request)\.\s*(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)',
        r'(?:uni|wx)\.request\s*\(\s*\{[^}]*url\s*:\s*[\'"`]([^\'"`]+)',
        r'(?:fetch|axios)\s*\(\s*[\'"`]([^\'"`]+)',
        r'(?:get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)',
    ]
    for pat in api_patterns:
        for m in re.finditer(pat, script):
            groups = m.groups()
            if len(groups) == 2:
                method, url = groups
            else:
                method, url = "unknown", groups[0]
            comp["api_calls"].append({"method": method.upper(), "url": url})
            result["api_calls"].append({
                "url": url, "method": method.upper(),
                "file": rel_path, "line": content[:m.start()].count('\n') + 1,
            })

    result["components"].append(comp)


# ======== JavaScript/TypeScript 解析 ========

def _parse_js_file(content: str, rel_path: str, result: Dict):
    """解析 JS/TS 文件"""
    # 函数
    for m in re.finditer(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', content):
        name, params = m.groups()
        result["functions"].append({
            "name": name, "file": rel_path,
            "line": content[:m.start()].count('\n') + 1,
            "params": [p.strip() for p in params.split(',') if p.strip()],
        })

    # 箭头函数
    for m in re.finditer(r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>', content):
        name, params = m.groups()
        result["functions"].append({
            "name": name, "file": rel_path,
            "line": content[:m.start()].count('\n') + 1,
            "params": [p.strip() for p in params.split(',') if p.strip()],
        })

    # API 调用
    for m in re.finditer(r'(?:fetch|axios)\s*[\.(]\s*[\'"`]([^\'"`]+)', content):
        result["api_calls"].append({
            "url": m.group(1), "method": "unknown",
            "file": rel_path, "line": content[:m.start()].count('\n') + 1,
        })

    # 条件分支
    for m in re.finditer(r'if\s*\(([^)]+)\)', content):
        result["conditions"].append({
            "expression": m.group(1).strip(),
            "file": rel_path,
            "line": content[:m.start()].count('\n') + 1,
            "context": "js_if",
        })


# ======== Python 解析 ========

def _parse_python_file(content: str, rel_path: str, result: Dict):
    """解析 Python 文件"""
    # 类
    for m in re.finditer(r'class\s+(\w+)\s*(?:\([^)]*\))?\s*:', content):
        result["components"].append({
            "name": m.group(1), "file": rel_path,
            "type": "python_class",
            "line": content[:m.start()].count('\n') + 1,
        })

    # 函数/方法
    for m in re.finditer(r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)', content):
        name, params = m.groups()
        line = content[:m.start()].count('\n') + 1
        # 检查装饰器
        decorators = []
        lines_above = content[:m.start()].split('\n')
        for l in reversed(lines_above[-5:]):
            l = l.strip()
            if l.startswith('@'):
                decorators.append(l)
            elif l and not l.startswith('#'):
                break

        func = {
            "name": name, "file": rel_path, "line": line,
            "params": [p.strip().split(':')[0].strip() for p in params.split(',') if p.strip()],
            "decorators": decorators,
        }
        result["functions"].append(func)

        # 路由提取
        for dec in decorators:
            route_match = re.search(r'@(?:app|router)\.\s*(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)', dec)
            if route_match:
                result["routes"].append({
                    "path": route_match.group(2), "method": route_match.group(1).upper(),
                    "handler": name, "file": rel_path,
                })

    # 条件分支
    for m in re.finditer(r'\bif\s+(.+?):', content):
        expr = m.group(1).strip()
        if len(expr) < 200:  # 过滤过长的误匹配
            result["conditions"].append({
                "expression": expr,
                "file": rel_path,
                "line": content[:m.start()].count('\n') + 1,
                "context": "python_if",
            })


# ======== Java 解析 ========

def _parse_java_file(content: str, rel_path: str, result: Dict):
    """解析 Java 文件"""
    # 类
    for m in re.finditer(r'(?:public|private|protected)?\s*class\s+(\w+)', content):
        class_comp = {
            "name": m.group(1), "file": rel_path,
            "type": "java_class",
            "line": content[:m.start()].count('\n') + 1,
            "fields": [],          # 字段列表（含中文标签）
            "chinese_labels": [],  # 所有中文标注（@ApiModelProperty 值）
        }
        result["components"].append(class_comp)

    # 字段级注解提取（@ApiModelProperty + 验证注解）
    _extract_java_fields(content, rel_path, result)

    # 方法
    for m in re.finditer(
        r'(?:public|private|protected)\s+(?:static\s+)?(?:[\w<>\[\]]+)\s+(\w+)\s*\(([^)]*)\)',
        content
    ):
        name, params = m.groups()
        if name in ('if', 'for', 'while', 'switch', 'catch'):
            continue
        line = content[:m.start()].count('\n') + 1
        # 检查注解
        annotations = []
        lines_above = content[:m.start()].split('\n')
        for l in reversed(lines_above[-5:]):
            l = l.strip()
            if l.startswith('@'):
                annotations.append(l)
            elif l and not l.startswith('//') and not l.startswith('*'):
                break

        result["functions"].append({
            "name": name, "file": rel_path, "line": line,
            "params": [p.strip().split()[-1] if p.strip() else '' for p in params.split(',') if p.strip()],
            "annotations": annotations,
        })

        # 路由提取
        for ann in annotations:
            route_match = re.search(
                r'@(?:Get|Post|Put|Delete|Patch|Request)Mapping\s*\(\s*(?:value\s*=\s*)?[\'"]([^\'"]+)',
                ann
            )
            if route_match:
                method = "GET"
                if "Post" in ann: method = "POST"
                elif "Put" in ann: method = "PUT"
                elif "Delete" in ann: method = "DELETE"
                elif "Patch" in ann: method = "PATCH"
                result["routes"].append({
                    "path": route_match.group(1), "method": method,
                    "handler": name, "file": rel_path,
                })

    # 条件分支
    for m in re.finditer(r'if\s*\(([^)]+)\)', content):
        result["conditions"].append({
            "expression": m.group(1).strip(),
            "file": rel_path,
            "line": content[:m.start()].count('\n') + 1,
            "context": "java_if",
        })


def _extract_java_fields(content: str, rel_path: str, result: Dict):
    """
    从 Java 源码中提取字段声明 + @ApiModelProperty 中文标签 + 验证注解。
    将中文标签注入到对应 class component 的 fields / chinese_labels 中。
    """
    # 找所有 @ApiModelProperty("中文") 或 @ApiModelProperty(value="中文")
    api_model_re = re.compile(
        r'@ApiModelProperty\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']',
        re.MULTILINE
    )
    # 字段声明: private Type fieldName;
    field_decl_re = re.compile(
        r'(?:private|protected|public)\s+(?:[\w<>\[\],\s]+?)\s+(\w+)\s*[;=]'
    )
    # 验证注解
    validation_re = re.compile(
        r'@(NotNull|NotBlank|NotEmpty|Size|Min|Max|Digits|Pattern|Email|DecimalMin|DecimalMax)'
    )

    lines = content.split('\n')
    # 找到当前文件对应的 class component
    file_comps = [c for c in result["components"]
                  if c["file"] == rel_path and c["type"] == "java_class"]

    # 逐行扫描，收集字段信息
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # 检测 @ApiModelProperty
        am_match = api_model_re.search(line)
        if am_match:
            chinese_label = am_match.group(1).strip()
            # 向下找字段声明（通常在 1-5 行内）
            field_name = None
            validations = []
            for j in range(i, min(i + 6, len(lines))):
                fline = lines[j].strip()
                vm = validation_re.search(fline)
                if vm:
                    validations.append(vm.group(1))
                fm = field_decl_re.search(fline)
                if fm:
                    field_name = fm.group(1)
                    break

            field_info = {
                "label": chinese_label,
                "field_name": field_name or "",
                "validations": validations,
                "file": rel_path,
                "line": i + 1,
            }

            # 注入到 class component
            if file_comps:
                file_comps[-1]["fields"].append(field_info)
                file_comps[-1]["chinese_labels"].append(chinese_label)

            # 同时加入全局搜索（让 code_items 能索引到中文）
            result.setdefault("java_fields", []).append(field_info)
        i += 1

    # 提取 @ApiModel(description="...") 类描述
    api_model_class_re = re.compile(
        r'@ApiModel\s*\([^)]*(?:description|value)\s*=\s*["\']([^"\']+)["\']'
    )
    for m in api_model_class_re.finditer(content):
        desc = m.group(1).strip()
        if file_comps and desc:
            file_comps[-1].setdefault("description", "")
            file_comps[-1]["description"] = desc


# ======== 汇总工具 ========

def summarize_code_analysis(analysis: Dict) -> str:
    """将代码分析结果汇总为文本摘要（给 AI prompt 用）"""
    lines = []
    lines.append(f"代码目录: {analysis['directory']}")
    lines.append(f"语言: {', '.join(analysis['languages_detected'])}")
    stats = analysis['stats']
    lines.append(f"文件数: {stats['total_files']}, 总行数: {stats['total_lines']}")
    lines.append("")

    if analysis["components"]:
        lines.append(f"## 组件/类 ({len(analysis['components'])})")
        for comp in analysis["components"][:50]:
            name = comp["name"]
            ctype = comp.get("type", "")
            methods = comp.get("methods", [])
            lines.append(f"  - {name} ({ctype}) [{comp['file']}]")
            if methods:
                lines.append(f"    方法: {', '.join(methods[:20])}")
            fields = comp.get("data_fields", [])
            if fields:
                lines.append(f"    数据字段: {', '.join(fields[:20])}")
            conds = comp.get("template_conditions", [])
            if conds:
                lines.append(f"    条件: {', '.join(conds[:10])}")
        lines.append("")

    if analysis["routes"]:
        lines.append(f"## API 路由 ({len(analysis['routes'])})")
        for r in analysis["routes"][:50]:
            lines.append(f"  - {r['method']} {r['path']} → {r['handler']} [{r['file']}]")
        lines.append("")

    if analysis["functions"]:
        lines.append(f"## 函数/方法 ({len(analysis['functions'])})")
        for f in analysis["functions"][:80]:
            decs = f.get("decorators", f.get("annotations", []))
            dec_str = f" {decs[0]}" if decs else ""
            lines.append(f"  - {f['name']}({', '.join(f.get('params', [])[:5])}){dec_str} [{f['file']}:{f['line']}]")
        lines.append("")

    if analysis["api_calls"]:
        lines.append(f"## 外部 API 调用 ({len(analysis['api_calls'])})")
        seen = set()
        for a in analysis["api_calls"][:50]:
            key = f"{a['method']} {a['url']}"
            if key not in seen:
                seen.add(key)
                lines.append(f"  - {key} [{a['file']}]")
        lines.append("")

    if analysis["conditions"]:
        lines.append(f"## 条件分支 ({len(analysis['conditions'])} 个)")
        # 只列前 30 个
        for c in analysis["conditions"][:30]:
            expr = c["expression"][:80]
            lines.append(f"  - if ({expr}) [{c['file']}:{c['line']}]")

    return "\n".join(lines)
