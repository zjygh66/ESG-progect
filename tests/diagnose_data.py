#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""数据诊断脚本"""

import csv
from pathlib import Path

# 检查 section_locations.csv
section_path = Path('project/project/outputs/reports/section_locations.csv')
if section_path.exists():
    with open(section_path, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    print(f"section_locations.csv 总记录数: {len(rows)}")
    
    # 检查唯一 doc_id
    doc_ids = set(r.get('doc_id', '') for r in rows)
    print(f"唯一 doc_id 数: {len(doc_ids)}")
    
    # 检查唯一银行
    stock_codes = set(r.get('stock_code', '') for r in rows if r.get('stock_code', ''))
    print(f"有 stock_code 的记录数: {len(stock_codes)}")
    print(f"stock_code 样例: {list(stock_codes)[:10]}")
    
    # 检查议题分布
    issues = {}
    for r in rows:
        issue = r.get('issue_name', '')
        issues[issue] = issues.get(issue, 0) + 1
    print("\n议题分布:")
    for issue, count in sorted(issues.items(), key=lambda x: -x[1]):
        print(f"  {issue}: {count}")
else:
    print("section_locations.csv 不存在")

# 检查 markdown 目录
md_dir = Path('project/project/data/parsed/markdown')
if md_dir.exists():
    banks = [d.name for d in md_dir.iterdir() if d.is_dir()]
    print(f"\nmarkdown 目录下的银行数: {len(banks)}")
    print(f"银行列表: {banks[:20]}")
    
    # 统计每个银行的文件数
    for bank in banks[:5]:
        files = list((md_dir / bank).glob('*.md'))
        print(f"  {bank}: {len(files)} 个文件")
else:
    print("\nmarkdown 目录不存在")
