"""
Test Discovery Agent（测试发现代理）
基于代码变更自动发现高风险测试点
"""
import re
import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class RiskLevel(Enum):
    """风险等级"""
    CRITICAL = "critical"  # 严重：涉及金额、权限、安全
    HIGH = "high"          # 高：核心业务逻辑
    MEDIUM = "medium"      # 中：一般功能
    LOW = "low"            # 低：UI、文案


class TestType(Enum):
    """测试类型"""
    API = "api"
    UI = "ui"
    INTEGRATION = "integration"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class TestPoint:
    """测试点"""
    test_point: str           # 测试点描述
    reason: str               # 发现原因
    risk_level: str           # 风险等级
    suggested_test_type: str  # 建议测试类型
    api_path: Optional[str] = None      # 相关API路径
    changed_fields: Optional[List[str]] = None  # 变更字段
    suggested_scenarios: Optional[List[str]] = None  # 建议测试场景
    priority: str = "P1"      # 优先级
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


class TestDiscoveryAgent:
    """
    测试发现代理（企业级）
    
    特性：
    - 基于Swagger变更发现新增/修改的API
    - 基于Git Diff发现代码变更
    - 基于失败日志发现高风险区域
    - 自动识别高风险字段（金额、权限、状态）
    - 生成结构化测试点
    """
    
    # 高风险关键字
    CRITICAL_KEYWORDS = {
        'amount', 'price', 'money', 'payment', 'balance', 'fee', 'cost',  # 金额
        'auth', 'permission', 'role', 'token', 'password', 'secret',      # 权限
        'status', 'state', 'enabled', 'disabled', 'active', 'deleted'     # 状态
    }
    
    # 高风险操作
    CRITICAL_OPERATIONS = {
        'create', 'delete', 'update', 'modify', 'transfer', 'withdraw',
        'deposit', 'refund', 'cancel', 'approve', 'reject'
    }
    
    def __init__(self):
        """初始化发现代理"""
        self.discovered_points: List[TestPoint] = []
    
    def discover_from_swagger_changes(
        self, 
        old_swagger: str, 
        new_swagger: str
    ) -> List[TestPoint]:
        """
        从Swagger变更发现测试点
        
        Args:
            old_swagger: 旧版Swagger文件路径
            new_swagger: 新版Swagger文件路径
            
        Returns:
            发现的测试点列表
        """
        from modules.swagger import ApiSpecLoader
        
        test_points = []
        
        # 加载两个版本的Swagger
        old_loader = ApiSpecLoader(old_swagger) if Path(old_swagger).exists() else None
        new_loader = ApiSpecLoader(new_swagger)
        
        old_apis = {f"{api['method']}:{api['path']}": api 
                   for api in (old_loader.get_all_apis() if old_loader else [])}
        new_apis = {f"{api['method']}:{api['path']}": api 
                   for api in new_loader.get_all_apis()}
        
        # 1. 发现新增的API
        added_apis = set(new_apis.keys()) - set(old_apis.keys())
        for api_key in added_apis:
            api = new_apis[api_key]
            points = self._analyze_new_api(api)
            test_points.extend(points)
        
        # 2. 发现修改的API
        modified_apis = set(new_apis.keys()) & set(old_apis.keys())
        for api_key in modified_apis:
            old_api = old_apis[api_key]
            new_api = new_apis[api_key]
            points = self._analyze_modified_api(old_api, new_api)
            test_points.extend(points)
        
        # 3. 发现删除的API（需要测试兼容性）
        deleted_apis = set(old_apis.keys()) - set(new_apis.keys())
        for api_key in deleted_apis:
            api = old_apis[api_key]
            test_points.append(TestPoint(
                test_point=f"验证{api['method']} {api['path']}已正确下线",
                reason="API已删除，需要验证客户端兼容性",
                risk_level=RiskLevel.HIGH.value,
                suggested_test_type=TestType.API.value,
                api_path=api['path'],
                suggested_scenarios=["验证返回404", "验证客户端降级处理"],
                priority="P0"
            ))
        
        self.discovered_points.extend(test_points)
        return test_points
    
    def _analyze_new_api(self, api: Dict) -> List[TestPoint]:
        """分析新增API"""
        test_points = []
        
        # 基础测试点
        risk_level = self._calculate_api_risk(api)
        
        test_points.append(TestPoint(
            test_point=f"验证新增接口 {api['method']} {api['path']} 的基本功能",
            reason="新增API，需要完整测试",
            risk_level=risk_level.value,
            suggested_test_type=TestType.API.value,
            api_path=api['path'],
            suggested_scenarios=[
                "正常流程测试",
                "参数校验测试",
                "权限验证测试",
                "异常处理测试"
            ],
            priority="P0" if risk_level == RiskLevel.CRITICAL else "P1"
        ))
        
        # 分析高风险字段
        high_risk_fields = self._find_high_risk_fields(api)
        for field in high_risk_fields:
            test_points.append(TestPoint(
                test_point=f"验证{api['path']}中{field}字段的边界和异常情况",
                reason=f"高风险字段：{field}",
                risk_level=RiskLevel.CRITICAL.value,
                suggested_test_type=TestType.API.value,
                api_path=api['path'],
                changed_fields=[field],
                suggested_scenarios=[
                    f"{field}为0",
                    f"{field}为负数",
                    f"{field}为null",
                    f"{field}超出范围"
                ],
                priority="P0"
            ))
        
        return test_points
    
    def _analyze_modified_api(self, old_api: Dict, new_api: Dict) -> List[TestPoint]:
        """分析修改的API"""
        test_points = []
        
        # 1. 检查参数变更
        old_params = self._extract_param_names(old_api)
        new_params = self._extract_param_names(new_api)
        
        added_params = new_params - old_params
        removed_params = old_params - new_params
        
        if added_params:
            test_points.append(TestPoint(
                test_point=f"验证{new_api['path']}新增参数的处理",
                reason=f"新增参数: {', '.join(added_params)}",
                risk_level=RiskLevel.HIGH.value,
                suggested_test_type=TestType.API.value,
                api_path=new_api['path'],
                changed_fields=list(added_params),
                suggested_scenarios=[
                    "不传新参数（向后兼容）",
                    "传入新参数",
                    "新参数为null",
                    "新参数为无效值"
                ],
                priority="P0"
            ))
        
        if removed_params:
            test_points.append(TestPoint(
                test_point=f"验证{new_api['path']}删除参数后的兼容性",
                reason=f"删除参数: {', '.join(removed_params)}",
                risk_level=RiskLevel.CRITICAL.value,
                suggested_test_type=TestType.API.value,
                api_path=new_api['path'],
                changed_fields=list(removed_params),
                suggested_scenarios=[
                    "旧客户端仍传入已删除参数",
                    "验证是否正确忽略",
                    "验证不会报错"
                ],
                priority="P0"
            ))
        
        # 2. 检查响应变更
        old_response_fields = self._extract_response_fields(old_api)
        new_response_fields = self._extract_response_fields(new_api)
        
        if old_response_fields != new_response_fields:
            test_points.append(TestPoint(
                test_point=f"验证{new_api['path']}响应结构变更",
                reason="响应字段发生变化",
                risk_level=RiskLevel.HIGH.value,
                suggested_test_type=TestType.API.value,
                api_path=new_api['path'],
                suggested_scenarios=[
                    "验证新字段存在",
                    "验证旧客户端兼容性",
                    "验证字段类型正确"
                ],
                priority="P0"
            ))
        
        return test_points
