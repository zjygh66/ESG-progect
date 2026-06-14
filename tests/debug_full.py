"""
详细调试脚本 - 检查每一步
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.extract.field_extractor import extract_rule_fields

# 报告路径
report_path = "project/project/data/parsed/markdown/000001/2021-1212533363.md"

print("步骤1: 检查文件是否存在")
print(f"文件路径: {report_path}")
print(f"文件存在: {os.path.exists(report_path)}")

# 读取报告内容
print("\n步骤2: 读取报告内容")
with open(report_path, 'r', encoding='utf-8') as f:
    content = f.read()
print(f"报告内容长度: {len(content)} 字符")

# 提取绿色金融章节
print("\n步骤3: 查找绿色金融章节")
lines = content.split('\n')
print(f"总行数: {len(lines)}")

# 查找所有包含"绿色金融"的行
green_lines = []
for i, line in enumerate(lines):
    if "绿色金融" in line:
        green_lines.append((i, line))

print(f"找到 {len(green_lines)} 行包含'绿色金融'")
for i, (line_num, line) in enumerate(green_lines[:10]):
    print(f"  第 {line_num+1} 行: {line[:50]}")

# 找到实际章节（跳过目录）
print("\n步骤4: 查找实际章节内容")
start_idx = -1
for line_num, line in green_lines:
    if line_num > 2800 and "9.1" in line:
        start_idx = line_num
        break

if start_idx == -1:
    print("未找到实际章节，使用第一个匹配")
    if green_lines:
        start_idx = green_lines[0][0]

print(f"起始行: {start_idx}")

# 提取内容
print("\n步骤5: 提取章节内容")
if start_idx != -1:
    end_idx = min(start_idx + 200, len(lines))
    green_finance_content = '\n'.join(lines[start_idx:end_idx])
    print(f"提取内容长度: {len(green_finance_content)}")
    print(f"内容预览: {green_finance_content[:150]}...")
else:
    print("无法提取内容")
    sys.exit(1)

# 字段提取
print("\n步骤6: 调用字段提取")
result = extract_rule_fields(
    text=green_finance_content,
    issue_name="绿色金融",
    source_page=47,
    doc_id="2021-1212533363",
    stock_code="000001",
    report_year=2021,
)

print(f"提取结果类型: {type(result)}")
print(f"提取结果长度: {len(result)}")
print("提取结果:")
for key, value in result.items():
    print(f"  {key}: {value}")

# 检查结果是否为空
print("\n步骤7: 检查结果")
if not result:
    print("结果为空！")
else:
    print("结果正常")
