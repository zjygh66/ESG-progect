#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单份报告字段提取测试脚本（修复版 - source_page 问题）

发现：markdown 文件中只有一个页码标记 "## 第 1 页"，没有分页
策略：使用 section_locations 中的 start_page（章节序号）作为 source_page
"""
import os
import sys
import csv
import re

sys.path.insert(0, '.')

from src.extract.field_extractor import extract_rule_fields
from src.extract.llm_extractor import extract_risk_tone


def load_section_locations(csv_path):
    """加载 section_locations.csv 文件"""
    sections = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                start_page = int(row.get('start_page', '0').strip())
            except ValueError:
                start_page = 0
            try:
                end_page = int(row.get('end_page', '0').strip())
            except ValueError:
                end_page = 0
            
            section_title = row.get('section_title', '')
            
            # 从 section_title 中提取页码（如果有）
            actual_page = _extract_page_from_title(section_title)
            
            sections.append({
                'doc_id': row.get('doc_id', ''),
                'issue_name': row.get('issue_name', ''),
                'section_title': section_title,
                'start_page': start_page,  # 章节序号
                'end_page': end_page,      # 章节序号
                'actual_page': actual_page, # 如果有的话
            })
    return sections


def _extract_page_from_title(section_title):
    """从 section_title 中提取页码"""
    if not section_title:
        return None
    
    # 尝试匹配末尾的数字（如 "... 16"）
    match = re.search(r'\.\s+(\d+)\s*$', section_title.strip())
    if match:
        return int(match.group(1))
    
    # 尝试匹配 "第 X 页" 格式
    match = re.search(r'第\s*(\d+)\s*页', section_title)
    if match:
        return int(match.group(1))
    
    return None


def main():
    """主测试函数"""
    print("=" * 60)
    print("单份报告字段提取测试（修复版）")
    print("=" * 60)
    
    # 配置路径
    section_locations_path = 'project/project/outputs/reports/section_locations.csv'
    parsed_dir = 'project/project/data/parsed/markdown'
    output_path = 'outputs/results/test_base_records.csv'
    log_path = 'outputs/results/test_log.txt'
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write("=" * 60 + "\n")
        log.write("单份报告字段提取测试（修复版）\n")
        log.write("=" * 60 + "\n\n")
        
        # 1. 读取 section_locations.csv
        log.write("[步骤1] 读取 section_locations.csv...\n")
        sections = load_section_locations(section_locations_path)
        log.write(f"  成功加载 {len(sections)} 条记录\n")
        
        # 选择一条测试记录（如绿色金融，因为用户提到了 start_page=6）
        target_doc_id = '2021-1212533363'
        
        # 选择消费者权益保护记录（有实际页码9）
        target_sections = [s for s in sections if s['doc_id'] == target_doc_id and s['issue_name'] == '消费者权益保护']
        
        if not target_sections:
            # 如果找不到，尝试第一个记录
            target_sections = [s for s in sections if s['doc_id'] == target_doc_id][:1]
        
        if not target_sections:
            log.write(f"  未找到 doc_id 为 {target_doc_id} 的记录\n")
            return
        
        test_section = target_sections[0]
        log.write(f"\n  测试记录详情:\n")
        log.write(f"    doc_id: {test_section['doc_id']}\n")
        log.write(f"    issue_name: {test_section['issue_name']}\n")
        log.write(f"    section_title: {test_section['section_title']}\n")
        log.write(f"    start_page (章节序号): {test_section['start_page']}\n")
        log.write(f"    end_page (章节序号): {test_section['end_page']}\n")
        log.write(f"    actual_page (目录页码): {test_section['actual_page']}\n")
        
        stock_code = '000001'
        report_year = '2021'
        
        # 使用 section_title 中提取的实际页码作为 source_page
        # 如果没有，则使用 start_page（章节序号）
        source_page = test_section['actual_page'] if test_section['actual_page'] else test_section['start_page']
        log.write(f"    source_page (用于输出): {source_page}\n")
        
        # 2. 读取 markdown 文件
        log.write(f"\n[步骤2] 读取 markdown 文件...\n")
        md_path = os.path.join(parsed_dir, stock_code, f"{target_doc_id}.md")
        log.write(f"  文件路径: {md_path}\n")
        
        if not os.path.exists(md_path):
            log.write(f"  文件不存在\n")
            return
        
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        log.write(f"  文件内容长度: {len(content)} 字符\n")
        
        # 注意：markdown 文件没有分页标记，整个报告是一个连续的文本
        # 因此截取前10000字符用于测试（和原来保持一致）
        log.write(f"\n[步骤3] 截取文本（前10000字符）\n")
        log.write(f"  注意：markdown 文件只有一个页码标记 '## 第 1 页'，没有分页\n")
        
        extracted_text = content[:10000]
        
        # 打印截取的文本片段（用于人工检查）
        log.write(f"\n[截取的文本片段]\n")
        log.write("-" * 60 + "\n")
        preview_length = min(1000, len(extracted_text))
        log.write(extracted_text[:preview_length] + "\n")
        if len(extracted_text) > preview_length:
            log.write("...（文本被截断）\n")
        log.write("-" * 60 + "\n")
        
        # 4. 字段提取
        log.write(f"\n[步骤4] 字段提取...\n")
        rule_result = extract_rule_fields(
            text=extracted_text,
            issue_name=test_section['issue_name'],
            source_page=source_page,  # 使用 section_title 中提取的页码
            doc_id=target_doc_id,
            stock_code=stock_code,
            report_year=report_year,
            matrix_importance=None,
            debug=True,
        )
        
        log.write(f"\n  [字段提取结果汇总]\n")
        log.write(f"    source_page (章节序号): {test_section['start_page']}\n")
        log.write(f"    source_page (目录页码): {test_section['actual_page']}\n")
        log.write(f"    source_page (in result): {rule_result['source_page']}\n")
        log.write(f"    has_policy_ref: {rule_result['has_policy_ref']}\n")
        log.write(f"    has_scope_statement: {rule_result['has_scope_statement']}\n")
        log.write(f"    has_case_study: {rule_result['has_case_study']}\n")
        log.write(f"    has_kpi_value: {rule_result['has_kpi_value']}\n")
        log.write(f"    has_yoy_change: {rule_result['has_yoy_change']}\n")
        log.write(f"    has_method_note: {rule_result['has_method_note']}\n")
        log.write(f"    has_assurance: {rule_result['has_assurance']}\n")
        log.write(f"    verifiability_score: {rule_result['verifiability_score']}\n")
        log.write(f"    evidence_snippet (前200字): {rule_result['evidence_snippet'][:200]}...\n")
        
        # 5. LLM 字段提取
        log.write(f"\n  [LLM字段提取 - 风险语调]\n")
        try:
            risk_tone = extract_risk_tone(extracted_text[:2000])
            log.write(f"    risk_tone: {risk_tone}\n")
        except Exception as e:
            log.write(f"    LLM调用失败，使用规则保底\n")
            risk_tone = "展示性"
        
        # 6. 输出 CSV
        log.write(f"\n[步骤5] 输出 CSV 文件...\n")
        
        output_fieldnames = [
            'company_code', 'report_year', 'issue_name', 'anchor_type', 
            'source_page', 'evidence_snippet',
            'has_policy_ref', 'has_scope_statement', 'has_case_study',
            'risk_tone', 'has_kpi_value', 'has_yoy_change', 
            'has_method_note', 'has_assurance',
            'verifiability_score', 'spotlight_bias_flag'
        ]
        
        output_record = {
            'company_code': stock_code,
            'report_year': report_year,
            'issue_name': rule_result['issue_name'],
            'anchor_type': 'narrative',
            'source_page': rule_result['source_page'],
            'evidence_snippet': rule_result['evidence_snippet'],
            'has_policy_ref': rule_result['has_policy_ref'],
            'has_scope_statement': rule_result['has_scope_statement'],
            'has_case_study': rule_result['has_case_study'],
            'risk_tone': risk_tone,
            'has_kpi_value': rule_result['has_kpi_value'],
            'has_yoy_change': rule_result['has_yoy_change'],
            'has_method_note': rule_result['has_method_note'],
            'has_assurance': rule_result['has_assurance'],
            'verifiability_score': rule_result['verifiability_score'],
            'spotlight_bias_flag': rule_result['spotlight_bias_flag']
        }
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerow(output_record)
        
        log.write(f"  已保存到: {output_path}\n")
        log.write(f"\n测试完成！\n")
    
    print("测试完成，日志已保存到 outputs/results/test_log.txt")
    print("CSV 已保存到 outputs/results/test_base_records.csv")


if __name__ == "__main__":
    main()