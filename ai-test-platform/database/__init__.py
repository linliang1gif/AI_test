#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库层 - SQLite/PostgreSQL持久化
"""

from .session import get_db, get_db_session, init_db, close_db, get_db_info
from .models import (
    Base,
    Project,
    Environment,
    AuthProfile,
    ApiSpec,
    TestCase,
    TestRun,
    RunCase,
    RunStep,
    Report,
    HealingRecord,
    SystemSettings,
    RunStatusHistory
)
from .repository import (
    BaseRepository,
    ProjectRepository,
    EnvironmentRepository,
    TestCaseRepository,
    TestRunRepository,
    RunCaseRepository,
    ReportRepository,
    HealingRecordRepository,
    get_project_repo,
    get_environment_repo,
    get_test_case_repo,
    get_test_run_repo,
    get_run_case_repo,
    get_report_repo,
    get_healing_record_repo
)

__all__ = [
    # Session
    'get_db',
    'get_db_session',
    'init_db',
    'close_db',
    'get_db_info',
    # Models
    'Base',
    'Project',
    'Environment',
    'AuthProfile',
    'ApiSpec',
    'TestCase',
    'TestRun',
    'RunCase',
    'RunStep',
    'Report',
    'HealingRecord',
    'SystemSettings',
    'RunStatusHistory',
    # Repositories
    'BaseRepository',
    'ProjectRepository',
    'EnvironmentRepository',
    'TestCaseRepository',
    'TestRunRepository',
    'RunCaseRepository',
    'ReportRepository',
    'HealingRecordRepository',
    'get_project_repo',
    'get_environment_repo',
    'get_test_case_repo',
    'get_test_run_repo',
    'get_run_case_repo',
    'get_report_repo',
    'get_healing_record_repo'
]
