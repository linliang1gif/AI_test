"""
P2-2 启动初始化
- 数据库 init_db + 自动建表
- Phase 迁移
- 可选模块初始化（不阻塞启动）
"""
import logging

logger = logging.getLogger("startup")


async def on_startup():
    """FastAPI startup 事件回调"""
    _check_database()
    _run_migrations()
    _init_optional_modules()


def _check_database():
    """检查数据库连接和关键表"""
    logger.info("=" * 60)
    logger.info("数据库健康检查")
    logger.info("=" * 60)
    try:
        from database import init_db, get_db_session
        from sqlalchemy import inspect as sa_inspect, text

        init_db()

        with get_db_session() as db:
            db.execute(text("SELECT 1"))
            inspector = sa_inspect(db.bind)
            tables = inspector.get_table_names()
            db_url = str(db.bind.url)

            logger.info(f"数据库类型: sqlite")
            logger.info(f"数据库URL: {db_url}")

            required = [
                "projects", "environments", "test_cases", "test_runs",
                "run_cases", "run_steps", "api_specs", "api_endpoints",
                "execution_records", "test_reports", "report_test_cases",
                "ai_report_analyses",
            ]
            existing = [t for t in required if t in tables]
            missing = [t for t in required if t not in tables]

            if missing:
                logger.warning(f"缺少表: {missing}")
            else:
                logger.info(f"所有关键表已存在 ({len(existing)} 个)")
    except Exception as e:
        logger.error(f"数据库检查失败: {e}")


