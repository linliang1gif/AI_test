#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAPD 对接服务

提供:
  - TAPD 配置管理（workspace_id, api_user, api_password）
  - 推送缺陷到 TAPD
  - 查询 TAPD 缺陷状态

TAPD Open API 文档: https://www.tapd.cn/help/show#1120003271001000708
"""

import json
import re as _re
import time
from pathlib import Path
from typing import Optional, Dict, Any

import requests

# ── 配置文件路径 ──
TAPD_CONFIG_DIR = Path("data/tapd")
TAPD_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
TAPD_CONFIG_FILE = TAPD_CONFIG_DIR / "config.json"


def load_tapd_config() -> Dict[str, Any]:
    """加载 TAPD 配置"""
    if TAPD_CONFIG_FILE.exists():
        try:
            return json.loads(TAPD_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_tapd_config(config: Dict[str, Any]):
    """保存 TAPD 配置"""
    TAPD_CONFIG_FILE.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def test_tapd_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """测试 TAPD 连接是否正常"""
    workspace_id = config.get("workspace_id", "")
    api_user = config.get("api_user", "")
    api_password = config.get("api_password", "")

    if not all([workspace_id, api_user, api_password]):
        return {"success": False, "message": "请填写完整的 TAPD 配置"}

    try:
        # 用 /bugs/count 接口测试连接（在"项目协作"权限范围内）
        resp = requests.get(
            "https://api.tapd.cn/bugs/count",
            params={"workspace_id": workspace_id},
            auth=(api_user, api_password),
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == 1:
                bug_count = data.get("data", {}).get("count", 0)
                return {"success": True, "message": f"连接成功！项目当前有 {bug_count} 个缺陷"}
            else:
                return {"success": False, "message": f"TAPD 返回错误: {data.get('info', '未知')}"}
        elif resp.status_code == 401:
            return {"success": False, "message": "认证失败: API 账号或密码错误"}
        elif resp.status_code == 403:
            return {"success": False, "message": "权限不足: 请确认 API 账号有「缺陷」读写权限，且空间ID正确"}
        else:
            return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except requests.exceptions.Timeout:
        return {"success": False, "message": "连接超时，请检查网络"}
    except Exception as e:
        return {"success": False, "message": f"连接异常: {str(e)}"}


# ── TAPD 严重程度映射 ──
SEVERITY_MAP = {
    "critical": "fatal",     # TAPD: fatal/serious/normal/prompt/advice
    "major": "serious",
    "minor": "normal",
    "trivial": "prompt",
}

# ── TAPD 优先级映射 ──
PRIORITY_MAP = {
    "P0": "urgent",          # TAPD: urgent/high/medium/low/insignificant
    "P1": "high",
    "P2": "medium",
    "P3": "low",
}


def push_bug_to_tapd(
    config: Dict[str, Any],
    title: str,
    description: str,
    severity: str = "major",
    priority: str = "P2",
    module: str = "",
    reporter: str = "",
    extra_fields: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    推送缺陷到 TAPD

    Returns:
        {"success": True, "bug_id": "xxx", "url": "https://www.tapd.cn/..."}
        or {"success": False, "message": "error detail"}
    """
    workspace_id = config.get("workspace_id", "")
    api_user = config.get("api_user", "")
    api_password = config.get("api_password", "")

    if not all([workspace_id, api_user, api_password]):
        return {"success": False, "message": "TAPD 未配置，请先在配置页面设置 TAPD 信息"}

    tapd_severity = SEVERITY_MAP.get(severity, "normal")
    tapd_priority = PRIORITY_MAP.get(priority, "medium")

    # TAPD 描述字段需要 HTML 格式才能换行
    html_description = description.replace("\n", "<br>")

    bug_data = {
        "workspace_id": workspace_id,
        "title": title,
        "description": html_description,
        "severity": tapd_severity,
        "priority": tapd_priority,
        "bugtype": config.get("default_bug_type", "codeerr"),  # codeerr/interface/performance/function/others
        "reporter": reporter or config.get("default_reporter", ""),
        "current_owner": config.get("default_assignee", ""),
    }

    if module:
        bug_data["module"] = module

    if extra_fields:
        bug_data.update(extra_fields)

    # 移除空值
    bug_data = {k: v for k, v in bug_data.items() if v}

    try:
        resp = requests.post(
            "https://api.tapd.cn/bugs",
            data=bug_data,
            auth=(api_user, api_password),
            timeout=15,
        )
        result = resp.json()

        if result.get("status") == 1 and result.get("data"):
            bug_info = result["data"].get("Bug", {})
            bug_id = bug_info.get("id", "")
            tapd_url = f"https://www.tapd.cn/{workspace_id}/bugtrace/bugs/view?bug_id={bug_id}"
            return {
                "success": True,
                "bug_id": bug_id,
                "url": tapd_url,
                "title": bug_info.get("title", title),
            }
        else:
            return {"success": False, "message": f"TAPD 创建失败: {result.get('info', resp.text[:200])}"}
    except requests.exceptions.Timeout:
        return {"success": False, "message": "推送超时，请稍后重试"}
    except Exception as e:
        return {"success": False, "message": f"推送异常: {str(e)}"}


