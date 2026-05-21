#!/usr/bin/env python3
"""Test YApi token with basic open API"""
import sys, requests
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'https://yapi.szhibu.com'
PID = 489
TOKEN = 'c04bfe9b326c50459b30ad8aac90c5449b72d220c9577cf1386ad1df8552debfd'

# Test 1: /api/project/get (documented open API)
print("=== Test /api/project/get ===")
r = requests.get(f"{BASE}/api/project/get", params={'id': PID, 'token': TOKEN}, timeout=10)
d = r.json()
print(f"  errcode: {d.get('errcode')}")
print(f"  errmsg: {d.get('errmsg')}")
if d.get('errcode') == 0:
    print(f"  project name: {d['data'].get('name', '?')}")

# Test 2: /api/interface/list_menu
print("\n=== Test /api/interface/list_menu ===")
r = requests.get(f"{BASE}/api/interface/list_menu", params={'project_id': PID, 'token': TOKEN}, timeout=10)
d = r.json()
print(f"  errcode: {d.get('errcode')}")
print(f"  errmsg: {d.get('errmsg')}")
if d.get('errcode') == 0 and isinstance(d.get('data'), list):
    total = sum(len(cat.get('list', [])) for cat in d['data'])
    print(f"  categories: {len(d['data'])}")
    print(f"  total interfaces: {total}")

# Test 3: /api/interface/list (paginated)
print("\n=== Test /api/interface/list ===")
r = requests.get(f"{BASE}/api/interface/list", params={
    'project_id': PID, 'token': TOKEN, 'page': 1, 'limit': 5
}, timeout=10)
d = r.json()
print(f"  errcode: {d.get('errcode')}")
print(f"  errmsg: {d.get('errmsg')}")
if d.get('errcode') == 0:
    data = d.get('data', {})
    if isinstance(data, dict):
        print(f"  count: {data.get('count', '?')}")
        items = data.get('list', [])
    elif isinstance(data, list):
        items = data
    else:
        items = []
    for item in items[:3]:
        print(f"    {item.get('method','?')} {item.get('path','?')} - {item.get('title','?')}")
