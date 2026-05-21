#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的API服务器 - 为前端提供AI提供商数据
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import requests

class SimpleAPIHandler(BaseHTTPRequestHandler):
    
    # 全局状态存储 - 默认使用Ollama
    current_provider = "ollama"
    current_model = "qwen2.5:1.5b"
    
    def __init__(self, *args, **kwargs):
        # 启动时自动设置为Ollama默认配置
        super().__init__(*args, **kwargs)
    
    @classmethod
    def initialize_default_provider(cls):
        """初始化默认AI提供商为Ollama"""
        cls.current_provider = "ollama"
        cls.current_model = "qwen2.5:1.5b"
        print(f"🤖 默认AI提供商已设置: {cls.current_provider} ({cls.current_model})")
        
        # 验证Ollama连接
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model["name"] for model in models_data.get("models", [])]
                if cls.current_model in available_models:
                    print(f"✅ Ollama模型 {cls.current_model} 已确认可用")
                else:
                    print(f"⚠️  默认模型 {cls.current_model} 不可用，可用模型: {available_models}")
                    if available_models:
                        cls.current_model = available_models[0]
                        print(f"🔄 自动切换到: {cls.current_model}")
            else:
                print(f"❌ Ollama服务响应异常: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Ollama连接检查失败: {e}")
            print("💡 请确保Ollama服务正在运行: ollama serve")
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        
        # 设置CORS头
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 解析路径
        path = self.path
        
        if path == '/api/ai/providers/list':
            # 返回AI提供商列表
            response = self.get_ai_providers()
        elif path.startswith('/api/ai/providers/') and path.endswith('/status'):
            # 检查特定提供商状态
            provider_id = path.split('/')[-2]
            response = self.check_provider_status(provider_id)
        elif path == '/api/ai/current':
            # 获取当前AI配置
            response = self.get_current_ai_config()
        elif path == '/api/dashboard/stats':
            # 仪表板统计
            response = {
                "totalTests": 156,
                "passed": 142,
                "failed": 14,
                "coverage": 85,
                "recentTests": [
                    {"id": 1, "name": "用户登录接口", "status": "passed", "time": "2分钟前"},
                    {"id": 2, "name": "支付网关", "status": "failed", "time": "5分钟前"}
                ]
            }
        elif path == '/api/ai/generate':
            # AI文本生成
            response = {"error": "Method not allowed", "message": "Use POST for AI generation"}
        else:
            # 默认响应
            response = {"error": "Endpoint not found", "path": path}
        
        # 发送响应
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def do_POST(self):
        """处理POST请求"""
        
        # 设置CORS头
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 读取请求体
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            data = {}
        
        path = self.path
        
        if path == '/api/ai/providers/select':
            # 选择AI提供商
            provider_id = data.get('provider_id')
            response = self.select_provider(provider_id)
        elif path == '/api/ai/providers/switch':
            # 切换AI提供商（兼容性端点）
            provider = data.get('provider')
            model = data.get('model')
            response = self.switch_provider(provider, model)
        elif path.startswith('/api/ai/providers/') and path.endswith('/test'):
            # 测试提供商连接
            provider_id = path.split('/')[-2]
            response = self.test_provider(provider_id)
        elif path == '/api/ai/generate':
            # AI文本生成
            response = self.generate_ai_text(data)
        else:
            response = {"error": "Endpoint not found", "path": path}
        
        # 发送响应
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def get_current_ai_config(self):
        """获取当前AI配置"""
        return {
            "current_provider": self.current_provider,
            "current_model": self.current_model,
            "provider_info": {
                "id": self.current_provider,
                "name": self.current_provider.title(),
                "model": self.current_model,
                "status": "active"
            }
        }
    
    def get_ai_providers(self):
        """获取AI提供商列表"""
        
        # 检查Ollama状态
        ollama_status = "unavailable"
        ollama_models = []
        
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models_data = response.json()
                ollama_models = [model["name"] for model in models_data.get("models", [])]
                ollama_status = "available"
        except:
            pass
        
        providers = [
            {
                "id": "ollama",
                "name": "Ollama",
                "description": "本地AI模型服务",
                "type": "local",
                "status": ollama_status,
                "models": ollama_models,
                "default_model": "qwen2.5:1.5b" if ollama_models else "",
                "config": {
                    "base_url": "http://localhost:11434",
                    "timeout": 60
                }
            },
            {
                "id": "deepseek",
                "name": "DeepSeek",
                "description": "DeepSeek AI API服务",
                "type": "cloud",
                "status": "available",
                "models": ["deepseek-chat", "deepseek-coder"],
                "default_model": "deepseek-chat",
                "config": {
                    "base_url": "https://api.deepseek.com",
                    "api_key": "sk-***"
                }
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "OpenAI GPT API服务",
                "type": "cloud",
                "status": "unavailable",
                "models": ["gpt-3.5-turbo", "gpt-4"],
                "default_model": "gpt-3.5-turbo",
                "config": {
                    "base_url": "https://api.openai.com/v1",
                    "api_key": ""
                }
            }
        ]
        
        return {
            "providers": providers,
            "current": self.current_provider,
            "current_model": self.current_model
        }
    
    def check_provider_status(self, provider_id):
        """检查提供商状态"""
        
        if provider_id == "ollama":
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=3)
                if response.status_code == 200:
                    models_data = response.json()
                    models = [model["name"] for model in models_data.get("models", [])]
                    
                    return {
                        "provider": {
                            "id": "ollama",
                            "name": "Ollama",
                            "status": "available",
                            "models": models,
                            "response_time": "< 1s"
                        }
                    }
            except:
                pass
            
            return {
                "provider": {
                    "id": "ollama",
                    "name": "Ollama",
                    "status": "unavailable",
                    "models": [],
                    "error": "Service not responding"
                }
            }
        
        return {"error": "Provider not found"}
    
    def test_provider(self, provider_id):
        """测试提供商连接"""
        
        # 统一转换为小写，支持大小写不敏感
        provider_id_lower = provider_id.lower()
        
        if provider_id_lower == "ollama":
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=3)
                if response.status_code == 200:
                    models_data = response.json()
                    models = [model["name"] for model in models_data.get("models", [])]
                    
                    return {
                        "success": True,
                        "message": "连接成功",
                        "provider": {
                            "id": "ollama",
                            "name": "Ollama",
                            "status": "available",
                            "models": models,
                            "response_time": "< 1s"
                        }
                    }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"连接失败: {str(e)}",
                    "provider": {
                        "id": "ollama",
                        "name": "Ollama",
                        "status": "unavailable",
                        "error": str(e)
                    }
                }
        
        elif provider_id_lower == "deepseek":
            return {
                "success": False,
                "message": "DeepSeek需要API密钥配置",
                "provider": {
                    "id": "deepseek",
                    "name": "DeepSeek",
                    "status": "unavailable",
                    "error": "API key not configured"
                }
            }
        
        elif provider_id_lower == "openai":
            return {
                "success": False,
                "message": "OpenAI需要API密钥配置",
                "provider": {
                    "id": "openai",
                    "name": "OpenAI",
                    "status": "unavailable",
                    "error": "API key not configured"
                }
            }
        
        return {
            "success": False,
            "message": f"未知的提供商: {provider_id}",
            "error": "Provider not found"
        }
    
    def generate_ai_text(self, data):
        """AI文本生成"""
        
        prompt = data.get('prompt', '')
        # 使用全局配置，但允许覆盖
        provider = data.get('provider', self.current_provider)
        model = data.get('model', self.current_model)
        
        if not prompt:
            return {
                "success": False,
                "error": "Prompt is required"
            }
        
        try:
            if provider.lower() == "ollama":
                ollama_response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    },
                    timeout=30
                )
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=60
                )
                
                if ollama_response.status_code == 200:
                    result = ollama_response.json()
                    return {
                        "success": True,
                        "response": result.get("response", ""),
                        "model": model,
                        "provider": provider,
                        "done": result.get("done", True),
                        "current_config": {
                            "provider": self.current_provider,
                            "model": self.current_model
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Ollama API error: {ollama_response.status_code}",
                        "message": ollama_response.text
                    }
            
            elif provider.lower() == "deepseek":
                return {
                    "success": False,
                    "error": "DeepSeek provider not implemented yet",
                    "message": "Please configure DeepSeek API key"
                }
            
            elif provider.lower() == "openai":
                return {
                    "success": False,
                    "error": "OpenAI provider not implemented yet", 
                    "message": "Please configure OpenAI API key"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown provider: {provider}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"AI generation failed: {str(e)}"
            }
    
    def switch_provider(self, provider, model=None):
        """切换AI提供商（兼容性方法）"""
        
        if not provider:
            return {"success": False, "error": "Provider is required"}
        
        # 更新全局状态
        self.current_provider = provider
        if model:
            self.current_model = model
        
        # 调用select_provider方法
        result = self.select_provider(provider)
        
        # 增强返回信息
        if result.get("success"):
            result["current_provider"] = self.current_provider
            result["current_model"] = self.current_model
            result["message"] = f"已切换到 {provider.title()} 提供商 ({self.current_model})"
        
        return result
    
    def select_provider(self, provider_id):
        """选择提供商"""
        
        if not provider_id:
            return {"success": False, "error": "Provider ID is required"}
        
        # 更新全局状态
        self.current_provider = provider_id
        
        # 模拟选择逻辑
        providers = {
            "ollama": "Ollama",
            "deepseek": "DeepSeek", 
            "openai": "OpenAI"
        }
        
        if provider_id in providers:
            return {
                "success": True,
                "message": f"已切换到 {providers[provider_id]} 提供商",
                "provider": {
                    "id": provider_id,
                    "name": providers[provider_id]
                },
                "current_provider": self.current_provider,
                "current_model": self.current_model
            }
        else:
            return {"success": False, "error": "Provider not found"}

def run_server(port=8000):
    """启动服务器"""
    
    # 初始化默认AI提供商
    SimpleAPIHandler.initialize_default_provider()
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleAPIHandler)
    
    print(f"🚀 简单API服务器启动")
    print(f"📍 地址: http://localhost:{port}")
    print(f"🔗 AI提供商API: http://localhost:{port}/api/ai/providers/list")
    print(f"📊 仪表板API: http://localhost:{port}/api/dashboard/stats")
    print(f"🎯 默认AI提供商: {SimpleAPIHandler.current_provider} ({SimpleAPIHandler.current_model})")
    print("=" * 50)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        httpd.server_close()

if __name__ == "__main__":
    run_server()