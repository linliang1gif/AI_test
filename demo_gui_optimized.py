#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 测试用例生成器 - GUI 优化演示

本脚本展示优化后的 GUI 界面功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动优化后的 GUI"""
    try:
        from PySide6.QtWidgets import QApplication
        from app.gui.main_window import MainWindow
        
        print("🚀 启动 AI 测试用例生成器 v3.3 Pro")
        print("📋 优化功能包括:")
        print("   ✅ 配置模板快速选择")
        print("   ✅ API Key 实时验证")
        print("   ✅ 详细进度显示和时间估算")
        print("   ✅ 文件统计和质量分析")
        print("   ✅ 增强的预览表格（含测试点列）")
        print("   ✅ 用例复制和批量操作")
        print("   ✅ 美化的界面和按钮样式")
        print("   ✅ 配置验证和智能提示")
        print()
        
        app = QApplication(sys.argv)
        
        # 设置应用程序样式
        app.setStyle('Fusion')
        
        window = MainWindow()
        window.show()
        
        print("✨ GUI 界面已启动，请在窗口中体验优化后的功能！")
        
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装 PySide6: pip install PySide6")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()