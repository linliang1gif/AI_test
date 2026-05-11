#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自修复引擎

pytest执行失败后自动分析错误并修复代码：
1. 收集错误日志
2. 发送给AI分析
3. AI生成修复后的代码
4. 自动修改脚本
5. 重新执行pytest
"""

import os
import time
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 知识库（懒加载）
try:
    from knowledge.healing_knowledge import HealingKnowledge, THRESHOLD_HIT as HEALING_THRESHOLD
    _healing_knowledge = HealingKnowledge()
except Exception:
    _healing_knowledge = None
    HEALING_THRESHOLD = 0.80

class SelfHealingEngine:
    """自修复引擎"""
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.healing_history = []
        
        # 导入其他模块
        from .error_analyzer import ErrorAnalyzer
        from .code_fixer import CodeFixer
        
        self.error_analyzer = ErrorAnalyzer()
        self.code_fixer = CodeFixer()
    
    def run_with_healing(self, test_files: List[str], pytest_args: List[str] = None) -> Dict[str, Any]:
        """运行测试并在失败时自动修复"""
        pytest_args = pytest_args or ['-v', '--tb=short']
        
        healing_result = {
            'success': False,
            'total_attempts': 0,
            'healing_attempts': [],
            'final_result': None,
            'healing_history': []
        }
        
        for attempt in range(self.max_retries + 1):
            healing_result['total_attempts'] = attempt + 1
            
            logger.info(f"\n🔄 执行测试 - 第 {attempt + 1} 次尝试")
            
            # 执行pytest
            test_result = self._run_pytest(test_files, pytest_args)
            
            if test_result['success']:
                logger.info("✅ 测试执行成功！")
                healing_result['success'] = True
                healing_result['final_result'] = test_result
                break
            
            if attempt >= self.max_retries:
                logger.info(f"❌ 达到最大重试次数 ({self.max_retries})，停止自修复")
                healing_result['final_result'] = test_result
                break
            
            # 分析错误并尝试修复
            logger.info(f"🔍 分析错误并尝试修复...")
            
            healing_attempt = self._attempt_healing(test_result, attempt + 1)
            healing_result['healing_attempts'].append(healing_attempt)
            
            if not healing_attempt['fixed']:
                logger.info(f"❌ 第 {attempt + 1} 次修复失败")
                healing_result['final_result'] = test_result
                break
            
            logger.info(f"✅ 第 {attempt + 1} 次修复完成，等待 {self.retry_delay} 秒后重试...")
            time.sleep(self.retry_delay)
        
        return healing_result
    
    def _run_pytest(self, test_files: List[str], pytest_args: List[str]) -> Dict[str, Any]:
        """执行pytest测试"""
        try:
            # 构建pytest命令
            cmd = ['python', '-m', 'pytest'] + pytest_args + test_files
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'pytest执行超时',
                'command': ' '.join(cmd)
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f'执行pytest失败: {str(e)}',
                'command': ' '.join(cmd)
            }
    
    def _attempt_healing(self, test_result: Dict[str, Any], attempt_number: int) -> Dict[str, Any]:
        """尝试修复测试"""
        healing_attempt = {
            'attempt_number': attempt_number,
            'timestamp': time.time(),
            'errors_analyzed': [],
            'fixes_applied': [],
            'fixed': False,
            'error_message': ''
        }
        
        try:
            # 1. 分析错误
            logger.info("  📊 分析测试错误...")
            errors = self.error_analyzer.analyze_pytest_output(
                test_result['stdout'], 
                test_result['stderr']
            )
            
            healing_attempt['errors_analyzed'] = errors
            
            if not errors:
                healing_attempt['error_message'] = '未找到可分析的错误'
                return healing_attempt
            
            # 2. 为每个错误生成修复方案
            logger.info(f"  🔧 为 {len(errors)} 个错误生成修复方案...")
            
            all_fixes_successful = True
            
            for error in errors:
                fix_result = self._fix_single_error(error)
                healing_attempt['fixes_applied'].append(fix_result)
                
                if not fix_result['success']:
                    all_fixes_successful = False
                    logger.info(f"    ❌ 修复失败: {fix_result['error']}")
                else:
                    logger.info(f"    ✅ 修复成功: {fix_result['file_path']}")
            
            healing_attempt['fixed'] = all_fixes_successful
            
            if all_fixes_successful:
                logger.info("  🎉 所有错误修复完成")
            else:
                healing_attempt['error_message'] = '部分错误修复失败'
            
        except Exception as e:
            healing_attempt['error_message'] = f'修复过程异常: {str(e)}'
            logger.info(f"  ❌ 修复过程异常: {e}")
        
        # 记录修复历史
        self.healing_history.append(healing_attempt)
        
        return healing_attempt
    
    def _fix_single_error(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """修复单个错误（RAG增强版）"""
        fix_result = {
            'error_type': error.get('type', 'unknown'),
            'file_path': error.get('file_path', ''),
            'success': False,
            'error': '',
            'changes_made': [],
            'from_knowledge_base': False,
            'pattern_id': None
        }

        try:
            # 1. 检索历史修复方案
            matched_pattern = None
            if _healing_knowledge:
                try:
                    patterns = _healing_knowledge.search_fix_pattern(error, top_k=3)
                    if patterns and patterns[0]['similarity'] >= HEALING_THRESHOLD:
                        matched_pattern = patterns[0]
                except Exception as _e:
                    logger.debug("[P2] self-healing fallback: %s", _e)

            file_path = Path(error.get('file_path', ''))
            if not file_path.exists():
                fix_result['error'] = f'文件不存在: {file_path}'
                return fix_result

            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()

            # 2. 命中历史修复，直接应用
            if matched_pattern:
                fixed_code = matched_pattern['fix_pattern']
                logger.info(f"  ✅ 命中历史修复方案（相似度 {matched_pattern['similarity']:.2f}），跳过AI生成")
                fix_result['from_knowledge_base'] = True
                fix_result['pattern_id'] = matched_pattern['pattern_id']
            else:
                # 3. AI 生成修复代码
                fixed_code = self.code_fixer.fix_code(
                    original_code=original_code,
                    error_info=error,
                    file_path=str(file_path)
                )

            if not fixed_code or fixed_code == original_code:
                fix_result['error'] = 'AI未能生成有效的修复代码'
                if matched_pattern and _healing_knowledge:
                    try:
                        _healing_knowledge.update_pattern_result(matched_pattern['pattern_id'], False)
                    except Exception as _e:
                        logger.debug("[P2] self-healing fallback: %s", _e)
                return fix_result

            # 备份原文件
            backup_path = file_path.with_suffix(f'{file_path.suffix}.backup.{int(time.time())}')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_code)

            # 写入修复后的代码
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_code)

            fix_result['success'] = True
            fix_result['changes_made'] = [
                f'备份原文件到: {backup_path}',
                f'应用{"历史" if matched_pattern else "AI"}修复到: {file_path}'
            ]

            # 4. 更新/入库修复结果
            if _healing_knowledge:
                try:
                    if matched_pattern:
                        _healing_knowledge.update_pattern_result(matched_pattern['pattern_id'], True)
                    else:
                        # AI 生成的新方案入库
                        _healing_knowledge.save_healing_pattern(
                            error_type=error.get('type', 'unknown'),
                            error_snippet=error.get('message', '')[:300],
                            fix_code=fixed_code,
                            success=True
                        )
                except Exception as _e:
                    logger.debug("[P2] self-healing fallback: %s", _e)

        except Exception as e:
            fix_result['error'] = str(e)

        return fix_result
    
    def get_healing_summary(self) -> Dict[str, Any]:
        """获取修复摘要"""
        total_attempts = len(self.healing_history)
        successful_fixes = sum(1 for attempt in self.healing_history if attempt['fixed'])
        
        return {
            'total_healing_attempts': total_attempts,
            'successful_fixes': successful_fixes,
            'success_rate': successful_fixes / total_attempts if total_attempts > 0 else 0,
            'healing_history': self.healing_history
        }
    
    def export_healing_report(self, output_path: str) -> str:
        """导出修复报告"""
        import json
        
        report = {
            'timestamp': time.time(),
            'summary': self.get_healing_summary(),
            'detailed_history': self.healing_history
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return str(output_file)