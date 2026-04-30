#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型定义 - SQLAlchemy ORM
兼容SQLite和PostgreSQL
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Project(Base):
    """项目表"""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='active')  # active/archived
    owner = Column(String(100))
    team = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    environments = relationship("Environment", back_populates="project", cascade="all, delete-orphan")
    api_specs = relationship("ApiSpec", back_populates="project", cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="project")


class Environment(Base):
    """环境表"""
    __tablename__ = 'environments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    name = Column(String(100), nullable=False)  # dev/test/staging/prod
    base_url = Column(String(500), nullable=False)
    is_protected = Column(Boolean, default=False)  # 是否保护环境(如prod)
    allow_write = Column(Boolean, default=True)  # 是否允许写操作测试
    timeout_seconds = Column(Integer, default=30)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    project = relationship("Project", back_populates="environments")
    auth_profile = relationship("AuthProfile", back_populates="environment", uselist=False, cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="environment")


class AuthProfile(Base):
    """鉴权配置表"""
    __tablename__ = 'auth_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    environment_id = Column(Integer, ForeignKey('environments.id'), nullable=False, unique=True)
    auth_type = Column(String(50), nullable=False)  # none/bearer/apikey/cookie/custom
    auth_config = Column(Text)  # 鉴权配置JSON(TODO: 后续需加密存储)
    default_headers = Column(JSON)  # 默认请求头
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    environment = relationship("Environment", back_populates="auth_profile")


class ApiSpec(Base):
    """API规范表"""
    __tablename__ = 'api_specs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    source_type = Column(String(50), nullable=False)  # url/file
    source_url = Column(String(500))
    version = Column(String(50))
    raw_spec_path = Column(String(500))  # 原始文件路径
    imported_at = Column(DateTime, default=datetime.now)
    api_count = Column(Integer, default=0)
    
    # 关联关系
    project = relationship("Project", back_populates="api_specs")


class TestCase(Base):
    """测试用例表"""
    __tablename__ = 'test_cases'
    
    id = Column(String(100), primary_key=True)  # TC_001格式
    title = Column(String(500), nullable=False)
    module = Column(String(200))
    priority = Column(String(50), nullable=False)  # critical/high/medium/low
    status = Column(String(50), default='pending')  # pending/passed/failed/skipped
    
    # 测试步骤和期望
    steps = Column(JSON)  # 步骤列表
    expected = Column(Text)
    
    # 数据语义
    data_type = Column(String(50))  # valid/invalid/boundary/edge
    expected_behavior = Column(String(50))  # success/client_error/server_error
    
    # 执行配置
    execution_config = Column(JSON)
    assertions = Column(JSON)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = Column(String(100), default='system')
    tags = Column(JSON)
    
    # 关联信息
    test_point_id = Column(String(100))
    api_id = Column(String(100))
    dataset_id = Column(String(100))
    source = Column(String(100))  # swagger/manual/ai_generated
    
    # 关联关系
    run_cases = relationship("RunCase", back_populates="test_case")


class TestRun(Base):
    """测试执行表"""
    __tablename__ = 'test_runs'
    
    id = Column(String(100), primary_key=True)  # RUN_timestamp格式
    project_id = Column(Integer, ForeignKey('projects.id'))
    environment_id = Column(Integer, ForeignKey('environments.id'))
    
    trigger_type = Column(String(50))  # manual/scheduled/ci/api
    status = Column(String(50), default='created')  # created/queued/preparing/running/healing/passed/failed/aborted
    trace_id = Column(String(100), unique=True)  # 全局追踪ID
    
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Float)  # 秒
    
    # 统计信息
    total_cases = Column(Integer, default=0)
    passed_cases = Column(Integer, default=0)
    failed_cases = Column(Integer, default=0)
    skipped_cases = Column(Integer, default=0)
    
    summary = Column(Text)
    
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(String(100), default='system')
    
    # 关联关系
    project = relationship("Project", back_populates="test_runs")
    environment = relationship("Environment", back_populates="test_runs")
    run_cases = relationship("RunCase", back_populates="test_run", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="test_run", uselist=False, cascade="all, delete-orphan")


