"""
分析系统API接口
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from .integrated_report_system import IntegratedReportSystem
from core import ExecutionResult, TestCaseStatus


router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# 全局报告系统实例
report_system = IntegratedReportSystem()


class AnalysisRequest(BaseModel):
    """分析请求"""
    execution_id: str
    results: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None


class TrendRequest(BaseModel):
    """趋势分析请求"""
    days: int = 7


class ComparisonRequest(BaseModel):
    """对比请求"""
    execution_id1: str
    execution_id2: str


@router.post("/comprehensive")
async def generate_comprehensive_analysis(request: AnalysisRequest):
    """
    生成综合分析报告
    
    Args:
        request: 分析请求
        
    Returns:
        综合分析报告
    """
    try:
        # 转换结果数据
        results = _convert_to_execution_results(request.results)
        
        # 生成报告
        report = report_system.generate_comprehensive_report(
            execution_id=request.execution_id,
            results=results,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "report": report
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SaveReportRequest(BaseModel):
    """保存报告请求"""
    execution_id: str
    results: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    formats: Optional[List[str]] = None


@router.post("/save-report")
async def save_analysis_report(request: SaveReportRequest):
    """
    保存分析报告到文件
    
    Args:
        request: 保存报告请求
        
    Returns:
        保存的文件路径
    """
    try:
        formats = request.formats or ['json', 'html']
        
        # 转换结果数据
        execution_results = _convert_to_execution_results(request.results)
        
        # 保存报告
        file_paths = report_system.save_report(
            execution_id=request.execution_id,
            results=execution_results,
            metadata=request.metadata,
            output_dir="reports",
            formats=formats
        )
        
        return {
            "success": True,
            "file_paths": file_paths
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trend")
async def analyze_trend(request: TrendRequest):
    """
    分析测试趋势
    
    Args:
        request: 趋势分析请求
        
    Returns:
        趋势分析报告
    """
    try:
        trend_analysis = report_system.trend_analyzer.analyze_trend(days=request.days)
        
        return {
            "success": True,
            "trend_analysis": trend_analysis
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_executions(request: ComparisonRequest):
    """
    对比两次执行
    
    Args:
        request: 对比请求
        
    Returns:
        对比报告
    """
    try:
        comparison = report_system.trend_analyzer.compare_executions(
            execution_id1=request.execution_id1,
            execution_id2=request.execution_id2
        )
        
        if 'error' in comparison:
            raise HTTPException(status_code=404, detail=comparison['error'])
        
        return {
            "success": True,
            "comparison": comparison
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_execution_history(days: int = 7):
    """
    获取执行历史
    
    Args:
        days: 查询最近N天
        
    Returns:
        执行历史列表
    """
    try:
        records = report_system.trend_analyzer._load_recent_records(days)
        
        # 按时间倒序排序
        records.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "success": True,
            "total": len(records),
            "records": records
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(days: int = 7):
    """
    获取统计信息
    
    Args:
        days: 统计最近N天
        
    Returns:
        统计信息
    """
    try:
        trend_analysis = report_system.trend_analyzer.analyze_trend(days=days)
        
        stats = {
            "period": trend_analysis['period'],
            "total_executions": trend_analysis['total_executions'],
            "summary": trend_analysis.get('summary', {}),
            "insights": trend_analysis.get('insights', [])
        }
        
        return {
            "success": True,
            "statistics": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _convert_to_execution_results(results_data: List[Dict[str, Any]]) -> List[ExecutionResult]:
    """转换字典数据为ExecutionResult对象"""
    results = []
    
    for data in results_data:
        # 解析状态
        status_str = data.get('status', 'passed')
        if isinstance(status_str, str):
            status = TestCaseStatus[status_str.upper()]
        else:
            status = status_str
        
        # 解析时间
        start_time = data.get('start_time')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        elif start_time is None:
            start_time = datetime.now()
        
        end_time = data.get('end_time')
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)
        elif end_time is None:
            end_time = datetime.now()
        
        result = ExecutionResult(
            test_case_id=data.get('test_case_id', ''),
            status=status,
            duration=data.get('duration', 0.0),
            start_time=start_time,
            end_time=end_time,
            error=data.get('error'),
            response=data.get('response'),
            healing_applied=data.get('healing_applied', False),
            healing_level=data.get('healing_level'),
            healing_details=data.get('healing_details')
        )
        
        results.append(result)
    
    return results
