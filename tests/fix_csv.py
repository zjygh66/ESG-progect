#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复 base_records.csv 中的 company_code 和 company_name"""

import csv
from pathlib import Path
from collections import defaultdict

project_root = Path(r"e:\abcdefu\大学\26-3\机器学习与数据挖掘\B")
MARKDOWN_DIR = project_root / 'project/project/data/parsed/markdown'
INPUT_CSV = project_root / 'outputs/results/base_records_20260615_012033.csv'
OUTPUT_CSV = project_root / 'outputs/results/base_records_fixed.csv'
BANK_TREND_CSV = project_root / 'outputs/results/bank_trend.csv'
YEAR_COMPARISON_CSV = project_root / 'outputs/results/year_comparison.csv'
QUALITY_REPORT = project_root / 'outputs/results/data_quality_report.md'

# 银行代码映射表
BANK_NAMES = {
    "000001": "平安银行",
    "001227": "宁波银行",
    "002142": "宁波银行(宁银消金)",
    "002807": "江阴银行",
    "002839": "张家港银行",
    "002936": "郑州银行",
    "002948": "青岛银行",
    "002958": "重庆银行",
    "002966": "南京银行",
    "600000": "浦发银行",
    "600015": "华夏银行",
    "600016": "民生银行",
    "600036": "招商银行",
    "600908": "无锡银行",
    "600919": "江苏银行",
    "600926": "杭州银行",
    "600928": "西安银行",
    "601009": "南京银行",
    "601077": "重庆农村商业银行",
    "601128": "常熟银行",
    "601166": "兴业银行",
    "601169": "北京银行",
    "601187": "厦门银行",
    "601229": "上海银行",
    "601288": "农业银行",
    "601328": "交通银行",
    "601398": "工商银行",
    "601528": "瑞丰银行",
    "601577": "长沙银行",
    "601658": "邮储银行",
    "601665": "齐鲁银行",
    "601818": "光大银行",
    "601825": "农业银行",
    "601838": "成都银行",
    "601860": "长沙银行",
    "601916": "浙商银行",
    "601939": "建设银行",
    "601963": "重庆银行",
    "601988": "中国银行",
    "601997": "贵阳银行",
    "601998": "中信银行",
    "603323": "苏农银行",
}

def get_company_name(stock_code: str) -> str:
    return BANK_NAMES.get(stock_code, stock_code)

def build_doc_mapping():
    """扫描 markdown 目录，建立 doc_id -> stock_code 映射"""
    doc_to_stock = {}
    
    if not MARKDOWN_DIR.exists():
        print(f"  Markdown 目录不存在: {MARKDOWN_DIR}")
        return doc_to_stock
    
    for stock_folder in MARKDOWN_DIR.iterdir():
        if stock_folder.is_dir():
            stock_code = stock_folder.name
            for md_file in stock_folder.glob("*.md"):
                doc_id = md_file.stem
                doc_to_stock[doc_id] = stock_code
    
    print(f"  建立 doc_id -> stock_code 映射: {len(doc_to_stock)} 个文档")
    return doc_to_stock

def fix_csv():
    """修复 CSV 文件"""
    # 建立 doc_id -> stock_code 映射
    doc_to_stock = build_doc_mapping()
    
    # 读取现有 CSV
    if not INPUT_CSV.exists():
        print(f"  CSV 文件不存在: {INPUT_CSV}")
        return
    
    rows = []
    with open(INPUT_CSV, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            doc_id = row.get('doc_id', '')
            # 从映射中获取 stock_code
            stock_code = doc_to_stock.get(doc_id, '')
            if stock_code:
                row['company_code'] = stock_code
                row['company_name'] = get_company_name(stock_code)
            rows.append(row)
    
    print(f"  读取 {len(rows)} 条记录")
    
    # 添加缺失的列
    if 'company_code' not in fieldnames:
        fieldnames = ['company_code', 'company_name'] + list(fieldnames)
    
    # 写回 CSV
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"  已修复并保存: {OUTPUT_CSV}")
    
    # 统计
    codes = set(r.get('company_code', '') for r in rows if r.get('company_code'))
    print(f"  唯一银行数: {len(codes)}")
    
    return rows

def generate_bank_trend(rows):
    """生成银行趋势表"""
    # 按 (company_code, issue_name, report_year) 聚合
    aggregated = defaultdict(lambda: {'scores': [], 'count': 0})
    
    for r in rows:
        key = (r.get('company_code', ''), r.get('issue_name', ''), r.get('report_year', ''))
        score = int(r.get('verifiability_score', 0) or 0)
        aggregated[key]['scores'].append(score)
        aggregated[key]['count'] += 1
    
    # 构建输出数据
    output_data = []
    for (company_code, issue_name, year), data in sorted(aggregated.items()):
        if not company_code:
            continue
        avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
        output_data.append({
            'company_code': company_code,
            'company_name': get_company_name(company_code),
            'issue_name': issue_name,
            'report_year': year,
            'avg_verifiability_score': round(avg_score, 2),
            'record_count': data['count'],
        })
    
    # 保存
    fieldnames = ['company_code', 'company_name', 'issue_name', 'report_year', 'avg_verifiability_score', 'record_count']
    with open(BANK_TREND_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_data)
    
    print(f"  银行趋势已保存: {BANK_TREND_CSV} ({len(output_data)} 条)")

