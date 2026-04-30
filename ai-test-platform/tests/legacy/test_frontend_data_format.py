"""
测试前后端数据格式对齐
验证修复后的前端能正确显示后端返回的数据
"""
import requests
import json

def test_pipeline_data_format():
    """测试 Pipeline API 返回的数据格式"""
    print("=" * 70)
    print("测试前后端数据格式对齐")
    print("=" * 70)
    
    # 1. 调用 Pipeline API
    print("\n【步骤1】调用 Pipeline API")
    url = "http://localhost:8000/api/pipeline/run"
    
    payload = {
        "requirement": "测试支付模块的微信支付功能",
        "git_diff": "+def wechat_pay():\n+    return {'status': 'success'}",
        "priority": "P1",
        "use_case_generator": True
    }
    
    print(f"   请求: POST {url}")
    print(f"   参数: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        
        if response.status_code != 200:
            print(f"   ❌ API 调用失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
        
        result = response.json()
        print(f"   ✅ API 调用成功")
        
        # 2. 验证数据结构
        print("\n【步骤2】验证数据结构")
        
        # 验证顶层字段
        required_fields = ['trace_id', 'requirement', 'decision', 'timeline']
        for field in required_fields:
            if field in result:
                print(f"   ✅ {field}: 存在")
            else:
                print(f"   ❌ {field}: 缺失")
        
        # 3. 验证 execution 数据格式
        if 'execution' in result and result['execution']:
            print("\n【步骤3】验证 execution 数据格式")
            execution = result['execution']
            
            print(f"   execution.mode: {execution.get('mode')}")
            print(f"   execution.summary: {execution.get('summary')}")
            
            if 'results' in execution:
                print(f"   execution.results: {len(execution['results'])} 个任务")
                
                # 检查第一个 result 的格式
                if execution['results']:
                    first_result = execution['results'][0]
                    print(f"\n   第一个任务的字段:")
                    for key in first_result.keys():
                        print(f"      - {key}: {type(first_result[key]).__name__}")
                    
                    # 验证前端需要的字段
                    if 'case' in first_result:
                        print(f"   ✅ case 字段存在")
                        case = first_result['case']
                        print(f"      case.name: {case.get('name', 'N/A')}")
                    else:
                        print(f"   ❌ case 字段缺失")
                    
                    if 'status' in first_result:
                        print(f"   ✅ status 字段存在: {first_result['status']}")
                    else:
                        print(f"   ❌ status 字段缺失")
                    
                    if 'duration' in first_result:
                        print(f"   ✅ duration 字段存在: {first_result['duration']}")
                    else:
                        print(f"   ❌ duration 字段缺失")
        
        # 4. 验证 healing 数据格式
        if 'healing' in result and result['healing']:
            print("\n【步骤4】验证 healing 数据格式")
            healing = result['healing']
            
            if 'summary' in healing:
                print(f"   ✅ summary 字段存在")
                print(f"      total: {healing['summary'].get('total')}")
                print(f"      healed: {healing['summary'].get('healed')}")
                print(f"      failed: {healing['summary'].get('failed')}")
            else:
                print(f"   ❌ summary 字段缺失")
            
            if 'healed' in healing:
                print(f"   ✅ healed 字段存在: {len(healing['healed'])} 个任务")
            else:
                print(f"   ❌ healed 字段缺失")
            
            if 'failed' in healing:
                print(f"   ✅ failed 字段存在: {len(healing['failed'])} 个任务")
            else:
                print(f"   ❌ failed 字段缺失")
        
        # 5. 验证 timeline
        if 'timeline' in result:
            print("\n【步骤5】验证 timeline")
            timeline = result['timeline']
            print(f"   timeline 事件数: {len(timeline)}")
            
            total_duration = sum(event.get('duration', 0) for event in timeline)
            print(f"   总耗时: {total_duration:.2f}s")
            
            for event in timeline:
                stage = event.get('stage', 'unknown')
                duration = event.get('duration', 0)
                status = event.get('status', 'unknown')
                print(f"      - {stage}: {duration:.2f}s ({status})")
        
        # 6. 保存完整响应
        print("\n【步骤6】保存完整响应")
        output_file = "output/pipeline_response.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"   ✅ 已保存到: {output_file}")
        
        print("\n" + "=" * 70)
        print("✅ 测试完成")
        print("=" * 70)
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"   ❌ 请求超时")
        return False
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_pipeline_data_format()
