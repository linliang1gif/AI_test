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
    
    # 迭代关联
    iteration_id = Column(Integer, ForeignKey('iterations.id'), nullable=True)
    
    # 关联关系
    run_cases = relationship("RunCase", back_populates="test_case")
    iteration = relationship("Iteration", back_populates="test_cases")


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
    
    # 迭代关联
    iteration_id = Column(Integer, ForeignKey('iterations.id'), nullable=True)
    
    # 关联关系
    project = relationship("Project", back_populates="test_runs")
    environment = relationship("Environment", back_populates="test_runs")
    run_cases = relationship("RunCase", back_populates="test_run", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="test_run", uselist=False, cascade="all, delete-orphan")
    iteration = relationship("Iteration", back_populates="test_runs")


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


# ══════════════════════════════════════════════════════════════════
#  Phase C1: 需求-代码对比 DB 持久化模型
# ══════════════════════════════════════════════════════════════════

class CodeSnapshot(Base):
    """代码快照元数据"""
    __tablename__ = 'code_snapshots'

    id = Column(String(100), primary_key=True)
    project_id = Column(Integer, default=None)
    name = Column(String(300), nullable=False)
    source_type = Column(String(50), default='zip_upload')  # zip_upload/git_clone
    source_path = Column(String(500), default='')
    file_count = Column(Integer, default=0)
    language_stats_json = Column(JSON, default=dict)
    ignored_dirs_json = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class RequirementPoint(Base):
    """需求点"""
    __tablename__ = 'requirement_points'

    id = Column(String(100), primary_key=True)
    project_id = Column(Integer, default=None)
    source_type = Column(String(50), default='manual')  # manual/document/axure
    source_id = Column(String(100), default=None)
    point_type = Column(String(50), default='feature')  # feature/rule/field/axure_note
    title = Column(String(500), nullable=False)
    description = Column(Text, default='')
    keywords_json = Column(JSON, default=list)
    priority = Column(String(50), default='medium')
    module_name = Column(String(200), default='')
    created_at = Column(DateTime, default=datetime.now)


class CodeCompareReport(Base):
    """需求-代码对比报告"""
    __tablename__ = 'code_compare_reports'

    id = Column(String(100), primary_key=True)
    project_id = Column(Integer, default=None)
    requirement_source_id = Column(String(100), default=None)
    code_snapshot_id = Column(String(100), default=None)
    analysis_mode = Column(String(50), default='rule_based')  # rule_based/ai_deep/fallback
    total_requirement_points = Column(Integer, default=0)
    implemented_count = Column(Integer, default=0)
    missing_count = Column(Integer, default=0)
    extra_count = Column(Integer, default=0)
    uncertain_count = Column(Integer, default=0)
    risk_count = Column(Integer, default=0)
    summary = Column(Text, default='')
    code_summary = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    findings = relationship("CodeCompareFinding", back_populates="report", cascade="all, delete-orphan")


class CodeCompareFinding(Base):
    """需求-代码对比 Finding"""
    __tablename__ = 'code_compare_findings'

    id = Column(String(100), primary_key=True)
    report_id = Column(String(100), ForeignKey('code_compare_reports.id'), nullable=False)
    finding_type = Column(String(50), default='implemented')  # implemented/missing/extra/uncertain/risk
    requirement_point_id = Column(String(100), default=None)
    requirement_point_json = Column(JSON, default=dict)
    matched_symbols_json = Column(JSON, default=list)
    confidence = Column(Float, default=0.0)
    risk_level = Column(String(50), default='medium')
    evidence_json = Column(JSON, default=dict)
    analysis = Column(Text, default='')
    suggested_test_cases_json = Column(JSON, default=list)
    manual_status = Column(String(50), default=None)
    target_type = Column(String(50), default=None)
    target_id = Column(String(200), default=None)
    reviewer = Column(String(100), default=None)
    review_comment = Column(Text, default=None)
    converted_at = Column(DateTime, default=None)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    report = relationship("CodeCompareReport", back_populates="findings")


