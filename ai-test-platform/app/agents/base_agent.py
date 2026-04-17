#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基础Agent类

所有专业化Agent的基类，提供通用功能：
- AI客户端管理
- 日志记录
- 错误处理
- 性能监控
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pathlib import Path

class BaseAgent(ABC):
    """基础Agent类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.created_at = time.time()
        self.execution_history = []
        
        # 设置日志
        self.logger = self._setup_logger()
        
        # 导入AI客户端
        try:
            from ...ai.ai_client import get_ai_client
            self.ai_client = get_ai_client()
        except ImportError:
            # 兼容性处理
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent))
            from ai.ai_client import get_ai_client
            self.ai_client = get_ai_client()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(f"Agent.{self.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - Agent.{self.name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行Agent任务 - 子类必须实现"""
        pass
    
    def execute_with_monitoring(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """带监控的执行"""
        execution_id = f"{self.name}_{int(time.time())}"
        start_time = time.time()
        
        self.logger.info(f"开始执行任务: {execution_id}")
        
        execution_record = {
            'execution_id': execution_id,
            'start_time': start_time,
            'input_data': input_data,
            'success': False,
            'result': None,
            'error': None,
            'duration': 0
        }
        
        try:
            # 验证输入
            validation_result = self.validate_input(input_data)
            if not validation_result['valid']:
                raise ValueError(f"输入验证失败: {validation_result['error']}")
            
            # 执行任务
            result = self.execute(input_data)
            
            # 验证输出
            output_validation = self.validate_output(result)
            if not output_validation['valid']:
                self.logger.warning(f"输出验证警告: {output_validation['error']}")
            
            execution_record['success'] = True
            execution_record['result'] = result
            
            self.logger.info(f"任务执行成功: {execution_id}")
            
        except Exception as e:
            execution_record['error'] = str(e)
            self.logger.error(f"任务执行失败: {execution_id} - {e}")
            
            # 返回错误结果
            execution_record['result'] = {
                'success': False,
                'error': str(e),
                'agent': self.name
            }
        
        finally:
            execution_record['duration'] = time.time() - start_time
            self.execution_history.append(execution_record)
        
        return execution_record['result']
    
    def validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证输入数据 - 子类可重写"""
        if not isinstance(input_data, dict):
            return {
                'valid': False,
                'error': '输入数据必须是字典类型'
            }
        
        return {'valid': True, 'error': None}
    
    def validate_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证输出数据 - 子类可重写"""
        if not isinstance(output_data, dict):
            return {
                'valid': False,
                'error': '输出数据必须是字典类型'
            }
        
        if 'success' not in output_data:
            return {
                'valid': False,
                'error': '输出数据必须包含success字段'
            }
        
        return {'valid': True, 'error': None}
    
    def get_system_prompt(self) -> str:
        """获取系统提示词 - 子类可重写"""
        return f"""你是一个专业的{self.name}，负责{self.description}。

请遵循以下原则：
1. 专业性：基于软件测试最佳实践
2. 准确性：确保输出结果的准确性和完整性
3. 可执行性：生成的内容必须可以直接使用
4. 标准化：遵循行业标准和规范

请以JSON格式返回结果，包含success字段表示执行状态。"""
    
    def call_ai(self, prompt: str, system_prompt: str = None) -> str:
        """调用AI服务"""
        try:
            system_prompt = system_prompt or self.get_system_prompt()
            response = self.ai_client.generate_text(prompt, system_prompt)
            return response
        except Exception as e:
            self.logger.error(f"AI调用失败: {e}")
            raise
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计"""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'success_rate': 0,
                'average_duration': 0,
                'total_duration': 0
            }
        
        total = len(self.execution_history)
        successful = sum(1 for record in self.execution_history if record['success'])
        total_duration = sum(record['duration'] for record in self.execution_history)
        
        return {
            'total_executions': total,
            'success_rate': successful / total,
            'average_duration': total_duration / total,
            'total_duration': total_duration,
            'last_execution': self.execution_history[-1]['start_time']
        }
    
    def export_execution_log(self, output_path: str) -> str:
        """导出执行日志"""
        import json
        
        log_data = {
            'agent_info': {
                'name': self.name,
                'description': self.description,
                'created_at': self.created_at
            },
            'statistics': self.get_execution_stats(),
            'execution_history': self.execution_history
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        return str(output_file)
    
    def __str__(self) -> str:
        return f"Agent({self.name}): {self.description}"
    
    def __repr__(self) -> str:
        stats = self.get_execution_stats()
        return f"<Agent {self.name} - {stats['total_executions']} executions, {stats['success_rate']:.1%} success>"