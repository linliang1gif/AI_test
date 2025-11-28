import os
import pandas as pd
from docx import Document

# ===== 配置 =====
FOLDER = r"D:\360Downloads\easy_davinci-main\easy_davinci-main\api_test_framework\ai测试"
AI_AVAILABLE = False  # 离线模式

# ===== 读取需求文档 =====
def read_docx(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ 文件不存在：{file_path}")
    doc = Document(file_path)
    return [p.text.strip() for p in doc.paragraphs if p.text.strip()]

# ===== 离线生成测试步骤 =====
def generate_steps(req_text, scenario):
    steps = []
    steps.append(f"Step1. 执行操作 '{req_text}' - {scenario}")
    steps.append(f"Step2. 验证系统对 '{req_text}' 的 {scenario} 响应")
    steps.append(f"Step3. 检查数据或界面变化是否符合预期")
    return "\n".join(steps)

# ===== 生成测试用例 =====
def generate_test_cases(requirements):
    cases = []
    scenario_types = ["正常流程", "异常输入", "边界条件", "系统异常"]
    priority_map = {"正常流程": "高", "异常输入": "高", "边界条件": "中", "系统异常": "低"}

    tc_counter = 1
    for req in requirements:
        for scenario in scenario_types:
            case = {
                "用例编号": f"TC-{tc_counter:03d}",
                "用例标题": f"{req[:20]}-{scenario}",
                "前置条件": "用户已登录 / 数据已初始化",
                "测试步骤": generate_steps(req, scenario),
                "预期结果": f"系统正确处理 {scenario}，符合需求 '{req}'",
                "优先级": priority_map[scenario]
            }
            cases.append(case)
            tc_counter += 1
    return cases

# ===== 保存到 Excel =====
def save_to_excel(cases, filename):
    try:
        df = pd.DataFrame(cases)
        df.to_excel(filename, index=False)
        print(f"✅ 测试用例已导出到 {filename}")
    except PermissionError:
        print(f"❌ 保存失败：请关闭 Excel 文件后重试（{filename}）")

# ===== 批量处理文件夹 =====
if __name__ == "__main__":
    for file in os.listdir(FOLDER):
        if file.startswith("~$") or not file.endswith(".docx"):
            continue  # 跳过临时文件和非 docx 文件

        file_path = os.path.join(FOLDER, file)
        print(f"📄 正在处理文件：{file}")

        try:
            requirements = read_docx(file_path)
            if not requirements:
                print(f"❌ 文件 {file} 内容为空或无有效段落")
                continue

            cases = generate_test_cases(requirements)
            # 打印前 3 条示例
            print(f"📋 {file} 示例测试用例：")
            for case in cases[:3]:
                print("===")
                for k, v in case.items():
                    print(f"{k}: {v}")

            # 保存 Excel
            base_name = os.path.splitext(file)[0]
            excel_file = os.path.join(FOLDER, f"{base_name}_测试用例.xlsx")
            save_to_excel(cases, excel_file)
            print(f"✅ 共生成 {len(cases)} 条测试用例\n")

        except Exception as e:
            print(f"❌ 处理文件 {file} 时出错：{e}")
