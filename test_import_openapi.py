#!/usr/bin/env python3
import requests

BACKEND_URL = "http://localhost:8000"
PROJECT_ID = 8
FILE_PATH = r"D:\360Downloads\蓝点\api.json"

url = f"{BACKEND_URL}/api/v2/swagger/import-file?project_id={PROJECT_ID}&generate_cases=false"

with open(FILE_PATH, 'rb') as f:
    files = {'file': ('api.json', f, 'application/json')}
    response = requests.post(url, files=files, timeout=60)

print(f"状态码: {response.status_code}")
print(f"响应: {response.text[:1000]}")
