#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ollama CPU版本自动安装和配置脚本

专门为没有显卡的Windows用户设计
"""

import os
import sys
import time
import requests
import subprocess
import json
from pathlib import Path

class OllamaCPUInstaller:
    """Ollama CPU版本安装器"""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.recommended_models = [
            "qwen2.5:1.5b",      # 1.5B参数，平衡性能和质量
            "deepseek-coder:1.3b", # 1.3B参数，专门用于代码
            "llama3.2:1b"        # 1B参数，最轻量
        ]
        
    def print_header(self):
        """打印标题"""
        print("=" * 60)
        print("🚀 Ollama CPU版本安装器")
        print("   专为无显卡用户优化")
        print("=" * 60)
        print()
    
    def check_system_requirements(self):
        """检查系统要求"""
        print("1️⃣ 检查系统要求...")
        
        # 检查操作系统
        if os.name != 'nt':
            print("❌ 此脚本仅支持Windows系统")
            return False
        
        print("✅ 操作系统: Windows")
        
        # 检查内存（简单估算）
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            print(f"✅ 系统内存: {memory_gb:.1f}GB")
            
            if memory_gb < 8:
                print("⚠️  警告: 内存少于8GB，建议使用最小模型")
            else:
                print("✅ 内存充足，可以运行推荐模型")
                
        except ImportError:
            print("⚠️  无法检测内存大小，请确保至少有8GB RAM")
        
        print()
        return True
    
    def check_ollama_installation(self):
        """检查Ollama是否已安装"""
        print("2️⃣ 检查Ollama安装状态...")
        
        try:
            # 检查ollama命令是否可用
            result = subprocess.run(['ollama', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Ollama已安装: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        print("❌ Ollama未安装")
        return False
    
    def install_ollama(self):
        """安装Ollama"""
        print("3️⃣ 安装Ollama...")
        print()
        print("请按照以下步骤手动安装Ollama:")
        print()
        print("方法1 - 官网下载 (推荐):")
        print("1. 打开浏览器访问: https://ollama.ai")
        print("2. 点击 'Download for Windows'")
        print("3. 下载 OllamaSetup.exe")
        print("4. 双击运行安装程序")
        print("5. 安装完成后会自动启动服务")
        print()
        print("方法2 - 命令行安装:")
        print("如果你有winget，可以运行:")
        print("winget install Ollama.Ollama")
        print()
        
        input("安装完成后，请按Enter继续...")
        
        # 等待用户安装
        for i in range(30):
            if self.check_ollama_service():
                print("✅ Ollama安装成功！")
                return True
            print(f"等待Ollama服务启动... ({i+1}/30)")
            time.sleep(2)
        
        print("❌ Ollama服务启动超时，请检查安装")
        return False
    
    def check_ollama_service(self):
        """检查Ollama服务是否运行"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def wait_for_service(self):
        """等待Ollama服务启动"""
        print("4️⃣ 等待Ollama服务启动...")
        
        for i in range(30):
            if self.check_ollama_service():
                print("✅ Ollama服务运行正常")
                return True
            print(f"等待服务启动... ({i+1}/30)")
            time.sleep(2)
        
        print("❌ Ollama服务启动失败")
        print("请尝试手动启动: ollama serve")
        return False
    
    def get_installed_models(self):
        """获取已安装的模型"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
        except:
            pass
        return []
    
    def download_model(self, model_name):
        """下载模型"""
        print(f"📥 下载模型: {model_name}")
        print("   这可能需要几分钟时间，请耐心等待...")
        
        try:
            # 使用ollama命令下载模型
            process = subprocess.Popen(
                ['ollama', 'pull', model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )
            
            # 实时显示下载进度
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"   {output.strip()}")
            
            if process.returncode == 0:
                print(f"✅ 模型 {model_name} 下载成功")
                return True
            else:
                print(f"❌ 模型 {model_name} 下载失败")
                return False
                
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return False
    
    def install_models(self):
        """安装推荐模型"""
        print("5️⃣ 安装CPU优化模型...")
        print()
        
        installed_models = self.get_installed_models()
        print(f"已安装模型: {installed_models}")
        print()
        
        # 推荐模型安装
        print("推荐安装以下CPU优化模型:")
        for i, model in enumerate(self.recommended_models, 1):
            print(f"{i}. {model}")
        print()
        
        choice = input("请选择要安装的模型 (1-3, 或 'all' 安装全部, 'skip' 跳过): ").strip().lower()
        
        if choice == 'skip':
            print("跳过模型安装")
            return True
        elif choice == 'all':
            models_to_install = self.recommended_models
        elif choice in ['1', '2', '3']:
            idx = int(choice) - 1
            models_to_install = [self.recommended_models[idx]]
        else:
            print("无效选择，安装默认模型")
            models_to_install = [self.recommended_models[0]]  # 默认安装第一个
        
        # 下载选中的模型
        success_count = 0
        for model in models_to_install:
            if model not in installed_models:
                if self.download_model(model):
                    success_count += 1
            else:
                print(f"✅ 模型 {model} 已存在")
                success_count += 1
        
        print(f"\n模型安装完成: {success_count}/{len(models_to_install)}")
        return success_count > 0
    
    def test_model(self, model_name):
        """测试模型"""
        print(f"🧪 测试模型: {model_name}")
        
        try:
            # 发送测试请求
            payload = {
                "model": model_name,
                "prompt": "请用一句话介绍软件测试的重要性。",
                "stream": False,
                "options": {
                    "num_predict": 50,
                    "temperature": 0.3
                }
            }
            
            print("   发送测试请求...")
            start_time = time.time()
            
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=60
            )
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                print(f"✅ 测试成功 (耗时: {response_time:.1f}秒)")
                print(f"   响应: {response_text[:100]}...")
                return True
            else:
                print(f"❌ 测试失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
    
    def configure_ai_platform(self):
        """配置AI测试平台"""
        print("6️⃣ 配置AI测试平台...")
        
        # 获取已安装的模型
        installed_models = self.get_installed_models()
        if not installed_models:
            print("❌ 没有可用的模型")
            return False
        
        # 选择默认模型
        default_model = None
        for model in self.recommended_models:
            if model in installed_models:
                default_model = model
                break
        
        if not default_model:
            default_model = installed_models[0]
        
        print(f"默认模型: {default_model}")
        
        # 更新环境变量文件
        env_file = Path("../.env")
        env_content = []
        
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.readlines()
        
        # 更新或添加Ollama配置
        ollama_config = {
            'OLLAMA_BASE_URL': 'http://localhost:11434',
            'OLLAMA_MODELS': ','.join(installed_models),
            'DEFAULT_AI_PROVIDER': 'ollama',
            'DEFAULT_AI_MODEL': default_model,
            'AI_MAX_TOKENS': '512',
            'AI_TEMPERATURE': '0.3',
            'AI_TIMEOUT': '120'
        }
        
        # 更新配置
        updated_lines = []
        updated_keys = set()
        
        for line in env_content:
            key = line.split('=')[0].strip()
            if key in ollama_config:
                updated_lines.append(f"{key}={ollama_config[key]}\n")
                updated_keys.add(key)
            else:
                updated_lines.append(line)
        
        # 添加新配置
        for key, value in ollama_config.items():
            if key not in updated_keys:
                updated_lines.append(f"{key}={value}\n")
        
        # 写入文件
        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            print("✅ AI测试平台配置更新成功")
            return True
        except Exception as e:
            print(f"❌ 配置更新失败: {e}")
            return False
    
    def run_integration_test(self):
        """运行集成测试"""
        print("7️⃣ 运行集成测试...")
        
        try:
            result = subprocess.run([
                sys.executable, 'test_ollama_integration.py'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ 集成测试通过")
                print(result.stdout)
                return True
            else:
                print("❌ 集成测试失败")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ 集成测试异常: {e}")
            return False
    
    def print_usage_guide(self):
        """打印使用指南"""
        print("\n" + "=" * 60)
        print("🎉 Ollama CPU版本安装完成！")
        print("=" * 60)
        print()
        print("📋 使用指南:")
        print("1. 启动AI测试平台后端:")
        print("   python backend_api_server.py")
        print()
        print("2. 启动前端 (新终端):")
        print("   cd frontend")
        print("   npm run dev")
        print()
        print("3. 在浏览器中访问:")
        print("   http://localhost:3000")
        print()
        print("4. 切换到Ollama提供商:")
        print("   - 进入'AI分析'页面")
        print("   - 点击'管理提供商'")
        print("   - 选择Ollama并测试连接")
        print("   - 切换提供商")
        print()
        print("💡 性能提示:")
        print("- CPU运行响应时间: 2-10秒")
        print("- 推荐使用简洁的提示词")
        print("- 可以同时保持DeepSeek作为备用")
        print()
        print("🔧 如需帮助，请查看:")
        print("- docs/ollama-cpu-setup.md")
        print("- 运行: python test_ollama_integration.py")
        print()
    
    def run(self):
        """运行安装流程"""
        self.print_header()
        
        # 1. 检查系统要求
        if not self.check_system_requirements():
            return False
        
        # 2. 检查Ollama安装
        if not self.check_ollama_installation():
            if not self.install_ollama():
                return False
        
        # 3. 等待服务启动
        if not self.wait_for_service():
            return False
        
        # 4. 安装模型
        if not self.install_models():
            print("⚠️  没有安装任何模型，但可以稍后手动安装")
        
        # 5. 测试模型
        installed_models = self.get_installed_models()
        if installed_models:
            test_model = installed_models[0]
            self.test_model(test_model)
        
        # 6. 配置AI平台
        self.configure_ai_platform()
        
        # 7. 运行集成测试
        self.run_integration_test()
        
        # 8. 显示使用指南
        self.print_usage_guide()
        
        return True

def main():
    """主函数"""
    installer = OllamaCPUInstaller()
    
    try:
        success = installer.run()
        if success:
            print("🎉 安装成功完成！")
        else:
            print("❌ 安装过程中遇到问题")
    except KeyboardInterrupt:
        print("\n\n⏹️  安装被用户中断")
    except Exception as e:
        print(f"\n\n❌ 安装过程中发生错误: {e}")

if __name__ == "__main__":
    main()