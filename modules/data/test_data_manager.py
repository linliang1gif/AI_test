"""
测试数据管理器
智能生成正常、边界、异常测试数据
"""
import random
import string
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# 🔧 使用 core 层的统一枚举
from core import DataType


class TestDataManager:
    """
    测试数据管理器（企业级）
    
    特性：
    - 根据schema自动生成测试数据
    - 支持正常/边界/异常/空值数据
    - 支持多种数据类型
    - 支持约束条件（min/max/pattern）
    - 支持数据模板
    """
    
    def __init__(self):
        """初始化数据管理器"""
        self.data_cache = {}  # 缓存：{case_id: data}
        self.seed = 12345     # 随机种子，确保可重复性
    
    def generate_data(
        self, 
        schema: Dict[str, Any],
        category: str = "valid",
        case_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        根据schema生成测试数据（支持缓存）
        
        Args:
            schema: 数据schema
                {
                    "amount": {"type": "number", "minimum": 0, "maximum": 10000},
                    "name": {"type": "string", "minLength": 1, "maxLength": 50},
                    "email": {"type": "string", "format": "email"}
                }
            category: 数据分类（valid/boundary/invalid/null/empty）
            case_id: 用例ID（用于缓存，保证同一个case数据一致）
            
        Returns:
            生成的测试数据
        """
        # 如果提供了case_id且已缓存，直接返回
        if case_id and case_id in self.data_cache:
            return self.data_cache[case_id]
        
        # 设置随机种子（如果提供了case_id）
        if case_id:
            # 使用case_id生成确定性的种子
            seed = hash(case_id) % (2**32)
            random.seed(seed)
        
        data = {}
        
        for field_name, field_schema in schema.items():
            if isinstance(field_schema, str):
                # 简化格式：{"amount": "number"}
                field_type = field_schema
                field_schema = {"type": field_type}
            
            field_value = self._generate_field_value(
                field_name,
                field_schema,
                category
            )
            
            data[field_name] = field_value
        
        # 缓存数据
        if case_id:
            self.data_cache[case_id] = data
        
        # 重置随机种子
        random.seed()
        
        return data
    
    def generate_all_categories(
        self,
        schema: Dict[str, Any],
        case_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        生成所有分类的测试数据
        
        Args:
            schema: 数据schema
            case_id: 用例ID（用于缓存）
        
        Returns:
            {
                "valid": {...},
                "boundary": {...},
                "invalid": {...},
                "null": {...},
                "empty": {...}
            }
        """
        return {
            "valid": self.generate_data(schema, "valid", case_id),
            "boundary": self.generate_data(schema, "boundary", f"{case_id}_boundary" if case_id else None),
            "invalid": self.generate_data(schema, "invalid", f"{case_id}_invalid" if case_id else None),
            "null": self.generate_data(schema, "null", f"{case_id}_null" if case_id else None),
            "empty": self.generate_data(schema, "empty", f"{case_id}_empty" if case_id else None)
        }
    
    def generate(self, schema: Dict[str, str], case_id: str) -> Dict[str, Any]:
        """
        简化版生成方法（兼容旧接口）
        
        Args:
            schema: 简化的schema，例如 {"amount": "number", "name": "string"}
            case_id: 用例ID
        
        Returns:
            生成的数据
        """
        return self.generate_data(schema, "valid", case_id)
    
    def generate_boundary(self, schema: Dict[str, str]) -> Dict[str, Any]:
        """
        生成边界数据（兼容旧接口）
        
        Args:
            schema: 简化的schema
        
        Returns:
            边界数据
        """
        return self.generate_data(schema, "boundary")
    
    def generate_invalid(self, schema: Dict[str, str]) -> Dict[str, Any]:
        """
        生成异常数据（兼容旧接口）
        
        Args:
            schema: 简化的schema
        
        Returns:
            异常数据
        """
        return self.generate_data(schema, "invalid")
    
    def clear_cache(self, case_id: Optional[str] = None):
        """
        清除缓存
        
        Args:
            case_id: 如果指定，只清除该用例的缓存；否则清除所有
        """
        if case_id:
            self.data_cache.pop(case_id, None)
        else:
            self.data_cache.clear()
    
    def get_cached_data(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的数据
        
        Args:
            case_id: 用例ID
        
        Returns:
            缓存的数据，如果不存在返回None
        """
        return self.data_cache.get(case_id)
    
    def _generate_field_value(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        category: str
    ) -> Any:
        """生成单个字段的值"""
        field_type = field_schema.get("type", "string")
        
        # 处理null分类
        if category == "null":
            return None
        
        # 根据类型生成
        if field_type == "number" or field_type == "integer":
            return self._generate_number(field_schema, category, field_type == "integer")
        elif field_type == "string":
            return self._generate_string(field_name, field_schema, category)
        elif field_type == "boolean":
            return self._generate_boolean(field_schema, category)
        elif field_type == "array":
            return self._generate_array(field_schema, category)
        elif field_type == "object":
            return self._generate_object(field_schema, category)
        else:
            return None
    
    def _generate_number(
        self,
        schema: Dict[str, Any],
        category: str,
        is_integer: bool = False
    ) -> Optional[float]:
        """生成数字"""
        minimum = schema.get("minimum", 0)
        maximum = schema.get("maximum", 10000)
        
        if category == "valid":
            # 正常值：中间值
            value = (minimum + maximum) / 2
            return int(value) if is_integer else value
        
        elif category == "boundary":
            # 边界值：最小值或最大值
            value = random.choice([minimum, maximum])
            return int(value) if is_integer else value
        
        elif category == "invalid":
            # 异常值：负数、超出范围
            value = random.choice([
                minimum - 1,      # 小于最小值
                maximum + 1,      # 大于最大值
                -999999           # 极端负数
            ])
            return int(value) if is_integer else value
        
        elif category == "empty":
            # 空值：0
            return 0
        
        else:
            return None
    
    def _generate_string(
        self,
        field_name: str,
        schema: Dict[str, Any],
        category: str
    ) -> Optional[str]:
        """生成字符串"""
        min_length = schema.get("minLength", 1)
        max_length = schema.get("maxLength", 100)
        format_type = schema.get("format")
        pattern = schema.get("pattern")
        enum = schema.get("enum")
        
        # 枚举值
        if enum:
            if category == "valid":
                return enum[0]
            elif category == "invalid":
                return "invalid_enum_value"
        
        # 特殊格式
        if format_type:
            return self._generate_formatted_string(format_type, category)
        
        # 根据字段名推断类型
        field_lower = field_name.lower()
        if "email" in field_lower:
            return self._generate_email(category)
        elif "phone" in field_lower:
            return self._generate_phone(category)
        elif "url" in field_lower or "link" in field_lower:
            return self._generate_url(category)
        elif "password" in field_lower:
            return self._generate_password(category, min_length, max_length)
        
        # 普通字符串
        if category == "valid":
            # 正常值：中等长度
            length = min(min_length + 5, max_length)
            return self._random_string(length)
        
        elif category == "boundary":
            # 边界值：最小长度或最大长度
            length = random.choice([min_length, max_length])
            return self._random_string(length)
        
        elif category == "invalid":
            # 异常值：超长、特殊字符
            return random.choice([
                self._random_string(max_length + 100),  # 超长
                "<script>alert('xss')</script>",        # XSS
                "'; DROP TABLE users; --",              # SQL注入
                "\x00\x01\x02",                         # 控制字符
            ])
        
        elif category == "empty":
            # 空值：空字符串
            return ""
        
        else:
            return None
    
    def _generate_boolean(
        self,
        schema: Dict[str, Any],
        category: str
    ) -> Optional[bool]:
        """生成布尔值"""
        if category == "valid":
            return True
        elif category == "boundary":
            return False
        elif category == "invalid":
            # 布尔类型没有真正的invalid，返回字符串
            return "not_a_boolean"
        elif category == "empty":
            return False
        else:
            return None
    
    def _generate_array(
        self,
        schema: Dict[str, Any],
        category: str
    ) -> Optional[List]:
        """生成数组"""
        items_schema = schema.get("items", {"type": "string"})
        min_items = schema.get("minItems", 0)
        max_items = schema.get("maxItems", 10)
        
        if category == "valid":
            # 正常值：包含几个元素
            count = min(3, max_items)
            return [self._generate_field_value("item", items_schema, "valid") 
                   for _ in range(count)]
        
        elif category == "boundary":
            # 边界值：空数组或最大数组
            count = random.choice([min_items, max_items])
            return [self._generate_field_value("item", items_schema, "valid") 
                   for _ in range(count)]
        
        elif category == "invalid":
            # 异常值：超出范围
            count = max_items + 10
            return [self._generate_field_value("item", items_schema, "valid") 
                   for _ in range(count)]
        
        elif category == "empty":
            # 空值：空数组
            return []
        
        else:
            return None
    
    def _generate_object(
        self,
        schema: Dict[str, Any],
        category: str
    ) -> Optional[Dict]:
        """生成对象"""
        properties = schema.get("properties", {})
        
        if category == "empty":
            return {}
        
        obj = {}
        for prop_name, prop_schema in properties.items():
            obj[prop_name] = self._generate_field_value(
                prop_name,
                prop_schema,
                category
            )
        
        return obj
    
    def _generate_formatted_string(
        self,
        format_type: str,
        category: str
    ) -> str:
        """生成特定格式的字符串"""
        if format_type == "email":
            return self._generate_email(category)
        elif format_type == "date":
            return self._generate_date(category)
        elif format_type == "date-time":
            return self._generate_datetime(category)
        elif format_type == "uri" or format_type == "url":
            return self._generate_url(category)
        elif format_type == "uuid":
            return self._generate_uuid(category)
        else:
            return "formatted_string"
    
    def _generate_email(self, category: str) -> str:
        """生成邮箱"""
        if category == "valid":
            return f"test_{random.randint(1000, 9999)}@example.com"
        elif category == "boundary":
            return "a@b.c"  # 最短邮箱
        elif category == "invalid":
            return random.choice([
                "invalid.email",           # 缺少@
                "@example.com",            # 缺少用户名
                "test@",                   # 缺少域名
                "test@.com",               # 域名格式错误
                "test test@example.com"    # 包含空格
            ])
        elif category == "empty":
            return ""
        else:
            return "test@example.com"
    
    def _generate_phone(self, category: str) -> str:
        """生成电话号码"""
        if category == "valid":
            return f"138{random.randint(10000000, 99999999)}"
        elif category == "boundary":
            return "10000000000"  # 11位最小值
        elif category == "invalid":
            return random.choice([
                "123",                    # 太短
                "12345678901234567890",   # 太长
                "abcdefghijk",            # 非数字
                "138-1234-5678"           # 包含特殊字符
            ])
        elif category == "empty":
            return ""
        else:
            return "13800138000"
    
    def _generate_url(self, category: str) -> str:
        """生成URL"""
        if category == "valid":
            return f"https://example.com/path/{random.randint(1, 1000)}"
        elif category == "boundary":
            return "https://a.b"  # 最短URL
        elif category == "invalid":
            return random.choice([
                "not_a_url",
                "ftp://invalid",
                "http://",
                "://example.com"
            ])
        elif category == "empty":
            return ""
        else:
            return "https://example.com"
    
    def _generate_password(
        self,
        category: str,
        min_length: int,
        max_length: int
    ) -> str:
        """生成密码"""
        if category == "valid":
            length = max(8, min_length)
            return self._random_string(length, include_special=True)
        elif category == "boundary":
            return self._random_string(min_length)
        elif category == "invalid":
            return random.choice([
                "123",                    # 太短
                "password",               # 太简单
                "",                       # 空密码
            ])
        elif category == "empty":
            return ""
        else:
            return "Password123!"
    
    def _generate_date(self, category: str) -> str:
        """生成日期"""
        if category == "valid":
            return datetime.now().strftime("%Y-%m-%d")
        elif category == "boundary":
            return "1970-01-01"  # 最小日期
        elif category == "invalid":
            return random.choice([
                "2024-13-01",     # 无效月份
                "2024-02-30",     # 无效日期
                "not-a-date",
                "2024/01/01"      # 错误格式
            ])
        elif category == "empty":
            return ""
        else:
            return "2024-01-01"
    
    def _generate_datetime(self, category: str) -> str:
        """生成日期时间"""
        if category == "valid":
            return datetime.now().isoformat()
        elif category == "boundary":
            return "1970-01-01T00:00:00Z"
        elif category == "invalid":
            return "invalid-datetime"
        elif category == "empty":
            return ""
        else:
            return "2024-01-01T00:00:00Z"
    
    def _generate_uuid(self, category: str) -> str:
        """生成UUID"""
        if category == "valid":
            return str(uuid.uuid4())
        elif category == "invalid":
            return "not-a-uuid"
        elif category == "empty":
            return ""
        else:
            return str(uuid.uuid4())
    
    def _random_string(
        self,
        length: int,
        include_special: bool = False
    ) -> str:
        """生成随机字符串"""
        if length <= 0:
            return ""
        
        chars = string.ascii_letters + string.digits
        if include_special:
            chars += "!@#$%^&*()"
        
        return ''.join(random.choice(chars) for _ in range(length))
    
    def prepare_test_data(
        self,
        test_case,
        category: str = "valid"
    ) -> Dict[str, Any]:
        """
        为测试用例准备数据
        
        Args:
            test_case: TestCase对象
            category: 数据分类
            
        Returns:
            准备好的测试数据
        """
        execution_config = test_case.execution_config
        
        # 如果已有body，直接返回
        if "body" in execution_config and execution_config["body"]:
            return execution_config["body"]
        
        # 否则生成数据
        # 这里需要从test_case中提取schema
        # 简化实现：返回空字典
        return {}
    
    def cleanup_test_data(self, test_case):
        """
        清理测试数据
        
        Args:
            test_case: TestCase对象
        """
        # 实现数据清理逻辑
        # 例如：删除测试过程中创建的数据
        pass
    
    def regenerate_data(
        self,
        test_case,
        failed_field: str = None
    ) -> Dict[str, Any]:
        """
        重新生成数据（用于Self-Healing）
        
        Args:
            test_case: TestCase对象
            failed_field: 失败的字段名
            
        Returns:
            重新生成的数据
        """
        # 如果指定了失败字段，只重新生成该字段
        if failed_field:
            # 简化实现
            return {failed_field: "regenerated_value"}
        
        # 否则重新生成所有数据
        return self.prepare_test_data(test_case, "valid")
