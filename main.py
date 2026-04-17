from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.gui.main_window import MainWindow
from app.config import load_config
from app.core.document_loader import read_document
from app.core.chunker import split_text
from app.test_design.testpoint_generator import TestPointGenerator
from app.test_design.testcase_generator import TestCaseGenerator
from app.automation.api_script_generator import ApiScriptGenerator
from app.core.exporter import export_cases


def main() -> None:
    """主程序入口 - 启动GUI"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def demo_new_workflow(file_path: str) -> None:
    """
    演示新的工作流程：需求文档 -> 测试点 -> 测试用例 -> Excel
    
    Args:
        file_path: 需求文档路径
    """
    print("🚀 开始新的AI测试用例生成流程...")
    
    # 1. 加载配置
    config = load_config()
    print(f"✅ 配置加载完成，使用模型: {config.model}")
    
    # 2. 解析需求文档
    requirement_file = Path(file_path)
    if not requirement_file.exists():
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📄 读取需求文档: {requirement_file.name}")
    requirement_text = read_document(requirement_file)
    if not requirement_text:
        print("❌ 文档内容为空")
        return
    
    print(f"📊 文档长度: {len(requirement_text)} 字符")
    
    # 3. 分块处理（如果文档太长）
    chunks = split_text(requirement_text, config.chunk_size)
    print(f"📝 文档分为 {len(chunks)} 个段落")
    
    # 4. 生成测试点
    print("🧠 AI生成测试点...")
    testpoint_generator = TestPointGenerator(config)
    test_points = testpoint_generator.generate_test_points_for_chunks(chunks)
    
    if not test_points:
        print("❌ 未生成任何测试点")
        return
    
    print(f"✅ 生成测试点 {len(test_points)} 个:")
    for i, point in enumerate(test_points, 1):
        print(f"   {i}. {point}")
    
    # 5. 根据测试点生成测试用例
    print("\n🧠 AI根据测试点生成测试用例...")
    testcase_generator = TestCaseGenerator(config)
    test_cases = testcase_generator.generate_test_cases(test_points)
    
    if not test_cases:
        print("❌ 未生成任何测试用例")
        return
    
    print(f"✅ 生成测试用例 {len(test_cases)} 条")
    
    # 6. 转换为Excel格式
    excel_cases = []
    for idx, case in enumerate(test_cases, 1):
        excel_case = {
            "序号": idx,
            "项目名称": config.project_name or "测试项目",
            "模块名称": config.module_name or requirement_file.stem,
            "子模块名称": config.submodule_name or "",
            "测试点": case.get("test_point", ""),  # 新增字段
            "用例标题": case.get("title", ""),
            "前置条件": case.get("precondition", ""),
            "操作步骤": case.get("steps", ""),
            "预期结果": case.get("expected", ""),
            "优先级": case.get("priority", "中")
        }
        excel_cases.append(excel_case)
    
    # 7. 导出Excel
    config.ensure_output_dir()
    output_file = config.output_dir / f"{requirement_file.stem}_测试用例_新流程.xlsx"
    
    print(f"📊 导出Excel: {output_file}")
    export_cases(excel_cases, output_file, sheet_name="测试用例")
    
    # 8. 生成API自动化测试脚本（新增功能）
    print("\n🤖 AI生成API自动化测试脚本...")
    try:
        api_generator = ApiScriptGenerator(config)
        api_scripts = api_generator.generate_scripts_by_module(test_cases)
        
        if api_scripts:
            saved_files = api_generator.save_scripts_to_files(api_scripts)
            print(f"✅ API测试脚本生成成功，共 {len(saved_files)} 个文件：")
            for file_path in saved_files:
                print(f"   📄 {file_path}")
            
            # 生成配置文件
            conftest_content = api_generator.generate_conftest_py()
            conftest_path = Path("tests") / "conftest.py"
            conftest_path.parent.mkdir(exist_ok=True)
            conftest_path.write_text(conftest_content, encoding="utf-8")
            print(f"   📄 {conftest_path}")
            
            requirements_content = api_generator.generate_requirements_txt()
            req_path = Path("tests") / "requirements.txt"
            req_path.write_text(requirements_content, encoding="utf-8")
            print(f"   📄 {req_path}")
        else:
            print("⚠️ 未生成API测试脚本")
            
    except Exception as e:
        print(f"⚠️ API脚本生成失败：{e}")
    
    print(f"\n🎉 完成！共生成 {len(test_cases)} 条测试用例")
    print(f"📁 输出文件:")
    print(f"   Excel: {output_file}")
    if 'saved_files' in locals():
        print(f"   API脚本: tests/ 目录下的 {len(saved_files)} 个文件")


if __name__ == "__main__":
    # 如果有命令行参数，运行演示流程
    if len(sys.argv) > 1:
        demo_new_workflow(sys.argv[1])
    else:
        main()


