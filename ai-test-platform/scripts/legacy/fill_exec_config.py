"""为迭代1的测试用例填充 execution_config，关联真实磅秤系统API"""
import sqlite3, json, os

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "test_platform.db")

# 用例ID -> execution_config 映射
CONFIGS = {
    "TC_9_1_d62b39ba": {
        # 验证点击"监控"按钮后弹出监控弹窗 → 获取设备列表
        "method": "POST",
        "url": "/basic/basicDevice/page",
        "headers": {"Content-Type": "application/json"},
        "body": {"pageNo": 1, "pageSize": 20},
        "timeout": 10,
    },
    "TC_9_1_8561c956": {
        # 验证弹窗中播放所有绑定监控的实时画面 → 获取播放地址
        "method": "POST",
        "url": "/basic/basicDevice/getStream",
        "headers": {"Content-Type": "application/json"},
        "body": {"deviceSerial": "test_device"},
        "timeout": 10,
    },
    "TC_9_1_a2f0821c": {
        # 验证根据绑定监控台数自动调节画面尺寸 → 获取设备列表验证数量
        "method": "POST",
        "url": "/basic/basicDevice/page",
        "headers": {"Content-Type": "application/json"},
        "body": {"pageNo": 1, "pageSize": 100},
        "timeout": 10,
    },
    "TC_9_1_93d419e4": {
        # 验证双击放大预览 → 获取流地址验证有效性
        "method": "POST",
        "url": "/basic/basicDevice/getStream",
        "headers": {"Content-Type": "application/json"},
        "body": {"deviceSerial": "test_device"},
        "timeout": 10,
    },
    "TC_9_1_54c97b22": {
        # 验证摄像头方向调整 → PTZ控制
        "method": "POST",
        "url": "/basic/basicDevice/ptz",
        "headers": {"Content-Type": "application/json"},
        "body": {"deviceSerial": "test_device", "direction": "up", "speed": 1},
        "timeout": 10,
    },
}

conn = sqlite3.connect(DB)
c = conn.cursor()

updated = 0
for case_id, config in CONFIGS.items():
    config_json = json.dumps(config, ensure_ascii=False)
    c.execute("UPDATE test_cases SET execution_config=? WHERE id=?", (config_json, case_id))
    if c.rowcount > 0:
        updated += 1
        print(f"  [OK] {case_id} -> {config['method']} {config['url']}")
    else:
        print(f"  [SKIP] {case_id} not found")

conn.commit()
print(f"\nUpdated {updated}/{len(CONFIGS)} test cases")

# 同时重置执行集状态以便重新执行
c.execute("UPDATE iteration_execution_sets SET status='created', run_id=NULL WHERE iteration_id=1")
print(f"Reset execution set status to 'created'")

conn.commit()
conn.close()
