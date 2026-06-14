"""
平安银行报告字段提取脚本

从平安银行2021年可持续发展报告中提取ESG字段，输出结构化CSV数据。

作者：C 同学
日期：2026-06-14
"""

import os
import sys
import csv
import re

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.extract.field_extractor import extract_rule_fields, normalize_issue_name


def extract_pingan_report():
    """
    提取平安银行报告的ESG字段
    """
    print("步骤1: 读取报告文件...")
    # 报告路径
    report_path = "project/project/data/parsed/markdown/000001/2021-1212533363.md"
    
    # 检查文件是否存在
    if not os.path.exists(report_path):
        print(f"错误：文件不存在: {report_path}")
        return []
    
    # 读取报告内容
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"报告内容长度: {len(content)} 字符")
    
    # 定义需要提取的议题
    issues = [
        {"name": "绿色金融", "anchor_type": "narrative", "source_page": 47},
        {"name": "风险管理", "anchor_type": "narrative", "source_page": 16},
        {"name": "普惠金融", "anchor_type": "narrative", "source_page": 37},
        {"name": "消费者权益保护", "anchor_type": "narrative", "source_page": 31},
        {"name": "员工权益", "anchor_type": "narrative", "source_page": 56},
        {"name": "信息安全与隐私保护", "anchor_type": "narrative", "source_page": 29},
    ]
    
    # 存储结果
    results = []
    
    print("\n步骤2: 提取各议题字段...")
    for issue in issues:
        print(f"\n正在处理议题: {issue['name']}")
        
        # 提取相关章节内容
        issue_content = extract_section_content(content, issue['name'], issue['source_page'])
        
        if not issue_content:
            print(f"  警告：未找到 {issue['name']} 相关内容")
            continue
        
        print(f"  提取到内容长度: {len(issue_content)} 字符")
        
        # 字段提取
        print("  开始字段提取...")
        result = extract_rule_fields(
            text=issue_content,
            issue_name=issue['name'],
            source_page=issue['source_page'],
            doc_id="2021-1212533363",
            stock_code="000001",
            report_year=2021,
        )
        print(f"  字段提取完成")
        
        # 添加 anchor_type 字段
        result['anchor_type'] = issue['anchor_type']
        
        # 重命名字段以匹配用户要求的格式
        result['company_code'] = result.pop('stock_code')
        
        results.append(result)
        print(f"  结果: risk_tone={result['risk_tone']}, verifiability_score={result['verifiability_score']}")
    
    # 输出CSV
    print("\n步骤3: 输出CSV文件...")
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
    
    return results


def extract_section_content(content: str, issue_name: str, page: int) -> str:
    """
    从报告内容中提取指定议题的相关内容
    
    参数:
        content: 报告全文
        issue_name: 议题名称
        page: 起始页码
    
    返回:
        str: 提取的文本内容
    """
    # 定义议题关键词映射
    keywords = {
        '绿色金融': ['绿色金融', '绿色信贷', '碳中和', '双碳'],
        '风险管理': ['风险管理', '风险治理', '全面风险'],
        '普惠金融': ['普惠金融', '小微企业', '小微金融'],
        '消费者权益保护': ['消费者权益', '客户权益', '消保'],
        '员工权益': ['员工权益', '员工发展', '员工关怀'],
        '信息安全与隐私保护': ['信息安全', '数据安全', '隐私保护'],
    }
    
    issue_keywords = keywords.get(issue_name, [issue_name])
    
    # 首先尝试按议题名称搜索（更可靠）
    lines = content.split('\n')
    matched_lines = []
    found_keyword = False
    line_count = 0
    max_lines = 150
    
    for line in lines:
        # 检查是否包含议题关键词
        if any(kw in line for kw in issue_keywords):
            found_keyword = True
            line_count = 0
        
        if found_keyword:
            matched_lines.append(line)
            line_count += 1
            if line_count >= max_lines:
                break
    
    if matched_lines:
        print(f"  通过关键词匹配提取到 {len(matched_lines)} 行内容")
        return '\n'.join(matched_lines)[:3000]
    
    # 如果按关键词找不到，尝试查找章节标题
    chapter_pattern = rf"(##+\s*{issue_name}|##+\s*[0-9. ]+{issue_name})"
    match = re.search(chapter_pattern, content)
    if match:
        # 找到章节标题后，提取后续内容
        start_pos = match.end()
        # 查找下一个章节标题作为结束
        next_chapter = re.search(r'##+\s', content[start_pos:])
        if next_chapter:
            end_pos = start_pos + next_chapter.start()
        else:
            end_pos = start_pos + 3000
        
        section_text = content[start_pos:end_pos]
        print(f"  通过章节标题提取到 {len(section_text)} 字符")
        return section_text[:3000]
    
    # 如果都找不到，返回报告前3000字符作为兜底
    print(f"  未找到相关内容，使用报告开头")
    return content[:3000]


if __name__ == "__main__":
    print("=" * 60)
    print("平安银行ESG报告字段提取")
    print("=" * 60)
    
    results = extract_pingan_report()
    
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
