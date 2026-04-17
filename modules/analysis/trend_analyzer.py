"""
趋势分析器
分析测试结果的历史趋势
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
import os


class TrendAnalyzer:
    """趋势分析器"""
    
    def __init__(self, storage_path: str = "test_history"):
        """
        初始化趋势分析器
        
        Args:
            storage_path: 历史数据存储路径
        """
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def save_execution_record(self, execution_id: str, results: List[Any], metadata: Optional[Dict] = None):
        """
        保存执行记录
        
        Args:
            execution_id: 执行ID
            results: 测试结果列表
            metadata: 元数据（如触发方式、分支、提交ID等）
        """
        record = {
            'execution_id': execution_id,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
            'summary': self._generate_summary(results)
        }
        
        # 保存到文件
        filename = f"{execution_id}.json"
        filepath = os.path.join(self.storage_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
    
    def _generate_summary(self, results: List[Any]) -> Dict[str, Any]:
        """生成执行摘要"""
        from core import TestCaseStatus
        
        total = len(results)
        if total == 0:
            return {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'pass_rate': 0.0,
                'total_duration': 0.0
            }
        
        passed = sum(1 for r in results if r.status == TestCaseStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestCaseStatus.FAILED)
        total_duration = sum(r.duration for r in results)
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': round(passed / total * 100, 2),
            'total_duration': round(total_duration, 2)
        }
    
    def analyze_trend(self, days: int = 7) -> Dict[str, Any]:
        """
        分析趋势
        
        Args:
            days: 分析最近N天的数据
            
        Returns:
            趋势分析报告
        """
        # 加载历史记录
        records = self._load_recent_records(days)
        
        if not records:
            return {
                'period': f'最近{days}天',
                'total_executions': 0,
                'trend': {},
                'insights': []
            }
        
        # 按时间排序
        records.sort(key=lambda x: x['timestamp'])
        
        # 计算趋势
        trend_data = {
            'pass_rate_trend': [],
            'execution_count_trend': [],
            'duration_trend': [],
            'failure_trend': []
        }
        
        for record in records:
            summary = record['summary']
            timestamp = record['timestamp']
            
            trend_data['pass_rate_trend'].append({
                'timestamp': timestamp,
                'value': summary['pass_rate']
            })
            
            trend_data['execution_count_trend'].append({
                'timestamp': timestamp,
                'value': summary['total']
            })
            
            trend_data['duration_trend'].append({
                'timestamp': timestamp,
                'value': summary['total_duration']
            })
            
            trend_data['failure_trend'].append({
                'timestamp': timestamp,
                'value': summary['failed']
            })
        
        # 生成洞察
        insights = self._generate_insights(records, trend_data)
        
        return {
            'period': f'最近{days}天',
            'total_executions': len(records),
            'trend': trend_data,
            'insights': insights,
            'summary': self._calculate_period_summary(records)
        }
    
    def _load_recent_records(self, days: int) -> List[Dict]:
        """加载最近N天的记录"""
        cutoff_date = datetime.now() - timedelta(days=days)
        records = []
        
        if not os.path.exists(self.storage_path):
            return records
        
        for filename in os.listdir(self.storage_path):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.storage_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    record = json.load(f)
                    
                # 检查时间
                record_time = datetime.fromisoformat(record['timestamp'])
                if record_time >= cutoff_date:
                    records.append(record)
            except Exception as e:
                print(f"加载记录失败 {filename}: {e}")
                continue
        
        return records
    
    def _generate_insights(self, records: List[Dict], trend_data: Dict) -> List[Dict[str, str]]:
        """生成趋势洞察"""
        insights = []
        
        if len(records) < 2:
            return insights
        
        # 分析通过率趋势
        pass_rates = [item['value'] for item in trend_data['pass_rate_trend']]
        if len(pass_rates) >= 3:
            recent_avg = sum(pass_rates[-3:]) / 3
            earlier_avg = sum(pass_rates[:3]) / 3
            
            if recent_avg > earlier_avg + 5:
                insights.append({
                    'type': 'improvement',
                    'message': f'通过率呈上升趋势，从 {earlier_avg:.1f}% 提升到 {recent_avg:.1f}%'
                })
            elif recent_avg < earlier_avg - 5:
                insights.append({
                    'type': 'degradation',
                    'message': f'通过率呈下降趋势，从 {earlier_avg:.1f}% 降至 {recent_avg:.1f}%'
                })
        
        # 分析执行时间趋势
        durations = [item['value'] for item in trend_data['duration_trend']]
        if len(durations) >= 3:
            recent_avg = sum(durations[-3:]) / 3
            earlier_avg = sum(durations[:3]) / 3
            
            if recent_avg > earlier_avg * 1.2:
                insights.append({
                    'type': 'performance',
                    'message': f'执行时间增加了 {((recent_avg/earlier_avg - 1) * 100):.1f}%，建议检查性能'
                })
        
        # 分析失败趋势
        failures = [item['value'] for item in trend_data['failure_trend']]
        recent_failures = sum(failures[-3:]) if len(failures) >= 3 else sum(failures)
        
        if recent_failures > 10:
            insights.append({
                'type': 'stability',
                'message': f'最近失败用例较多 ({recent_failures}个)，建议关注稳定性'
            })
        
        return insights
    
    def _calculate_period_summary(self, records: List[Dict]) -> Dict[str, Any]:
        """计算周期汇总"""
        if not records:
            return {}
        
        total_executions = len(records)
        total_tests = sum(r['summary']['total'] for r in records)
        total_passed = sum(r['summary']['passed'] for r in records)
        total_failed = sum(r['summary']['failed'] for r in records)
        total_duration = sum(r['summary']['total_duration'] for r in records)
        
        avg_pass_rate = sum(r['summary']['pass_rate'] for r in records) / total_executions
        
        return {
            'total_executions': total_executions,
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'avg_pass_rate': round(avg_pass_rate, 2),
            'total_duration': round(total_duration, 2),
            'avg_duration_per_execution': round(total_duration / total_executions, 2)
        }
    
    def compare_executions(self, execution_id1: str, execution_id2: str) -> Dict[str, Any]:
        """
        对比两次执行
        
        Args:
            execution_id1: 第一次执行ID
            execution_id2: 第二次执行ID
            
        Returns:
            对比报告
        """
        record1 = self._load_record(execution_id1)
        record2 = self._load_record(execution_id2)
        
        if not record1 or not record2:
            return {'error': '无法加载执行记录'}
        
        summary1 = record1['summary']
        summary2 = record2['summary']
        
        return {
            'execution1': {
                'id': execution_id1,
                'timestamp': record1['timestamp'],
                'summary': summary1
            },
            'execution2': {
                'id': execution_id2,
                'timestamp': record2['timestamp'],
                'summary': summary2
            },
            'comparison': {
                'pass_rate_change': round(summary2['pass_rate'] - summary1['pass_rate'], 2),
                'duration_change': round(summary2['total_duration'] - summary1['total_duration'], 2),
                'test_count_change': summary2['total'] - summary1['total']
            }
        }
    
    def _load_record(self, execution_id: str) -> Optional[Dict]:
        """加载单个记录"""
        filepath = os.path.join(self.storage_path, f"{execution_id}.json")
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载记录失败: {e}")
            return None
