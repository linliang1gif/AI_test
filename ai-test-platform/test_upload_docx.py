#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试Word文档上传"""

import requests

# 测试文件上传
files = {'file': open('../需求文档.docx', 'rb')}

try:
    response = requests.post('http://localhost:8000/api/testcases/generate', files=files)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {response.headers}")
    print(f"响应内容: {response.text[:500]}")
except Exception as e:
    print(f"错误: {e}")
