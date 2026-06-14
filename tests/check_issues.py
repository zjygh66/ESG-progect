#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查议题分布"""

import csv
from collections import Counter

# 读取 section_locations.csv
with open('md222/output/section_locations.csv', 'r', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

issues = [r.get('issue_name', '') for r in rows]
c = Counter(issues)

print('议题分布:')
for k, v in sorted(c.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')

print(f'\n总记录数: {len(rows)}')
print(f'唯一议题数: {len(c)}')