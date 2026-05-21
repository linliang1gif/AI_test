#!/usr/bin/env python3
"""测试文件夹生成接口"""
import requests

r = requests.post("http://127.0.0.1:8001/api/ai/generate-testcases-from-folder", json={
    "folder_path": r"G:\需求\付款单-企业小程序_v1.2.3_files",
    "count": 3,
    "provider": "mock",
})
print(f"HTTP {r.status_code}")
d = r.json()
print(f"success={d.get('success')}")
print(f"count={d.get('count')}")
print(f"saved_ids={d.get('saved_ids', [])[:5]}")
if d.get("error"):
    print(f"error={d.get('error')}")
    print(f"detail={d.get('detail')}")