_TITLE_BODY_MAX = 50
# 标题切句标点：先用强标点（句末），再用弱标点（逗号）兜底
_TITLE_STRONG_DELIMS = ("。", "！", "？", "；", ";", "\n")
_TITLE_WEAK_DELIMS = ("，", ",", "、")
_TITLE_SENTENCE_DELIMS = _TITLE_STRONG_DELIMS  # 向后兼容

# 代码快照名 → 中文模块名
_SNAPSHOT_NAME_MAP = {
    "purchaseOrder": "采购订单",
    "purchaseInbound": "采购入库",
    "stockDetail": "库存明细",
    "inventory": "库存明细",
    "personalCenter": "个人中心",
    "orderReceiving": "接单管理",
    "login": "登录",
    "payment": "付款单",
    "settlement": "结算单",
    "estimate": "暂估应付单",
}

# 纯组件类型占位词（不应作为字段名）
_COMPONENT_TYPE_NOISE = {
    "矩形", "文本框", "下拉列表", "下拉框", "按钮", "图片", "图标",
    "图形", "线框", "组件", "区域", "输入框", "复选框", "单选框",
    "标签", "链接", "列表", "表格",
}


def _normalize_module_name(snapshot_name: str) -> str:
    """snapshot 名 → 中文模块名（兜底返回去掉 _snapshot 后缀的原文）"""
    if not snapshot_name:
        return ""
    s = snapshot_name.strip()
    s = _re.sub(r"_snapshot$", "", s, flags=_re.IGNORECASE)
    s = s.strip()
    if s in _SNAPSHOT_NAME_MAP:
        return _SNAPSHOT_NAME_MAP[s]
    # 大小写不敏感再试一次
    for k, v in _SNAPSHOT_NAME_MAP.items():
        if k.lower() == s.lower():
            return v
    return s


def _clean_field_name(name: str) -> str:
    """清理字段名里的装饰符号；纯组件类型词丢弃返回空"""
    if not name:
        return ""
    n = name.strip()
    # 去首尾星号 / 必填标识
    n = n.lstrip("*＊").rstrip("*＊").strip()
    # 去掉前后的 ( ) （ ）
    m = _re.match(r"^[（(](.+?)[)）]$", n)
    if m:
        n = m.group(1).strip()
    # 整体是组件类型噪音 → 丢弃
    if n in _COMPONENT_TYPE_NOISE:
        return ""
    return n


def _split_first_segment(s: str, delims) -> str:
    """按给定标点切首段，返回标点之前的部分（不含标点）"""
    earliest = len(s)
    for d in delims:
        idx = s.find(d)
        if idx >= 0 and idx < earliest:
            earliest = idx
    return s[:earliest].strip() if earliest < len(s) else s


_HTML_ENTITY_RE = _re.compile(r"&[a-zA-Z#0-9]+;")