class RequirementConfirmQuestion(Base):
    """需求确认问题"""
    __tablename__ = 'requirement_confirm_questions'

    id = Column(String(100), primary_key=True)
    project_id = Column(Integer, default=None)
    finding_id = Column(String(100), default=None)
    title = Column(String(500), nullable=False)
    question = Column(Text, nullable=False)
    context = Column(Text, default='')
    evidence_json = Column(JSON, default=dict)
    status = Column(String(50), default='open')  # open/answered/closed
    owner = Column(String(100), default='product')
    answer = Column(Text, default=None)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ══════════════════════════════════════════════════════════════════
#  AI Product Studio 数据模型
# ══════════════════════════════════════════════════════════════════

class ProductIdea(Base):
    """产品想法"""
    __tablename__ = 'product_ideas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    idea_id = Column(String(100), unique=True, nullable=False)
    project_id = Column(Integer, default=None)
    title = Column(String(500), nullable=False)
    product_direction = Column(Text, default='')
    target_users = Column(Text, default='')
    pain_points = Column(Text, default='')
    existing_assets = Column(Text, default='')
    current_blockers = Column(Text, default='')
    constraints = Column(Text, default='')
    status = Column(String(50), default='created')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    artifacts = relationship("ProductArtifact", back_populates="idea", cascade="all, delete-orphan")
    runs = relationship("ProductStudioRun", back_populates="idea", cascade="all, delete-orphan")


class ProductStudioRun(Base):
    """Product Studio AI 执行记录"""
    __tablename__ = 'product_studio_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), unique=True, nullable=False)
    idea_id = Column(String(100), ForeignKey('product_ideas.idea_id'), nullable=False)
    run_type = Column(String(50), nullable=False)  # product_solution/prd/prototype/test_strategy/acceptance_criteria
    input_payload = Column(JSON, default=dict)
    output_text = Column(Text, default='')
    output_json = Column(JSON, default=None)
    status = Column(String(50), default='created')  # created/running/succeeded/failed
    model_name = Column(String(200), default='')
    token_input = Column(Integer, default=0)
    token_output = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)
    trace_id = Column(String(100), nullable=False)
    error_message = Column(Text, default=None)
    started_at = Column(DateTime, default=None)
    finished_at = Column(DateTime, default=None)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    idea = relationship("ProductIdea", back_populates="runs")


class ProductArtifact(Base):
    """Product Studio 产物"""
    __tablename__ = 'product_artifacts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(String(100), unique=True, nullable=False)
    idea_id = Column(String(100), ForeignKey('product_ideas.idea_id'), nullable=False)
    run_id = Column(String(100), default=None)
    artifact_type = Column(String(50), nullable=False)  # product_solution/prd/prototype/high_fidelity_prototype/test_strategy/acceptance_criteria
    title = Column(String(500), default='')
    content_markdown = Column(Text, default='')
    content_json = Column(JSON, default=None)
    status = Column(String(50), default='draft')  # draft/confirmed/archived
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    idea = relationship("ProductIdea", back_populates="artifacts")


class ProductArtifactTraceLink(Base):
    """Product Studio 产物 → 测试资产 追溯关联"""
    __tablename__ = 'product_artifact_trace_links'

    id = Column(Integer, primary_key=True, autoincrement=True)
    link_id = Column(String(100), unique=True, nullable=False)
    artifact_id = Column(String(100), ForeignKey('product_artifacts.artifact_id'), nullable=False)
    source_artifact_type = Column(String(50), nullable=False)  # prd/product_solution/requirement_point/test_strategy/acceptance_criteria
    target_type = Column(String(50), nullable=False)  # requirement_point/test_case/test_point/high_fidelity_prototype
    target_id = Column(String(100), nullable=False)
    generation_run_id = Column(String(100), default=None)
    confidence_score = Column(Float, default=0.0)
    status = Column(String(50), default='draft')  # draft/confirmed/rejected
    quality_score = Column(Float, default=None)
    quality_reason = Column(Text, default=None)
    review_reason = Column(Text, default=None)
    reviewed_at = Column(DateTime, default=None)
    reviewed_by = Column(String(100), default=None)
    promoted_at = Column(DateTime, default=None)
    promoted_target_id = Column(String(100), default=None)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ══════════════════════════════════════════════════════════════════
