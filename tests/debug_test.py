"""
调试测试脚本
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 测试1：检查报告文件
report_path = "project/project/data/parsed/markdown/000001/2021-1212533363.md"
print(f"文件是否存在: {os.path.exists(report_path)}")

# 测试2：读取报告内容
with open(report_path, 'r', encoding='utf-8') as f:
    content = f.read()
print(f"报告内容长度: {len(content)} 字符")

# 测试3：检查是否包含绿色金融关键词
print(f"包含'绿色金融': {'绿色金融' in content}")
print(f"包含'风险管理': {'风险管理' in content}")

# 测试4：测试字段提取
from src.extract.field_extractor import extract_rule_fields

test_text = """平安银行大力发展绿色金融，积极响应政策要求，完善绿色金融机制建设。
本行制定《绿色融资业务认证标识管理办法》，明确绿色信贷范围。
2021年末，本行绿色信贷余额691.35亿元，同比增长204.6%。
【案例】武汉分行给予亿纬动力9亿元绿色信贷支持。"""

print("\n测试字段提取:")
result = extract_rule_fields(
    text=test_text,
    issue_name="绿色金融",
    source_page=47,
    doc_id="2021-1212533363",
    stock_code="000001",
    report_year=2021,
)
print(f"提取结果: {result}")
print(f"结果长度: {len(result)}")
