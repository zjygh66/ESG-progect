"""
平安银行绿色金融报告字段提取脚本
输出格式符合用户要求
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
    
    print(f"报告内容长度: {len(content)} 字符")
    
    # 提取绿色金融章节（从第2860行左右开始的实际内容）
    lines = content.split('\n')
    
    # 找到绿色金融章节的起始位置
    start_idx = -1
    for i, line in enumerate(lines):
        if "9.1  绿色金融" in line and i > 2800:  # 跳过目录中的绿色金融
            start_idx = i
            break
    
    if start_idx == -1:
        print("错误：未找到绿色金融章节")
        return
    
    print(f"找到绿色金融章节，起始行: {start_idx + 1}")
    
    # 提取章节内容（取200行）
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
    
    # 添加 anchor_type 字段
    result['anchor_type'] = "narrative"
    
    # 重命名字段
    result['company_code'] = result.pop('stock_code')
    
    print("\n提取结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # 输出CSV
    output_file = "outputs/results/base_records.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 定义输出字段顺序（按照用户要求的顺序）
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
        writer.writerow(result)
    
    print(f"\n提取完成！结果已保存到: {output_file}")
    
    # 打印CSV内容预览
    print("\n" + "=" * 60)
    print("CSV输出内容")
    print("=" * 60)
    with open(output_file, 'r', encoding='utf-8-sig') as f:
        print(f.read())

if __name__ == "__main__":
    main()
