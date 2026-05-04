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


def _init_optional_modules():
    """初始化可选模块，失败不阻塞"""
    # Pilot Backend
    try:
        pass  # 当前已禁用
    except Exception as e:
        logger.warning(f"Pilot Backend 初始化失败: {e}")
