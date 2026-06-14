"""
测试批量处理功能
"""
import sys
sys.path.insert(0, '.')

from src.extract.field_extractor import (
    load_section_locations,
    build_doc_id_to_stock_code_mapping,
    extract_rule_fields,
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
mapping = build_doc_id_to_stock_code_mapping('project/project/data/parsed/markdown')
print(f"\n映射记录数: {len(mapping)}")
print(f"平安银行 stock_code: {mapping.get('2021-1212533363', '未找到')}")

# 测试单条提取
import os
md_path = os.path.join('project/project/data/parsed/markdown', '000001', '2021-1212533363.md')
print(f"\nMarkdown 文件路径: {md_path}")
print(f"文件存在: {os.path.exists(md_path)}")

if os.path.exists(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"文件内容长度: {len(content)}")
    
    # 测试绿色金融提取
    result = extract_rule_fields(
        text=content,
        issue_name="绿色金融",
        source_page=47,
        doc_id="2021-1212533363",
        stock_code="000001",
        report_year=2021,
    )
    print(f"\n绿色金融提取结果:")
    print(f"  issue_name: {result['issue_name']}")
    print(f"  risk_tone: {result['risk_tone']}")
    print(f"  verifiability_score: {result['verifiability_score']}")