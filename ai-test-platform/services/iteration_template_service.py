# -*- coding: utf-8 -*-
"""Built-in iteration templates for the D2-3A iteration center."""
from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Optional


def _tp(module_name: str, test_point: str, risk_level: str = "P1", priority: str = "medium", test_type: str = "functional") -> dict:
    return {
        "module_name": module_name,
        "test_point": test_point,
        "risk_level": risk_level,
        "priority": priority,
        "test_type": test_type,
    }


_TEMPLATES: List[dict] = [
    {
        "template_key": "general_feature",
        "template_name": "通用功能迭代模板",
        "description": "适用于常规页面、表单、列表、状态流转和基础业务功能需求。",
        "default_test_points": [
            _tp("基础功能", "主流程功能是否按需求完成", "P1", "high"),
            _tp("表单校验", "必填、长度、格式、边界值校验是否完整", "P1", "high"),
            _tp("状态流转", "新增、编辑、删除、启停、提交等状态流转是否正确", "P1", "high"),
            _tp("列表查询", "筛选、分页、排序、搜索结果是否正确", "P2"),
            _tp("异常处理", "接口异常、空数据、无权限时页面提示是否清晰", "P1", "high"),
            _tp("数据一致性", "刷新、返回、重新进入页面后数据是否一致", "P1", "high"),
            _tp("兼容回归", "新功能是否影响历史入口和原有数据", "P1", "high"),
        ],
        "default_risk_points": ["表单边界漏测", "状态流转遗漏", "历史数据兼容风险", "异常提示不清晰"],
        "default_execution_sets": ["smoke", "iteration", "regression"],
        "suggested_defect_templates": ["接口字段契约不一致", "本地环境代理异常"],
    },
    {
        "template_key": "payment_amount",
        "template_name": "支付/金额类迭代模板",
        "description": "适用于付款单、分账、个税、服务费、支付状态等资金类需求。",
        "default_test_points": [
            _tp("金额计算", "金额计算正确性", "P0", "high"),
            _tp("税费规则", "个税计算规则", "P0", "high"),
            _tp("服务费", "服务费计算规则", "P0", "high"),
            _tp("承担方", "承担方切换", "P0", "high"),
            _tp("金额联动", "实付金额联动", "P0", "high"),
            _tp("支付状态", "已付款状态冻结", "P0", "high"),
            _tp("幂等", "重复支付幂等", "P0", "high", "api"),
            _tp("分账", "分账部分成功/失败", "P0", "high", "api"),
            _tp("银行接口", "银行接口异常", "P0", "high", "api"),
            _tp("凭证回写", "附件/凭证回写", "P1", "high"),
            _tp("前后端金额", "前端展示金额与后端金额一致", "P0", "high"),
            _tp("支付请求", "后端金额与支付请求金额一致", "P0", "high", "api"),
        ],
        "default_risk_points": ["金额精度/四舍五入风险", "重复支付风险", "分账部分失败补偿风险", "已付款数据被修改风险"],
        "default_execution_sets": ["smoke", "iteration", "regression"],
        "suggested_defect_templates": ["接口字段契约不一致"],
    },
    {
        "template_key": "erp_sync",
        "template_name": "ERP/第三方同步类迭代模板",
        "description": "适用于ERP、支付网关、银行、外部仓储等第三方同步需求。",
        "default_test_points": [
            _tp("同步触发", "业务动作是否按需求触发第三方同步", "P0", "high"),
            _tp("字段映射", "本地字段与第三方字段映射是否正确", "P0", "high", "api"),
            _tp("同步幂等", "重复触发同步是否幂等", "P0", "high", "api"),
            _tp("失败重试", "第三方失败、超时、返回异常时是否可重试", "P0", "high", "api"),
            _tp("部分成功", "部分同步成功/失败时本地状态是否正确", "P0", "high"),
            _tp("状态回写", "第三方状态回写后页面和本地记录是否一致", "P1", "high"),
            _tp("日志追踪", "同步请求、响应、trace_id 是否可追踪", "P1"),
            _tp("历史兼容", "历史单据重新同步是否兼容", "P1"),
        ],
        "default_risk_points": ["字段映射错位", "重复同步产生脏数据", "失败无补偿", "第三方状态与本地状态不一致"],
        "default_execution_sets": ["smoke", "iteration", "regression"],
        "suggested_defect_templates": ["ERP附件同步异常", "接口字段契约不一致"],
    },
    {
        "template_key": "video_attachment",
        "template_name": "视频/附件类迭代模板",
        "description": "适用于图片、视频、文件上传、附件回写、影像展示和文件同步类需求。",
        "default_test_points": [
            _tp("当前页面", "当前页面是否展示附件/视频", "P0", "high"),
            _tp("记录页面", "记录页面是否展示附件/视频", "P0", "high"),
            _tp("页面状态", "清理/切单后是否残留", "P1", "high"),
            _tp("空附件", "附件为空时显示", "P2"),
            _tp("加载异常", "附件加载失败提示", "P1", "high"),
            _tp("重复操作", "重复点击防抖", "P1", "high"),
            _tp("权限", "权限不足访问", "P1", "high"),
            _tp("第三方同步", "ERP 附件同步", "P0", "high"),
            _tp("文件校验", "文件类型校验", "P1", "high"),
            _tp("文件有效期", "文件过期/失效处理", "P1", "high"),
        ],
        "default_risk_points": ["当前页和记录页字段不一致", "重复点击生成多份附件", "第三方附件同步不一致", "文件失效无提示"],
        "default_execution_sets": ["smoke", "iteration", "regression"],
        "suggested_defect_templates": ["卸货录像展示/ERP不一致", "当前页拿不到卸货视频", "清理/切单后残留影像"],
    },
    {
        "template_key": "api_contract",
        "template_name": "接口字段契约模板",
        "description": "适用于前后端字段、枚举、错误码、分页、兼容字段变更类需求。",
        "default_test_points": [
            _tp("字段命名", "前端字段名与后端字段名一致", "P0", "high", "api"),
            _tp("必填校验", "必填字段校验", "P0", "high", "api"),
            _tp("枚举", "枚举值一致", "P0", "high", "api"),
            _tp("空值默认值", "空值/默认值处理", "P1", "high", "api"),
            _tp("字段类型", "字段类型一致", "P0", "high", "api"),
            _tp("分页", "列表字段分页一致", "P1", "high", "api"),
            _tp("错误码", "错误码结构一致", "P1", "high", "api"),
            _tp("老字段", "老字段兼容", "P1", "high", "api"),
            _tp("新字段", "新字段展示", "P1", "high"),
            _tp("异常提示", "接口异常提示", "P1", "high"),
        ],
        "default_risk_points": ["字段名不一致", "枚举值未同步", "空值导致页面不展示", "老字段兼容被破坏"],
        "default_execution_sets": ["smoke", "iteration", "regression"],
        "suggested_defect_templates": ["接口字段契约不一致"],
    },
]


def list_iteration_templates() -> List[dict]:
    return deepcopy(_TEMPLATES)


def get_iteration_template(template_key: Optional[str]) -> Optional[dict]:
    if not template_key:
        return None
    for template in _TEMPLATES:
        if template["template_key"] == template_key:
            return deepcopy(template)
    return None

