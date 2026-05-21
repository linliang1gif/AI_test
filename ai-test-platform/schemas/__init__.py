# FROZEN MODULE — 仅允许 bug fix 和必要 shim
# 新功能请进入主线，参见 docs/architecture/SYSTEM_MAINLINE.md
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic Schemas - 请求和响应模型
"""

from .project_schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    EnvironmentCreate,
    EnvironmentUpdate,
    EnvironmentResponse,
    AuthProfileCreate,
    AuthProfileUpdate,
    AuthProfileResponse
)

from .test_run_schemas import (
    TestRunCreate,
    TestRunUpdate,
    TestRunResponse,
    RunCaseResponse,
    StatusUpdateRequest,
    StatusHistoryResponse,
    StateTransitionInfo
)

__all__ = [
    'ProjectCreate',
    'ProjectUpdate',
    'ProjectResponse',
    'EnvironmentCreate',
    'EnvironmentUpdate',
    'EnvironmentResponse',
    'AuthProfileCreate',
    'AuthProfileUpdate',
    'AuthProfileResponse',
    'TestRunCreate',
    'TestRunUpdate',
    'TestRunResponse',
    'RunCaseResponse',
    'StatusUpdateRequest',
    'StatusHistoryResponse',
    'StateTransitionInfo'
]
