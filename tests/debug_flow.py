"""
详细调试脚本 - 查看提取流程
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.extract.field_extractor import extract_rule_fields

# 报告路径
report_path = "project/project/data/parsed/markdown/000001/2021-1212533363.md"

# 读取报告内容
with open(report_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"报告内容长度: {len(content)} 字符")

# 测试绿色金融议题
issue_name = "绿色金融"
keywords = ['绿色金融', '绿色信贷']

# 找到包含关键词的行
lines = content.split('\n')
start_idx = -1
for i, line in enumerate(lines):
    if any(kw in line for kw in keywords):
        start_idx = i
        break

if start_idx == -1:
    print("未找到绿色金融相关内容")
    sys.exit(1)

print(f"找到起始行: {start_idx + 1}")

# 提取内容
end_idx = min(start_idx + 150, len(lines))
issue_content = '\n'.join(lines[start_idx:end_idx])[:3000]

print(f"提取内容长度: {len(issue_content)}")
print(f"提取内容前200字符: {issue_content[:200]}...")

# 调用字段提取
print("\n调用字段提取...")
result = extract_rule_fields(
    text=issue_content,
    issue_name=issue_name,
    source_page=47,
    doc_id="2021-1212533363",
    stock_code="000001",
    report_year=2021,
)

print(f"\n提取结果:")
for key, value in result.items():
    print(f"  {key}: {value}")

print(f"\n结果包含字段数: {len(result)}")
