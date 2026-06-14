"""
简单测试批量处理功能
"""
import os
import sys

sys.path.insert(0, '.')

from src.extract.field_extractor import (
    load_section_locations,
    build_doc_id_to_stock_code_mapping,
)

# 读取 section_locations.csv
sections = load_section_locations('project/project/outputs/reports/section_locations.csv')
print(f"总记录数: {len(sections)}")

# 过滤平安银行记录
pingan_sections = [s for s in sections if s['doc_id'] == '2021-1212533363']
print(f"平安银行记录数: {len(pingan_sections)}")

for s in pingan_sections:
    print(f"  - {s['issue_name']}: start_page={s['start_page']}, end_page={s['end_page']}")

# 检查映射
doc_id_to_stock = build_doc_id_to_stock_code_mapping('project/project/data/parsed/markdown')
print(f"\n映射记录数: {len(doc_id_to_stock)}")
print(f"平安银行 stock_code: {doc_id_to_stock.get('2021-1212533363', '未找到')}")

# 检查文件路径
parsed_dir = 'project/project/data/parsed/markdown'
stock_code = doc_id_to_stock.get('2021-1212533363', '')
if stock_code:
    md_path = os.path.join(parsed_dir, stock_code, '2021-1212533363.md')
    print(f"\nMarkdown 文件路径: {md_path}")
    print(f"文件存在: {os.path.exists(md_path)}")