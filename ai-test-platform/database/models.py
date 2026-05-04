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
    case_type = Column(String(50), default='api')  # api/functional/web_ui
    
    # Phase 16: 用例治理字段
    module_name = Column(String(200))  # 模块名
    api_pattern = Column(String(50))   # list/page/detail/save/modify/delete/unknown
    risk_level = Column(String(10))    # P0/P1/P2
    executable = Column(Boolean, default=True)        # 是否可自动执行
    requires_auth = Column(Boolean, default=False)     # 是否需要认证
    requires_dependency = Column(Boolean, default=False)  # 是否需要前置数据
    destructive = Column(Boolean, default=False)       # 是否为破坏性操作
    assertion_status = Column(String(50))  # has_assertion/no_assertion
    last_run_status = Column(String(50))   # passed/failed/pending
    failure_category = Column(String(50))  # auth_error/env_error/request_error/response_error/assertion_error/dependency_error/timeout_error/unknown_error
    
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


class AiReportAnalysis(Base):
    """AI 分析报告表 (Phase 19)"""
    __tablename__ = 'ai_report_analyses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), ForeignKey('test_runs.id'), nullable=False)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=True)
    health_score = Column(Integer, default=0)
    release_recommendation = Column(String(20))  # pass/caution/block
    summary = Column(Text)
    key_findings_json = Column(JSON)
    risk_points_json = Column(JSON)
    failure_analysis_json = Column(JSON)
    skipped_analysis_json = Column(JSON)
    suggestions_json = Column(JSON)
    next_actions_json = Column(JSON)
    provider = Column(String(50), default='rule_based')  # rule_based/llm
    created_at = Column(DateTime, default=datetime.now)


class TestSuite(Base):
    """测试集表"""
    __tablename__ = 'test_suites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False)
    description = Column(Text)
    project_id = Column(Integer, ForeignKey('projects.id'))
    suite_type = Column(String(50), default='mixed')  # smoke/regression/release/api/web_ui/visual/performance/mixed
    priority = Column(String(50), default='medium')  # critical/high/medium/low
    status = Column(String(50), default='active')  # active/archived/deleted
    created_by = Column(String(100), default='system')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    project = relationship("Project")
    suite_cases = relationship("TestSuiteCase", back_populates="suite", cascade="all, delete-orphan")


class TestSuiteCase(Base):
    """测试集-用例关联表"""
    __tablename__ = 'test_suite_cases'

    id = Column(Integer, primary_key=True, autoincrement=True)
    suite_id = Column(Integer, ForeignKey('test_suites.id'), nullable=False)
    case_id = Column(String(100), ForeignKey('test_cases.id'), nullable=False)
    case_type = Column(String(50), default='api')  # api/web_ui/visual/performance/functional
    sort_order = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    # 关联
    suite = relationship("TestSuite", back_populates="suite_cases")
    test_case = relationship("TestCase")


class TestDataset(Base):
    """测试数据集"""
    __tablename__ = 'test_datasets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default='')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    dataset_type = Column(String(50), default='common_fixture')  # account/api_payload/ui_form/performance_pool/common_fixture/cleanup_rule
    case_type = Column(String(50), default='api')  # api/web_ui/visual/performance
    status = Column(String(50), default='active')  # active/archived/deleted
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    items = relationship("TestDatasetItem", back_populates="dataset", cascade="all, delete-orphan")
    bindings = relationship("TestDataBinding", back_populates="dataset", cascade="all, delete-orphan")


class TestDatasetItem(Base):
    """测试数据集数据项"""
    __tablename__ = 'test_dataset_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey('test_datasets.id'), nullable=False)
    key = Column(String(200), nullable=False)
    value_json = Column(JSON, default=None)
    is_sensitive = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    dataset = relationship("TestDataset", back_populates="items")


class TestDataBinding(Base):
    """测试数据集-用例绑定"""
    __tablename__ = 'test_data_bindings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey('test_datasets.id'), nullable=False)
    case_id = Column(String(100), ForeignKey('test_cases.id'), nullable=False)
    binding_type = Column(String(50), default='input')  # input/fixture/cleanup
    created_at = Column(DateTime, default=datetime.now)

    dataset = relationship("TestDataset", back_populates="bindings")
    test_case = relationship("TestCase")


class Defect(Base):
    """缺陷主表"""
    __tablename__ = 'defects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, default='')
    project_id = Column(Integer, default=None)
    module = Column(String(200), default='')
    severity = Column(String(50), default='major')        # blocker/critical/major/minor/trivial
    priority = Column(String(10), default='P2')            # P0/P1/P2/P3
    status = Column(String(50), default='open')            # open/confirmed/fixed/verified/closed/rejected/reopened
    source = Column(String(50), default='manual')          # manual/run_failure/failure_analysis/quality_gate/visual_diff/performance_regression/data_issue
    failure_category = Column(String(100), default='')
    case_id = Column(String(100), default=None)
    run_id = Column(String(100), default=None)
    run_case_id = Column(String(100), default=None)
    report_id = Column(String(100), default=None)
    trace_path = Column(String(500), default=None)
    screenshot_path = Column(String(500), default=None)
    evidence_json = Column(JSON, default=None)
    duplicate_key = Column(String(500), default=None)
    created_by = Column(String(100), default='system')
    assigned_to = Column(String(100), default=None)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    closed_at = Column(DateTime, default=None)

    events = relationship("DefectEvent", back_populates="defect", cascade="all, delete-orphan", order_by="DefectEvent.created_at")


class DefectEvent(Base):
    """缺陷事件/状态流转记录"""
    __tablename__ = 'defect_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    defect_id = Column(Integer, ForeignKey('defects.id'), nullable=False)
    event_type = Column(String(50), nullable=False)        # status_change/comment/link_run/update
    from_status = Column(String(50), default=None)
    to_status = Column(String(50), default=None)
    comment = Column(Text, default='')
    evidence_json = Column(JSON, default=None)
    created_by = Column(String(100), default='system')
    created_at = Column(DateTime, default=datetime.now)

    defect = relationship("Defect", back_populates="events")


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
