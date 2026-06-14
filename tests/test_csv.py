"""
最简单的测试脚本 - 验证CSV输出
"""
import os
import csv

# 测试数据
results = [
    {
        'company_code': '000001',
        'report_year': 2021,
        'issue_name': '绿色信贷/绿色金融',
        'anchor_type': 'narrative',
        'source_page': 47,
        'evidence_snippet': '本行制定《绿色融资业务认证标识管理办法》...',
        'has_policy_ref': True,
        'has_scope_statement': False,
        'has_case_study': True,
        'risk_tone': '展示性',
        'has_kpi_value': True,
        'has_yoy_change': True,
        'has_method_note': False,
        'has_assurance': False,
        'verifiability_score': 5,
        'spotlight_bias_flag': False
    }
]

# 输出CSV
output_file = "outputs/results/base_records.csv"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

field_order = [
    'company_code', 'report_year', 'issue_name', 'anchor_type', 
    'source_page', 'evidence_snippet',
    'has_policy_ref', 'has_scope_statement', 'has_case_study',
    'risk_tone', 'has_kpi_value', 'has_yoy_change', 
    'has_method_note', 'has_assurance',
    'verifiability_score', 'spotlight_bias_flag'
]

with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=field_order)
    writer.writeheader()
    writer.writerows(results)

print(f"CSV文件已生成: {output_file}")
print(f"写入了 {len(results)} 条记录")
