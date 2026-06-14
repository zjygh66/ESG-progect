"""
平安银行报告字段提取脚本 - 修正版
"""
import os
import sys
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.extract.field_extractor import extract_rule_fields

def extract_section(content: str, keyword: str, lines_after=150):
    """提取包含关键词的章节内容"""
    lines = content.split('\n')
    start_idx = -1
    
    # 查找实际章节内容（不是目录）
    for i, line in enumerate(lines):
        # 查找类似 "9.1 绿色金融" 这样的章节标题，但排除目录行（目录行后面有很多点）
        if keyword in line and line.count('.') <= 3 and len(line.strip()) < 50:
            start_idx = i
            break
    
    if start_idx == -1:
        # 如果找不到，用简单的关键词匹配
        for i, line in enumerate(lines):
            if keyword in line:
                start_idx = i
                break
    
    if start_idx == -1:
        return ""
    
    # 提取后续内容
    end_idx = min(start_idx + lines_after, len(lines))
    return '\n'.join(lines[start_idx:end_idx])[:3000]

def main():
    print("=" * 60)
    print("平安银行ESG报告字段提取")
    print("=" * 60)
    
    # 报告路径
    report_path = "project/project/data/parsed/markdown/000001/2021-1212533363.md"
    
    # 读取报告内容
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"报告内容长度: {len(content)} 字符")
    
    # 定义需要提取的议题
    issues = [
        {"name": "绿色金融", "anchor_type": "narrative", "source_page": 47, "keyword": "9.1 绿色金融"},
        {"name": "风险管理", "anchor_type": "narrative", "source_page": 16, "keyword": "风险管理"},
        {"name": "普惠金融", "anchor_type": "narrative", "source_page": 37, "keyword": "普惠金融"},
        {"name": "消费者权益保护", "anchor_type": "narrative", "source_page": 31, "keyword": "消费者权益"},
        {"name": "员工权益", "anchor_type": "narrative", "source_page": 56, "keyword": "员工权益"},
        {"name": "信息安全与隐私保护", "anchor_type": "narrative", "source_page": 29, "keyword": "信息安全"},
    ]
    
    # 存储结果
    results = []
    
    for issue in issues:
        print(f"\n正在处理议题: {issue['name']}")
        
        # 提取相关章节内容
        issue_content = extract_section(content, issue['keyword'])
        
        if not issue_content:
            print(f"  警告：未找到 {issue['name']} 相关内容")
            continue
        
        print(f"  提取到内容长度: {len(issue_content)} 字符")
        print(f"  内容预览: {issue_content[:100]}...")
        
        # 字段提取
        result = extract_rule_fields(
            text=issue_content,
            issue_name=issue['name'],
            source_page=issue['source_page'],
            doc_id="2021-1212533363",
            stock_code="000001",
            report_year=2021,
        )
        
        # 添加 anchor_type 字段
        result['anchor_type'] = issue['anchor_type']
        
        # 重命名字段以匹配用户要求的格式
        result['company_code'] = result.pop('stock_code')
        
        results.append(result)
        print(f"  完成: risk_tone={result['risk_tone']}, verifiability_score={result['verifiability_score']}")
    
    # 输出CSV
    output_file = "outputs/results/base_records.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 定义输出字段顺序
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
    
    print(f"\n提取完成！结果已保存到: {output_file}")
    print(f"共提取 {len(results)} 条记录")
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("提取结果摘要")
    print("=" * 60)
    print(f"{'议题':<20} {'风险语调':<12} {'可核查性评分':<8} {'偏差标志'}")
    print("-" * 60)
    for r in results:
        bias = "★" if r['spotlight_bias_flag'] else " "
        print(f"{r['issue_name']:<20} {r['risk_tone']:<12} {r['verifiability_score']:<8} {bias}")
    print("=" * 60)

if __name__ == "__main__":
    main()
