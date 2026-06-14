#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速全量提取测试脚本（限制处理数量用于测试）
"""

import sys
import time
from pathlib import Path

# 获取项目根目录
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

from src.extract.batch_extract_all import load_section_locations, load_processed_ids, save_processed_ids
from src.extract.batch_extract_all import OUTPUT_DIR, LOGS_DIR, OUTPUT_CSV, ERROR_CSV, LOG_FILE
from src.extract.batch_extract_all import process_single_record, save_results, save_errors, save_log
from src.extract.batch_extract_all import generate_data_quality_report, save_sample_check

# 测试限制数量
TEST_LIMIT = 50  # 改为 50 条用于快速测试

def main():
    print("=" * 60)
    print(f"快速全量提取测试（限制 {TEST_LIMIT} 条）")
    print("=" * 60)

    start_time = time.time()

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # 加载断点续传记录
    processed_ids = load_processed_ids()
    print(f"\n已处理记录数: {len(processed_ids)}")

    # 加载 section_locations
    sections = load_section_locations()
    print(f"总记录数: {len(sections)}")

    # 过滤未处理的记录
    pending_sections = [s for s in sections if s.get('doc_id', '') not in processed_ids]
    print(f"待处理记录数: {min(TEST_LIMIT, len(pending_sections))}")

    # 只处理前 TEST_LIMIT 条
    pending_sections = pending_sections[:TEST_LIMIT]

    # 处理每条记录
    results = []
    for i, section in enumerate(pending_sections, 1):
        doc_id = section.get('doc_id', '')
        issue_name = section.get('issue_name', '')

        print(f"  [{i}/{len(pending_sections)}] {doc_id} | {issue_name[:20]}...")

        record_start = time.time()
        result = process_single_record(section, processed_ids)
        record_time = time.time() - record_start

        if result:
            results.append(result)
            processed_ids.add(doc_id)
        else:
            print(f"    [WARN] 处理失败")

        # 每 10 条打印进度
        if i % 10 == 0:
            elapsed = time.time() - start_time
            print(f"  进度: {i}/{len(pending_sections)} | 已耗时: {elapsed:.0f}秒")

    # 保存结果
    print("\n保存结果...")
    save_results(results)

    total_time = time.time() - start_time
    print(f"\n测试完成！处理 {len(results)} 条记录，耗时 {total_time:.1f} 秒")

if __name__ == "__main__":
    main()
