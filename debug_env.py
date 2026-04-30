#!/usr/bin/env python3
"""
调试环境变量读取
"""

import os
from pathlib import Path

def load_env():
    """加载环境变量"""
    env_file = Path(__file__).parent / ".env.bluedot"
    print(f"环境变量文件: {env_file}")
    print(f"文件存在: {env_file.exists()}")
    
    if env_file.exists():
        print(f"\n文件内容:")
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
        
        print(f"\n解析环境变量:")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    # 脱敏显示
                    if 'PASSWORD' in key or 'SECRET' in key:
                        display_value = f"{value[:2]}...{value[-2:]}" if len(value) > 4 else "***"
                    else:
                        display_value = value
                    print(f"  {key} = {display_value}")

if __name__ == "__main__":
    print("="*60)
    print("环境变量调试")
    print("="*60)
    
    load_env()
    
    print(f"\n读取到的配置:")
    print(f"  SSO_URL: {os.getenv('BLUEDOT_SSO_URL')}")
    print(f"  BASE_URL: {os.getenv('BLUEDOT_BASE_URL')}")
    print(f"  CLIENT_ID: {os.getenv('BLUEDOT_CLIENT_ID')}")
    print(f"  CLIENT_SECRET: {os.getenv('BLUEDOT_CLIENT_SECRET', '***')[:2]}...")
    print(f"  USERNAME: {os.getenv('BLUEDOT_USERNAME')}")
    print(f"  PASSWORD: {os.getenv('BLUEDOT_PASSWORD', '***')[:2]}...")
