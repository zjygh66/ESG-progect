#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量测试脚本：测试 000001（平安银行）和 001227（宁波银行）的所有报告
"""
import os
import sys
import csv
import time
import re
from pathlib import Path
from collections import defaultdict

# 获取项目根目录（tests 的上一级）
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

print("[DEBUG] Script started", flush=True)
print(f"[DEBUG] project_root: {project_root}", flush=True)

from src.extract.field_extractor import extract_rule_fields
from src.extract.llm_extractor import extract_risk_tone

print("[DEBUG] Imports successful", flush=True)


# 配置路径
PROJECT_DIR = Path('project/project')
SECTION_LOCATIONS_PATH = PROJECT_DIR / 'outputs/reports/section_locations.csv'
METADATA_PATH = Path('data/metadata.csv')  # 暂不使用
MARKDOWN_DIR = PROJECT_DIR / 'data/parsed/markdown'
OUTPUT_DIR = Path('outputs/results')
OUTPUT_CSV = OUTPUT_DIR / 'batch_test_PinganNingbo.csv'
OUTPUT_STATS = OUTPUT_DIR / 'batch_test_stats.txt'

print(f"[DEBUG] PROJECT_DIR: {PROJECT_DIR}", flush=True)
print(f"[DEBUG] MARKDOWN_DIR: {MARKDOWN_DIR}", flush=True)
print(f"[DEBUG] MARKDOWN_DIR exists: {MARKDOWN_DIR.exists()}", flush=True)

# 目标银行
TARGET_STOCK_CODES = ['000001', '001227']


def load_doc_ids_from_folders():
    """从 markdown 文件夹结构获取 stock_code -> doc_ids 映射"""
    print("    [DEBUG] load_doc_ids_from_folders() called", flush=True)
    stock_to_docs = defaultdict(list)
    
    if not MARKDOWN_DIR.exists():
        print(f"    [DEBUG] MARKDOWN_DIR does not exist: {MARKDOWN_DIR}", flush=True)
        return stock_to_docs
    
    print(f"    [DEBUG] MARKDOWN_DIR: {MARKDOWN_DIR}", flush=True)
    print(f"    [DEBUG] Listing folders...", flush=True)
    folder_count = 0
    for folder in MARKDOWN_DIR.iterdir():
        folder_count += 1
        if folder_count <= 5:
            print(f"    [DEBUG] Found folder: {folder.name}", flush=True)
        if folder.is_dir() and folder.name in TARGET_STOCK_CODES:
            stock_code = folder.name
            print(f"    [DEBUG] Found target folder: {stock_code}", flush=True)
            for md_file in folder.glob('*.md'):
                doc_id = md_file.stem  # 文件名不含扩展名
                stock_to_docs[stock_code].append(doc_id)
    
    print(f"    [DEBUG] stock_to_docs: {dict(stock_to_docs)}", flush=True)
    return stock_to_docs


def load_section_locations(sections_path):
    """加载 section_locations.csv"""
    sections = []
    with open(sections_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sections.append({
                'doc_id': row.get('doc_id', '').strip(),
                'issue_name': row.get('issue_name', '').strip(),
                'section_title': row.get('section_title', '').strip(),
                'start_page': int(row.get('start_page', '0').strip()) if row.get('start_page', '').strip().isdigit() else 0,
                'end_page': int(row.get('end_page', '0').strip()) if row.get('end_page', '').strip().isdigit() else 0,
            })
    return sections


def extract_actual_page(section_title):
    """从 section_title 中提取页码"""
    if not section_title:
        return None
    # 尝试匹配末尾的数字（如 "... 16"）
    match = re.search(r'\.\s+(\d+)\s*$', section_title.strip())
    if match:
        return int(match.group(1))
    return None


def get_markdown_path(stock_code, doc_id):
    """获取 markdown 文件路径"""
    md_path = MARKDOWN_DIR / stock_code / f"{doc_id}.md"
    if md_path.exists():
        return md_path
    # 尝试其他可能的路径格式
    for folder in MARKDOWN_DIR.iterdir():
        if folder.is_dir() and folder.name == stock_code:
            for md_file in folder.glob(f"{doc_id}.*"):
                if md_file.suffix == '.md':
                    return md_file
    return None


def process_record(record, stock_to_docs, stats):
    """处理单条记录"""
    print(f"    [DEBUG] process_record() start: doc_id={record['doc_id']}", flush=True)
    doc_id = record['doc_id']
    
    # 从 stock_to_docs 查找 stock_code
    stock_code = None
    for sc, docs in stock_to_docs.items():
        if doc_id in docs:
            stock_code = sc
            break
    
    if not stock_code:
        stats['skipped_no_metadata'] += 1
        return None
    
    print(f"    [DEBUG] stock_code={stock_code}", flush=True)
    
    # 获取 markdown 文件路径
    print(f"    [DEBUG] Getting markdown path...", flush=True)
    md_path = get_markdown_path(stock_code, doc_id)
    print(f"    [DEBUG] md_path={md_path}", flush=True)
    if not md_path:
        stats['skipped_no_file'] += 1
        return None
    
    # 读取文件内容
    print(f"    [DEBUG] Reading file...", flush=True)
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"    [DEBUG] File read successfully, length={len(content)}", flush=True)
    except Exception as e:
        stats['skipped_read_error'] += 1
        return None
    
    # 截取前10000字符
    print(f"    [DEBUG] Truncating text...", flush=True)
    extracted_text = content[:10000]
    print(f"    [DEBUG] Text truncated to {len(extracted_text)} chars", flush=True)
    
    # source_page：使用 start_page（章节序号）
    source_page = record['start_page']
    
    # 字段提取
    print(f"    [DEBUG] Calling extract_rule_fields...", flush=True)
    start_time = time.time()
    try:
        rule_result = extract_rule_fields(
            text=extracted_text,
            issue_name=record['issue_name'],
            source_page=source_page,
            doc_id=doc_id,
            stock_code=stock_code,
            report_year=doc_id[:4],  # 从 doc_id 提取年份
            matrix_importance=None,
            debug=False,
            use_llm=False,  # 跳过 LLM 调用（使用规则保底）
        )
        print(f"    [DEBUG] extract_rule_fields successful", flush=True)
    except Exception as e:
        stats['field_extract_error'] += 1
        print(f"    [DEBUG] extract_rule_fields failed: {e}", flush=True)
        return None
    
    # 更新 LLM 统计
    if rule_result.get('llm_success', False):
        stats['llm_success'] += 1
    else:
        stats['llm_failed'] += 1
    
    elapsed = time.time() - start_time
    stats['total_time'] += elapsed
    print(f"    [DEBUG] process_record() done, elapsed={elapsed:.3f}s", flush=True)
    
    return {
        'company_code': stock_code,
        'report_year': doc_id[:4],
        'issue_name': rule_result['issue_name'],
        'anchor_type': 'narrative',
        'source_page': rule_result['source_page'],
        'evidence_snippet': rule_result['evidence_snippet'],
        'has_policy_ref': rule_result['has_policy_ref'],
        'has_scope_statement': rule_result['has_scope_statement'],
        'has_case_study': rule_result['has_case_study'],
        'risk_tone': rule_result['risk_tone'],
        'has_kpi_value': rule_result['has_kpi_value'],
        'has_yoy_change': rule_result['has_yoy_change'],
        'has_method_note': rule_result['has_method_note'],
        'has_assurance': rule_result['has_assurance'],
        'verifiability_score': rule_result['verifiability_score'],
        'spotlight_bias_flag': rule_result['spotlight_bias_flag'],
        'elapsed': elapsed,
    }


def main():
    print("[DEBUG] main() started", flush=True)
    print("=" * 60)
    print("批量测试：000001（平安银行）和 001227（宁波银行）")
    print("=" * 60)
    
    # 确保输出目录存在
    print(f"[DEBUG] Creating output directory: {OUTPUT_DIR}", flush=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[DEBUG] Output directory created", flush=True)
    
    # 初始化统计
    stats = {
        'total_records': 0,
        'processed_records': 0,
        'skipped_no_metadata': 0,
        'skipped_no_file': 0,
        'skipped_read_error': 0,
        'field_extract_error': 0,
        'llm_success': 0,
        'llm_failed': 0,
        'total_time': 0,
        'by_bank': defaultdict(int),
        'field_true_counts': defaultdict(int),
    }
    
    # 1. 从文件夹获取目标银行的 doc_ids
    print("\n[步骤1] 加载数据文件...", flush=True)
    print(f"  [DEBUG] Calling load_doc_ids_from_folders()...", flush=True)
    stock_to_docs = load_doc_ids_from_folders()
    print(f"  stock_to_docs: {dict(stock_to_docs)}", flush=True)
    target_doc_ids = set()
    for stock_code, doc_ids in stock_to_docs.items():
        print(f"  {stock_code}: {len(doc_ids)} 个报告")
        for doc_id in doc_ids:
            target_doc_ids.add(doc_id)
    print(f"  目标银行 doc_ids 总数: {len(target_doc_ids)}")
    
    # 2. 加载 section_locations.csv
    print(f"  [DEBUG] Loading section_locations...", flush=True)
    all_sections = load_section_locations(SECTION_LOCATIONS_PATH)
    print(f"  section_locations.csv: {len(all_sections)} 条记录", flush=True)
    
    # 3. 筛选目标银行的记录
    target_records = []
    for section in all_sections:
        doc_id = section['doc_id']
        if doc_id in target_doc_ids:
            # 从 stock_to_docs 反向查找 stock_code
            stock_code = None
            for sc, docs in stock_to_docs.items():
                if doc_id in docs:
                    stock_code = sc
                    break
            if stock_code:
                target_records.append(section)
                stats['by_bank'][stock_code] += 1
    
    stats['total_records'] = len(target_records)
    print(f"  目标银行记录数: {stats['total_records']} 条")
    for bank, count in stats['by_bank'].items():
        print(f"    {bank}: {count} 条")
    
    if not target_records:
        print("\n未找到目标银行的记录！")
        return
    
    # 4. 处理每条记录
    print(f"\n[步骤2] 开始处理 {stats['total_records']} 条记录...", flush=True)
    results = []
    
    for i, record in enumerate(target_records):
        if (i + 1) % 10 == 0:
            print(f"  已处理 {i + 1}/{stats['total_records']} 条...", flush=True)
        
        print(f"  [DEBUG] Processing record {i+1}/{stats['total_records']}: {record['doc_id']}", flush=True)
        result = process_record(record, stock_to_docs, stats)
        print(f"  [DEBUG] Processed: {result is not None}", flush=True)
        if result:
            results.append(result)
            stats['processed_records'] += 1
            
            # 统计字段True比例
            for field in ['has_policy_ref', 'has_scope_statement', 'has_case_study',
                          'has_kpi_value', 'has_yoy_change', 'has_method_note', 
                          'has_assurance', 'spotlight_bias_flag']:
                if result.get(field):
                    stats['field_true_counts'][field] += 1
    
    print(f"  处理完成！成功: {stats['processed_records']} 条")
    
    # 5. 输出 CSV
    print(f"\n[步骤3] 输出 CSV 文件...")
    output_fieldnames = [
        'company_code', 'report_year', 'issue_name', 'anchor_type', 
        'source_page', 'evidence_snippet',
        'has_policy_ref', 'has_scope_statement', 'has_case_study',
        'risk_tone', 'has_kpi_value', 'has_yoy_change', 
        'has_method_note', 'has_assurance',
        'verifiability_score', 'spotlight_bias_flag'
    ]
    
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        for r in results:
            # 移除 elapsed 字段（不输出到CSV）
            row = {k: v for k, v in r.items() if k != 'elapsed'}
            writer.writerow(row)
    
    print(f"  已保存到: {OUTPUT_CSV}")
    
    # 6. 输出统计信息
    print(f"\n[步骤4] 统计信息...")
    
    stats_text = []
    stats_text.append("=" * 60)
    stats_text.append("批量测试统计报告")
    stats_text.append("=" * 60)
    stats_text.append(f"\n测试范围: {', '.join(TARGET_STOCK_CODES)}")
    stats_text.append(f"\n总处理条数: {stats['processed_records']}")
    stats_text.append(f"\n各银行记录数:")
    for bank, count in stats['by_bank'].items():
        stats_text.append(f"  {bank}: {count} 条")
    
    stats_text.append(f"\nLLM 调用:")
    stats_text.append(f"  成功: {stats['llm_success']}")
    stats_text.append(f"  失败: {stats['llm_failed']}")
    if stats['llm_success'] + stats['llm_failed'] > 0:
        llm_rate = stats['llm_success'] / (stats['llm_success'] + stats['llm_failed']) * 100
        stats_text.append(f"  成功率: {llm_rate:.1f}%")
    
    avg_time = stats['total_time'] / stats['processed_records'] if stats['processed_records'] > 0 else 0
    stats_text.append(f"\n平均处理耗时: {avg_time:.3f} 秒/条")
    
    stats_text.append(f"\n跳过记录数:")
    stats_text.append(f"  无metadata映射: {stats['skipped_no_metadata']}")
    stats_text.append(f"  文件不存在: {stats['skipped_no_file']}")
    stats_text.append(f"  读取错误: {stats['skipped_read_error']}")
    stats_text.append(f"  字段提取错误: {stats['field_extract_error']}")
    
    stats_text.append(f"\n各字段为 True 的比例:")
    n = stats['processed_records']
    for field, count in stats['field_true_counts'].items():
        pct = count / n * 100 if n > 0 else 0
        stats_text.append(f"  {field}: {count}/{n} ({pct:.1f}%)")
    
    stats_text.append("\n" + "=" * 60)
    
    stats_output = '\n'.join(stats_text)
    print(stats_output)
    
    with open(OUTPUT_STATS, 'w', encoding='utf-8') as f:
        f.write(stats_output)
    print(f"\n统计报告已保存到: {OUTPUT_STATS}")
    
    print("\n批量测试完成！")


if __name__ == "__main__":
    main()