class RunCase(Base):
    """测试用例执行记录表"""
    __tablename__ = 'run_cases'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), ForeignKey('test_runs.id'), nullable=False)
    test_case_id = Column(String(100), ForeignKey('test_cases.id'), nullable=False)
    
    status = Column(String(50), default='pending')  # pending/running/passed/failed/skipped
    retry_count = Column(Integer, default=0)
    
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Float)  # 秒
    
    error_message = Column(Text)
    error_type = Column(String(100))
    stack_trace = Column(Text)
    
    # 请求响应快照
    request_snapshot = Column(JSON)
    response_snapshot = Column(JSON)
    
    # 断言结果
    assertions_passed = Column(Integer, default=0)
    assertions_failed = Column(Integer, default=0)
    assertion_details = Column(JSON)
    
    # 修复信息
    healing_applied = Column(Boolean, default=False)
    healing_level = Column(String(50))
    healing_details = Column(Text)
    
    # 关联关系
    test_run = relationship("TestRun", back_populates="run_cases")
    test_case = relationship("TestCase", back_populates="run_cases")
    run_steps = relationship("RunStep", back_populates="run_case", cascade="all, delete-orphan")


class RunStep(Base):
    """执行步骤表"""
    __tablename__ = 'run_steps'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_case_id = Column(Integer, ForeignKey('run_cases.id'), nullable=False)
    
    step_name = Column(String(200), nullable=False)
    step_order = Column(Integer, default=0)
    status = Column(String(50), default='pending')  # pending/running/passed/failed/skipped
    
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Float)  # 秒
    
    input_snapshot = Column(JSON)
    output_snapshot = Column(JSON)
    
    error_message = Column(Text)
    error_type = Column(String(100))
    
    # 关联关系
    run_case = relationship("RunCase", back_populates="run_steps")


class Report(Base):
    """测试报告表"""
    __tablename__ = 'reports'
    
    id = Column(String(100), primary_key=True)  # REPORT_timestamp格式
    run_id = Column(String(100), ForeignKey('test_runs.id'), unique=True, nullable=False)
    
    title = Column(String(500), nullable=False)
    report_type = Column(String(50), default='comprehensive')  # comprehensive/coverage/bug
    format = Column(String(50), default='html')  # html/pdf/json
    
    file_path = Column(String(500))
    file_size = Column(Integer)  # 字节
    
    # 统计信息
    total_tests = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    pass_rate = Column(Float, default=0.0)
    
    # 修复统计
    healing_summary = Column(JSON)
    healed_cases = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联关系 - Report属于TestRun (多对一)
    test_run = relationship("TestRun", back_populates="report")


class HealingRecord(Base):
    """修复记录表"""
    __tablename__ = 'healing_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_case_id = Column(String(100), nullable=False)
    run_case_id = Column(Integer)
    
    error_type = Column(String(100), nullable=False)
    healing_level = Column(String(50), nullable=False)  # low/medium/high
    healing_strategy = Column(String(200), nullable=False)
    
    success = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)
    
    before_snapshot = Column(JSON)
    after_snapshot = Column(JSON)
    
    details = Column(Text)
    risk_assessment = Column(Text)
    
    timestamp = Column(DateTime, default=datetime.now)


class SystemSettings(Base):
    """系统设置表"""
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(200), unique=True, nullable=False)
    value = Column(Text)
    value_type = Column(String(50), default='string')  # string/int/float/bool/json
    description = Column(Text)
    category = Column(String(100))  # general/security/execution/notification
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class RunStatusHistory(Base):
    """执行状态历史表"""
    __tablename__ = 'run_status_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # run/run_case/run_step
    entity_id = Column(String(100), nullable=False)  # 对应实体的ID
    from_status = Column(String(50))  # 原状态(首次创建时为NULL)
    to_status = Column(String(50), nullable=False)  # 新状态
    changed_at = Column(DateTime, default=datetime.now, nullable=False)
    changed_by = Column(String(100), default='system')  # 操作人/系统
    reason = Column(Text)  # 状态变更原因
    
    # 索引优化查询
    __table_args__ = (
        {'comment': '执行状态历史记录表,用于追踪run/run_case/run_step的状态变更'}
    ,)
