from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .db import Base


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="active")
    owner: Mapped[str] = mapped_column(String(100), default="unknown")
    team: Mapped[str] = mapped_column(String(100), default="")
    default_role: Mapped[str] = mapped_column(String(32), default="admin")
    tags: Mapped[dict] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    environments = relationship("EnvironmentModel", back_populates="project", cascade="all, delete-orphan")
    apis = relationship("ApiSpecModel", back_populates="project", cascade="all, delete-orphan")
    test_cases = relationship("TestCaseModel", back_populates="project", cascade="all, delete-orphan")
    test_runs = relationship("TestRunModel", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("ReportModel", back_populates="project", cascade="all, delete-orphan")


class EnvironmentModel(Base):
    __tablename__ = "environments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    environment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), default="")
    auth_type: Mapped[str] = mapped_column(String(32), default="none")
    auth_config: Mapped[dict] = mapped_column(JSON, default=dict)
    openapi_source: Mapped[dict] = mapped_column(JSON, default=dict)
    default_headers: Mapped[dict] = mapped_column(JSON, default=dict)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    retry_policy: Mapped[dict] = mapped_column(JSON, default=dict)
    env_var_mapping: Mapped[dict] = mapped_column(JSON, default=dict)
    data_isolation_key: Mapped[str] = mapped_column(String(200), default="")
    allow_write_operations: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_self_healing: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_auto_test_data: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("ProjectModel", back_populates="environments")
    test_runs = relationship("TestRunModel", back_populates="environment")


class ApiSpecModel(Base):
    __tablename__ = "api_specs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), default="url")
    source_location: Mapped[str] = mapped_column(String(1000), default="")
    spec_version: Mapped[str] = mapped_column(String(64), default="")
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[dict] = mapped_column(JSON, default=list)
    parameters: Mapped[dict] = mapped_column(JSON, default=list)
    request_body: Mapped[dict] = mapped_column(JSON, default=dict)
    responses: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_definition: Mapped[dict] = mapped_column(JSON, default=dict)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project = relationship("ProjectModel", back_populates="apis")
    test_cases = relationship("TestCaseModel", back_populates="api_spec")


class TestCaseModel(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    api_spec_id: Mapped[int | None] = mapped_column(ForeignKey("api_specs.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    module: Mapped[str] = mapped_column(String(200), default="default")
    priority: Mapped[str] = mapped_column(String(32), default="medium")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    case_type: Mapped[str] = mapped_column(String(100), default="功能测试")
    scenario_type: Mapped[str] = mapped_column(String(64), default="valid")
    expected_behavior: Mapped[str] = mapped_column(String(64), default="success")
    source: Mapped[str] = mapped_column(String(64), default="openapi_generated")
    description: Mapped[str] = mapped_column(Text, default="")
    steps: Mapped[dict] = mapped_column(JSON, default=list)
    expected: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[dict] = mapped_column(JSON, default=list)
    execution_config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("ProjectModel", back_populates="test_cases")
    api_spec = relationship("ApiSpecModel", back_populates="test_cases")
    run_steps = relationship("RunStepModel", back_populates="test_case")
    healing_records = relationship("HealingRecordModel", back_populates="test_case")


class DatasetModel(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[dict] = mapped_column(JSON, default=list)
    schema: Mapped[dict] = mapped_column(JSON, default=dict)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestRunModel(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    environment_id: Mapped[int | None] = mapped_column(ForeignKey("environments.id"), nullable=True, index=True)
    report_id: Mapped[int | None] = mapped_column(ForeignKey("reports.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="created")
    trigger_source: Mapped[str] = mapped_column(String(64), default="manual")
    requested_by_role: Mapped[str] = mapped_column(String(32), default="admin")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    selected_case_ids: Mapped[dict] = mapped_column(JSON, default=list)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    status_history: Mapped[dict] = mapped_column(JSON, default=list)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("ProjectModel", back_populates="test_runs")
    environment = relationship("EnvironmentModel", back_populates="test_runs")
    run_steps = relationship("RunStepModel", back_populates="test_run", cascade="all, delete-orphan")
    report = relationship("ReportModel", back_populates="test_run", foreign_keys=[report_id], post_update=True)
    healing_records = relationship("HealingRecordModel", back_populates="test_run", cascade="all, delete-orphan")


class RunStepModel(Base):
    __tablename__ = "run_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("test_runs.id"), nullable=False, index=True)
    test_case_id: Mapped[int | None] = mapped_column(ForeignKey("test_cases.id"), nullable=True, index=True)
    step_name: Mapped[str] = mapped_column(String(200), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="created")
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    output_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    test_run = relationship("TestRunModel", back_populates="run_steps")
    test_case = relationship("TestCaseModel", back_populates="run_steps")
    healing_records = relationship("HealingRecordModel", back_populates="run_step")


class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("test_runs.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    report_type: Mapped[str] = mapped_column(String(64), default="execution")
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    failure_overview: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    project = relationship("ProjectModel", back_populates="reports")
    test_run = relationship("TestRunModel", back_populates="report", foreign_keys=[run_id])


class HealingRecordModel(Base):
    __tablename__ = "healing_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("test_runs.id"), nullable=False, index=True)
    run_step_id: Mapped[int | None] = mapped_column(ForeignKey("run_steps.id"), nullable=True, index=True)
    test_case_id: Mapped[int | None] = mapped_column(ForeignKey("test_cases.id"), nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), default="low")
    before_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    after_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(Text, default="")
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    test_run = relationship("TestRunModel", back_populates="healing_records")
    run_step = relationship("RunStepModel", back_populates="healing_records")
    test_case = relationship("TestCaseModel", back_populates="healing_records")


class SystemSettingModel(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    description: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
