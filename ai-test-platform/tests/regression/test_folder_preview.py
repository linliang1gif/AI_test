import requests, json

r = requests.post("http://127.0.0.1:8001/api/ai/folder-preview", json={
    "folder_path": r"G:\需求\付款单-企业小程序_v1.2.3_files"
})
print(f"HTTP {r.status_code}")
d = r.json()
print(f"success={d.get('success')}")
s = d.get("structured", {}).get("stats", {})
print(f"stats: annotations={s.get('axure_notes')}, features={s.get('features')}, rules={s.get('rules')}")
print(f"raw_text_length={d.get('raw_text_length')}")
notes = d.get("structured", {}).get("axure_notes", [])
print(f"axure_notes count={len(notes)}")
if notes:
    print(f"  first: {notes[0][:80]}")
