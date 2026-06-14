"""
检查批量处理逻辑
"""
import os
import sys

sys.path.insert(0, '.')

from src.extract.field_extractor import (
    load_section_locations,
    build_doc_id_to_stock_code_mapping,
)

# 读取 section_locations.csv
section_locations_path = 'project/project/outputs/reports/section_locations.csv'
parsed_dir = 'project/project/data/parsed/markdown'

sections = load_section_locations(section_locations_path)
doc_id_to_stock = build_doc_id_to_stock_code_mapping(parsed_dir)

print(f"加载 {len(sections)} 条 section_locations 记录")
print(f"建立 {len(doc_id_to_stock)} 个 doc_id -> stock_code 映射")

# 检查每个记录的处理情况
processed_count = 0
skipped_count = 0

for sec in sections:
    doc_id = sec["doc_id"]
    issue_name = sec["issue_name"]
    
    if not doc_id:
        skipped_count += 1
        continue
    
    # 查找 stock_code
    stock_code = doc_id_to_stock.get(doc_id, "")
    
    # 读取 markdown 文件
    if stock_code:
        md_path = os.path.join(parsed_dir, stock_code, f"{doc_id}.md")
    else:
        md_path = None
    
    if md_path and os.path.exists(md_path):
        processed_count += 1
    else:
        skipped_count += 1
        if doc_id == '2021-1212533363':
            print(f"跳过平安银行记录: {issue_name}, md_path={md_path}, exists={os.path.exists(md_path) if md_path else False}")

print(f"\n处理: {processed_count} 条")
print(f"跳过: {skipped_count} 条")

# 检查平安银行记录
pingan_sections = [s for s in sections if s['doc_id'] == '2021-1212533363']
print(f"\n平安银行记录数: {len(pingan_sections)}")

for sec in pingan_sections:
    stock_code = doc_id_to_stock.get(sec['doc_id'], "")
    md_path = os.path.join(parsed_dir, stock_code, f"{sec['doc_id']}.md")
    exists = os.path.exists(md_path) if md_path else False
    print(f"  {sec['issue_name']}: stock_code={stock_code}, md_path={md_path}, exists={exists}")