def _run_migrations():
    """轻量级迁移检查"""
    # Phase 16 治理字段
    try:
        from database import get_db_session
        from sqlalchemy import inspect as sa_inspect, text
        with get_db_session() as db:
            inspector = sa_inspect(db.bind)
            cols = [c["name"] for c in inspector.get_columns("test_cases")]
            new_cols = {
                "risk_level": "VARCHAR(20) DEFAULT 'unknown'",
                "api_pattern": "VARCHAR(200)",
                "destructive": "BOOLEAN DEFAULT 0",
                "last_reviewed_at": "TIMESTAMP",
            }
            added = []
            for col, typedef in new_cols.items():
                if col not in cols:
                    db.execute(text(f"ALTER TABLE test_cases ADD COLUMN {col} {typedef}"))
                    added.append(col)
            if added:
                db.commit()
                logger.info(f"Phase 16 迁移: 添加字段 {added}")
            else:
                logger.info("Phase 16 治理字段已存在，无需迁移")
    except Exception as e:
        logger.warning(f"Phase 16 迁移检查失败: {e}")

    # P2-3 case_type 字段
    try:
        from database import get_db_session
        from sqlalchemy import text as _text
        with get_db_session() as db:
            from sqlalchemy import inspect as _insp
            cols = [c["name"] for c in _insp(db.bind).get_columns("test_cases")]
            if "case_type" not in cols:
                db.execute(_text("ALTER TABLE test_cases ADD COLUMN case_type VARCHAR(50) DEFAULT 'api'"))
                db.commit()
                logger.info("P2-3 迁移: 添加 case_type 字段")
            else:
                logger.info("P2-3 case_type 字段已存在")
    except Exception as e:
        logger.warning(f"P2-3 迁移失败: {e}")

    # Phase 19 ai_report_analyses 表
    try:
        from database import get_db_session
        from sqlalchemy import inspect as sa_inspect
        with get_db_session() as db:
            inspector = sa_inspect(db.bind)
            if "ai_report_analyses" not in inspector.get_table_names():
                from database.models import AiReportAnalysis
                AiReportAnalysis.__table__.create(db.bind)
                logger.info("Phase 19 迁移: 已创建 ai_report_analyses 表")
            else:
                logger.info("Phase 19 ai_report_analyses 表已存在")
    except Exception as e:
        logger.warning(f"Phase 19 迁移失败: {e}")


    # P2-10 test_suites + test_suite_cases 表
    try:
        from database import get_db_session
        from sqlalchemy import inspect as sa_inspect
        with get_db_session() as db:
            inspector = sa_inspect(db.bind)
            tables = inspector.get_table_names()
            created = []
            if "test_suites" not in tables:
                from database.models import TestSuite
                TestSuite.__table__.create(db.bind)
                created.append("test_suites")
            if "test_suite_cases" not in tables:
                from database.models import TestSuiteCase
                TestSuiteCase.__table__.create(db.bind)
                created.append("test_suite_cases")
            if created:
                logger.info(f"P2-10 迁移: 已创建 {created}")
            else:
                logger.info("P2-10 test_suites/test_suite_cases 表已存在")
    except Exception as e:
        logger.warning(f"P2-10 迁移失败: {e}")


    # P3-2 test_datasets + test_dataset_items + test_data_bindings 表
    try:
        from database import get_db_session
        from sqlalchemy import inspect as sa_inspect
        with get_db_session() as db:
            inspector = sa_inspect(db.bind)
            tables = inspector.get_table_names()
            created = []
            if "test_datasets" not in tables:
                from database.models import TestDataset
                TestDataset.__table__.create(db.bind)
                created.append("test_datasets")
            if "test_dataset_items" not in tables:
                from database.models import TestDatasetItem
                TestDatasetItem.__table__.create(db.bind)
                created.append("test_dataset_items")
            if "test_data_bindings" not in tables:
                from database.models import TestDataBinding
                TestDataBinding.__table__.create(db.bind)
                created.append("test_data_bindings")
            if created:
                logger.info(f"P3-2 迁移: 已创建 {created}")
            else:
                logger.info("P3-2 test_datasets/test_dataset_items/test_data_bindings 表已存在")
    except Exception as e:
        logger.warning(f"P3-2 迁移失败: {e}")


    # P3-3B defects + defect_events 表
    try:
        from database import get_db_session
        from sqlalchemy import inspect as sa_inspect
        with get_db_session() as db:
            inspector = sa_inspect(db.bind)
            tables = inspector.get_table_names()
            created = []
            if "defects" not in tables:
                from database.models import Defect
                Defect.__table__.create(db.bind)
                created.append("defects")
            if "defect_events" not in tables:
                from database.models import DefectEvent
                DefectEvent.__table__.create(db.bind)
                created.append("defect_events")
            if created:
                logger.info(f"P3-3B 迁移: 已创建 {created}")
            else:
                logger.info("P3-3B defects/defect_events 表已存在")
    except Exception as e:
        logger.warning(f"P3-3B 迁移失败: {e}")


    # Phase C1: code_compare 5 张新表
    try:
        from database import get_db_session
        from sqlalchemy import inspect as sa_inspect
        with get_db_session() as db:
            inspector = sa_inspect(db.bind)
            tables = inspector.get_table_names()
            created = []
            _C1_MODELS = [
                ("code_snapshots", "CodeSnapshot"),
                ("requirement_points", "RequirementPoint"),
                ("code_compare_reports", "CodeCompareReport"),
                ("code_compare_findings", "CodeCompareFinding"),
                ("requirement_confirm_questions", "RequirementConfirmQuestion"),
            ]
            for tbl_name, cls_name in _C1_MODELS:
                if tbl_name not in tables:
                    import importlib
                    mod = importlib.import_module("database.models")
                    cls = getattr(mod, cls_name)
                    cls.__table__.create(db.bind)
                    created.append(tbl_name)
            if created:
                logger.info(f"Phase C1 迁移: 已创建 {created}")
            else:
                logger.info("Phase C1 code_compare 表已全部存在")
    except Exception as e:
        logger.warning(f"Phase C1 迁移失败: {e}")


    # P3-5.1 性能索引 — 聚合查询加速
    try:
        from database import get_db_session
        from sqlalchemy import text as _text
        with get_db_session() as db:
            _INDEXES = [
                # test_runs
                ("ix_test_runs_created_at",   "test_runs",        "created_at"),
                ("ix_test_runs_project_id",   "test_runs",        "project_id"),
                ("ix_test_runs_status",       "test_runs",        "status"),
                ("ix_test_runs_trigger_type", "test_runs",        "trigger_type"),
                # run_cases
                ("ix_run_cases_run_id",       "run_cases",        "run_id"),
                ("ix_run_cases_case_id",      "run_cases",        "test_case_id"),
                ("ix_run_cases_status",       "run_cases",        "status"),
                # test_cases
                ("ix_test_cases_case_type",   "test_cases",       "case_type"),
                ("ix_test_cases_module",      "test_cases",       "module"),
                ("ix_test_cases_priority",    "test_cases",       "priority"),
                ("ix_test_cases_status",      "test_cases",       "status"),
                # defects
                ("ix_defects_project_id",     "defects",          "project_id"),
                ("ix_defects_status",         "defects",          "status"),
                ("ix_defects_severity",       "defects",          "severity"),
                ("ix_defects_case_id",        "defects",          "case_id"),
                ("ix_defects_duplicate_key",  "defects",          "duplicate_key"),
                # test_suite_cases
                ("ix_tsc_suite_id",           "test_suite_cases", "suite_id"),
                ("ix_tsc_case_id",            "test_suite_cases", "case_id"),
                # test_data_bindings
                ("ix_tdb_case_id",            "test_data_bindings", "case_id"),
                ("ix_tdb_dataset_id",         "test_data_bindings", "dataset_id"),
                # defect_events
                ("ix_de_defect_id",           "defect_events",    "defect_id"),
                ("ix_de_event_type",          "defect_events",    "event_type"),
            ]
            created = []
            from sqlalchemy import inspect as _insp
            tables = _insp(db.bind).get_table_names()
            for idx_name, tbl, col in _INDEXES:
                if tbl not in tables:
                    continue
                try:
                    db.execute(_text(
                        f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tbl} ({col})"
                    ))
                    created.append(idx_name)
                except Exception as _e:
                    logger.debug("[P2] startup probe fallback: %s", _e)  # index may already exist in older SQLite
            db.commit()
            if created:
                logger.info(f"P3-5.1 索引迁移: 已创建/确认 {len(created)} 个索引")
            else:
                logger.info("P3-5.1 索引已全部存在")
    except Exception as e:
        logger.warning(f"P3-5.1 索引迁移失败: {e}")


def _init_optional_modules():
    """初始化可选模块，失败不阻塞"""
    # Pilot Backend
    try:
        pass  # 当前已禁用
    except Exception as e:
        logger.warning(f"Pilot Backend 初始化失败: {e}")
