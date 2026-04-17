"""
GitLab Webhook 处理器
用于接收GitLab的push事件并触发测试

使用方法:
1. 在GitLab项目设置中添加Webhook
2. URL: http://your-server:8000/webhook/gitlab
3. Secret Token: 配置密钥（可选）
4. Trigger: Push events
"""
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional, Dict, Any
import hmac
import hashlib
import requests


def create_gitlab_webhook_router(
    trigger_api_url: str = "http://localhost:8000/api/trigger/git-push",
    webhook_secret: Optional[str] = None
) -> APIRouter:
    """
    创建GitLab Webhook路由
    
    Args:
        trigger_api_url: 触发API的URL
        webhook_secret: GitLab Webhook密钥（用于验证请求）
    """
    router = APIRouter(prefix="/webhook", tags=["Webhook"])
    
    def verify_token(token: Optional[str]) -> bool:
        """验证GitLab Token"""
        if not webhook_secret:
            return True  # 如果未配置密钥，跳过验证
        return token == webhook_secret
    
    @router.post("/gitlab")
    async def gitlab_webhook(
        request: Request,
        x_gitlab_token: Optional[str] = Header(None),
        x_gitlab_event: Optional[str] = Header(None)
    ):
        """
        GitLab Push事件处理器
        """
        # 验证Token
        if not verify_token(x_gitlab_token):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # 检查事件类型
        if x_gitlab_event != "Push Hook":
            return {"message": "Event ignored", "event": x_gitlab_event}
        
        # 解析JSON
        data = await request.json()
        
        # 提取信息
        project = data.get("project", {})
        repo_name = project.get("path_with_namespace", "unknown")
        
        ref = data.get("ref", "")
        branch = ref.replace("refs/heads/", "")
        
        # 获取最新的commit
        commits = data.get("commits", [])
        if not commits:
            return {"message": "No commits in push"}
        
        latest_commit = commits[-1]
        commit_id = latest_commit.get("id", "")
        commit_message = latest_commit.get("message", "")
        
        # 获取作者信息
        author_info = latest_commit.get("author", {})
        author = author_info.get("name", "")
        
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
                "status": result.get("status"),
                "repo": repo_name,
                "branch": branch,
                "commit": commit_id[:8]
            }
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to trigger test: {str(e)}"
            )
    
    @router.get("/gitlab/health")
    async def gitlab_health():
        """健康检查接口"""
        return {
            "status": "healthy",
            "service": "GitLab Webhook Handler",
            "trigger_api": trigger_api_url
        }
    
    return router


# 使用示例
if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI(title="GitLab Webhook Handler")
    
    # 添加webhook路由
    webhook_router = create_gitlab_webhook_router(
        trigger_api_url="http://localhost:8000/api/trigger/git-push",
        webhook_secret="your-webhook-secret"  # 在GitLab设置中配置的密钥
    )
    app.include_router(webhook_router)
    
    @app.get("/")
    def root():
        return {
            "message": "GitLab Webhook Handler is running",
            "endpoints": {
                "webhook": "/webhook/gitlab",
                "health": "/webhook/gitlab/health"
            }
        }
    
    # 启动服务
    print("=" * 60)
    print("🚀 GitLab Webhook Handler")
    print("=" * 60)
    print(f"Webhook URL: http://0.0.0.0:8001/webhook/gitlab")
    print(f"Health Check: http://0.0.0.0:8001/webhook/gitlab/health")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