def _strip_html_entities(s: str) -> str:
    """剥离常见 HTML entity（&nbsp; &amp; 等），避免分号被误判为标点"""
    return _HTML_ENTITY_RE.sub(" ", s)


def _extract_field_from_requirement(text: str) -> str:
    """从需求文本里抽取一个简短的「字段名/子模块」作标题主体

    策略（按优先级）：
    1. 含 【XXX】 → 取首个「非组件类型」的 【】 内容
    2. 含 《XXX》 → 取首个《》
    3. 若 【】 全是组件类型噪音 → 剥离 【】 后再做切句
    4. 按强标点（句末）切首句；切不动时再用弱标点（逗号、顿号）
    5. 去掉条号前缀（"1、" "1." 等）；保底截 50 字符 + 省略号
    """
    if not text:
        return ""
    # 先剥 HTML entity，避免 &nbsp; / &amp; 里的分号干扰切句
    s = _strip_html_entities(text).strip()
    # 多空格压成一个
    s = _re.sub(r"\s+", " ", s)

    bracketed = _re.findall(r"【([^】]+)】", s)
    if bracketed:
        for b in bracketed:
            cleaned = _clean_field_name(b)
            if cleaned:
                return cleaned[:_TITLE_BODY_MAX]
        # 所有【】都是噪音 → 剥离它们后再切
        s = _re.sub(r"【[^】]+】", "", s).strip()

    book = _re.findall(r"《([^》]+)》", s)
    if book:
        cleaned = _clean_field_name(book[0])
        if cleaned:
            return cleaned[:_TITLE_BODY_MAX]

    # 先去掉条号前缀
    s = _re.sub(r"^\s*\d+\s*[、.\)）]\s*", "", s).strip()
    if not s:
        return ""

    # 按强标点切首句
    head = _split_first_segment(s, _TITLE_STRONG_DELIMS)
    # 切不动（整段无强标点）→ 用弱标点
    if head == s:
        head = _split_first_segment(s, _TITLE_WEAK_DELIMS)
    # 再去掉条号前缀（多次嵌套场景）
    head = _re.sub(r"^\s*\d+\s*[、.\)）]\s*", "", head).strip()
    if len(head) > _TITLE_BODY_MAX:
        head = head[:_TITLE_BODY_MAX] + "..."
    return head


# 向后兼容旧函数名（其他模块/测试可能引用）
def _extract_title_body(text: str) -> str:
    return _extract_field_from_requirement(text)


_TYPE_ISSUE_DESC = {
    "missing": "代码中未找到对应实现",
    "uncertain": "实现存疑，需复核",
    "extra": "代码包含需求外多余实现",
    "risk": "实现可能存在风险",
    "inconsistent": "实现与需求不一致",
}


def _build_issue_desc(finding: Dict) -> str:
    """基于 finding.inconsistencies / type 生成问题描述"""
    finding_type = finding.get("type", "unknown")
    inconsistencies = finding.get("inconsistencies") or []

    if isinstance(inconsistencies, list) and inconsistencies:
        first = inconsistencies[0]
        if isinstance(first, dict):
            aspect = (first.get("aspect") or "").strip()
            if aspect:
                return f"{aspect} 实现与需求不一致"

    return _TYPE_ISSUE_DESC.get(finding_type, "需要复核")


_TYPE_LABEL_ZH = {
    "missing": "需求未实现",
    "inconsistent": "实现不一致",
    "risk": "风险项",
    "uncertain": "实现存疑",
    "extra": "多余代码",
}

# 把白盒对比的存疑措辞重写为 bug 风格断言
_BUG_TONE_REPLACEMENTS = [
    ("候选代码中未发现", "代码缺失"),
    ("候选代码中未明确实现", "未实现"),
    ("候选代码中未明确展示", "未展示"),
    ("候选代码中未明确", "未明确实现"),
    ("候选代码中未实现", "未实现"),
    ("候选代码中未", "未"),
    ("候选代码中存在", "代码中存在"),
    ("候选代码中", ""),
    ("可能始终", "始终"),
    ("可能未实现", "未实现"),
    ("可能不一致", "不一致"),
    ("无法确认是否", "未确认"),
    ("未明确实现或说明", "未实现"),
    ("未明确实现", "未实现"),
    ("未明确展示", "未展示"),
    ("未明确说明", "未提供"),
    ("未明确", ""),
    ("[复核] ", ""),
]


