import requests

# 创建一个临时需求文档
with open("scripts/tmp_req.txt", "w", encoding="utf-8") as f:
    f.write("付款单功能需求：支持新增付款单、审核付款单、付款操作、查询付款单列表")

with open("scripts/tmp_req.txt", "rb") as f:
    resp = requests.post("http://127.0.0.1:8001/api/ai/generate-testcases-from-file", 
        files={"file": ("req.txt", f, "text/plain")},
        data={"module": "付款单", "count": "5", "provider": "mock"}
    )

print(f"HTTP {resp.status_code}")
d = resp.json()
print(f"success={d.get('success')}")
print(f"count={d.get('count')}")
print(f"saved_ids={d.get('saved_ids', [])[:3]}")
if d.get("error"):
    print(f"error={d['error']}")
    print(f"detail={d.get('detail')}")
    print(f"raw={d.get('raw_response_preview', '')[:200]}")
