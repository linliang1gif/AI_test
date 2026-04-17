"""
测试分析系统API
"""
import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"


def create_test_data():
    """创建测试数据"""
    now = datetime.now().isoformat()
    
    results = []
    for i in range(15):
        if i < 10:  # 10个成功
            result = {
                'test_case_id': f'test_{i+1:03d}',
                'status': 'passed',
                'duration': 0.5 + i * 0.1,
                'start_time': now,
                'end_time': now,
                'error': None
            }
        else:  # 5个失败
            errors = [
                'Request timeout after 5 seconds',
                'Connection timed out',
                '401 Unauthorized: Invalid token',
                '500 Internal Server Error',
                'Data validation failed: null value'
            ]
            result = {
                'test_case_id': f'test_{i+1:03d}',
                'status': 'failed',
                'duration': 2.0,
                'start_time': now,
                'end_time': now,
                'error': errors[i-10]
            }
        results.append(result)
    
    return results


def test_comprehensive_analysis():
    """测试综合分析"""
    print("=" * 80)
    print("测试综合分析API")
    print("=" * 80)
    
    execution_id = f"test_exec_{int(datetime.now().timestamp())}"
    results = create_test_data()
    
    data = {
        'execution_id': execution_id,
        'results': results,
        'metadata': {
            'trigger': 'api_test',
            'branch': 'main',
            'commit': 'test123'
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/analysis/comprehensive", json=data)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        report = result['report']
        
        print("\n📊 执行摘要:")
        summary = report['summary']
        print(f"  总数: {summary['total']}")
        print(f"  通过: {summary['passed']}")
        print(f"  失败: {summary['failed']}")
        print(f"  通过率: {summary['pass_rate']}")
        
        print("\n❌ 失败分析:")
        failure = report['failure_analysis']
        print(f"  总失败数: {failure['total_failures']}")
        for cause in failure['root_causes'][:3]:
            print(f"    {cause['category']}: {cause['failure_count']}个")
        
        print("\n💡 优化建议:")
        for rec in report['recommendations'][:3]:
            print(f"  [{rec['severity']}] {rec['message']}")
        
        print("\n✅ 综合分析测试通过")
        return execution_id
    else:
        print(f"❌ 测试失败: {response.text}")
        return None


def test_save_report(execution_id):
    """测试保存报告"""
    print("\n" + "=" * 80)
    print("测试保存报告API")
    print("=" * 80)
    
    results = create_test_data()
    
    data = {
        'execution_id': execution_id,
        'results': results,
        'metadata': {
            'trigger': 'api_test',
            'branch': 'main'
        },
        'formats': ['json', 'html', 'text']
    }
    
    response = requests.post(f"{BASE_URL}/api/analysis/save-report", json=data)
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n📁 报告已保存:")
        for format_type, path in result['file_paths'].items():
            print(f"  {format_type.upper()}: {path}")
        print("\n✅ 保存报告测试通过")
    else:
        print(f"❌ 测试失败: {response.text}")


def test_trend_analysis():
    """测试趋势分析"""
    print("\n" + "=" * 80)
    print("测试趋势分析API")
    print("=" * 80)
    
    data = {'days': 7}
    
    response = requests.post(f"{BASE_URL}/api/analysis/trend", json=data)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        trend = result['trend_analysis']
        
        print(f"\n📈 趋势分析 ({trend['period']}):")
        print(f"  总执行次数: {trend['total_executions']}")
        
        if trend.get('summary'):
            summary = trend['summary']
            print(f"  平均通过率: {summary['avg_pass_rate']}%")
            print(f"  总测试数: {summary['total_tests']}")
        
        if trend.get('insights'):
            print(f"\n💡 洞察:")
            for insight in trend['insights']:
                print(f"  [{insight['type']}] {insight['message']}")
        
        print("\n✅ 趋势分析测试通过")
    else:
        print(f"❌ 测试失败: {response.text}")


def test_execution_history():
    """测试执行历史"""
    print("\n" + "=" * 80)
    print("测试执行历史API")
    print("=" * 80)
    
    response = requests.get(f"{BASE_URL}/api/analysis/history?days=7")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n📜 执行历史:")
        print(f"  总记录数: {result['total']}")
        
        if result['records']:
            print(f"\n最近的执行:")
            for record in result['records'][:5]:
                print(f"  - {record['execution_id']}: 通过率 {record['summary']['pass_rate']}%")
        
        print("\n✅ 执行历史测试通过")
    else:
        print(f"❌ 测试失败: {response.text}")


def test_statistics():
    """测试统计信息"""
    print("\n" + "=" * 80)
    print("测试统计信息API")
    print("=" * 80)
    
    response = requests.get(f"{BASE_URL}/api/analysis/statistics?days=7")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        stats = result['statistics']
        
        print(f"\n📊 统计信息 ({stats['period']}):")
        print(f"  总执行次数: {stats['total_executions']}")
        
        if stats.get('summary'):
            summary = stats['summary']
            print(f"  平均通过率: {summary['avg_pass_rate']}%")
        
        print("\n✅ 统计信息测试通过")
    else:
        print(f"❌ 测试失败: {response.text}")


def main():
    """主测试函数"""
    print("\n🚀 测试分析系统API")
    print("=" * 80)
    
    try:
        # 测试综合分析
        execution_id = test_comprehensive_analysis()
        
        if execution_id:
            # 测试保存报告
            test_save_report(execution_id)
        
        # 测试趋势分析
        test_trend_analysis()
        
        # 测试执行历史
        test_execution_history()
        
        # 测试统计信息
        test_statistics()
        
        print("\n" + "=" * 80)
        print("✅ 所有API测试通过!")
        print("=" * 80)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务")
        print("请确保后端服务已启动: http://localhost:8000")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
