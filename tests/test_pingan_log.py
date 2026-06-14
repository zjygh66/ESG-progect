"""
详细测试批量处理功能 - 输出到文件
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

# 创建日志文件
log_file = 'outputs/test_log.txt'
os.makedirs(os.path.dirname(log_file), exist_ok=True)

with open(log_file, 'w', encoding='utf-8') as log:
    # 读取 section_locations.csv
    section_locations_path = 'project/project/outputs/reports/section_locations.csv'
    parsed_dir = 'project/project/data/parsed/markdown'
    output_path = 'outputs/results/base_records.csv'
    
    sections = load_section_locations(section_locations_path)
    doc_id_to_stock = build_doc_id_to_stock_code_mapping(parsed_dir)
    
    log.write(f"加载 {len(sections)} 条 section_locations 记录\n")
    log.write(f"建立 {len(doc_id_to_stock)} 个 doc_id -> stock_code 映射\n")
    
    results = []
    processed_count = 0
    
    # 只处理平安银行记录
    pingan_sections = [s for s in sections if s['doc_id'] == '2021-1212533363']
    log.write(f"平安银行记录数: {len(pingan_sections)}\n")
    
    for sec in pingan_sections:
        doc_id = sec["doc_id"]
        issue_name = sec["issue_name"]
        start_page = sec["start_page"]
        end_page = sec["end_page"]
        
        log.write(f"\n处理: {issue_name}\n")
        
        if not doc_id:
            log.write("  跳过：无 doc_id\n")
            continue
        
        # 查找 stock_code
        stock_code = doc_id_to_stock.get(doc_id, "")
        report_year = extract_year_from_doc_id(doc_id)
        log.write(f"  stock_code: {stock_code}, report_year: {report_year}\n")
        
        # 读取 markdown 文件
        if stock_code:
            md_path = os.path.join(parsed_dir, stock_code, f"{doc_id}.md")
        else:
            md_path = None
        
        if md_path and os.path.exists(md_path):
            log.write(f"  文件存在: {md_path}\n")
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            log.write(f"  文件内容长度: {len(content)}\n")
        else:
            log.write(f"  文件不存在，跳过\n")
            continue
        
        # 提取字段
        source_page = start_page if start_page is not None else 0
        log.write(f"  source_page: {source_page}\n")
        
        try:
            record = extract_rule_fields(
                text=content,
                issue_name=issue_name,
                source_page=source_page,
                doc_id=doc_id,
                stock_code=stock_code,
                report_year=report_year,
                matrix_importance=None,
            )
            
            log.write(f"  提取结果: issue_name={record['issue_name']}, risk_tone={record['risk_tone']}\n")
            results.append(record)
            processed_count += 1
        except Exception as e:
            log.write(f"  错误: {e}\n")
    
    log.write(f"\n成功处理 {processed_count} 条记录\n")
    log.write(f"results 列表长度: {len(results)}\n")
    
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
        
        log.write(f"\noutput_results 列表长度: {len(output_results)}\n")
        
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerows(output_results)
        
        log.write(f"已生成 {len(output_results)} 条记录 -> {output_path}\n")
    else:
        log.write("未生成任何记录\n")

print("测试完成，日志已保存到 outputs/test_log.txt")