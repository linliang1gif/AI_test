#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实时监控知识库导入状态
"""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("📊 知识库导入状态监控")
print("=" * 70)

try:
    from knowledge.knowledge_manager import get_knowledge_manager
    
    km = get_knowledge_manager()
    
    print("\n开始监控... (每5秒刷新一次，按Ctrl+C停止)\n")
    
    last_api_count = 0
    last_backend_count = 0
    last_frontend_count = 0
    
    while True:
        try:
            stats = km.get_knowledge_stats()
            
            api_count = stats.get('apis', {}).get('total', 0)
            backend_count = stats.get('code', {}).get('backend', 0)
            frontend_count = stats.get('code', {}).get('frontend', 0)
            
            # 清屏效果
            print("\r" + " " * 70, end="")
            
            # 显示当前状态
            status = f"\r📊 APIs: {api_count} | Backend: {backend_count} | Frontend: {frontend_count}"
            
            # 显示增量
            if api_count > last_api_count:
                status += f" | +{api_count - last_api_count} APIs"
            if backend_count > last_backend_count:
                status += f" | +{backend_count - last_backend_count} Backend"
            if frontend_count > last_frontend_count:
                status += f" | +{frontend_count - last_frontend_count} Frontend"
            
            print(status, end="", flush=True)
            
            # 更新计数
            last_api_count = api_count
            last_backend_count = backend_count
            last_frontend_count = frontend_count
            
            # 如果有数据了,显示完成提示
            if api_count > 0 or backend_count > 0 or frontend_count > 0:
                if api_count >= 100:  # 假设目标是导入大量API
                    print("\n\n✅ 导入完成!")
                    print(f"   - APIs: {api_count}")
                    print(f"   - Backend: {backend_count}")
                    print(f"   - Frontend: {frontend_count}")
                    break
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n⏹️  监控已停止")
            print(f"\n最终状态:")
            print(f"   - APIs: {api_count}")
            print(f"   - Backend: {backend_count}")
            print(f"   - Frontend: {frontend_count}")
            break
        except Exception as e:
            print(f"\n❌ 监控出错: {e}")
            time.sleep(5)
            
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
