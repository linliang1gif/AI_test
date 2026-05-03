"""
P2-2 统一路由注册
所有 include_router 集中在此，避免分散注册和重复注册。
可选模块缺失时只 warning，不阻塞启动。
"""
import logging

logger = logging.getLogger("router_registry")

# 可选模块可用性标志（供 health 端点读取）
MODULE_FLAGS: dict = {}


def _safe_import(module_path: str, attr: str, label: str):
    """安全导入模块，失败返回 None"""
    try:
        mod = __import__(module_path, fromlist=[attr])
        obj = getattr(mod, attr)
        MODULE_FLAGS[label] = True
        return obj
    except Exception as e:
        MODULE_FLAGS[label] = False
        logger.warning(f"{label} 导入失败: {e}")
        return None


def register_routers(app):
    """将所有路由集中注册到 app 上"""

    # ── 基础端点 (/health, /readiness, /admin) ──
    from backend.health import router as health_router
    app.include_router(health_router)

    # ── 可选的 agent / strategy / orchestrator 等旧模块 ──
    _optional_routers = [
        ("agent.controller",              "router", "/api", "test_agent"),
        ("routes.ai_routes",              "router", "/api", "ai_routes"),
        ("strategy.controller",           "router", "/api", "strategy_engine"),
        ("orchestrator.controller",       "router", "/api", "orchestrator"),
        ("self_healing.controller",       "router", "/api", "self_healing"),
        ("pipeline.controller",           "router", "/api", "pipeline"),
        ("case_generator.controller",     "case_router", "/api", "case_generator"),
    ]
    for mod_path, attr, prefix, label in _optional_routers:
        router = _safe_import(mod_path, attr, label)
        if router:
            app.include_router(router, prefix=prefix)
            logger.info(f"✅ {label} 已加载")

    # ── routes/ 下的核心路由（无 prefix，路由文件内部已含 /api/v2 等前缀） ──
    _core_routes = [
        ("routes.project_config_routes",     "router", "项目配置路由"),
        ("routes.test_run_routes",           "router", "测试执行路由"),
        ("routes.observability_routes",      "router", "可观测性路由"),
        ("routes.execution_trigger_routes",  "router", "执行触发路由"),
        ("routes.case_governance_routes",    "router", "用例治理路由"),
        ("routes.case_execute_routes",       "router", "用例一键执行路由"),
        ("routes.swagger_routes",            "router", "Swagger导入路由"),
        ("routes.executor_v2_routes",        "router", "Executor V2 路由"),
        ("routes.batch_run_routes",          "router", "批量执行中心路由"),
        ("routes.mock_routes",               "router", "Mock API 路由"),
        ("routes.demo_routes",               "router", "Demo 路由"),
        ("routes.dashboard_routes",          "router", "Dashboard 路由"),
        ("routes.ai_report_routes",          "router", "AI 报告分析路由"),
        ("routes.real_project_routes",       "router", "真实项目快速接入路由"),
        ("routes.ai_case_review_routes",     "router", "AI 用例评审路由"),
        ("routes.page_scanner_routes",       "router", "页面扫描路由"),
        ("routes.performance_routes",        "router", "性能测试路由"),
        ("routes.web_ui_batch_routes",       "router", "Web UI 批量执行路由"),
        ("routes.test_suite_routes",         "router", "测试集管理路由"),
    ]
    for mod_path, attr, label in _core_routes:
        router = _safe_import(mod_path, attr, label)
        if router:
            app.include_router(router)
            logger.info(f"✅ {label} 已加载")

    # ── report_routes 特殊：导出两个 router ──
    try:
        from routes.report_routes import router as report_router, reports_router
        app.include_router(report_router)
        app.include_router(reports_router)
        MODULE_FLAGS["report_routes"] = True
        logger.info("✅ 测试报告路由已加载")
    except Exception as e:
        MODULE_FLAGS["report_routes"] = False
        logger.warning(f"测试报告路由导入失败: {e}")

    # ── modules SDK 相关（可选） ──
    MODULE_FLAGS["modules_sdk"] = False
    MODULE_FLAGS["core_models"] = False
    MODULE_FLAGS["model_converter"] = False
    try:
        from modules.swagger import SwaggerTestCaseGenerator
        MODULE_FLAGS["modules_sdk"] = True
    except ImportError:
        pass
    try:
        from core import TestCase as _TC
        MODULE_FLAGS["core_models"] = True
    except ImportError:
        pass
    try:
        from utils.model_converter import testcase_to_dict as _
        MODULE_FLAGS["model_converter"] = True
    except ImportError:
        pass

    # ── 触发系统（仅注册一次，避免重复） ──
    try:
        from modules.trigger.test_trigger_system import TestTriggerSystem
        from modules.trigger.trigger_api import create_trigger_router
        trigger_system = TestTriggerSystem(pipeline_service=None)
        trigger_router = create_trigger_router(trigger_system)
        app.include_router(trigger_router)
        MODULE_FLAGS["trigger_system"] = True
        logger.info("✅ 触发系统已加载")
    except ImportError as e:
        MODULE_FLAGS["trigger_system"] = False
        logger.warning(f"触发系统导入失败: {e}")

    # ── 分析系统（可选） ──
    analysis_router = _safe_import("modules.analysis.analysis_api", "router", "analysis_system")
    if analysis_router:
        app.include_router(analysis_router)
        logger.info("✅ 分析系统已加载")

    # ── 测试数据工厂标志 ──
    try:
        from test_data.data_factory import factory
        MODULE_FLAGS["test_data_factory"] = True
    except ImportError:
        MODULE_FLAGS["test_data_factory"] = False

    logger.info(f"路由注册完成，可用模块: {sum(v for v in MODULE_FLAGS.values() if v)}/{len(MODULE_FLAGS)}")