#  AI Dev Studio 数据模型
# ══════════════════════════════════════════════════════════════════

class DevTask(Base):
    """开发任务"""
    __tablename__ = 'dev_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dev_task_id = Column(String(100), unique=True, nullable=False)
    source_type = Column(String(50), nullable=False)  # product_artifact / test_case / manual
    source_id = Column(String(100), default=None)
    idea_id = Column(String(100), default=None)
    project_id = Column(Integer, default=None)
    title = Column(String(500), nullable=False)
    description = Column(Text, default='')
    status = Column(String(50), default='created')  # created / planning / planned / archived
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    artifacts = relationship("DevArtifact", back_populates="task", cascade="all, delete-orphan")
    runs = relationship("DevStudioRun", back_populates="task", cascade="all, delete-orphan")


class DevStudioRun(Base):
    """Dev Studio AI 执行记录"""
    __tablename__ = 'dev_studio_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), unique=True, nullable=False)
    dev_task_id = Column(String(100), ForeignKey('dev_tasks.dev_task_id'), nullable=False)
    run_type = Column(String(50), nullable=False)  # dev_plan / api_design / db_design / file_impact / test_plan
    input_payload = Column(JSON, default=dict)
    output_text = Column(Text, default='')
    output_json = Column(JSON, default=None)
    status = Column(String(50), default='created')  # created / running / succeeded / failed
    model_name = Column(String(200), default='')
    token_input = Column(Integer, default=0)
    token_output = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)
    trace_id = Column(String(100), nullable=False)
    batch_id = Column(String(100), default=None)
    error_message = Column(Text, default=None)
    started_at = Column(DateTime, default=None)
    finished_at = Column(DateTime, default=None)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    task = relationship("DevTask", back_populates="runs")


class DevArtifact(Base):
    """Dev Studio 产物"""
    __tablename__ = 'dev_artifacts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dev_artifact_id = Column(String(100), unique=True, nullable=False)
    dev_task_id = Column(String(100), ForeignKey('dev_tasks.dev_task_id'), nullable=False)
    run_id = Column(String(100), default=None)
    artifact_type = Column(String(50), nullable=False)  # dev_plan / api_design / db_design / file_impact / test_plan
    title = Column(String(500), default='')
    content_markdown = Column(Text, default='')
    content_json = Column(JSON, default=None)
    status = Column(String(50), default='draft')  # draft / confirmed / archived
    batch_id = Column(String(100), default=None)
    batch_index = Column(Integer, default=None)
    parent_artifact_id = Column(String(100), default=None)
    reference_artifact_ids = Column(Text, default=None)  # JSON string
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    task = relationship("DevTask", back_populates="artifacts")


# ── Phase 7: CodeMap ──────────────────────────────────────────

class CodeMapSnapshot(Base):
    __tablename__ = 'code_map_snapshots'
    snapshot_id = Column(String(100), primary_key=True)
    dev_task_id = Column(String(100), default=None)
    project_root = Column(String(1000), nullable=False)
    total_files = Column(Integer, default=0)
    total_dirs = Column(Integer, default=0)
    backend_files = Column(Integer, default=0)
    frontend_files = Column(Integer, default=0)
    scan_duration_ms = Column(Integer, default=0)
    status = Column(String(50), default='completed')  # completed / failed
    error_message = Column(Text, default=None)
    created_at = Column(DateTime, default=datetime.now)

    files = relationship("CodeMapFile", back_populates="snapshot", cascade="all, delete-orphan")


