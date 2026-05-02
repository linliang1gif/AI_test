"""
P2-2 统一配置管理
所有环境变量在此集中读取，业务代码不再到处 os.getenv。
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)


class Settings:
    """集中式配置，属性懒读环境变量"""

    # ── 运行模式 ──
    @property
    def APP_MODE(self) -> str:
        return os.getenv("APP_MODE", "mock")

    @property
    def USE_MOCK_DATA(self) -> bool:
        return os.getenv("USE_MOCK_DATA", "false").lower() == "true"

    @property
    def DEBUG_MODE(self) -> bool:
        return os.getenv("DEBUG_MODE", "false").lower() == "true"

    @property
    def TESTING(self) -> bool:
        return os.getenv("TESTING", "false").lower() == "true"

    # ── URL ──
    @property
    def MOCK_API_BASE_URL(self) -> str:
        return os.getenv("MOCK_API_BASE_URL", "https://httpbin.org")

    @property
    def TARGET_API_BASE_URL(self) -> str:
        return os.getenv("TARGET_API_BASE_URL", "")

    # ── AI ──
    @property
    def AI_PROVIDER(self) -> str:
        return os.getenv("AI_PROVIDER", "none")

    @property
    def AI_ANALYSIS_MODE(self) -> str:
        return os.getenv("AI_ANALYSIS_MODE", "rule")

    @property
    def DEFAULT_AI_PROVIDER(self) -> str:
        return os.getenv("DEFAULT_AI_PROVIDER", "ollama")

    # ── 数据库 ──
    @property
    def SQLITE_DB_PATH(self) -> str:
        return os.getenv("SQLITE_DB_PATH", "data/test_platform.db")

    @property
    def CHROMA_DB_PATH(self) -> str:
        return os.getenv("CHROMA_DB_PATH", "knowledge/chroma_db")

    # ── 服务器 ──
    @property
    def BACKEND_HOST(self) -> str:
        return os.getenv("BACKEND_HOST", "0.0.0.0")

    @property
    def BACKEND_PORT(self) -> int:
        return int(os.getenv("BACKEND_PORT", "8000"))

    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")

    # ── 安全 ──
    @property
    def TARGET_API_TOKEN(self) -> str:
        """返回掩码值用于日志，真实值请用 _raw_token"""
        val = os.getenv("TARGET_API_TOKEN", "")
        return val[:4] + "****" if len(val) > 4 else "****" if val else ""

    @property
    def _raw_token(self) -> str:
        return os.getenv("TARGET_API_TOKEN", "")


settings = Settings()
