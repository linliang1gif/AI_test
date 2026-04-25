from openai import OpenAI
import pandas as pd
from docx import Document
import os
import time
import re
from openpyxl.styles import PatternFill, Alignment

# ===== 配置 DeepSeek API Key =====
import os as _os
client = OpenAI(
    api_key=_os.getenv("DEEPSEEK_API_KEY", ""),
    base_url=_os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
)

# ===== 读取 Word 文档 =====
def read_docx(file_path):
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

# ===== 文本分段 =====
def split_text(text, max_chars=3000):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

# ===== 调用 DeepSeek 生成测试用例（带重试） =====
def generate_test_cases(requirement_text, retries=3):
    prompt = f"""
你是一名资深的软件测试专家，任务是根据需求文档生成专业的功能测试用例。

请输出 **覆盖完整的测试用例集**，要求如下：

【输出格式】
用例编号：TC-001
用例标题：简洁描述验证目标
前置条件：测试执行前的必要状态（如用户已登录/数据库已有数据）
测试步骤：
Step1. 操作步骤
Step2. 操作步骤
...
预期结果：明确、可验证的结果
优先级：高/中/低

【生成规则】
1. 覆盖所有需求点，包括：
   - 正常路径
   - 异常输入
   - 边界条件
   - 系统异常或特殊场景
2. 测试步骤必须用 Step1 / Step2 编号
3. 优先级判定：
   - 高：核心业务/用户体验/系统安全
   - 中：常见功能
   - 低：边界或极少使用场景
4. 用例数：根据需求复杂度自动决定（不少于10条）

【需求文档内容】
{requirement_text}
"""

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️ 调用失败，第 {attempt+1} 次重试中... 错误：{e}")
            time.sleep(3)
    raise RuntimeError("❌ 多次调用失败，请检查网络或 API Key")

# ===== 修复格式 =====
def fix_format(ai_output):
    fixed_lines = []
    lines = ai_output.split("\n")
    case_id = 1

    for line in lines:
        line = line.strip()
        if re.match(r"^用例编号", line):
            fixed_lines.append(f"用例编号：TC-{case_id:03d}")
            case_id += 1
        elif line.startswith("用例标题") and "：" not in line:
            fixed_lines.append("用例标题：" + line.replace("用例标题", "").strip())
        elif line.startswith("前置条件") and "：" not in line:
            fixed_lines.append("前置条件：" + line.replace("前置条件", "").strip())
        elif line.startswith("测试步骤") and "：" not in line:
            fixed_lines.append("测试步骤：\n" + line.replace("测试步骤", "").strip())
        elif line.startswith("预期结果") and "：" not in line:
            fixed_lines.append("预期结果：" + line.replace("预期结果", "").strip())
        elif line.startswith("优先级") and "：" not in line:
            fixed_lines.append("优先级：" + line.replace("优先级", "").strip())
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)

# ===== 保存日志 =====
def save_log(ai_output, log_file):
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(ai_output)
    print(f"📝 AI 原始输出已保存到 {log_file}")

# ===== 解析到 Excel 并标红异常 =====
def parse_to_excel(ai_output, output_file="test_cases.xlsx"):
    cases, current_case = [], {}
    for line in ai_output.split("\n"):
        line = line.strip()
        if line.startswith("用例编号"):
            if current_case:
                cases.append(current_case)
                current_case = {}
            current_case["用例编号"] = line.split("：")[-1].strip()
        elif line.startswith("用例标题"):
            current_case["用例标题"] = line.split("：")[-1].strip()
        elif line.startswith("前置条件"):
            current_case["前置条件"] = line.split("：")[-1].strip()
        elif line.startswith("测试步骤"):
            current_case["测试步骤"] = ""
        elif line.startswith("Step"):
            current_case["测试步骤"] += line + "\n"
        elif line.startswith("预期结果"):
            current_case["预期结果"] = line.split("：")[-1].strip()
        elif line.startswith("优先级"):
            current_case["优先级"] = line.split("：")[-1].strip()
    if current_case:
        cases.append(current_case)

    if cases:
        df = pd.DataFrame(cases)
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
            ws = writer.sheets["Sheet1"]
            wrap_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
            for col in ws.columns:
                for cell in col:
                    cell.alignment = Alignment(wrap_text=True)
                    # 异常标红：步骤为空或优先级为空
                    if cell.column_letter == 'D' and (cell.value is None or cell.value.strip() == ""):
                        cell.fill = wrap_fill
                    if cell.column_letter == 'F' and (cell.value is None or cell.value.strip() == ""):
                        cell.fill = wrap_fill
        print(f"✅ 测试用例已导出到 {output_file}，缺失步骤/优先级已标黄")
    else:
        print("⚠️ 未解析出测试用例，请检查 AI 输出")

# ===== 主流程 =====
if __name__ == "__main__":
    folder = os.path.dirname(os.path.abspath(__file__))
    docx_files = [f for f in os.listdir(folder) if f.endswith(".docx")]
    if not docx_files:
        print("❌ 文件夹中未找到任何 .docx 文件")
        exit(1)

    for file in docx_files:
        print(f"📄 正在处理文件：{file}")
        requirement_text = read_docx(os.path.join(folder, file))
        parts = split_text(requirement_text)
        all_ai_results = []

        for idx, part in enumerate(parts, 1):
            print(f"📝 分段 {idx}/{len(parts)} 正在生成用例...")
            ai_result = generate_test_cases(part)
            all_ai_results.append(ai_result)

        final_ai_output = "\n".join(all_ai_results)
        fixed_output = fix_format(final_ai_output)

        log_file = file.replace(".docx", "_AI原始输出.txt")
        save_log(fixed_output, log_file)

        excel_file = file.replace(".docx", "_测试用例.xlsx")
        parse_to_excel(fixed_output, excel_file)
