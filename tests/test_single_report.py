#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单份报告字段提取测试脚本

测试目标：
以一份真实报告为例，验证字段提取流程是否正确，输出结构化的 CSV 结果。

测试步骤：
1. 读取 section_locations.csv，选择一条记录（doc_id 为 2021-1212533363）
2. 根据 doc_id 从 metadata.csv 找到对应的 stock_code 和 report_year
3. 读取对应的 content.md
4. 根据 start_page 和 end_page 截取对应页码范围的文本
5. 对截取文本进行字段提取（规则字段 + LLM 字段）
6. 输出为 CSV 格式
"""

import os
import sys
import csv

# 添加项目路径到系统路径
sys.path.insert(0, '.')

from src.extract.field_extractor import extract_rule_fields
from src.extract.llm_extractor import extract_risk_tone


def load_section_locations(csv_path):
    """
    加载 section_locations.csv 文件
    :param csv_path: 文件路径
    :return: 记录列表
    """
    sections = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 处理页码字段，确保转换为整数
            try:
                start_page = int(row.get('start_page', '0').strip())
            except ValueError:
                start_page = 0
            
            try:
                end_page = int(row.get('end_page', '0').strip())
            except ValueError:
                end_page = 0
            
            sections.append({
                'doc_id': row.get('doc_id', ''),
                'issue_name': row.get('issue_name', ''),
                'section_title': row.get('section_title', ''),
                'start_page': start_page,
                'end_page': end_page,
                'confidence': int(row.get('confidence', '0')) if row.get('confidence', '').strip() else 0,
                'quality_issue': row.get('quality_issue', '')
            })
    return sections


def load_metadata(csv_path):
    """
    加载 metadata.csv 文件
    :param csv_path: 文件路径
    :return: doc_id 到 stock_code 和 report_year 的映射字典
    """
    metadata_map = {}
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 从公告标题中提取年份
            title = row.get('announcement_title', '')
            report_year = ''
            # 尝试从标题中提取年份（如 "2021年度ESG报告"）
            for year in ['2025', '2024', '2023', '2022', '2021']:
                if year in title:
                    report_year = year
                    break
            
            doc_id = row.get('pdf_url', '').split('announcementId=')[-1].split('&')[0] if 'announcementId=' in row.get('pdf_url', '') else ''
            if doc_id:
                metadata_map[doc_id] = {
                    'stock_code': row.get('stock_code', ''),
                    'report_year': report_year,
                    'stock_name': row.get('stock_name', '')
                }
    return metadata_map


def extract_text_by_page(content, start_page, end_page):
    """
    根据页码范围截取文本
    :param content: 完整文本内容
    :param start_page: 起始页码
    :param end_page: 结束页码
    :return: 截取的文本片段
    """
    # 简单的页码分割逻辑：假设文本中包含页码标记
    # 实际实现可能需要根据具体的文本格式进行调整
    
    # 先尝试按页面标记分割
    pages = []
    current_page = ""
    lines = content.split('\n')
    
    for line in lines:
        # 检查是否有页码标记（如 "第X页" 或 "Page X"）
        if '第' in line and '页' in line:
            if current_page.strip():
                pages.append(current_page.strip())
            current_page = line + '\n'
        else:
            current_page += line + '\n'
    
    if current_page.strip():
        pages.append(current_page.strip())
    
    # 如果无法按页码分割，返回整个内容作为第一页
    if not pages:
        pages = [content.strip()]
    
    # 截取指定页码范围的内容
    if start_page <= 0:
        start_page = 1
    
    if end_page < start_page:
        end_page = start_page
    
    # 确保页码不超出范围
    start_idx = min(start_page - 1, len(pages) - 1)
    end_idx = min(end_page - 1, len(pages) - 1)
    
    extracted_text = '\n\n'.join(pages[start_idx:end_idx + 1])
    
    return extracted_text


def main():
    """
    主测试函数
    """
    print("=" * 60)
    print("单份报告字段提取测试")
    print("=" * 60)
    
    # 配置路径
    section_locations_path = 'project/project/outputs/reports/section_locations.csv'
    metadata_path = 'data/metadata.csv'
    parsed_dir = 'project/project/data/parsed/markdown'
    output_path = 'outputs/results/test_base_records.csv'
    
    # 1. 读取 section_locations.csv
    print("\n[步骤1] 读取 section_locations.csv...")
    try:
        sections = load_section_locations(section_locations_path)
        print(f"  成功加载 {len(sections)} 条记录")
        
        # 查找 doc_id 为 2021-1212533363 的记录
        target_doc_id = '2021-1212533363'
        target_sections = [s for s in sections if s['doc_id'] == target_doc_id]
        
        if not target_sections:
            print(f"  未找到 doc_id 为 {target_doc_id} 的记录")
            return
        
        print(f"  找到 {len(target_sections)} 条相关记录")
        
        # 选择第一条记录进行测试
        test_section = target_sections[0]
        print(f"  测试记录: issue_name={test_section['issue_name']}, start_page={test_section['start_page']}, end_page={test_section['end_page']}")
        
    except Exception as e:
        print(f"  读取 section_locations.csv 失败: {e}")
        return
    
    # 2. 从 metadata.csv 获取 stock_code 和 report_year
    print("\n[步骤2] 读取 metadata.csv...")
    try:
        metadata_map = load_metadata(metadata_path)
        print(f"  成功加载 {len(metadata_map)} 条元数据记录")
        
        if target_doc_id in metadata_map:
            stock_code = metadata_map[target_doc_id]['stock_code']
            report_year = metadata_map[target_doc_id]['report_year']
            stock_name = metadata_map[target_doc_id]['stock_name']
            print(f"  找到匹配记录: stock_code={stock_code}, stock_name={stock_name}, report_year={report_year}")
        else:
            print(f"  未找到 doc_id={target_doc_id} 的元数据，使用默认值")
            stock_code = '000001'
            report_year = '2021'
        
    except Exception as e:
        print(f"  读取 metadata.csv 失败: {e}")
        stock_code = '000001'
        report_year = '2021'
    
    # 3. 读取对应的 content.md
    print("\n[步骤3] 读取 markdown 文件...")
    md_path = os.path.join(parsed_dir, stock_code, f"{target_doc_id}.md")
    print(f"  文件路径: {md_path}")
    
    if not os.path.exists(md_path):
        print(f"  文件不存在: {md_path}")
        return
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"  文件内容长度: {len(content)} 字符")
    except Exception as e:
        print(f"  读取文件失败: {e}")
        return
    
    # 4. 根据 start_page 和 end_page 截取文本
    print("\n[步骤4] 截取页码范围的文本...")
    start_page = test_section['start_page']
    end_page = test_section['end_page']
    print(f"  页码范围: {start_page} - {end_page}")
    
    extracted_text = extract_text_by_page(content, start_page, end_page)
    print(f"  截取文本长度: {len(extracted_text)} 字符")
    
    # 打印截取的文本片段（用于人工检查）
    print("\n[截取的文本片段]")
    print("-" * 60)
    preview_length = min(1000, len(extracted_text))
    print(extracted_text[:preview_length])
    if len(extracted_text) > preview_length:
        print("...（文本被截断）")
    print("-" * 60)
    
    # 5. 字段提取
    print("\n[步骤5] 字段提取...")
    
    # 规则字段提取（启用调试模式）
    print("\n  [规则字段提取]")
    try:
        rule_result = extract_rule_fields(
            text=extracted_text,
            issue_name=test_section['issue_name'],
            source_page=start_page,  # 使用 section_locations 中的 start_page
            doc_id=target_doc_id,
            stock_code=stock_code,
            report_year=report_year,
            matrix_importance=None,
            debug=True,  # 启用调试输出
        )
        print(f"\n    字段提取结果:")
        print(f"    has_policy_ref: {rule_result['has_policy_ref']}")
        print(f"    has_scope_statement: {rule_result['has_scope_statement']}")
        print(f"    has_case_study: {rule_result['has_case_study']}")
        print(f"    has_kpi_value: {rule_result['has_kpi_value']}")
        print(f"    has_yoy_change: {rule_result['has_yoy_change']}")
        print(f"    has_method_note: {rule_result['has_method_note']}")
        print(f"    has_assurance: {rule_result['has_assurance']}")
        print(f"    verifiability_score: {rule_result['verifiability_score']}")
        print(f"    spotlight_bias_flag: {rule_result['spotlight_bias_flag']}")
        print(f"    evidence_snippet: {rule_result['evidence_snippet'][:150]}..." if rule_result['evidence_snippet'] else "    evidence_snippet: None")
    except Exception as e:
        print(f"    规则字段提取失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # LLM 字段提取（风险语调）
    print("\n  [LLM字段提取 - 风险语调]")
    try:
        risk_tone = extract_risk_tone(extracted_text[:2000])
        print(f"    risk_tone: {risk_tone}")
    except Exception as e:
        print(f"    LLM调用失败，使用规则保底")
        risk_tone = "展示性"  # 规则保底
    
    # 6. 输出 CSV
    print("\n[步骤6] 输出 CSV 文件...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 定义输出字段顺序
    output_fieldnames = [
        'company_code', 'report_year', 'issue_name', 'anchor_type', 
        'source_page', 'evidence_snippet',
        'has_policy_ref', 'has_scope_statement', 'has_case_study',
        'risk_tone', 'has_kpi_value', 'has_yoy_change', 
        'has_method_note', 'has_assurance',
        'verifiability_score', 'spotlight_bias_flag'
    ]
    
    # 构建输出记录
    output_record = {
        'company_code': stock_code,
        'report_year': report_year,
        'issue_name': test_section['issue_name'],
        'anchor_type': 'narrative',
        'source_page': start_page,
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
    
    # 写入 CSV
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerow(output_record)
    
    print(f"  已保存到: {output_path}")
    
    # 打印完整字段提取结果
    print("\n[完整字段提取结果]")
    print("-" * 60)
    for field in output_fieldnames:
        value = output_record[field]
        print(f"{field}: {value}")
    print("-" * 60)
    
    print("\n测试完成！")


if __name__ == "__main__":
    main()