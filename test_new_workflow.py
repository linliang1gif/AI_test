#!/usr/bin/env python3
"""
测试新的两阶段工作流程
使用方法：python test_new_workflow.py [需求文档路径]
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_config
from app.core.new_workflow import generate_with_new_workflow


def test_new_workflow():
    """测试新的工作流程"""
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法：python test_new_workflow.py <需求文档路径>")
        print("示例：python test_new_workflow.py 需求文档.docx")
        return
    
    file_path = sys.argv[1]
    doc_file = Path(file_path)
    
    if not doc_file.exists():
        print(f"❌ 文件不存在：{file_path}")
        return
    
    print("🚀 开始测试新的AI测试用例生成流程...")
    print(f"📄 输入文件：{doc_file.name}")
    
    # 加载配置
    config = load_config()
    print(f"⚙️ 使用模型：{config.model}")
    print(f"📁 输出目录：{config.output_dir}")
    
    # 确保输出目录存在
    config.ensure_output_dir()
    
    # 定义进度回调
    def progress_callback(message: str):
        print(message)
    
    try:
        # 执行新工作流程
        results = generate_with_new_workflow(
            files=[doc_file],
            config=config,
            log_callback=progress_callback
        )
        
        # 输出结果
        if results:
            result = results[0]
            if result.error:
                print(f"❌ 处理失败：{result.error}")
            else:
                print("\n🎉 处理完成！")
                print(f"📊 统计信息：")
                print(f"   - 测试点：{result.test_points_count} 个")
                print(f"   - 测试用例：{result.cases_count} 条")
                print(f"   - 质量评分：{result.quality_score}/100")
                print(f"📁 输出文件：{result.output_file}")
        else:
            print("❌ 未生成任何结果")
            
    except Exception as e:
        print(f"❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_new_workflow()