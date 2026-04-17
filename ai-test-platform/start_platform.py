#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 统一启动脚本
一键启动前后端服务
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

class PlatformStarter:
    """平台启动器"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.backend_process = None
        self.frontend_process = None
        
    def check_dependencies(self):
        """检查依赖"""
        print("🔍 检查依赖...")
        
        # 检查Python依赖
        try:
            import fastapi
            import uvicorn
            print("✅ Python依赖检查通过")
        except ImportError as e:
            print(f"❌ Python依赖缺失: {e}")
            print("请运行: pip install -r requirements.txt")
            return False
        
        # 检查Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js 已安装: {result.stdout.strip()}")
            else:
                print("❌ Node.js 未安装")
                return False
        except FileNotFoundError:
            print("❌ Node.js 未安装")
            return False
        
        # 检查前端依赖
        frontend_dir = self.root_dir / "frontend"
        node_modules = frontend_dir / "node_modules"
        
        if not node_modules.exists():
            print("⚠️  前端依赖未安装")
            print("正在安装前端依赖...")
            try:
                subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
                print("✅ 前端依赖安装完成")
            except subprocess.CalledProcessError:
                print("❌ 前端依赖安装失败")
                return False
        else:
            print("✅ 前端依赖已安装")
        
        return True
    
    def create_directories(self):
        """创建必要的目录"""
        print("\n📁 创建目录结构...")
        
        directories = [
            "data",
            "uploads",
            "output",
            "output/scripts",
            "logs",
            "knowledge"
        ]
        
        for dir_name in directories:
            dir_path = self.root_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print("✅ 目录结构创建完成")
    
    def start_backend(self):
        """启动后端服务"""
        print("\n🚀 启动后端服务...")
        
        backend_script = self.root_dir / "backend_api_server.py"
        
        if not backend_script.exists():
            print(f"❌ 后端脚本不存在: {backend_script}")
            return False
        
        try:
            self.backend_process = subprocess.Popen(
                [sys.executable, str(backend_script)],
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # 等待后端启动
            time.sleep(3)
            
            if self.backend_process.poll() is None:
                print("✅ 后端服务启动成功 - http://127.0.0.1:8081")
                return True
            else:
                print("❌ 后端服务启动失败")
                return False
                
        except Exception as e:
            print(f"❌ 后端启动异常: {e}")
            return False
    
    def start_frontend(self):
        """启动前端服务"""
        print("\n🚀 启动前端服务...")
        
        frontend_dir = self.root_dir / "frontend"
        
        if not frontend_dir.exists():
            print(f"❌ 前端目录不存在: {frontend_dir}")
            return False
        
        try:
            # Windows使用npm.cmd
            npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
            
            self.frontend_process = subprocess.Popen(
                [npm_cmd, "run", "dev"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # 等待前端启动
            time.sleep(5)
            
            if self.frontend_process.poll() is None:
                print("✅ 前端服务启动成功 - http://localhost:3000")
                return True
            else:
                print("❌ 前端服务启动失败")
                return False
                
        except Exception as e:
            print(f"❌ 前端启动异常: {e}")
            return False
    
    def stop_services(self):
        """停止所有服务"""
        print("\n🛑 停止服务...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("✅ 后端服务已停止")
            except Exception as e:
                print(f"⚠️  后端停止异常: {e}")
                try:
                    self.backend_process.kill()
                except:
                    pass
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print("✅ 前端服务已停止")
            except Exception as e:
                print(f"⚠️  前端停止异常: {e}")
                try:
                    self.frontend_process.kill()
                except:
                    pass
    
    def run(self):
        """运行平台"""
        print("=" * 60)
        print("🚀 AI Test Platform - 统一启动")
        print("=" * 60)
        
        # 检查依赖
        if not self.check_dependencies():
            print("\n❌ 依赖检查失败,请先安装依赖")
            return
        
        # 创建目录
        self.create_directories()
        
        # 启动后端
        if not self.start_backend():
            print("\n❌ 后端启动失败")
            return
        
        # 启动前端
        if not self.start_frontend():
            print("\n❌ 前端启动失败")
            self.stop_services()
            return
        
        print("\n" + "=" * 60)
        print("✅ AI Test Platform 启动成功!")
        print("=" * 60)
        print("\n📍 访问地址:")
        print("   前端界面: http://localhost:3000")
        print("   后端API:  http://127.0.0.1:8081")
        print("   API文档:  http://127.0.0.1:8081/docs")
        print("\n💡 提示:")
        print("   - 按 Ctrl+C 停止服务")
        print("   - 查看日志请检查终端输出")
        print("=" * 60)
        
        # 注册信号处理
        def signal_handler(sig, frame):
            print("\n\n收到停止信号...")
            self.stop_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
        
        # 保持运行
        try:
            while True:
                time.sleep(1)
                
                # 检查进程状态
                if self.backend_process and self.backend_process.poll() is not None:
                    print("\n❌ 后端服务意外停止")
                    break
                
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("\n❌ 前端服务意外停止")
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_services()

def main():
    """主函数"""
    starter = PlatformStarter()
    starter.run()

if __name__ == "__main__":
    main()