# 第二部分代码

    def discover_from_git_diff(self, diff_content: str) -> List[TestPoint]:
        """
        从Git Diff发现测试点
        
        Args:
            diff_content: Git diff内容
            
        Returns:
            发现的测试点列表
        """
        test_points = []
        
        # 解析diff
        changes = self._parse_git_diff(diff_content)
        
        for change in changes:
            # 分析变更类型
            if self._is_critical_change(change):
                test_points.append(TestPoint(
                    test_point=f"验证{change['file']}中{change['function']}的变更",
                    reason=f"修改了关键代码: {change['description']}",
                    risk_level=RiskLevel.CRITICAL.value,
                    suggested_test_type=TestType.API.value,
                    suggested_scenarios=[
                        "验证原有功能不受影响",
                        "验证新逻辑正确",
                        "验证边界情况"
                    ],
                    priority="P0"
                ))
        
        self.discovered_points.extend(test_points)
        return test_points
    
    def discover_from_failure_logs(self, log_content: str) -> List[TestPoint]:
        """
        从失败日志发现测试点
        
        Args:
            log_content: 失败日志内容
            
        Returns:
            发现的测试点列表
        """
        test_points = []
        
        # 解析日志
        failures = self._parse_failure_logs(log_content)
        
        for failure in failures:
            test_points.append(TestPoint(
                test_point=f"回归测试：{failure['api_path']}",
                reason=f"历史失败: {failure['error_message']}",
                risk_level=RiskLevel.HIGH.value,
                suggested_test_type=TestType.API.value,
                api_path=failure['api_path'],
                suggested_scenarios=[
                    "重现历史失败场景",
                    "验证修复有效",
                    "添加防护测试"
                ],
                priority="P0"
            ))
        
        self.discovered_points.extend(test_points)
        return test_points
    
    def _calculate_api_risk(self, api: Dict) -> RiskLevel:
        """计算API风险等级"""
        path = api['path'].lower()
        method = api['method'].upper()
        summary = api.get('summary', '').lower()
        
        # 检查关键字
        text = f"{path} {summary}"
        
        for keyword in self.CRITICAL_KEYWORDS:
            if keyword in text:
                return RiskLevel.CRITICAL
        
        for operation in self.CRITICAL_OPERATIONS:
            if operation in text:
                return RiskLevel.HIGH
        
        # 根据HTTP方法判断
        if method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            return RiskLevel.HIGH
        
        return RiskLevel.MEDIUM
    
    def _find_high_risk_fields(self, api: Dict) -> List[str]:
        """查找高风险字段"""
        high_risk_fields = []
        
        # 检查请求体
        if api.get('request_body'):
            schema = api['request_body'].get('schema', {})
            fields = self._extract_fields_from_schema(schema)
            
            for field in fields:
                if any(keyword in field.lower() for keyword in self.CRITICAL_KEYWORDS):
                    high_risk_fields.append(field)
        
        # 检查参数
        for param in api.get('parameters', []):
            param_name = param.get('name', '')
            if any(keyword in param_name.lower() for keyword in self.CRITICAL_KEYWORDS):
                high_risk_fields.append(param_name)
        
        return high_risk_fields
    
    def _extract_param_names(self, api: Dict) -> Set[str]:
        """提取参数名称"""
        params = set()
        
        # 路径参数、查询参数、请求头
        for param in api.get('parameters', []):
            params.add(param.get('name', ''))
        
        # 请求体字段
        if api.get('request_body'):
            schema = api['request_body'].get('schema', {})
            fields = self._extract_fields_from_schema(schema)
            params.update(fields)
        
        return params
    
    def _extract_response_fields(self, api: Dict) -> Set[str]:
        """提取响应字段"""
        fields = set()
        
        responses = api.get('responses', {})
        for status_code, response in responses.items():
            if status_code.startswith('2'):  # 成功响应
                schema = self._extract_response_schema(response)
                if schema:
                    response_fields = self._extract_fields_from_schema(schema)
                    fields.update(response_fields)
        
        return fields
    
    def _extract_fields_from_schema(self, schema: Dict) -> List[str]:
        """从schema提取字段名"""
        fields = []
        
        if schema.get('type') == 'object':
            properties = schema.get('properties', {})
            fields.extend(properties.keys())
            
            # 递归提取嵌套字段
            for prop_name, prop_schema in properties.items():
                if prop_schema.get('type') == 'object':
                    nested_fields = self._extract_fields_from_schema(prop_schema)
                    fields.extend([f"{prop_name}.{f}" for f in nested_fields])
        
        return fields
    
    def _extract_response_schema(self, response: Dict) -> Optional[Dict]:
        """提取响应schema"""
        if 'content' in response:
            content = response['content']
            if 'application/json' in content:
                return content['application/json'].get('schema', {})
        
        if 'schema' in response:
            return response['schema']
        
        return None
    
    def _parse_git_diff(self, diff_content: str) -> List[Dict]:
        """解析Git Diff"""
        changes = []
        
        # 简单解析（实际应该更复杂）
        lines = diff_content.split('\n')
        current_file = None
        
        for line in lines:
            if line.startswith('diff --git'):
                # 提取文件名
                match = re.search(r'b/(.+)$', line)
                if match:
                    current_file = match.group(1)
            
            elif line.startswith('+') and not line.startswith('+++'):
                # 新增的代码
                if current_file and any(keyword in line.lower() 
                                       for keyword in self.CRITICAL_KEYWORDS):
                    changes.append({
                        'file': current_file,
                        'function': 'unknown',
                        'description': line[1:].strip(),
                        'type': 'addition'
                    })
        
        return changes
    
    def _is_critical_change(self, change: Dict) -> bool:
        """判断是否是关键变更"""
        description = change.get('description', '').lower()
        
        # 检查关键字
        for keyword in self.CRITICAL_KEYWORDS:
            if keyword in description:
                return True
        
        for operation in self.CRITICAL_OPERATIONS:
            if operation in description:
                return True
        
        return False
    
    def _parse_failure_logs(self, log_content: str) -> List[Dict]:
        """解析失败日志"""
        failures = []
        
        # 简单解析（实际应该更复杂）
        lines = log_content.split('\n')
        
        for line in lines:
            if 'FAILED' in line or 'ERROR' in line:
                # 尝试提取API路径
                api_match = re.search(r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)', line)
                if api_match:
                    failures.append({
                        'api_path': api_match.group(2),
                        'method': api_match.group(1),
                        'error_message': line
                    })
        
        return failures
    
    def get_all_discovered_points(self) -> List[TestPoint]:
        """获取所有发现的测试点"""
        return self.discovered_points
    
    def export_to_json(self, test_points: List[TestPoint] = None) -> List[Dict]:
        """导出为JSON格式"""
        if test_points is None:
            test_points = self.discovered_points
        
        return [tp.to_dict() for tp in test_points]
    
    def get_statistics(self, test_points: List[TestPoint] = None) -> Dict:
        """获取统计信息"""
        if test_points is None:
            test_points = self.discovered_points
        
        total = len(test_points)
        by_risk = {}
        by_type = {}
        by_priority = {}
        
        for tp in test_points:
            # 按风险等级
            risk = tp.risk_level
            by_risk[risk] = by_risk.get(risk, 0) + 1
            
            # 按测试类型
            test_type = tp.suggested_test_type
            by_type[test_type] = by_type.get(test_type, 0) + 1
            
            # 按优先级
            priority = tp.priority
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        return {
            'total': total,
            'by_risk_level': by_risk,
            'by_test_type': by_type,
            'by_priority': by_priority
        }
    
    def filter_by_risk(self, min_risk: RiskLevel) -> List[TestPoint]:
        """按风险等级过滤"""
        risk_order = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3
        }
        
        min_level = risk_order[min_risk]
        
        return [
            tp for tp in self.discovered_points
            if risk_order.get(RiskLevel(tp.risk_level), 0) >= min_level
        ]
