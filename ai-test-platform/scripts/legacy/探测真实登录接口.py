#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
探测真实系统的登录接口

用于分析 https://dev-recycle.szhibu.com 的登录机制
"""

import requests
import json
from bs4 import BeautifulSoup
import re

def explore_login_system():
    """探测登录系统的接口和机制"""
    base_url = "https://dev-recycle.szhibu.com"
    
    print("🔍 开始探测回收系统登录机制")
    print("=" * 50)
    
    # 1. 访问首页，分析登录表单
    print("1. 访问首页分析...")
    try:
        response = requests.get(f"{base_url}/index", timeout=15, verify=False)
        print(f"   首页状态码: {response.status_code}")
        print(f"   响应时间: {len(response.content)} bytes")
        
        # 分析HTML内容，查找登录表单
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找表单
        forms = soup.find_all('form')
        print(f"   找到 {len(forms)} 个表单")
        
        for i, form in enumerate(forms):
            action = form.get('action', '无action')
            method = form.get('method', 'GET')
            print(f"   表单{i+1}: action='{action}', method='{method}'")
            
            # 查找输入字段
            inputs = form.find_all('input')
            for inp in inputs:
                name = inp.get('name', '')
                type_attr = inp.get('type', '')
                if name:
                    print(f"     输入字段: name='{name}', type='{type_attr}'")
        
        # 查找可能的登录相关JavaScript
        scripts = soup.find_all('script')
        print(f"   找到 {len(scripts)} 个脚本标签")
        
        for script in scripts:
            if script.string:
                # 查找可能的API端点
                api_matches = re.findall(r'["\'](/api/[^"\']*)["\']', script.string)
                if api_matches:
                    print(f"   发现API端点: {api_matches}")
                
                # 查找可能的登录函数
                login_matches = re.findall(r'(login|Login|signin|SignIn)[^(]*\([^)]*\)', script.string)
                if login_matches:
                    print(f"   发现登录函数: {login_matches[:3]}")  # 只显示前3个
        
    except Exception as e:
        print(f"   访问首页失败: {e}")
    
    # 2. 尝试常见的登录接口
    print("\n2. 尝试常见登录接口...")
    login_endpoints = [
        "/api/login",
        "/api/auth/login", 
        "/api/user/login",
        "/login",
        "/auth/login",
        "/api/v1/login",
        "/api/v1/auth/login",
        "/system/login",
        "/admin/login",
        "/user/login"
    ]
    
    test_data = {
        "username": "ldsit",
        "password": "654321",
        "merchant_id": "1014"
    }
    
    for endpoint in login_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"   测试: {endpoint}")
            
            # 尝试POST请求
            response = requests.post(
                url,
                json=test_data,
                timeout=10,
                verify=False,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            print(f"     状态码: {response.status_code}")
            if response.status_code != 404:
                print(f"     响应长度: {len(response.text)} bytes")
                if response.headers.get('content-type', '').startswith('application/json'):
                    try:
                        data = response.json()
                        print(f"     JSON响应: {str(data)[:100]}...")
                    except:
                        pass
                else:
                    print(f"     文本响应: {response.text[:100]}...")
            
        except Exception as e:
            print(f"     错误: {e}")
    
    # 3. 尝试GET方式访问登录相关页面
    print("\n3. 尝试访问登录相关页面...")
    login_pages = [
        "/login",
        "/login.html",
        "/login.jsp",
        "/admin",
        "/admin/login",
        "/system/login"
    ]
    
    for page in login_pages:
        try:
            url = f"{base_url}{page}"
            response = requests.get(url, timeout=10, verify=False)
            print(f"   {page}: 状态码 {response.status_code}")
            
            if response.status_code == 200:
                # 分析页面内容
                if 'login' in response.text.lower() or '登录' in response.text:
                    print(f"     ✅ 可能是登录页面")
                    
                    # 查找表单action
                    soup = BeautifulSoup(response.text, 'html.parser')
                    forms = soup.find_all('form')
                    for form in forms:
                        action = form.get('action')
                        if action:
                            print(f"     表单action: {action}")
                            
        except Exception as e:
            print(f"   {page}: 错误 {e}")
    
    print("\n" + "=" * 50)
    print("探测完成！")

if __name__ == "__main__":
    # 忽略SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    explore_login_system()