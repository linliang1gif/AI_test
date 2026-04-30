"""
Executor V2 - 断言引擎

支持的断言类型：
  - status_code     : 状态码匹配
  - response_time   : 响应时间上限 (ms)
  - json_path       : JSONPath 取值断言
  - field_exists    : 字段存在性
  - field_equals    : 字段等值断言
  - contains        : 响应体包含子串
  - schema          : JSON Schema 校验（委托 SchemaValidator）
"""

import re
from typing import Any, List, Optional

from .models import (
    AssertionDef,
    AssertionResult,
    AssertionType,
    HttpResponse,
)
from .schema_validator import SchemaValidator


class AssertionEngineV2:
    """断言引擎 V2"""

    def __init__(self):
        self._schema_validator = SchemaValidator()

    def run_assertions(
        self,
        assertions: List[AssertionDef],
        response: HttpResponse,
    ) -> List[AssertionResult]:
        """对一个 HttpResponse 执行全部断言，返回结果列表。"""
        results: List[AssertionResult] = []
        for a in assertions:
            result = self._run_single(a, response)
            results.append(result)
        return results

    # ------------------------------------------------------------------

    def _run_single(self, a: AssertionDef, resp: HttpResponse) -> AssertionResult:
        try:
            t = a.type
            if t == AssertionType.STATUS_CODE.value:
                return self._assert_status_code(a, resp)
            elif t == AssertionType.RESPONSE_TIME.value:
                return self._assert_response_time(a, resp)
            elif t == AssertionType.JSON_PATH.value:
                return self._assert_json_path(a, resp)
            elif t == AssertionType.FIELD_EXISTS.value:
                return self._assert_field_exists(a, resp)
            elif t == AssertionType.FIELD_EQUALS.value:
                return self._assert_field_equals(a, resp)
            elif t == AssertionType.CONTAINS.value:
                return self._assert_contains(a, resp)
            elif t == AssertionType.SCHEMA.value:
                return self._assert_schema(a, resp)
            else:
                return AssertionResult(
                    type=t, passed=False,
                    message=f"不支持的断言类型: {t}",
                )
        except Exception as e:
            return AssertionResult(
                type=a.type, passed=False,
                message=f"断言执行异常: {e}",
            )

    # ---------- 具体断言实现 ----------

    def _assert_status_code(self, a: AssertionDef, resp: HttpResponse) -> AssertionResult:
        expected = a.expected
        actual = resp.status_code
        # 支持单个值或列表
        if isinstance(expected, list):
            passed = actual in expected
        else:
            passed = actual == int(expected)
        return AssertionResult(
            type=a.type, passed=passed,
            expected=expected, actual=actual,
            message="" if passed else f"期望状态码 {expected}，实际 {actual}",
        )

    def _assert_response_time(self, a: AssertionDef, resp: HttpResponse) -> AssertionResult:
        max_ms = float(a.expected)
        actual = resp.elapsed_ms
        passed = actual <= max_ms
        return AssertionResult(
            type=a.type, passed=passed,
            expected=f"<= {max_ms}ms", actual=f"{actual:.2f}ms",
            message="" if passed else f"响应时间 {actual:.2f}ms 超过上限 {max_ms}ms",
        )

    def _assert_json_path(self, a: AssertionDef, resp: HttpResponse) -> AssertionResult:
        body = resp.body
        if body is None:
            return AssertionResult(
                type=a.type, passed=False, path=a.path,
                message="响应体不是有效 JSON",
            )
        actual = self._resolve_path(body, a.path)
        if actual is _MISSING:
            return AssertionResult(
                type=a.type, passed=False, path=a.path,
                expected=a.expected, actual="<path not found>",
                message=f"路径 {a.path} 不存在",
            )
        passed = self._compare(actual, a.expected, a.operator)
        return AssertionResult(
            type=a.type, passed=passed, path=a.path,
            expected=a.expected, actual=actual,
            message="" if passed else f"路径 {a.path}: 期望 {a.expected}，实际 {actual}",
        )

    def _assert_field_exists(self, a: AssertionDef, resp: HttpResponse) -> AssertionResult:
        body = resp.body
        if not isinstance(body, dict):
            return AssertionResult(
                type=a.type, passed=False, path=a.path,
                message="响应体不是 JSON 对象",
            )
        actual = self._resolve_path(body, a.path)
        passed = actual is not _MISSING
        return AssertionResult(
            type=a.type, passed=passed, path=a.path,
            expected="exists", actual="exists" if passed else "not found",
            message="" if passed else f"字段 {a.path} 不存在",
        )

    def _assert_field_equals(self, a: AssertionDef, resp: HttpResponse) -> AssertionResult:
        body = resp.body
        if body is None:
            return AssertionResult(
                type=a.type, passed=False, path=a.path,
                message="响应体不是有效 JSON",
            )
        actual = self._resolve_path(body, a.path)
        if actual is _MISSING:
            return AssertionResult(
                type=a.type, passed=False, path=a.path,
                expected=a.expected, actual="<not found>",
                message=f"字段 {a.path} 不存在",
            )
        passed = self._compare(actual, a.expected, a.operator)
        return AssertionResult(
            type=a.type, passed=passed, path=a.path,
            expected=a.expected, actual=actual,
            message="" if passed else f"字段 {a.path}: 期望 {a.expected}，实际 {actual}",
        )

    def _assert_contains(self, a: AssertionDef, resp: HttpResponse) -> AssertionResult:
        text = resp.body_text or ""
        expected = str(a.expected)
        passed = expected in text
        return AssertionResult(
            type=a.type, passed=passed,
            expected=expected,
            actual=text[:200] + "..." if len(text) > 200 else text,
            message="" if passed else f"响应体不包含 '{expected}'",
        )

    def _assert_schema(self, a: AssertionDef, resp: HttpResponse) -> AssertionResult:
        if resp.body is None:
            return AssertionResult(
                type=a.type, passed=False,
                message="响应体不是有效 JSON，无法校验 Schema",
            )
        schema = a.schema or a.expected
        if not schema or not isinstance(schema, dict):
            return AssertionResult(
                type=a.type, passed=False,
                message="未提供有效的 JSON Schema",
            )
        errors = self._schema_validator.validate(resp.body, schema)
        passed = len(errors) == 0
        return AssertionResult(
            type=a.type, passed=passed,
            expected="schema valid",
            actual="valid" if passed else "; ".join(errors[:3]),
            message="" if passed else f"Schema 校验失败: {errors[0]}",
        )

    # ---------- 工具方法 ----------

    @staticmethod
    def _resolve_path(obj: Any, path: str) -> Any:
        """
        简易 JSONPath 解析：支持 data.user.name / data.items[0].id 格式
        """
        if not path:
            return obj
        # 拆分路径
        parts = re.split(r'\.|\[(\d+)\]', path)
        parts = [p for p in parts if p is not None and p != ""]
        current = obj
        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    return _MISSING
                current = current[part]
            elif isinstance(current, (list, tuple)):
                try:
                    idx = int(part)
                    current = current[idx]
                except (ValueError, IndexError):
                    return _MISSING
            else:
                return _MISSING
        return current

    @staticmethod
    def _compare(actual: Any, expected: Any, operator: str = "eq") -> bool:
        """通用比较"""
        try:
            if operator == "eq":
                return actual == expected
            elif operator == "ne":
                return actual != expected
            elif operator == "gt":
                return float(actual) > float(expected)
            elif operator == "lt":
                return float(actual) < float(expected)
            elif operator == "gte":
                return float(actual) >= float(expected)
            elif operator == "lte":
                return float(actual) <= float(expected)
            elif operator == "contains":
                return str(expected) in str(actual)
            elif operator == "regex":
                return bool(re.search(str(expected), str(actual)))
            else:
                return actual == expected
        except Exception:
            return False


# 哨兵值
class _MissingSentinel:
    def __repr__(self):
        return "<MISSING>"

_MISSING = _MissingSentinel()
