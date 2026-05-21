import requests
r = requests.get("http://127.0.0.1:8001/api/ai/providers")
for p in r.json()["providers"]:
    print(f"{p['id']}: {p['status']} -> {p['models']}")
