#!/usr/bin/env python3
"""Try multiple YApi URL variants to find which one works"""
import sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'https://yapi.szhibu.com'
PID = 489
TOKEN = 'c04bfe9b326c50459b30ad8aac90c5449b72d220c9577cf1386ad1df8552debfd'

urls = [
    # 1. open plugin export - OpenAPIV2
    f"{BASE}/api/open/plugin/export-full?type=OpenAPIV2&pid={PID}&status=all&token={TOKEN}",
    # 2. open plugin export - json (YApi native)
    f"{BASE}/api/open/plugin/export-full?type=json&pid={PID}&status=all&token={TOKEN}",
    # 3. non-open plugin export
    f"{BASE}/api/plugin/export-full?type=OpenAPIV2&pid={PID}&status=all&token={TOKEN}",
    # 4. non-open plugin export json
    f"{BASE}/api/plugin/export-full?type=json&pid={PID}&status=all&token={TOKEN}",
    # 5. interface list menu (no auth needed sometimes)
    f"{BASE}/api/interface/list_menu?project_id={PID}&token={TOKEN}",
    # 6. open interface list
    f"{BASE}/api/open/interface/list_menu?project_id={PID}&token={TOKEN}",
    # 7. project info
    f"{BASE}/api/project/get?id={PID}&token={TOKEN}",
    # 8. open project info
    f"{BASE}/api/open/project/get?id={PID}&token={TOKEN}",
]

for i, url in enumerate(urls, 1):
    short = url.replace(TOKEN, 'TOKEN')
    try:
        r = requests.get(url, timeout=10, verify=True)
        body = r.text[:200]
        try:
            d = r.json()
            errcode = d.get('errcode', 'none')
            has_swagger = 'swagger' in d or 'openapi' in d
            top_keys = list(d.keys())[:5]
            if isinstance(d.get('data'), list):
                data_info = f"data is list[{len(d['data'])}]"
            elif isinstance(d.get('data'), dict):
                data_info = f"data keys: {list(d['data'].keys())[:5]}"
            else:
                data_info = f"data={d.get('data')}"
            print(f"[{i}] HTTP {r.status_code} | errcode={errcode} | swagger={has_swagger} | {data_info}")
        except:
            print(f"[{i}] HTTP {r.status_code} | NOT JSON | {body[:80]}")
    except Exception as e:
        print(f"[{i}] ERROR: {e}")
    print(f"    {short}")
    print()
