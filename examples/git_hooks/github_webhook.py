"""
GitHub Webhook 处理器
用于接收GitHub的push事件并触发测试

使用方法:
1. 在GitHub仓库设置中添加Webhook
2. Payload URL: http://your-server:8000/webhook/github
3. Content type: application/json
4. Events: Just the push event
"""
from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib
import requests
from typing import Dict, Any


def create_github_webhook_router(
    trigger_api_url: str = "http://localhost:8000/api/trigger/git-push",
    webhook_secret: str = None
) -> APIRouter:
    """
    创建GitHub Webhook路由
    
    Args:
        trigger_api_url: 触发API的URL
        webhook_secret: GitHub Webhook密钥（用于验证请求）
    """
    router = APIRouter(prefix="/webhook", tags=["Webhook"])
    
    def verify_signature(payload: bytes, signature: str) -> bool:
        """验证GitHub签名"""
        if not webhook_secret:
            return True  # 如果未配置密钥，跳过验证
        
        expected_signature = "sha256=" + hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    @router.post("/github")
    async def github_webhook(request: Request):
        """
        GitHub Push事件处理器
        """
        # 获取签名
        signature = request.headers.get("X-Hub-Signature-256", "")
        
        # 读取payload
        payload = await request.body()
        
        # 验证签名
        if not verify_signature(payload, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # 解析JSON
        data = await request.json()
        
        # 检查事件类型
        event_type = request.headers.get("X-GitHub-Event")
        if event_type != "push":
            return {"message": "Event ignored", "event": event_type}
        
        # 提取信息
        repo_name = data.get("repository", {}).get("full_name", "unknown")
        ref = data.get("ref", "")
        branch = ref.replace("refs/heads/", "")
        
        commits = data.get("commits", [])
        if not commits:
            return {"message": "No commits in push"}
        
        # 使用最新的commit
        latest_commit = commits[-1]
        commit_id = latest_commit.get("id", "")
        commit_message = latest_commit.get("message", "")
        author = latest_commit.get("author", {}).get("name", "")
        
        # 收集所有变更文件
        changed_files = []
        for commit in commits:
            changed_files.extend(commit.get("added", []))
            changed_files.extend(commit.get("modified", []))
            changed_files.extend(commit.get("removed", []))
        
        # 去重
        changed_files = list(set(changed_files))
        
        # 构建触发请求
        trigger_data = {
            "repo": repo_name,
            "branch": branch,
            "commit_id": commit_id,
            "commit_message": commit_message,
            "author": author,
            "changed_files": changed_files
        }
        
        # 发送到触发系统
        try:
            response = requests.post(
                trigger_api_url,
                json=trigger_data,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "message": "Test triggered successfully",
                "trigger_id": result.get("trigger_id"),
                "status": result.get("status")
            }
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to trigger test: {str(e)}"
            )
    
    return router


# 使用示例
if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI(title="GitHub Webhook Handler")
    
    # 添加webhook路由
    webhook_router = create_github_webhook_router(
        trigger_api_url="http://localhost:8000/api/trigger/git-push",
        webhook_secret="your-webhook-secret"  # 在GitHub设置中配置的密钥
    )
    app.include_router(webhook_router)
    
    @app.get("/")
    def root():
        return {"message": "GitHub Webhook Handler is running"}
    
    # 启动服务
    uvicorn.run(app, host="0.0.0.0", port=8001)
