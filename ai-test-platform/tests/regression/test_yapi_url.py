#!/usr/bin/env python3
import sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://yapi.szhibu.com/api/open/plugin/export-full?type=OpenAPIV2&pid=489&status=all&token=c04bfe9b326c50459b30ad8aac90c5449b72d220c9577cf1386ad1df8552debfd'

try:
    r = requests.get(url, timeout=15, verify=True)
    print(f"HTTP {r.status_code}")
    print(f"Content-Type: {r.headers.get('Content-Type', '?')}")
    text = r.text[:800]
    print(f"Body preview:\n{text}")
    try:
        d = r.json()
        keys = list(d.keys())[:15]
        print(f"\nJSON top keys: {keys}")
        print(f"Has 'swagger' key: {'swagger' in d}")
        print(f"Has 'openapi' key: {'openapi' in d}")
        # Check if it's wrapped in errcode
        if 'errcode' in d:
            print(f"errcode: {d['errcode']}, errmsg: {d.get('errmsg','')}")
        if 'data' in d:
            inner = d['data']
            if isinstance(inner, dict):
                print(f"data keys: {list(inner.keys())[:10]}")
                print(f"data has swagger: {'swagger' in inner}")
                print(f"data has openapi: {'openapi' in inner}")
    except Exception as e:
        print(f"JSON parse error: {e}")
except Exception as e:
    print(f"Request error: {e}")
