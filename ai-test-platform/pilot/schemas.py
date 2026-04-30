from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


EnvironmentType = Literal["dev", "test", "staging", "prod", "development", "production"]
AuthType = Literal["none", "bearer_token", "api_key", "cookie", "custom_header"]


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    owner: str = "unknown"
    team: str = ""
    status: str = "active"
    environment: str = "test"
    baseUrl: str = ""


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    team: Optional[str] = None
    status: Optional[str] = None


class EnvironmentBase(BaseModel):
    name: str
    environment_type: EnvironmentType
    base_url: str
    auth_type: AuthType = "none"
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    openapi_source: Dict[str, Any] = Field(default_factory=dict)
    default_headers: Dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = 30
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {"max_retries": 1, "retry_backoff_seconds": 1})
    env_var_mapping: Dict[str, str] = Field(default_factory=dict)
    data_isolation_key: str = ""
    allow_write_operations: bool = False
    allow_self_healing: bool = True
    allow_auto_test_data: bool = True
    is_default: bool = False

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        return max(1, min(value, 300))


class EnvironmentCreate(EnvironmentBase):
    project_id: int


class EnvironmentUpdate(BaseModel):
    name: Optional[str] = None
    environment_type: Optional[EnvironmentType] = None
    base_url: Optional[str] = None
    auth_type: Optional[AuthType] = None
    auth_config: Optional[Dict[str, Any]] = None
    openapi_source: Optional[Dict[str, Any]] = None
    default_headers: Optional[Dict[str, str]] = None
    timeout_seconds: Optional[int] = None
    retry_policy: Optional[Dict[str, Any]] = None
    env_var_mapping: Optional[Dict[str, str]] = None
    data_isolation_key: Optional[str] = None
    allow_write_operations: Optional[bool] = None
    allow_self_healing: Optional[bool] = None
    allow_auto_test_data: Optional[bool] = None
    is_default: Optional[bool] = None


class OpenApiImportFromUrl(BaseModel):
    project_id: int
    environment_id: int
    url: str


class OpenApiGenerateCasesRequest(BaseModel):
    project_id: int
    api_ids: Optional[List[int]] = None


class TestRunCreate(BaseModel):
    project_id: int
    environment_id: int
    test_case_ids: Optional[List[int]] = None
    name: Optional[str] = None
    trigger_source: str = "manual"


class ReportGenerateRequest(BaseModel):
    run_id: int


class SystemSettingUpdate(BaseModel):
    key: str
    value: Dict[str, Any]
    description: str = ""
