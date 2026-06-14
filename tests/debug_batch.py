#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""调试 batch_extract_all 的问题"""

import sys
from pathlib import Path

project_root = r"e:\abcdefu\大学\26-3\机器学习与数据挖掘\B"
sys.path.insert(0, project_root)

from src.extract.field_extractor import extract_rule_fields, filter_html_tags

# 读取文件
stock_code = "000001"
doc_id = "2021-1212533363"
issue_name = "风险管理"
source_page = 10

md_path = Path(project_root) / 'project/project/data/parsed/markdown' / stock_code / f"{doc_id}.md"
print(f"读取文件: {md_path}")

with open(md_path, 'r', encoding='utf-8') as f:
    content = f.read()

clean = filter_html_tags(content)
print(f"过滤后长度: {len(clean)}")

# 模拟批量处理中的调用
print("开始提取字段（batch_extract_all 模式）...")
try:
    result = extract_rule_fields(
        text=clean[:10000],
        issue_name=issue_name,
        source_page=source_page,
        doc_id=doc_id,
        stock_code=stock_code,
        report_year="2021",
        matrix_importance=None,
        debug=False,  # 关闭调试输出
        use_llm=True,
    )
    print(f"提取成功！llm_success={result.get('llm_success')}")
    print(f"verifiability_score={result.get('verifiability_score')}")
except Exception as e:
    print(f"提取失败: {e}")
    import traceback
    traceback.print_exc()