def generate_year_comparison(rows):
    """生成年度对比表"""
    # 按 (report_year, company_code, issue_name) 聚合
    aggregated = defaultdict(lambda: {'scores': [], 'count': 0})
    
    for r in rows:
        key = (r.get('report_year', ''), r.get('company_code', ''), r.get('issue_name', ''))
        score = int(r.get('verifiability_score', 0) or 0)
        aggregated[key]['scores'].append(score)
        aggregated[key]['count'] += 1
    
    # 构建输出数据
    output_data = []
    for (year, company_code, issue_name), data in sorted(aggregated.items()):
        if not company_code:
            continue
        avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
        output_data.append({
            'report_year': year,
            'company_code': company_code,
            'company_name': get_company_name(company_code),
            'issue_name': issue_name,
            'avg_verifiability_score': round(avg_score, 2),
            'record_count': data['count'],
        })
    
    # 保存
    fieldnames = ['report_year', 'company_code', 'company_name', 'issue_name', 'avg_verifiability_score', 'record_count']
    with open(YEAR_COMPARISON_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_data)
    
    print(f"  年度对比已保存: {YEAR_COMPARISON_CSV} ({len(output_data)} 条)")

def generate_quality_report(rows):
    """生成数据质量报告"""
    from datetime import datetime
    
    # 统计各银行记录数
    bank_stats = defaultdict(int)
    for r in rows:
        code = r.get('company_code', '') or 'unknown'
        bank_stats[code] += 1
    
    # 统计各议题记录数
    issue_stats = defaultdict(int)
    for r in rows:
        issue_stats[r.get('issue_name', '')] += 1
    
    # 统计各年份记录数
    year_stats = defaultdict(int)
    for r in rows:
        year_stats[r.get('report_year', '')] += 1
    
    # 评分分布
    score_dist = defaultdict(int)
    for r in rows:
        score_dist[int(r.get('verifiability_score', 0) or 0)] += 1
    
    # 字段完整率
    fields = ['source_page', 'evidence_snippet', 'risk_tone', 'matrix_importance']
    field_rates = {}
    for field in fields:
        count = sum(1 for r in rows if r.get(field))
        field_rates[field] = count / len(rows) * 100 if rows else 0
    
    # 生成报告
    report = f"""# 数据质量报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 一、处理概况

| 指标 | 数值 |
|------|------|
| 总记录数 | {len(rows)} |
| 唯一银行数 | {len(bank_stats)} |
| 唯一议题数 | {len(issue_stats)} |
| 唯一年份数 | {len(year_stats)} |

## 二、各银行记录数

| 银行代码 | 银行名称 | 记录数 |
|----------|----------|--------|
"""
    for code, count in sorted(bank_stats.items(), key=lambda x: -x[1]):
        name = get_company_name(code) if code != 'unknown' else 'unknown'
        report += f"| {code} | {name} | {count} |\n"
    
    report += """
## 三、各议题记录数

| 议题 | 记录数 |
|------|--------|
"""
    for issue, count in sorted(issue_stats.items(), key=lambda x: -x[1]):
        report += f"| {issue} | {count} |\n"
    
    report += """
## 四、各年份记录数

| 年份 | 记录数 |
|------|--------|
"""
    for year, count in sorted(year_stats.items()):
        report += f"| {year} | {count} |\n"
    
    report += """
## 五、评分分布

| 评分 | 记录数 | 占比 |
|------|--------|------|
"""
    for score, count in sorted(score_dist.items()):
        pct = count / len(rows) * 100 if rows else 0
        report += f"| {score} | {count} | {pct:.1f}% |\n"
    
    report += """
## 六、字段完整率

| 字段 | 完整率 |
|------|--------|
"""
    for field, rate in sorted(field_rates.items(), key=lambda x: -x[1]):
        report += f"| {field} | {rate:.1f}% |\n"
    
    report += """
---

报告生成时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(QUALITY_REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"  质量报告已保存: {QUALITY_REPORT}")

def main():
    print("=" * 60)
    print("修复 base_records.csv")
    print("=" * 60)
    
    rows = fix_csv()
    if rows:
        generate_bank_trend(rows)
        generate_year_comparison(rows)
        generate_quality_report(rows)
    
    print("\n完成！")

if __name__ == '__main__':
    main()