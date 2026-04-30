#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests

r = requests.get('http://localhost:8000/api/test-cases')
data = r.json()
cases = data.get('data', [])[:10]

print("当前测试用例标题:")
print("="*60)
for i, c in enumerate(cases, 1):
    title = c.get('title', 'N/A')
    print(f"{i}. {title}")
