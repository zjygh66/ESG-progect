"""
详细调试脚本
"""
import os
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 读取报告内容
report_path = "project/project/data/parsed/markdown/000001/2021-1212533363.md"
with open(report_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"报告总长度: {len(content)} 字符")

# 测试提取绿色金融章节
issue_name = "绿色金融"
keywords = ['绿色金融', '绿色信贷', '碳中和', '双碳']

lines = content.split('\n')
print(f"\n总共有 {len(lines)} 行")

# 查找包含关键词的行
matched_lines = []
for i, line in enumerate(lines):
    if any(kw in line for kw in keywords):
        print(f"第 {i+1} 行: {line.strip()[:100]}")
        matched_lines.append(i)

print(f"\n找到 {len(matched_lines)} 行包含关键词")

# 查看绿色金融章节内容
if matched_lines:
    start_line = matched_lines[0]
    end_line = min(start_line + 50, len(lines))
    print(f"\n提取第 {start_line+1} 到 {end_line} 行:")
    for i in range(start_line, end_line):
        print(f"{i+1:4d}: {lines[i].strip()[:80]}")
