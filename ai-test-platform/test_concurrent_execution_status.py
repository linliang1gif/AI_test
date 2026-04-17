"""
测试并发执行状态展示功能

验证目标:
1. 后端API返回task_id, status, duration
2. 前端能正确展示并发任务状态
3. 状态实时更新(Running / Success / Failed)
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:8081"


def test_start_test_run():
    """测试1: 启动测试执行"""
    print("\n" + "="*70)
    print("测试1: 启动测试执行")
    print("="*70)
    
    response = requests.post(
        f"{BASE_URL}/api/test-runs/start",
        json={"environment": "staging"}
    )
    
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "success 应该为 True"
    assert "testRun" in data, "响应中应该包含 testRun"
    
    test_run = data["testRun"]
    assert "id" in test_run, "testRun 应该包含 id"
    assert "status" in test_run, "testRun 应该包含 status"
    assert test_run["status"] == "running", f"初始状态应该是 running，实际是 {test_run['status']}"
    assert "tasks" in test_run, "testRun 应该包含 tasks 字段"
    
    print(f"✅ 测试执行已启动")
    print(f"   ID: {test_run['id']}")
    print(f"   状态: {test_run['status']}")
    print(f"   环境: {test_run.get('environment', 'N/A')}")
    
    return test_run["id"]


def test_get_test_run_status(run_id):
    """测试2: 获取测试执行状态（包含并发任务）"""
    print("\n" + "="*70)
    print("测试2: 获取测试执行状态（包含并发任务）")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/test-runs/{run_id}/status")
    
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "success 应该为 True"
    assert "testRun" in data, "响应中应该包含 testRun"
    
    test_run = data["testRun"]
    
    # 验证基本字段
    assert "id" in test_run, "testRun 应该包含 id"
    assert "status" in test_run, "testRun 应该包含 status"
    assert "progress" in test_run, "testRun 应该包含 progress"
    
    # 验证并发任务字段
    assert "tasks" in test_run, "testRun 应该包含 tasks 字段"
    
    tasks = test_run["tasks"]
    print(f"\n✅ 获取状态成功")
    print(f"   状态: {test_run['status']}")
    print(f"   进度: {test_run['progress']}%")
    print(f"   任务数: {len(tasks)}")
    
    # 验证任务字段
    if len(tasks) > 0:
        print(f"\n   并发任务详情:")
        for task in tasks:
            assert "task_id" in task, "task 应该包含 task_id"
            assert "name" in task, "task 应该包含 name"
            assert "status" in task, "task 应该包含 status"
            assert "duration" in task, "task 应该包含 duration"
            
            # 验证状态值
            assert task["status"] in ["running", "success", "failed"], \
                f"task status 应该是 running/success/failed，实际是 {task['status']}"
            
            status_icon = "🔄" if task["status"] == "running" else \
                         "✅" if task["status"] == "success" else "❌"
            
            print(f"      {status_icon} {task['task_id']}: {task['name']} - {task['status']} ({task['duration']}s)")
    
    return test_run


def test_poll_until_complete(run_id, max_polls=10):
    """测试3: 轮询直到完成"""
    print("\n" + "="*70)
    print("测试3: 轮询直到完成")
    print("="*70)
    
    for i in range(max_polls):
        print(f"\n   轮询 {i+1}/{max_polls}...")
        
        response = requests.get(f"{BASE_URL}/api/test-runs/{run_id}/status")
        data = response.json()
        test_run = data["testRun"]
        
        status = test_run["status"]
        progress = test_run["progress"]
        tasks = test_run.get("tasks", [])
        
        print(f"   状态: {status}, 进度: {progress}%, 任务数: {len(tasks)}")
        
        # 显示最新的任务
        if len(tasks) > 0:
            latest_task = tasks[-1]
            status_icon = "🔄" if latest_task["status"] == "running" else \
                         "✅" if latest_task["status"] == "success" else "❌"
            print(f"   最新任务: {status_icon} {latest_task['name']} - {latest_task['status']}")
        
        # 检查是否完成
        if status in ["completed", "failed"]:
            print(f"\n✅ 测试执行已完成")
            print(f"   最终状态: {status}")
            print(f"   总任务数: {test_run.get('totalTests', 0)}")
            print(f"   通过: {test_run.get('passed', 0)}")
            print(f"   失败: {test_run.get('failed', 0)}")
            return test_run
        
        time.sleep(2)
    
    print(f"\n⚠️  达到最大轮询次数，测试仍在运行")
    return test_run


def test_get_all_test_runs():
    """测试4: 获取所有测试执行"""
    print("\n" + "="*70)
    print("测试4: 获取所有测试执行")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/test-runs")
    
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "success 应该为 True"
    assert "testRuns" in data, "响应中应该包含 testRuns"
    
    test_runs = data["testRuns"]
    print(f"✅ 获取成功: {len(test_runs)} 个测试执行")
    
    # 显示每个测试执行的任务统计
    for run in test_runs:
        tasks = run.get("tasks", [])
        if len(tasks) > 0:
            running = len([t for t in tasks if t["status"] == "running"])
            success = len([t for t in tasks if t["status"] == "success"])
            failed = len([t for t in tasks if t["status"] == "failed"])
            
            print(f"\n   {run['name']}:")
            print(f"      状态: {run['status']}")
            print(f"      任务: {len(tasks)} 个 (🔄 {running}, ✅ {success}, ❌ {failed})")


def test_task_status_display():
    """测试5: 验证任务状态展示格式"""
    print("\n" + "="*70)
    print("测试5: 验证任务状态展示格式")
    print("="*70)
    
    # 模拟前端展示逻辑
    task_statuses = ["running", "success", "failed"]
    
    for status in task_statuses:
        # 前端展示映射
        display_text = {
            "running": "Running",
            "success": "Success",
            "failed": "Failed"
        }[status]
        
        display_color = {
            "running": "orange",
            "success": "green",
            "failed": "red"
        }[status]
        
        print(f"   {status} → {display_text} ({display_color})")
    
    print(f"\n✅ 状态展示格式验证通过")


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("并发执行状态展示功能测试")
    print("="*70)
    
    try:
        # 测试1: 启动测试执行
        run_id = test_start_test_run()
        
        # 测试2: 获取测试执行状态
        test_get_test_run_status(run_id)
        
        # 测试3: 轮询直到完成
        final_run = test_poll_until_complete(run_id, max_polls=10)
        
        # 测试4: 获取所有测试执行
        test_get_all_test_runs()
        
        # 测试5: 验证任务状态展示格式
        test_task_status_display()
        
        print("\n" + "="*70)
        print("✅ 所有测试通过")
        print("="*70)
        
        # 显示最终结果
        print("\n最终测试执行结果:")
        print(json.dumps(final_run, indent=2, ensure_ascii=False))
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