class CodeMapFile(Base):
    __tablename__ = 'code_map_files'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(100), ForeignKey('code_map_snapshots.snapshot_id'))
    file_path = Column(String(2000), nullable=False)
    relative_path = Column(String(2000), nullable=False)
    file_type = Column(String(50), default='unknown')   # py / jsx / ts / json / md / yaml / sql / etc
    category = Column(String(100), default='other')      # route / service / model / page / component / config / script / doc / test / other
    module = Column(String(200), default=None)           # e.g. routes/dev_studio_routes.py → dev_studio
    size_bytes = Column(Integer, default=0)
    line_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    snapshot = relationship("CodeMapSnapshot", back_populates="files")


# ── Iteration Management (D2-3A) ─────────────────────────────

class Iteration(Base):
    """迭代/版本管理表"""
    __tablename__ = 'iterations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    name = Column(String(200), nullable=False)
    code = Column(String(50))
    version = Column(String(50), default='')
    description = Column(Text, default='')
    start_date = Column(String(20))
    end_date = Column(String(20))
    planned_start_time = Column(String(30), default='')
    planned_release_time = Column(String(30), default='')
    status = Column(String(20), default='planning')  # planning/in_progress/testing/completed/archived
    owner = Column(String(100), default='')
    test_owner = Column(String(100), default='')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    project = relationship("Project")
    test_cases = relationship("TestCase", back_populates="iteration")
    test_runs = relationship("TestRun", back_populates="iteration")
    requirements = relationship("IterationRequirement", back_populates="iteration", cascade="all, delete-orphan")
    test_points = relationship("IterationTestPoint", back_populates="iteration", cascade="all, delete-orphan")
    execution_sets = relationship("IterationExecutionSet", back_populates="iteration", cascade="all, delete-orphan")


class IterationRequirement(Base):
    """迭代需求表"""
    __tablename__ = 'iteration_requirements'

    id = Column(Integer, primary_key=True, autoincrement=True)
    iteration_id = Column(Integer, ForeignKey('iterations.id'), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, default='')
    source_type = Column(String(50), default='manual')  # manual/jira/tapd/file
    source_url = Column(String(1000), default='')
    ai_summary = Column(Text, default='')
    risk_level = Column(String(10), default='P1')  # P0/P1/P2
    confirm_questions = Column(Text, default='')  # JSON array
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    iteration = relationship("Iteration", back_populates="requirements")
    test_points = relationship("IterationTestPoint", back_populates="requirement")


class IterationTestPoint(Base):
    """迭代测试点表"""
    __tablename__ = 'iteration_test_points'

    id = Column(Integer, primary_key=True, autoincrement=True)
    iteration_id = Column(Integer, ForeignKey('iterations.id'), nullable=False)
    requirement_id = Column(Integer, ForeignKey('iteration_requirements.id'), nullable=True)
    module_name = Column(String(200), default='')
    test_point = Column(Text, nullable=False)
    risk_level = Column(String(10), default='P1')  # P0/P1/P2
    priority = Column(String(10), default='medium')  # high/medium/low
    test_type = Column(String(50), default='functional')  # functional/api/performance/security
    recommended_api = Column(JSON, nullable=True)
    execution_config = Column(JSON, nullable=True)
    ai_generated = Column(Boolean, default=False)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    iteration = relationship("Iteration", back_populates="test_points")
    requirement = relationship("IterationRequirement", back_populates="test_points")


class IterationExecutionSet(Base):
    """迭代执行集表"""
    __tablename__ = 'iteration_execution_sets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    iteration_id = Column(Integer, ForeignKey('iterations.id'), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(50), default='iteration')  # smoke/iteration/regression
    status = Column(String(50), default='created')  # created/running/completed/failed
    case_count = Column(Integer, default=0)
    run_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    iteration = relationship("Iteration", back_populates="execution_sets")
    set_cases = relationship("IterationExecutionSetCase", back_populates="execution_set", cascade="all, delete-orphan")


class IterationExecutionSetCase(Base):
    """执行集-用例关联表"""
    __tablename__ = 'iteration_execution_set_cases'

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_set_id = Column(Integer, ForeignKey('iteration_execution_sets.id'), nullable=False)
    test_case_id = Column(String(100), ForeignKey('test_cases.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    execution_set = relationship("IterationExecutionSet", back_populates="set_cases")
    test_case = relationship("TestCase")