def _rewrite_actual_to_bug_tone(text: str) -> str:
    """把白盒对比的存疑措辞重写为 bug 风格断言

    例：
        "候选代码中未发现根据字段值隐藏非必填字段的逻辑，可能始终显示"
        →
        "代码缺失根据字段值隐藏非必填字段的逻辑，始终显示"
    """
    if not text:
        return text
    s = str(text)
    for old, new in _BUG_TONE_REPLACEMENTS:
        s = s.replace(old, new)
    # 整理多余空格
    s = _re.sub(r"\s+", " ", s).strip()
    # 去掉多余的首句"，"
    s = _re.sub(r"^[，,]\s*", "", s)
    return s


def _format_code_location(finding: Dict) -> str:
    """从 finding.code_evidence / evidence_snippet 拼代码定位字符串"""
    ev = finding.get("code_evidence")
    items = []
    if isinstance(ev, dict):
        items = [ev]
    elif isinstance(ev, list):
        items = [x for x in ev if isinstance(x, dict)]

    parts = []
    for item in items[:3]:
        fp = item.get("file") or item.get("file_path") or ""
        ln = item.get("line")
        ci = item.get("code_item") or item.get("symbol") or ""
        seg_parts = []
        if ci:
            seg_parts.append(str(ci))
        if fp:
            loc = str(fp)
            if ln and ln != 0:
                loc += f":{ln}"
            seg_parts.append(loc)
        if seg_parts:
            parts.append(" - ".join(seg_parts))

    if not parts:
        snippet = finding.get("evidence_snippet")
        if snippet:
            parts.append(str(snippet)[:200])
    return "\n".join(parts)


def _build_description_bug_template(
    finding: Dict,
    module: str,
    field_name: str,
    req_point: str,
    report_context: Dict = None,
) -> str:
    """生成符合 TAPD bug 模板的描述

    格式：
        【模块】xxx
        【操作步骤】1. ... 2. ...
        【预期结果】...
        【实际结果】...
        【需求出处】...
        【代码定位】...
        ── 追溯：报告ID / 快照 / 来源
    """
    finding_type = finding.get("type", "unknown")
    type_label = _TYPE_LABEL_ZH.get(finding_type, finding_type or "未知")

    inconsistencies = finding.get("inconsistencies") or []
    if not isinstance(inconsistencies, list):
        inconsistencies = []

    # ── 测试建议（test_points） ──
    test_sug = finding.get("test_suggestion")
    test_points = []
    if isinstance(test_sug, dict):
        tp = test_sug.get("test_points")
        if isinstance(tp, list):
            test_points = [str(x).strip() for x in tp if str(x).strip()]
    elif isinstance(test_sug, list):
        test_points = [str(x).strip() for x in test_sug if str(x).strip()]

    lines = []

    # 【模块】
    module_seg = f"{module}"
    if field_name:
        module_seg += f" - {field_name}"
    lines.append(f"【模块】{module_seg}")

    # 【操作步骤】（通用复现路径骨架）
    lines.append("\n【操作步骤】")
    repro_anchor = field_name or "目标功能"
    lines.append(f"1. 进入「{module}」模块对应页面（新增/编辑/查看）")
    lines.append(f"2. 触发「{repro_anchor}」相关交互")
    lines.append("3. 观察实际行为是否符合需求要求")

    # 【预期结果】
    lines.append("\n【预期结果】")
    if inconsistencies:
        idx = 0
        for inc in inconsistencies:
            if not isinstance(inc, dict):
                continue
            exp = (inc.get("expected") or "").strip()
            if exp:
                idx += 1
                lines.append(f"{idx}. {exp}")
        if idx == 0 and req_point:
            lines.append(req_point)
    elif req_point:
        lines.append(req_point)
    else:
        lines.append("-")

    # 【实际结果】（语气从"候选代码中未发现"重写为 bug 风格）
    lines.append("\n【实际结果】")
    if inconsistencies:
        idx = 0
        for inc in inconsistencies:
            if not isinstance(inc, dict):
                continue
            act = (inc.get("actual") or "").strip()
            if act:
                idx += 1
                lines.append(f"{idx}. {_rewrite_actual_to_bug_tone(act)}")
        if idx == 0:
            lines.append(_TYPE_ISSUE_DESC.get(finding_type, "需要复核"))
    else:
        analysis = (finding.get("analysis") or "").strip()
        if analysis:
            lines.append(_rewrite_actual_to_bug_tone(analysis))
        else:
            lines.append(_TYPE_ISSUE_DESC.get(finding_type, "需要复核"))

    # 【需求出处】
    if req_point:
        lines.append(f"\n【需求出处】\n{req_point}")

    # 【代码定位】
    code_loc = _format_code_location(finding)
    if code_loc:
        lines.append(f"\n【代码定位】\n{code_loc}")

    # ── 追溯 ──
    lines.append("\n---")
    if report_context:
        lines.append(f"报告ID：{report_context.get('report_id', '-')}")
        lines.append(f"快照：{report_context.get('code_snapshot_name', '-')}")
    lines.append(f"来源：代码评审（{type_label}）")

    return "\n".join(lines)


