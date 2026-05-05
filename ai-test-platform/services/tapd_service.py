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


def finding_to_tapd_bug(finding: Dict, report_context: Dict = None) -> Dict[str, str]:
    """将 finding 转换为 TAPD 缺陷字段"""
    finding_type = finding.get("type", "unknown")
    title_prefix = {
        "missing": "[需求未实现]",
        "uncertain": "[实现存疑]",
        "extra": "[多余代码]",
        "risk": "[风险项]",
    }.get(finding_type, "[白盒对比]")

    req_point = finding.get("requirement_point", "")
    title = f"{title_prefix} {req_point}"
    if len(title) > 200:
        title = title[:197] + "..."

    # 构造描述
    lines = []
    lines.append(f"## 需求点\n{req_point}\n")

    analysis = finding.get("analysis", "")
    if analysis:
        lines.append(f"## 分析说明\n{analysis}\n")

    evidence = finding.get("code_evidence", [])
    if evidence:
        lines.append("## 代码证据")
        for ev in evidence[:5]:
            fp = ev.get("file_path", "")
            snippet = ev.get("snippet", "")
            lines.append(f"- `{fp}`")
            if snippet:
                lines.append(f"  ```\n  {snippet[:500]}\n  ```")
        lines.append("")

    test_sug = finding.get("test_suggestion", {})
    if test_sug:
        lines.append("## 测试建议")
        lines.append(f"- 场景: {test_sug.get('scenario', '-')}")
        lines.append(f"- 步骤: {test_sug.get('steps', '-')}")
        lines.append(f"- 预期: {test_sug.get('expected', '-')}")
        lines.append("")

    if report_context:
        lines.append("---")
        lines.append(f"来源: AI测试平台 - 需求代码对比")
        lines.append(f"报告ID: {report_context.get('report_id', '-')}")
        lines.append(f"快照: {report_context.get('code_snapshot_name', '-')}")

    description = "\n".join(lines)

    # 映射严重程度
    confidence = finding.get("confidence", 0.5)
    if confidence >= 0.8:
        severity = "major"
    elif confidence >= 0.5:
        severity = "minor"
    else:
        severity = "trivial"

    if finding_type == "missing":
        severity = "major"

    return {
        "title": title,
        "description": description,
        "severity": severity,
        "priority": "P2" if finding_type == "missing" else "P3",
        "module": finding.get("module", ""),
    }
