#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
临时修复脚本 - 添加缺失的 /api/ai/current 端点
"""

import re

def fix_backend_api():
    """修复后端API，添加缺失的端点"""
    
    # 读取原文件
    with open('backend_api_server.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找插入位置 - 在 get_ai_providers_list 之前
    pattern = r'(\s+@self\.app\.get\("/api/ai/providers/list"\))'
    
    # 要插入的代码
    new_endpoint = '''
        @self.app.get("/api/ai/current")
        async def get_current_ai_config():
            """获取当前AI配置"""
            current_provider = None
            for provider in self.ai_providers:
                if provider["id"] == self.current_ai_provider:
                    current_provider = provider
                    break
            
            if current_provider:
                return {
                    "current_provider": current_provider["id"],
                    "current_model": current_provider["default_model"],
                    "provider_name": current_provider["name"],
                    "provider_type": current_provider["type"],
                    "status": current_provider["status"]
                }
            else:
                return {
                    "current_provider": "ollama",
                    "current_model": "qwen2.5:1.5b",
                    "provider_name": "Ollama",
                    "provider_type": "local",
                    "status": "available"
                }
        
\\1'''
    
    # 检查是否已经存在这个端点
    if '/api/ai/current' in content:
        print("✅ /api/ai/current 端点已存在")
        return True
    
    # 执行替换
    new_content = re.sub(pattern, new_endpoint, content)
    
    if new_content != content:
        # 写入修改后的文件
        with open('backend_api_server.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ 成功添加 /api/ai/current 端点")
        return True
    else:
        print("❌ 未找到插入位置")
        return False

if __name__ == "__main__":
    fix_backend_api()