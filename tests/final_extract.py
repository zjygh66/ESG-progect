"""
平安银行绿色金融报告字段提取 - 最终版
"""
import os
import sys
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.extract.field_extractor import extract_rule_fields

def main():
    print("=" * 60)
    print("平安银行绿色金融报告字段提取")
    print("=" * 60)
    
    # 报告路径
    report_path = "project/project/data/parsed/markdown/000001/2021-1212533363.md"
    
    # 读取报告内容
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取绿色金融章节（从第2869行开始）
    lines = content.split('\n')
    start_idx = 2869
    end_idx = min(start_idx + 200, len(lines))
    green_finance_content = '\n'.join(lines[start_idx:end_idx])
    
    print(f"提取内容长度: {len(green_finance_content)} 字符")
    
    # 字段提取
    result = extract_rule_fields(
        text=green_finance_content,
        issue_name="绿色金融",
        source_page=47,
        doc_id="2021-1212533363",
        stock_code="000001",
        report_year=2021,
    )
    
    # 定义输出字段顺序
    field_order = [
        'company_code', 'report_year', 'issue_name', 'anchor_type', 
        'source_page', 'evidence_snippet',
        'has_policy_ref', 'has_scope_statement', 'has_case_study',
        'risk_tone', 'has_kpi_value', 'has_yoy_change', 
        'has_method_note', 'has_assurance',
        'verifiability_score', 'spotlight_bias_flag'
    ]
    
    # 构建输出字典（只保留需要的字段）
    output_result = {
        'company_code': result['stock_code'],
        'report_year': result['report_year'],
        'issue_name': result['issue_name'],
        'anchor_type': "narrative",
        'source_page': result['source_page'],
        'evidence_snippet': result['evidence_snippet'],
        'has_policy_ref': result['has_policy_ref'],
        'has_scope_statement': result['has_scope_statement'],
        'has_case_study': result['has_case_study'],
        'risk_tone': result['risk_tone'],
        'has_kpi_value': result['has_kpi_value'],
        'has_yoy_change': result['has_yoy_change'],
        'has_method_note': result['has_method_note'],
        'has_assurance': result['has_assurance'],
        'verifiability_score': result['verifiability_score'],
        'spotlight_bias_flag': result['spotlight_bias_flag']
    }
    
    # 输出CSV
    output_file = "outputs/results/base_records.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=field_order)
        writer.writeheader()
        writer.writerow(output_result)
    
    print(f"\n提取完成！结果已保存到: {output_file}")
    
    # 打印结果
    print("\n" + "=" * 60)
    print("提取结果")
    print("=" * 60)
    print(f"company_code: {output_result['company_code']}")
    print(f"report_year: {output_result['report_year']}")
    print(f"issue_name: {output_result['issue_name']}")
    print(f"anchor_type: {output_result['anchor_type']}")
    print(f"source_page: {output_result['source_page']}")
    print(f"evidence_snippet: {output_result['evidence_snippet'][:50]}...")
    print(f"has_policy_ref: {output_result['has_policy_ref']}")
    print(f"has_scope_statement: {output_result['has_scope_statement']}")
    print(f"has_case_study: {output_result['has_case_study']}")
    print(f"risk_tone: {output_result['risk_tone']}")
    print(f"has_kpi_value: {output_result['has_kpi_value']}")
    print(f"has_yoy_change: {output_result['has_yoy_change']}")
    print(f"has_method_note: {output_result['has_method_note']}")
    print(f"has_assurance: {output_result['has_assurance']}")
    print(f"verifiability_score: {output_result['verifiability_score']}")
    print(f"spotlight_bias_flag: {output_result['spotlight_bias_flag']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
