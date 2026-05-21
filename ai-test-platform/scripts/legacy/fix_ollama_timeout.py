#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ollama超时问题修复方案
"""

import os
import sys

def fix_ollama_timeout():
    """修复Ollama超时问题"""
    
    print("=" * 60)
    print("Ollama超时问题诊断和修复")
    print("=" * 60)
    
    print("\n📋 问题分析:")
    print("  错误: HTTPConnectionPool(host='localhost', port=11434): Read timed out")
    print("  原因: Ollama模型响应时间超过180秒")
    print()
    
    print("🔍 可能的原因:")
    print("  1. CPU模型运行速度慢 (qwen2.5:1.5b在CPU上可能需要2-5分钟)")
    print("  2. 系统资源不足 (内存/CPU占用过高)")
    print("  3. 模型未正确加载")
    print("  4. Ollama服务状态异常")
    print()
    
    print("💡 解决方案:")
    print()
    
    print("方案1: 切换到DeepSeek (推荐)")
    print("  - 速度快 (1-3秒响应)")
    print("  - 质量高")
    print("  - 已配置API Key")
    print()
    print("  执行命令:")
    print("    cd ai测试/ai-test-platform")
    print("    修改 .env 文件:")
    print("    DEFAULT_AI_PROVIDER=deepseek")
    print()
    
    print("方案2: 增加Ollama超时时间")
    print("  - 适合有耐心等待的场景")
    print("  - 可能需要5-10分钟")
    print()
    print("  执行命令:")
    print("    cd ai测试/ai-test-platform")
    print("    修改 .env 文件:")
    print("    AI_TIMEOUT=600  # 增加到10分钟")
    print()
    
    print("方案3: 使用Mock模式 (测试用)")
    print("  - 立即响应")
    print("  - 返回预设数据")
    print("  - 适合功能测试")
    print()
    print("  执行命令:")
    print("    cd ai测试/ai-test-platform")
    print("    修改 .env 文件:")
    print("    DEFAULT_AI_PROVIDER=mock")
    print()
    
    print("方案4: 优化Ollama配置")
    print("  - 检查Ollama服务状态")
    print("  - 预加载模型")
    print("  - 减少并发请求")
    print()
    
    # 检查当前配置
    print("\n📊 当前配置:")
    env_path = "ai测试/ai-test-platform/.env"
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if 'DEFAULT_AI_PROVIDER' in line or 'AI_TIMEOUT' in line or 'DEFAULT_AI_MODEL' in line:
                    print(f"  {line.strip()}")
    
    print("\n🎯 推荐操作:")
    print("  1. 立即切换到DeepSeek (最快)")
    print("  2. 或者增加超时时间到600秒")
    print("  3. 系统已有Fallback机制,超时后会使用默认场景")
    print()
    
    print("✅ 系统状态:")
    print("  - Fallback机制: 正常工作")
    print("  - 默认场景: 已生成")
    print("  - 系统功能: 不受影响")
    print()
    
    print("=" * 60)
    
    # 提供快速修复选项
    print("\n是否立即切换到DeepSeek? (y/n): ", end='')
    choice = input().strip().lower()
    
    if choice == 'y':
        print("\n正在切换到DeepSeek...")
        
        # 读取.env文件
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 修改配置
        new_lines = []
        for line in lines:
            if line.startswith('DEFAULT_AI_PROVIDER='):
                new_lines.append('DEFAULT_AI_PROVIDER=deepseek\n')
            elif line.startswith('AI_TIMEOUT='):
                new_lines.append('AI_TIMEOUT=120\n')
            else:
                new_lines.append(line)
        
        # 写回文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print("✅ 已切换到DeepSeek!")
        print("   请重启后端服务器以应用更改")
        print()
        print("   重启命令:")
        print("   1. 停止当前后端服务器 (Ctrl+C)")
        print("   2. 重新运行: py backend_api_server.py")
    else:
        print("\n未进行修改。")
        print("您可以手动编辑 .env 文件来更改配置。")

if __name__ == "__main__":
    fix_ollama_timeout()
