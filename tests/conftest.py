"""
pytest配置文件
"""
import pytest
import requests
from typing import Generator


@pytest.fixture(scope="session")
def api_client() -> Generator[requests.Session, None, None]:
    """API客户端fixture"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json"
    })
    yield session
    session.close()


@pytest.fixture(scope="session")
def base_url() -> str:
    """基础URL fixture"""
    return "http://localhost:8080"  # 请根据实际情况修改


@pytest.fixture
def auth_headers() -> dict:
    """认证头部fixture"""
    return {
        "Authorization": "Bearer your_token_here"  # 请根据实际情况修改
    }


class ApiTestBase:
    """API测试基类"""
    
    def assert_success_response(self, response: requests.Response):
        """断言成功响应"""
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")
    
    def assert_error_response(self, response: requests.Response, expected_code: int = 400):
        """断言错误响应"""
        assert response.status_code == expected_code
        data = response.json()
        assert "error" in data or "message" in data
