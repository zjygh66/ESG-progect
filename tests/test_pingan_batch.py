"""
完整检查批量处理逻辑
"""
import os
import sys
import csv

sys.path.insert(0, '.')

from src.extract.field_extractor import (
    load_section_locations,
    build_doc_id_to_stock_code_mapping,
    extract_year_from_doc_id,
    extract_rule_fields,
)

# 读取 section_locations.csv
section_locations_path = 'project/project/outputs/reports/section_locations.csv'
parsed_dir = 'project/project/data/parsed/markdown'
output_path = 'outputs/results/base_records.csv'

sections = load_section_locations(section_locations_path)
doc_id_to_stock = build_doc_id_to_stock_code_mapping(parsed_dir)

print(f"加载 {len(sections)} 条 section_locations 记录")
print(f"建立 {len(doc_id_to_stock)} 个 doc_id -> stock_code 映射")

results = []
processed_count = 0

# 只处理平安银行记录
pingan_sections = [s for s in sections if s['doc_id'] == '2021-1212533363']
print(f"平安银行记录数: {len(pingan_sections)}")

for sec in pingan_sections:
    doc_id = sec["doc_id"]
    issue_name = sec["issue_name"]
    start_page = sec["start_page"]
    end_page = sec["end_page"]
    
    print(f"\n处理: {issue_name}")
    
    if not doc_id:
        print("  跳过：无 doc_id")
        continue
    
    # 查找 stock_code
    stock_code = doc_id_to_stock.get(doc_id, "")
    report_year = extract_year_from_doc_id(doc_id)
    print(f"  stock_code: {stock_code}, report_year: {report_year}")
    
    # 读取 markdown 文件
    if stock_code:
        md_path = os.path.join(parsed_dir, stock_code, f"{doc_id}.md")
    else:
        md_path = None
    
    if md_path and os.path.exists(md_path):
        print(f"  文件存在: {md_path}")
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"  文件内容长度: {len(content)}")
    else:
        print(f"  文件不存在，跳过")
        continue
    
    # 提取字段
    source_page = start_page if start_page is not None else 0
    print(f"  source_page: {source_page}")
    
    record = extract_rule_fields(
        text=content,
        issue_name=issue_name,
        source_page=source_page,
        doc_id=doc_id,
        stock_code=stock_code,
        report_year=report_year,
        matrix_importance=None,
    )
    
    print(f"  提取结果: issue_name={record['issue_name']}, risk_tone={record['risk_tone']}")
    results.append(record)
    processed_count += 1

print(f"\n成功处理 {processed_count} 条记录")
print(f"results 列表长度: {len(results)}")

# 输出结果
if results:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 定义用户要求的输出字段顺序
    output_fieldnames = [
        'company_code', 'report_year', 'issue_name', 'anchor_type', 
        'source_page', 'evidence_snippet',
        'has_policy_ref', 'has_scope_statement', 'has_case_study',
        'risk_tone', 'has_kpi_value', 'has_yoy_change', 
        'has_method_note', 'has_assurance',
        'verifiability_score', 'spotlight_bias_flag'
    ]
    
    # 转换结果格式
    output_results = []
    for record in results:
        output_record = {
            'company_code': record['stock_code'],
            'report_year': record['report_year'],
            'issue_name': record['issue_name'],
            'anchor_type': 'narrative',
            'source_page': record['source_page'],
            'evidence_snippet': record['evidence_snippet'],
            'has_policy_ref': record['has_policy_ref'],
            'has_scope_statement': record['has_scope_statement'],
            'has_case_study': record['has_case_study'],
            'risk_tone': record['risk_tone'],
            'has_kpi_value': record['has_kpi_value'],
            'has_yoy_change': record['has_yoy_change'],
            'has_method_note': record['has_method_note'],
            'has_assurance': record['has_assurance'],
            'verifiability_score': record['verifiability_score'],
            'spotlight_bias_flag': record['spotlight_bias_flag']
        }
        output_results.append(output_record)
    
    print(f"\noutput_results 列表长度: {len(output_results)}")
    
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(output_results)
    
    print(f"已生成 {len(output_results)} 条记录 -> {output_path}")
else:
    print("未生成任何记录")