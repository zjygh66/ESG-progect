#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速测试 LLM 调用"""

import sys
from pathlib import Path

project_root = r"e:\abcdefu\大学\26-3\机器学习与数据挖掘\B"
sys.path.insert(0, project_root)

from src.extract.field_extractor import extract_rule_fields, filter_html_tags

# 测试一条记录
stock_code = "000001"
doc_id = "2021-1212533363"
issue_name = "风险管理"
source_page = 10

# 读取文件
md_path = Path(project_root) / 'project/project/data/parsed/markdown' / stock_code / f"{doc_id}.md"
print(f"读取文件: {md_path}")

if md_path.exists():
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"文件长度: {len(content)}")
    
    # 过滤 HTML
    clean = filter_html_tags(content)
    print(f"过滤后长度: {len(clean)}")
    
    # 提取字段
    print("开始提取字段...")
    try:
        result = extract_rule_fields(
            text=clean[:10000],
            issue_name=issue_name,
            source_page=source_page,
            doc_id=doc_id,
            stock_code=stock_code,
            report_year="2021",
            matrix_importance=None,
            debug=True,
            use_llm=True,
        )
        print(f"\n提取结果:")
        for k, v in result.items():
            if k != 'evidence_snippet':
                print(f"  {k}: {v}")
            else:
                print(f"  evidence_snippet: {str(v)[:100]}...")
    except Exception as e:
        print(f"提取失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"文件不存在: {md_path}")