def finding_to_tapd_bug(finding: Dict, report_context: Dict = None) -> Dict[str, str]:
    """将 finding 转换为 TAPD 缺陷字段

    标题格式：`【模块-字段】问题描述`
    例：`【采购订单-个税承担方】默认值/下拉选项 实现与需求不一致`
    """
    finding_type = finding.get("type", "unknown")

    # ── 模块前缀 ──
    module = (
        finding.get("module")
        or _normalize_module_name((report_context or {}).get("code_snapshot_name", ""))
        or "白盒对比"
    )

    # ── 字段名/子模块 ──
    req_point = (
        finding.get("requirement")
        or finding.get("requirement_point")
        or finding.get("req_point")
        or ""
    )
    req_clean = req_point.lstrip()
    for prefix in ("[实现不一致]", "[需求未实现]", "[实现存疑]", "[多余代码]", "[风险项]", "[白盒对比]"):
        if req_clean.startswith(prefix):
            req_clean = req_clean[len(prefix):].lstrip()
            break
    field_name = _extract_field_from_requirement(req_clean)

    # ── 问题描述 ──
    issue_desc = _build_issue_desc(finding)

    # ── 拼标题 ──
    if field_name:
        title = f"【{module}-{field_name}】{issue_desc}"
    else:
        title = f"【{module}】{issue_desc}"
    if len(title) > 200:
        title = title[:197] + "..."

    description = _build_description_bug_template(
        finding, module, field_name, req_point, report_context,
    )

    # 严重程度：默认偏保守，避免大量 finding 都上"严重"
    # - major (TAPD: 严重)：仅 risk 类型 + high + 高置信，强信号才上
    # - minor (TAPD: 一般)：常规 inconsistent / missing high，需要复核
    # - trivial (TAPD: 提示)：低风险或低置信
    risk_level = (finding.get("risk_level") or "").lower()
    confidence = float(finding.get("confidence") or 0.5)

    if finding_type == "risk" and risk_level == "high" and confidence >= 0.9:
        severity = "major"
    elif risk_level == "low":
        severity = "trivial"
    elif confidence < 0.5:
        severity = "trivial"
    else:
        severity = "minor"

    # 优先级：risk/inconsistent → P2；其他 → P3
    priority = "P2" if finding_type in ("risk", "inconsistent") else "P3"

    return {
        "title": title,
        "description": description,
        "severity": severity,
        "priority": priority,
        "module": finding.get("module", ""),
    }


# ══════════════════════════════════════════════════════════════════
# TAPD Bug 状态回流（A1）
# ══════════════════════════════════════════════════════════════════

