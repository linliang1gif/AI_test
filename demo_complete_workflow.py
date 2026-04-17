#!/usr/bin/env python3
"""
完整演示新的两阶段AI测试用例生成工作流程
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_config
from app.core.document_loader import read_document
from app.core.chunker import split_text
from app.test_design.testpoint_generator import TestPointGenerator
from app.test_design.testcase_generator import TestCaseGenerator


def demo_step_by_step():
    """逐步演示新工作流程的每个阶段"""
    
    print("=" * 60)
    print("🚀 AI测试用例生成工具 - 新流程完整演示")
    print("=" * 60)
    
    # 1. 加载配置
    print("\n📋 第1步：加载配置")
    config = load_config()
    print(f"   ✅ API密钥: {'已配置' if config.api_key else '未配置'}")
    print(f"   ✅ 模型: {config.model}")
    print(f"   ✅ 基础URL: {config.base_url}")
    print(f"   ✅ 输出目录: {config.output_dir}")
    
    if not config.api_key:
        print("❌ 错误：未配置API密钥，请检查.env文件")
        return
    
    # 2. 读取需求文档
    print("\n📄 第2步：读取需求文档")
    doc_file = Path("需求文档.docx")
    if not doc_file.exists():
        print(f"❌ 错误：文件不存在 {doc_file}")
        return
    
    try:
        requirement_text = read_document(doc_file)
        print(f"   ✅ 文档读取成功")
        print(f"   📊 文档长度: {len(requirement_text)} 字符")
        print(f"   📝 前100字符预览: {requirement_text[:100]}...")
    except Exception as e:
        print(f"❌ 错误：文档读取失败 - {e}")
        return
    
    # 3. 文档分块
    print("\n✂️ 第3步：文档分块处理")
    chunks = split_text(requirement_text, config.chunk_size)
    print(f"   ✅ 分块完成，共 {len(chunks)} 个段落")
    for i, chunk in enumerate(chunks, 1):
        print(f"   📝 段落{i}: {len(chunk)} 字符")
    
    # 4. 生成测试点
    print("\n🧠 第4步：AI生成测试点")
    print("   正在调用AI生成测试点...")
    
    try:
        testpoint_generator = TestPointGenerator(config)
        test_points = testpoint_generator.generate_test_points_for_chunks(chunks)
        
        print(f"   ✅ 测试点生成成功，共 {len(test_points)} 个")
        print("   📋 生成的测试点:")
        for i, point in enumerate(test_points, 1):
            print(f"      {i}. {point}")
            
        # 保存测试点
        points_file = Path("output") / "演示_测试点.txt"
        points_file.parent.mkdir(exist_ok=True)
        points_file.write_text('\n'.join(f"{i}. {point}" for i, point in enumerate(test_points, 1)), encoding="utf-8")
        print(f"   💾 测试点已保存到: {points_file}")
        
    except Exception as e:
        print(f"❌ 错误：测试点生成失败 - {e}")
        return
    
    # 5. 生成测试用例
    print("\n🧠 第5步：AI根据测试点生成测试用例")
    print("   正在调用AI生成测试用例...")
    
    try:
        testcase_generator = TestCaseGenerator(config)
        test_cases = testcase_generator.generate_test_cases(test_points)
        
        print(f"   ✅ 测试用例生成成功，共 {len(test_cases)} 条")
        print("   📋 生成的测试用例预览:")
        for i, case in enumerate(test_cases[:3], 1):  # 只显示前3条
            print(f"      {i}. 测试点: {case.get('test_point', '')}")
            print(f"         标题: {case.get('title', '')}")
            print(f"         步骤: {case.get('steps', '')[:50]}...")
            print()
            
    except Exception as e:
        print(f"❌ 错误：测试用例生成失败 - {e}")
        return
    
    # 6. 导出Excel
    print("\n📊 第6步：导出Excel文件")
    try:
        from app.core.exporter import export_cases
        
        # 转换为Excel格式
        excel_cases = []
        for idx, case in enumerate(test_cases, 1):
            excel_case = {
                "序号": idx,
                "项目名称": config.project_name or "演示项目",
                "模块名称": config.module_name or "需求文档",
                "子模块名称": config.submodule_name or "",
                "测试点": case.get("test_point", ""),
                "用例标题": case.get("title", ""),
                "前置条件": case.get("precondition", ""),
                "操作步骤": case.get("steps", ""),
                "预期结果": case.get("expected", ""),
                "优先级": case.get("priority", "中")
            }
            excel_cases.append(excel_case)
        
        # 导出
        output_file = Path("output") / "演示_测试用例_新流程.xlsx"
        export_cases(excel_cases, output_file, sheet_name="测试用例")
        
        print(f"   ✅ Excel导出成功")
        print(f"   📁 文件位置: {output_file}")
        
    except Exception as e:
        print(f"❌ 错误：Excel导出失败 - {e}")
        return
    
    # 7. 总结
    print("\n🎉 第7步：流程完成总结")
    print("=" * 60)
    print("✅ 新流程演示完成！")
    print(f"📊 统计信息:")
    print(f"   - 输入文档: {doc_file.name} ({len(requirement_text)} 字符)")
    print(f"   - 文档分块: {len(chunks)} 个段落")
    print(f"   - 测试点: {len(test_points)} 个")
    print(f"   - 测试用例: {len(test_cases)} 条")
    print(f"📁 输出文件:")
    print(f"   - 测试点: output/演示_测试点.txt")
    print(f"   - 测试用例: output/演示_测试用例_新流程.xlsx")
    print("=" * 60)


def demo_simple():
    """简化版演示，直接调用新工作流程"""
    print("🚀 简化版新流程演示")
    
    try:
        from app.core.new_workflow import generate_with_new_workflow
        
        config = load_config()
        doc_file = Path("需求文档.docx")
        
        if not doc_file.exists():
            print(f"❌ 文件不存在: {doc_file}")
            return
        
        def progress_callback(msg: str):
            print(msg)
        
        results = generate_with_new_workflow(
            files=[doc_file],
            config=config,
            log_callback=progress_callback
        )
        
        if results and not results[0].error:
            result = results[0]
            print(f"\n🎉 处理完成！")
            print(f"📊 测试点: {result.test_points_count} 个")
            print(f"📊 测试用例: {result.cases_count} 条")
            print(f"📊 质量评分: {result.quality_score}/100")
            print(f"📁 输出文件: {result.output_file}")
        else:
            print("❌ 处理失败")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        demo_simple()
    else:
        demo_step_by_step()