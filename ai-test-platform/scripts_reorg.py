import subprocess, os, shutil
os.chdir(r"G:\AI项目\ai测试\ai-test-platform")

# Categories: (target_dir, list_of_files)
# DO NOT move: test_*, smoke_*, run_regression_all.py, check_api_contract.py,
#   scan_dangerous_routes.py, scan_print_usage.py (referenced by regression/test scripts)
#   ci_local.bat, ci_local.sh, ci_quality_gate.py (CI infrastructure, keep at root)

debug_files = [
    "debug_datajs.py", "debug_datajs2.py", "debug_datajs3.py", "debug_datajs4.py",
    "debug_datajs5.py", "debug_datajs6.py", "debug_datajs7.py",
    "debug_frontend_api.py", "debug_httpbin.py", "debug_react_issue.py", "debug_testcases.py",
    "diagnose.py", "diagnose_all_issues.py", "diagnose_anthropic_url.py",
    "diagnose_backend.py", "diagnose_deepseek.py", "diagnose_openai_key.py", "diagnose_upload_error.py",
]

migration_files = [
    "init_db.py", "migrate_add_iteration.py", "migrate_d2_3a_1_execution_closure.py",
    "migrate_d2_3a_iteration_center.py", "migrate_json_to_db.py", "migrate_testcases.py",
    "create_iteration_v125.py", "create_test_data.py",
]

tools_files = [
    "check_ai_provider.py", "check_all_features.py", "check_and_start_backend.py",
    "check_data_status.py", "check_db.py", "check_db_tables.py",
    "check_exec_status.py", "check_failure_data.py", "check_import_status.py",
    "check_knowledge_status.py", "check_reports_table.py", "check_scenario4.py", "check_system.py",
    "health_check.py", "cleanup_artifacts.py", "cleanup_projects.py",
    "setup_ollama_cpu.py", "use_ollama_config.py", "model_selector.py",
    "monitor_knowledge_import.py", "compare_apis.py",
]

# Legacy/one-off scripts → archive
archive_files = [
    "_gen_bluedot_cases.py", "_integration_verify.py",
    "_p11_frontend_verify.py", "_p11_response_spec.py", "_p11_response_spec2.py",
    "_p11_risk_scan.py", "_p11_test_guard.py", "_p11_verify_assertions.py",
    "_scan_swagger.py", "_test_ai_assertions.py", "_test_auth.py",
    "_test_phase10.py", "_test_swagger_gen.py", "_verify_no_mock.py",
    "add_missing_apis.py", "add_modules_sdk_apis.py", "add_sample_apis.py",
    "add_test_data_apis.py", "add_workflow_features.py",
    "auto_integrate_knowledge.py", "backend_api_modules_integration.py",
    "complete_decision_rag_integration.py", "complete_test.py",
    "fast_import_code.py", "fast_import_swagger.py", "fill_exec_config.py",
    "fix_api_endpoint.py", "fix_duplicate_ids.py", "fix_issues.py", "fix_ollama_timeout.py",
    "import_codebase_to_knowledge.py", "import_manual_to_kb.py", "import_swagger_to_knowledge.py",
    "integrate_decision_rag.py", "integrate_decision_rag_v2.py",
    "integrate_knowledge_to_workflows.py", "integrate_real_executor.py",
    "integrate_test_data_frontend.py",
    "optimize_script_generation.py", "preview_tapd_desc.py",
    "quick_import_knowledge.py", "quick_import_swagger.py",
    "quick_start_assertion.py", "quick_test.py", "quick_test_data_factory.py", "quick_test_testruns.py",
    "retry_v125_testcases.py", "clean_duplicate_testcases.py", "clean_iteration_requirements.py",
    "mock_target_system.py",
    "p10_fix_misplaced_logger.py", "p10_fix_silent.py", "p10_print_to_logger.py",
    "p10b_apply_confirm_guards.py", "p10b_classify_silent_excepts.py",
    "simple_api_server.py", "simple_web_server.py",
    "start_enhanced_platform.py", "start_platform.py", "start_react_platform.py",
    "start_local_backend.bat", "start_local_frontend.bat",
    # Data files
    "add_dialogs.txt", "ai_providers_mock_data.json",
    "frontend_backend_test_report_20260319_102832.json",
    "frontend_backend_test_report_20260319_103021.json",
    "integration_report.json", "sample_swagger.json", "swaggerApi (1).json",
    "test-swagger-example.json", "test_config.json",
    "test_doc.docx", "test_requirement.docx", "test_requirement.txt",
    "test_response.txt", "tmp_req.txt",
    # Chinese-named
    "\u4ea4\u4ed8\u603b\u7ed3.txt",
    "\u542f\u52a8\u5b8c\u6574\u9879\u76ee.py", "\u5feb\u901f\u4fee\u590d\u542f\u52a8.py",
    "\u63a2\u6d4b\u771f\u5b9e\u767b\u5f55\u63a5\u53e3.py", "\u68c0\u67e5\u9879\u76ee\u72b6\u6001.py",
    "\u89e3\u6790JWT_token.py", "\u8bca\u65adWeb\u95ee\u9898.py",
    "\u8bca\u65ad\u524d\u7aef\u95ee\u9898.py", "\u9a8c\u8bc1\u4fee\u590d\u7ed3\u679c.py",
]

# verify_* at root → scripts/verify/
verify_root_files = [
    "verify_api_fix.py", "verify_d2_2_final.py", "verify_executor_v2.py",
    "verify_local_ready.py", "verify_p1_9.py", "verify_p2_0.py", "verify_phase16_batch_run.py",
]

moves = []
for f in debug_files:
    moves.append((f"scripts/{f}", f"scripts/debug/{f}"))
for f in migration_files:
    moves.append((f"scripts/{f}", f"scripts/migration/{f}"))
for f in tools_files:
    moves.append((f"scripts/{f}", f"scripts/tools/{f}"))
for f in archive_files:
    moves.append((f"scripts/{f}", f"scripts/archive/{f}"))
for f in verify_root_files:
    moves.append((f"scripts/{f}", f"scripts/verify/{f}"))

# Create target dirs
for d in ["scripts/debug", "scripts/migration", "scripts/tools", "scripts/archive"]:
    os.makedirs(d, exist_ok=True)

moved = 0
skipped = 0
for src, dst in moves:
    if not os.path.exists(src):
        skipped += 1
        continue
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    moved += 1

print(f"Moved {moved}, skipped {skipped} (not found)")
r = subprocess.run(["git", "add", "-A", "scripts/"], capture_output=True, text=True)
print(f"git add: rc={r.returncode}")
if r.stderr.strip():
    print(f"  {r.stderr.strip()[:200]}")
print("DONE")