# TAPD bug 原生状态码 → 标准化状态
# 参考: https://www.tapd.cn/help/show#1120003271001000035
TAPD_STATUS_MAP = {
    "new": "new",                # 新建
    "in_progress": "in_progress",  # 处理中
    "resolved": "resolved",      # 已解决
    "verified": "verified",      # 已验证
    "closed": "closed",          # 已关闭
    "rejected": "rejected",      # 已拒绝
    "reopen": "reopen",          # 重新打开
    "postponed": "postponed",    # 延期
}

TAPD_STATUS_NAME_ZH = {
    "new": "新建",
    "in_progress": "处理中",
    "resolved": "已解决",
    "verified": "已验证",
    "closed": "已关闭",
    "rejected": "已拒绝",
    "reopen": "重新打开",
    "postponed": "延期",
    "unknown": "未知",
}


def fetch_tapd_bug_status(config: Dict[str, Any], bug_id: str) -> Dict[str, Any]:
    """
    从 TAPD 拉取单个 Bug 的当前状态

    Args:
        config: TAPD 配置 (workspace_id / api_user / api_password)
        bug_id: TAPD Bug ID

    Returns:
        {"success": True, "bug_id": "...", "tapd_status": "in_progress",
         "tapd_status_name": "处理中", "raw": {...}}
        or {"success": False, "code": "...", "message": "..."}
    """
    workspace_id = config.get("workspace_id", "")
    api_user = config.get("api_user", "")
    api_password = config.get("api_password", "")

    if not all([workspace_id, api_user, api_password]):
        return {
            "success": False,
            "code": "TAPD_NOT_CONFIGURED",
            "message": "TAPD 未配置",
        }

    if not bug_id:
        return {
            "success": False,
            "code": "BUG_ID_EMPTY",
            "message": "Bug ID 为空",
        }

    try:
        resp = requests.get(
            "https://api.tapd.cn/bugs",
            params={"workspace_id": workspace_id, "id": str(bug_id), "fields": "id,status,name,modified"},
            auth=(api_user, api_password),
            timeout=15,
        )
        try:
            result = resp.json()
        except ValueError:
            return {
                "success": False,
                "code": "TAPD_INVALID_RESPONSE",
                "message": f"TAPD 响应解析失败 (HTTP {resp.status_code})",
            }

        if result.get("status") != 1:
            # 不要把 api_password / token 暴露到日志或返回
            info = str(result.get("info", ""))[:200]
            return {
                "success": False,
                "code": "TAPD_API_ERROR",
                "message": f"TAPD 查询失败: {info}",
            }

        data = result.get("data") or []
        if not data:
            return {
                "success": False,
                "code": "TAPD_BUG_NOT_FOUND",
                "message": f"TAPD 未找到 Bug {bug_id}",
            }

        # data 是数组，取第一条
        bug_info = data[0].get("Bug", {}) if isinstance(data, list) else data.get("Bug", {})
        raw_status = (bug_info.get("status") or "").strip().lower()
        normalized_status = TAPD_STATUS_MAP.get(raw_status, raw_status or "unknown")
        status_name = TAPD_STATUS_NAME_ZH.get(normalized_status, normalized_status or "未知")

        return {
            "success": True,
            "bug_id": str(bug_info.get("id") or bug_id),
            "tapd_status": normalized_status,
            "tapd_status_name": status_name,
            "tapd_modified": bug_info.get("modified", ""),
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "code": "TAPD_TIMEOUT",
            "message": "TAPD 查询超时",
        }
    except requests.exceptions.RequestException as e:
        # 仅返回异常类型，不要把 URL/header 之类细节透出去
        return {
            "success": False,
            "code": "TAPD_REQUEST_ERROR",
            "message": f"TAPD 请求异常: {type(e).__name__}",
        }
    except Exception as e:
        return {
            "success": False,
            "code": "TAPD_UNKNOWN_ERROR",
            "message": f"TAPD 未知错误: {type(e).__name__}",
        }
