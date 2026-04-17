#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real Execution Engine - 真实执行引擎
统一的测试执行入口，支持API、脚本、命令三种执行类型
"""

import time
import uuid
import json
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from datetime import datetime


# ==================== 枚举定义 ====================

class ExecutionType(Enum):
    """执行类型"""
    API = "api"
    SCRIPT = "script"
    COMMAND = "command"


class ExecutionStatus(Enum):
    """执行状态"""
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"


class ErrorType(Enum):
    """错误类型"""
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    HTTP_ERROR = "http_error"
    JSON_DECODE_ERROR = "json_decode_error"
    SCRIPT_ERROR = "script_error"
    COMMAND_ERROR = "command_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


# ==================== 数据结构 ====================

@dataclass
class ExecutionResult:
    """执行结果统一数据结构"""
    # 基础信息
    trace_id: str
    execution_type: str
    status: str
    success: bool
    
    # 时间信息
    start_time: str
    end_time: str
    duration: float  # 秒
    
    # 响应信息
    status_code: Optional[int] = None
    response: Optional[Any] = None
    response_headers: Optional[Dict[str, str]] = None
    
    # 错误信息
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[str] = None
    
    # 额外信息
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class TestCase:
    """测试用例数据结构"""
    id: str
    name: str
    execution_type: str
    config: Dict[str, Any]
    
    # 可选字段
    description: Optional[str] = None
    tags: Optional[list] = None
    timeout: Optional[int] = 30


# ==================== 执行引擎 ====================

class ExecutionEngine:
    """
    真实执行引擎
    统一的测试执行入口，替换所有mock和简单requests调用
    """
    
    def __init__(self, default_timeout: int = 30):
        """
        初始化执行引擎
        
        Args:
            default_timeout: 默认超时时间（秒）
        """
        self.default_timeout = default_timeout
        self.session = requests.Session()
        
    def execute(self, test_case: Union[TestCase, Dict[str, Any]]) -> ExecutionResult:
        """
        统一执行入口
        
        Args:
            test_case: 测试用例对象或字典
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 转换为TestCase对象
        if isinstance(test_case, dict):
            test_case = TestCase(
                id=test_case.get('id', str(uuid.uuid4())),
                name=test_case.get('name', 'Unnamed Test'),
                execution_type=test_case.get('execution_type', 'api'),
                config=test_case.get('config', {}),
                description=test_case.get('description'),
                tags=test_case.get('tags'),
                timeout=test_case.get('timeout', self.default_timeout)
            )
        
        # 生成trace_id
        trace_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # 根据执行类型分发
            if test_case.execution_type == ExecutionType.API.value:
                result = self._execute_api(test_case, trace_id, start_time)
            elif test_case.execution_type == ExecutionType.SCRIPT.value:
                result = self._execute_script(test_case, trace_id, start_time)
            elif test_case.execution_type == ExecutionType.COMMAND.value:
                result = self._execute_command(test_case, trace_id, start_time)
            else:
                result = self._create_error_result(
                    trace_id=trace_id,
                    execution_type=test_case.execution_type,
                    start_time=start_time,
                    error_type=ErrorType.VALIDATION_ERROR,
                    error_message=f"不支持的执行类型: {test_case.execution_type}"
                )
            
            return result
            
        except Exception as e:
            return self._create_error_result(
                trace_id=trace_id,
                execution_type=test_case.execution_type,
                start_time=start_time,
                error_type=ErrorType.UNKNOWN_ERROR,
                error_message=str(e),
                error_details=self._get_exception_details(e)
            )
    
    # ==================== API 执行 ====================
    
    def _execute_api(
        self, 
        test_case: TestCase, 
        trace_id: str, 
        start_time: datetime
    ) -> ExecutionResult:
        """
        执行API测试
        
        Args:
            test_case: 测试用例
            trace_id: 追踪ID
            start_time: 开始时间
            
        Returns:
            ExecutionResult: 执行结果
        """
        config = test_case.config
        
        # 提取配置
        method = config.get('method', 'GET').upper()
        url = config.get('url', '')
        headers = config.get('headers', {})
        body = config.get('body', config.get('data', {}))
        timeout = test_case.timeout or self.default_timeout
        
        # 验证必需参数
        if not url:
            return self._create_error_result(
                trace_id=trace_id,
                execution_type=ExecutionType.API.value,
                start_time=start_time,
                error_type=ErrorType.VALIDATION_ERROR,
                error_message="URL不能为空"
            )
        
        try:
            # 发送HTTP请求
            request_start = time.time()
            
            if method == 'GET':
                response = self.session.get(
                    url, 
                    params=body if isinstance(body, dict) else None,
                    headers=headers, 
                    timeout=timeout
                )
            elif method == 'POST':
                response = self.session.post(
                    url, 
                    json=body if isinstance(body, dict) else None,
                    data=body if not isinstance(body, dict) else None,
                    headers=headers, 
                    timeout=timeout
                )
            elif method == 'PUT':
                response = self.session.put(
                    url, 
                    json=body if isinstance(body, dict) else None,
                    data=body if not isinstance(body, dict) else None,
                    headers=headers, 
                    timeout=timeout
                )
            elif method == 'DELETE':
                response = self.session.delete(
                    url, 
                    json=body if isinstance(body, dict) else None,
                    headers=headers, 
                    timeout=timeout
                )
            elif method == 'PATCH':
                response = self.session.patch(
                    url, 
                    json=body if isinstance(body, dict) else None,
                    headers=headers, 
                    timeout=timeout
                )
            else:
                return self._create_error_result(
                    trace_id=trace_id,
                    execution_type=ExecutionType.API.value,
                    start_time=start_time,
                    error_type=ErrorType.VALIDATION_ERROR,
                    error_message=f"不支持的HTTP方法: {method}"
                )
            
            request_duration = time.time() - request_start
            end_time = datetime.now()
            
            # 解析响应
            response_data = None
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text
            
            # 判断成功/失败
            success = 200 <= response.status_code < 400
            status = ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED
            
            return ExecutionResult(
                trace_id=trace_id,
                execution_type=ExecutionType.API.value,
                status=status.value,
                success=success,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration=request_duration,
                status_code=response.status_code,
                response=response_data,
                response_headers=dict(response.headers),
                metadata={
                    'method': method,
                    'url': url,
                    'request_headers': headers,
                    'request_body': body
                }
            )
            
        except requests.exceptions.Timeout:
            return self._create_error_result(
                trace_id=trace_id,
                execution_type=ExecutionType.API.value,
                start_time=start_time,
                error_type=ErrorType.TIMEOUT,
                error_message=f"请求超时（{timeout}秒）",
                metadata={'method': method, 'url': url}
            )
            
        except requests.exceptions.ConnectionError as e:
            return self._create_error_result(
                trace_id=trace_id,
                execution_type=ExecutionType.API.value,
                start_time=start_time,
                error_type=ErrorType.CONNECTION_ERROR,
                error_message="连接失败，请检查URL是否正确",
                error_details=str(e),
                metadata={'method': method, 'url': url}
            )
            
        except requests.exceptions.HTTPError as e:
            return self._create_error_result(
                trace_id=trace_id,
                execution_type=ExecutionType.API.value,
                start_time=start_time,
                error_type=ErrorType.HTTP_ERROR,
                error_message=f"HTTP错误: {e}",
                error_details=str(e),
                metadata={'method': method, 'url': url}
            )
    
    # ==================== 脚本执行 ====================
    
    def _execute_script(
        self, 
        test_case: TestCase, 
        trace_id: str, 
        start_time: datetime
    ) -> ExecutionResult:
        """
        执行Python脚本
        
        Args:
            test_case: 测试用例
            trace_id: 追踪ID
            start_time: 开始时间
            
        Returns:
            ExecutionResult: 执行结果
        """
        config = test_case.config
        script_content = config.get('script', config.get('content', ''))
        timeout = test_case.timeout or self.default_timeout
        
        if not script_content:
            return self._create_error_result(
                trace_id=trace_id,
                execution_type=ExecutionType.SCRIPT.value,
                start_time=start_time,
                error_type=ErrorType.VALIDATION_ERROR,
                error_message="脚本内容不能为空"
            )
        
        # 创建临时文件
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.py', 
                delete=False, 
                encoding='utf-8'
            ) as f:
                f.write(script_content)
                temp_file = f.name
            
            # 执行脚本
            exec_start = time.time()
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )
            exec_duration = time.time() - exec_start
            end_time = datetime.now()
            
            # 判断成功/失败
            success = result.returncode == 0
            status = ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED
            
            return ExecutionResult(
                trace_id=trace_id,
                execution_type=ExecutionType.SCRIPT.value,
                status=status.value,
                success=success,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration=exec_duration,
                status_code=result.returncode,
                response={
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                },
                metadata={
                    'script_length': len(script_content),
                    'temp_file': temp_file
                }
            )
            
        except subprocess.TimeoutExpired:
            return self._create_error_result(
                trace_id=trace_id,
                execution_type=ExecutionType.SCRIPT.value,
                start_time=start_time,
                error_type=ErrorType.TIMEOUT,
                error_message=f"脚本执行超时（{timeout}秒）"
            )
            
        except Exception as e:
            return self._create_error_result(
                trace_id=trace_id,
                execution_type=ExecutionType.SCRIPT.value,
                start_time=start_time,
                error_type=ErrorType.SCRIPT_ERROR,
                error_message=f"脚本执行失败: {str(e)}",
                error_details=self._get_exception_details(e)
            )
            
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    # ==================== 命令执行 ====================
    
    def _execute_command(
        self, 
        test_case: TestCase, 
        trace_id: str, 
        start_time: datetime
    ) -> ExecutionResult:
        """
        执行系统命令
        
        Args:
            test_case: 测试用例
            trace_id: 追踪ID
            start_time: 开始时间
            
        Returns:
            ExecutionResult: 执行结果
        """
        config = test_case.config
        command = config.get('command', '')
        cwd = config.get('cwd')
        env = config.get('env')
        timeout = test_case.timeout or self.default_timeout
        
        if not command:
            return self._create_error_result(
                trace_id=trace_id,
                execution_type=ExecutionType.COMMAND.value,
                start_time=start_time,
                error_type=ErrorType.VALIDATION_ERROR,
                error_message="命令不能为空"
            )
        
        try:
            # 执行命令
            exec_start = time.time()
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=env,
                encoding='utf-8'
            )
            exec_duration = time.time() - exec_start
            end_time = datetime.now()
            
            # 判断成功/失败
            success = result.returncode == 0
            status = ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED
            
            return ExecutionResult(
                trace_id=trace_id,
                execution_type=ExecutionType.COMMAND.value,
                status=status.value,
                success=success,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration=exec_duration,
                status_code=result.returncode,
                response={
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                },
                metadata={
                    'command': command,
                    'cwd': cwd
                }
            )
            
        except subprocess.TimeoutExpired:
            return self._create_error_result(
                trace_id=trace_id,
                execution_type=ExecutionType.COMMAND.value,
                start_time=start_time,
                error_type=ErrorType.TIMEOUT,
                error_message=f"命令执行超时（{timeout}秒）",
                metadata={'command': command}
            )
            
        except Exception as e:
            return self._create_error_result(
                trace_id=trace_id,
                execution_type=ExecutionType.COMMAND.value,
                start_time=start_time,
                error_type=ErrorType.COMMAND_ERROR,
                error_message=f"命令执行失败: {str(e)}",
                error_details=self._get_exception_details(e),
                metadata={'command': command}
            )
    
    # ==================== 辅助方法 ====================
    
    def _create_error_result(
        self,
        trace_id: str,
        execution_type: str,
        start_time: datetime,
        error_type: ErrorType,
        error_message: str,
        error_details: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """创建错误结果"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return ExecutionResult(
            trace_id=trace_id,
            execution_type=execution_type,
            status=ExecutionStatus.ERROR.value,
            success=False,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=duration,
            error_type=error_type.value,
            error_message=error_message,
            error_details=error_details,
            metadata=metadata
        )
    
    def _get_exception_details(self, exception: Exception) -> str:
        """获取异常详情"""
        import traceback
        return ''.join(traceback.format_exception(
            type(exception), 
            exception, 
            exception.__traceback__
        ))
    
    def close(self):
        """关闭会话"""
        self.session.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# ==================== 全局实例 ====================

_engine_instance = None

def get_execution_engine() -> ExecutionEngine:
    """获取全局执行引擎实例（单例模式）"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ExecutionEngine()
    return _engine_instance


# ==================== 便捷函数 ====================

def execute_api_test(
    url: str,
    method: str = 'GET',
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Any] = None,
    timeout: int = 30
) -> ExecutionResult:
    """
    便捷函数：执行API测试
    
    Args:
        url: 请求URL
        method: HTTP方法
        headers: 请求头
        body: 请求体
        timeout: 超时时间
        
    Returns:
        ExecutionResult: 执行结果
    """
    engine = get_execution_engine()
    test_case = {
        'id': str(uuid.uuid4()),
        'name': f'{method} {url}',
        'execution_type': 'api',
        'config': {
            'url': url,
            'method': method,
            'headers': headers or {},
            'body': body or {}
        },
        'timeout': timeout
    }
    return engine.execute(test_case)


def execute_script_test(
    script: str,
    timeout: int = 60
) -> ExecutionResult:
    """
    便捷函数：执行脚本测试
    
    Args:
        script: Python脚本内容
        timeout: 超时时间
        
    Returns:
        ExecutionResult: 执行结果
    """
    engine = get_execution_engine()
    test_case = {
        'id': str(uuid.uuid4()),
        'name': 'Script Test',
        'execution_type': 'script',
        'config': {
            'script': script
        },
        'timeout': timeout
    }
    return engine.execute(test_case)


def execute_command_test(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 60
) -> ExecutionResult:
    """
    便捷函数：执行命令测试
    
    Args:
        command: 系统命令
        cwd: 工作目录
        timeout: 超时时间
        
    Returns:
        ExecutionResult: 执行结果
    """
    engine = get_execution_engine()
    test_case = {
        'id': str(uuid.uuid4()),
        'name': f'Command: {command}',
        'execution_type': 'command',
        'config': {
            'command': command,
            'cwd': cwd
        },
        'timeout': timeout
    }
    return engine.execute(test_case)
