#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全量字段提取脚本 v2

功能：
1. 读取全部 section_locations.csv
2. 通过扫描 markdown 目录建立 stock_code 映射
3. 逐条处理，每 50 条打印进度
4. 支持断点续传（记录已处理的 doc_id+issue_name 组合）
5. 输出到 outputs/results/base_records.csv
6. 生成辅助输出：bank_trend.csv, year_comparison.csv

作者：陈欣悦
日期：2026-06-14
"""

import csv
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# 获取项目根目录
project_root = r"e:\abcdefu\大学\26-3\机器学习与数据挖掘\B"
sys.path.insert(0, project_root)

from src.extract.field_extractor import extract_rule_fields, filter_html_tags

# ========== 配置路径 ==========
PROJECT_DIR = Path(project_root) / 'project/project'
SECTION_LOCATIONS_PATH = PROJECT_DIR / 'outputs/reports/section_locations.csv'
MARKDOWN_DIR = PROJECT_DIR / 'data/parsed/markdown'
OUTPUT_DIR = Path(project_root) / 'outputs/results'
LOGS_DIR = Path(project_root) / 'outputs/logs'
# 时间戳文件名（避免文件锁定问题）
import datetime
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_CSV = OUTPUT_DIR / f'base_records_{TIMESTAMP}.csv'
# 同时保留一个固定名称的软链接指向最新文件
LATEST_CSV = OUTPUT_DIR / 'base_records.csv'
PROCESSED_IDS_FILE = LOGS_DIR / 'processed_ids_v2.json'  # 新版断点文件
ERROR_CSV = LOGS_DIR / 'extract_errors.csv'
LOG_FILE = LOGS_DIR / 'extract_log.txt'

# ========== 银行代码映射表 ==========
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
    "601229": "上海银行",
    "601288": "农业银行",
    "601328": "交通银行",
    "601398": "工商银行",
    "601577": "长沙银行",
    "601665": "齐鲁银行",
    "601818": "光大银行",
    "601838": "成都银行",
    "601860": "紫金银行",
    "601916": "招商银行(缩略)",
    "601939": "建设银行",
    "601963": "重庆银行(缩略)",
    "601988": "中国银行",
    "601997": "贵阳银行",
    "601998": "中信银行",
    "602001": "苏农银行",
    "603323": "苏农银行(缩略)",
    "603997": "宁波银行(缩略)",
}

# ========== 议题名称标准化映射 ==========
ISSUE_NAME_MAPPING = {
    "风险管理": "公司治理/风险管理",
    "公司治理": "公司治理/风险管理",
    "绿色金融": "绿色信贷/绿色金融",
    "消费者权益保护": "消费者权益保护",
    "普惠金融": "普惠金融",
    "乡村振兴": "员工权益",
    "员工权益": "员工权益",
    "信息安全": "信息安全与隐私保护",
}

# ========== 全局统计 ==========
stats = {
    'total': 0,
    'success': 0,
    'failed': 0,
    'llm_success': 0,
    'llm_failed': 0,
    'skip_no_file': 0,
    'skip_no_mapping': 0,
    'total_time': 0,
}


def normalize_issue_name(issue_name: str) -> str:
    """标准化议题名称"""
    return ISSUE_NAME_MAPPING.get(issue_name, issue_name)


def get_company_name(stock_code: str) -> str:
    """获取公司名称"""
    return BANK_NAMES.get(stock_code, stock_code)


def load_processed_ids() -> set:
    """加载已处理的 doc_id+issue 组合（用于断点续传）"""
    if PROCESSED_IDS_FILE.exists():
        try:
            with open(PROCESSED_IDS_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception as e:
            print(f"[WARN] 加载断点文件失败: {e}")
    return set()


def save_processed_ids(ids: set):
    """保存已处理的 doc_id+issue 组合"""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(PROCESSED_IDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(ids), f, ensure_ascii=False)
    except Exception as e:
        print(f"[WARN] 保存断点文件失败: {e}")


def build_doc_mapping() -> dict:
    """扫描 markdown 目录，建立 doc_id -> stock_code 映射"""
    doc_to_stock = {}
    
    if not MARKDOWN_DIR.exists():
        print(f"[ERROR] markdown 目录不存在: {MARKDOWN_DIR}")
        return doc_to_stock
    
    for stock_folder in MARKDOWN_DIR.iterdir():
        if stock_folder.is_dir():
            stock_code = stock_folder.name
            for md_file in stock_folder.glob('*.md'):
                doc_id = md_file.stem
                doc_to_stock[doc_id] = stock_code
    
    print(f"  建立 doc_id -> stock_code 映射: {len(doc_to_stock)} 个文档")
    return doc_to_stock


def load_section_locations() -> tuple:
    """加载 section_locations 并返回 (sections, doc_to_stock)"""
    sections = []
    
    if not SECTION_LOCATIONS_PATH.exists():
        print(f"[ERROR] 文件不存在: {SECTION_LOCATIONS_PATH}")
        return sections, {}
    
    with open(SECTION_LOCATIONS_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sections.append(row)
    
    # 建立 doc_id -> stock_code 映射
    doc_to_stock = build_doc_mapping()
    
    # 添加 stock_code 和 company_name
    for section in sections:
        doc_id = section.get('doc_id', '').strip()
        stock_code = doc_to_stock.get(doc_id, '')
        section['stock_code'] = stock_code
        section['company_name'] = get_company_name(stock_code)
        section['normalized_issue'] = normalize_issue_name(section.get('issue_name', ''))
    
    return sections, doc_to_stock


def process_single_record(record: dict, processed_ids: set) -> dict:
    """
    处理单条记录
    
    参数:
        record: section_locations 中的记录
        processed_ids: 已处理的 doc_id+issue 组合集合
    
    返回:
        dict: 处理结果，失败返回 None
    """
    doc_id = record.get('doc_id', '').strip()
    stock_code = record.get('stock_code', '')
    issue_name = record.get('issue_name', '')
    normalized_issue = record.get('normalized_issue', normalize_issue_name(issue_name))
    source_page = record.get('start_page', 0)
    
    # 创建唯一处理键（doc_id + issue_name 组合）
    process_key = f"{doc_id}|{issue_name}"
    
    # 检查是否已处理（断点续传）
    if process_key in processed_ids:
        return None
    
    # 检查 stock_code 映射
    if not stock_code:
        stats['skip_no_mapping'] += 1
        return None
    
    # 读取 markdown 文件
    md_path = MARKDOWN_DIR / stock_code / f"{doc_id}.md"
    if not md_path.exists():
        stats['skip_no_file'] += 1
        return None
    
    try:
        # 读取并过滤 HTML
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 过滤 HTML 标签
        clean_content = filter_html_tags(md_content)
        extracted_text = clean_content[:10000]  # 截断到合理长度
        
        # 提取字段
        result = extract_rule_fields(
            text=extracted_text,
            issue_name=normalized_issue,  # 使用标准化后的议题名称
            source_page=source_page,
            doc_id=doc_id,
            stock_code=stock_code,
            report_year=doc_id[:4] if len(doc_id) >= 4 else '',
            matrix_importance=None,
            debug=False,
            use_llm=False,  # 禁用 LLM 调用（LLM 服务不稳定）
        )
        
        # 添加额外字段
        result['company_name'] = get_company_name(stock_code)
        result['company_code'] = stock_code  # 添加 company_code 字段
        result['original_issue_name'] = issue_name  # 保留原始议题名称
        
        # 统计 LLM 调用结果
        if result.get('llm_success', False):
            stats['llm_success'] += 1
        else:
            stats['llm_failed'] += 1
        
        return result
        
    except Exception as e:
        # 记录异常但不中断程序
        error_info = {
            'doc_id': doc_id,
            'stock_code': stock_code,
            'issue_name': issue_name,
            'error': str(e)[:200],
        }
        stats.setdefault('errors', []).append(error_info)
        return None


def load_existing_results(doc_to_stock: dict) -> list:
    """加载已有的结果文件"""
    # 优先使用时间戳文件，其次使用 LATEST_CSV
    csv_file = OUTPUT_CSV if OUTPUT_CSV.exists() else (LATEST_CSV if LATEST_CSV.exists() else None)
    if not csv_file or not csv_file.exists():
        return []
    
    results = []
    try:
        with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 尝试从 doc_id 解析 stock_code
                # doc_id 格式: "2021-1212533363"，需要在 markdown 目录中查找对应的文档
                doc_id = row.get('doc_id', '')
                stock_code = row.get('stock_code', '') or row.get('company_code', '')
                
                # 如果 stock_code 为空，尝试从 doc_to_stock 映射中查找
                if not stock_code and doc_id:
                    stock_code = doc_to_stock.get(doc_id, '')
                
                # 设置 company_code 和 company_name
                if stock_code:
                    row['company_code'] = stock_code
                    row['company_name'] = get_company_name(stock_code)
                elif not row.get('company_code'):
                    row['company_code'] = ''
                    row['company_name'] = row.get('company_name', '')
                
                results.append(row)
        print(f"  已加载已有结果: {len(results)} 条")
    except Exception as e:
        print(f"  加载已有结果失败: {e}")
    return results


def save_results(results: list):
    """保存结果到 CSV（追加模式）"""
    if not results:
        return
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 删除旧文件（如果存在且被占用）
    if OUTPUT_CSV.exists():
        try:
            OUTPUT_CSV.unlink()
        except PermissionError:
            # 文件被占用，等待后重试
            import time
            time.sleep(1)
            try:
                OUTPUT_CSV.unlink()
            except:
                pass
    
    fieldnames = [
        'company_code', 'company_name', 'report_year', 'doc_id', 'issue_name', 
        'original_issue_name', 'anchor_type', 'source_page', 'source_page_warning', 
        'evidence_snippet',
        'has_policy_ref', 'has_scope_statement', 'has_case_study',
        'has_kpi_value', 'has_yoy_change', 'has_method_note', 'has_assurance',
        'verifiability_score', 'spotlight_bias_flag',
        'risk_tone', 'matrix_importance',
        'llm_success',
    ]
    
    # 使用临时文件保存，然后重命名（避免文件被占用的问题）
    import shutil
    temp_file = OUTPUT_DIR / f'base_records_temp_{os.getpid()}.csv'
    try:
        with open(temp_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)
        
        # 删除旧文件（如果存在）
        if OUTPUT_CSV.exists():
            try:
                OUTPUT_CSV.unlink()
            except PermissionError:
                pass
        
        # 重命名临时文件
        temp_file.rename(OUTPUT_CSV)
        
        # 同时复制到 LATEST_CSV
        try:
            if LATEST_CSV.exists():
                try:
                    LATEST_CSV.unlink()
                except PermissionError:
                    pass
            shutil.copy2(OUTPUT_CSV, LATEST_CSV)
        except Exception as e:
            print(f"  复制到最新文件失败: {e}")
    except Exception as e:
        print(f"  保存失败: {e}")
        # 尝试直接保存
        try:
            with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(results)
            # 同时复制到 LATEST_CSV
            shutil.copy2(OUTPUT_CSV, LATEST_CSV)
        except Exception as e2:
            print(f"  备用保存也失败: {e2}")
    
    print(f"  结果已保存: {OUTPUT_CSV}")


def save_errors():
    """保存异常记录到 CSV"""
    errors = stats.get('errors', [])
    if not errors:
        return
    
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['doc_id', 'stock_code', 'issue_name', 'error']
    
    with open(ERROR_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(errors)
    
    print(f"  异常记录已保存: {ERROR_CSV}")


def save_bank_trend(results: list):
    """保存银行-议题-年份趋势表"""
    # 按 (company_code, issue_name, report_year) 聚合
    aggregated = defaultdict(lambda: {'scores': [], 'count': 0})
    
    for r in results:
        key = (r.get('company_code', ''), r.get('issue_name', ''), r.get('report_year', ''))
        score = int(r.get('verifiability_score', 0) or 0)
        aggregated[key]['scores'].append(score)
        aggregated[key]['count'] += 1
    
    # 构建输出数据
    output_data = []
    for (company_code, issue_name, year), data in sorted(aggregated.items()):
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
    trend_path = OUTPUT_DIR / 'bank_trend.csv'
    with open(trend_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['company_code', 'company_name', 'issue_name', 'report_year', 'avg_verifiability_score', 'record_count'])
        writer.writeheader()
        writer.writerows(output_data)
    
    print(f"  银行趋势已保存: {trend_path}")


def save_year_comparison(results: list):
    """保存年份-银行对比表"""
    # 按 (year, company_code, issue_name) 聚合
    aggregated = defaultdict(lambda: {'scores': [], 'count': 0})
    
    for r in results:
        key = (r.get('report_year', ''), r.get('company_code', ''), r.get('issue_name', ''))
        score = int(r.get('verifiability_score', 0) or 0)
        aggregated[key]['scores'].append(score)
        aggregated[key]['count'] += 1
    
    # 构建输出数据
    output_data = []
    for (year, company_code, issue_name), data in sorted(aggregated.items()):
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
    comparison_path = OUTPUT_DIR / 'year_comparison.csv'
    with open(comparison_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['report_year', 'company_code', 'company_name', 'issue_name', 'avg_verifiability_score', 'record_count'])
        writer.writeheader()
        writer.writerows(output_data)
    
    print(f"  年度对比已保存: {comparison_path}")


def generate_data_quality_report(results: list):
    """生成数据质量报告"""
    total = len(results)
    
    # 按银行统计
    bank_stats = defaultdict(int)
    for r in results:
        bank_stats[r.get('company_code', 'unknown')] += 1
    
    # 按年份统计
    year_stats = defaultdict(int)
    for r in results:
        year_stats[r.get('report_year', 'unknown')] += 1
    
    # 按议题统计
    issue_stats = defaultdict(int)
    for r in results:
        issue_stats[r.get('issue_name', 'unknown')] += 1
    
    # 计算字段完整率
    null_rates = {}
    for field in ['source_page', 'evidence_snippet', 'risk_tone', 'matrix_importance',
                   'has_policy_ref', 'has_scope_statement', 'has_case_study']:
        if total > 0:
            null_count = sum(1 for r in results if not r.get(field))
            null_rates[field] = f"{(total - null_count)/total*100:.1f}%"
    
    # LLM 成功率
    llm_success_rate = stats['llm_success'] / max(1, total) * 100
    
    # 评分分布
    score_dist = defaultdict(int)
    for r in results:
        score_dist[int(r.get('verifiability_score', 0) or 0)] += 1
    
    # 缺失的议题
    all_issues = set(ISSUE_NAME_MAPPING.values())
    found_issues = set(issue_stats.keys())
    missing_issues = all_issues - found_issues
    
    report = f"""# 数据质量报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 一、处理概况

| 指标 | 数值 |
|------|------|
| 总记录数 | {total} |
| 成功处理 | {stats['success']} |
| 处理失败 | {stats['failed']} |
| 跳过（无文件） | {stats['skip_no_file']} |
| 跳过（无映射） | {stats['skip_no_mapping']} |
| 异常记录数 | {len(stats.get('errors', []))} |
| 总耗时 | {stats['total_time']:.1f} 秒 ({stats['total_time']/60:.1f} 分钟) |
| 平均耗时 | {stats['total_time']/max(1, stats['success']):.2f} 秒/条 |

## 二、LLM 调用统计

| 指标 | 数值 |
|------|------|
| LLM 成功 | {stats['llm_success']} ({llm_success_rate:.1f}%) |
| LLM 失败 | {stats['llm_failed']} ({100-llm_success_rate:.1f}%) |

## 三、各银行记录数

| 银行代码 | 银行名称 | 记录数 |
|----------|----------|--------|
"""
    
    for bank, count in sorted(bank_stats.items(), key=lambda x: -x[1]):
        name = get_company_name(bank)
        report += f"| {bank} | {name} | {count} |\n"
    
    report += """
## 四、各年份记录数

| 年份 | 记录数 |
|------|--------|
"""
    
    for year, count in sorted(year_stats.items()):
        report += f"| {year} | {count} |\n"
    
    report += """
## 五、各议题记录数

| 议题 | 记录数 |
|------|--------|
"""
    
    for issue, count in sorted(issue_stats.items(), key=lambda x: -x[1]):
        report += f"| {issue} | {count} |\n"
    
    if missing_issues:
        report += f"""
### 缺失的议题
以下预期议题在数据中未找到：{', '.join(missing_issues)}
"""
    
    report += """
## 六、字段完整率

| 字段 | 完整率 |
|------|--------|
"""
    
    for field, rate in null_rates.items():
        report += f"| {field} | {rate} |\n"
    
    report += """
## 七、评分分布

| 评分 | 记录数 | 占比 |
|------|--------|------|
"""
    
    for score, count in sorted(score_dist.items()):
        rate = count / max(1, total) * 100
        report += f"| {score} | {count} | {rate:.1f}% |\n"
    
    report += """
## 八、字段分布（布尔字段）

| 字段 | True 比例 |
|------|----------|
"""
    
    for field in ['has_policy_ref', 'has_scope_statement', 'has_case_study', 
                   'has_kpi_value', 'has_yoy_change', 'has_method_note', 'has_assurance']:
        if total > 0:
            true_count = sum(1 for r in results if r.get(field, False))
            rate = true_count / total * 100
            report += f"| {field} | {true_count}/{total} ({rate:.1f}%) |\n"
    
    report += """
## 九、异常记录摘要

"""
    
    errors = stats.get('errors', [])
    if errors:
        report += f"共 {len(errors)} 条异常\n\n"
        for err in errors[:5]:
            report += f"- {err['doc_id']}: {err['error'][:100]}...\n"
    else:
        report += "无异常记录\n"
    
    report += f"""
## 十、议题标准化映射

| 原始议题 | 标准议题 |
|----------|----------|
"""
    
    for orig, std in ISSUE_NAME_MAPPING.items():
        report += f"| {orig} | {std} |\n"
    
    report += """
---

报告生成时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
"""
    
    report_path = OUTPUT_DIR / 'data_quality_report.md'
    with open(report_path, 'w', encoding='utf-8-sig') as f:
        f.write(report)
    
    print(f"  质量报告已保存: {report_path}")
    return report_path


def save_sample_check(results: list, n: int = 10):
    """保存随机抽样检查结果"""
    import random
    
    if len(results) <= n:
        sample = results
    else:
        sample = random.sample(results, n)
    
    sample_path = OUTPUT_DIR / 'sample_check.csv'
    
    fieldnames = [
        'company_code', 'company_name', 'report_year', 'doc_id', 'issue_name', 
        'source_page', 'source_page_warning', 'evidence_snippet',
        'has_policy_ref', 'has_scope_statement', 'has_case_study',
        'has_kpi_value', 'has_yoy_change',
        'risk_tone', 'matrix_importance',
        'verifiability_score',
    ]
    
    with open(sample_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(sample)
    
    print(f"  抽样检查已保存: {sample_path}")


def main():
    print("=" * 60)
    print("全量字段提取开始 v2")
    print("=" * 60)
    
    start_time = time.time()
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载断点续传记录
    processed_ids = load_processed_ids()
    print(f"\n[步骤1] 加载数据...")
    print(f"  已处理记录数: {len(processed_ids)}")
    
    # 加载 section_locations
    sections, doc_to_stock = load_section_locations()
    stats['total'] = len(sections)
    print(f"  总记录数: {stats['total']}")
    print(f"  有效映射数: {len(doc_to_stock)}")
    
    # 过滤未处理的记录
    pending_sections = []
    for s in sections:
        key = f"{s.get('doc_id', '')}|{s.get('issue_name', '')}"
        if key not in processed_ids and s.get('stock_code', ''):
            pending_sections.append(s)
    
    print(f"  待处理记录数: {len(pending_sections)}")
    
    # 处理每条记录
    print(f"\n[步骤2] 开始处理...")
    results = load_existing_results(doc_to_stock)  # 加载已有结果
    print(f"  当前已有结果: {len(results)} 条")
    
    for i, section in enumerate(pending_sections, 1):
        doc_id = section.get('doc_id', '')
        issue_name = section.get('issue_name', '')
        
        # 每 50 条打印进度
        if i % 50 == 0 or i == 1:
            elapsed = time.time() - start_time
            avg_time = elapsed / i if i > 0 else 0
            remaining = len(pending_sections) - i
            print(f"  进度: {i}/{len(pending_sections)} ({i/len(pending_sections)*100:.1f}%) "
                  f"| 当前: {doc_id} | {issue_name[:15]}... | 预估剩余: {avg_time * remaining:.0f}秒")
        
        # 处理单条记录
        record_start = time.time()
        key = f"{doc_id}|{issue_name}"
        
        try:
            result = process_single_record(section, processed_ids)
        except KeyboardInterrupt:
            print("\n[用户中断] 保存断点...")
            save_processed_ids(processed_ids)
            raise
        except Exception as e:
            print(f"\n[ERROR] 处理记录 {doc_id} 时发生异常: {e}")
            stats['failed'] += 1
            result = None
        
        record_time = time.time() - record_start
        
        if result:
            results.append(result)
            stats['success'] += 1
            processed_ids.add(key)
        else:
            stats['failed'] += 1
        
        stats['total_time'] = time.time() - start_time
        
        # 每处理 10 条保存一次断点（更频繁保存）
        if i % 10 == 0:
            save_processed_ids(processed_ids)
    
    # 保存最终结果
    print(f"\n[步骤3] 保存结果...")
    save_results(results)
    save_errors()
    save_bank_trend(results)
    save_year_comparison(results)
    
    # 生成质量报告
    print(f"\n[步骤4] 生成数据质量报告...")
    generate_data_quality_report(results)
    save_sample_check(results)
    
    # 总耗时
    total_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print(f"全量提取完成！")
    print(f"共处理 {stats['success']} 条记录，耗时 {total_time:.1f} 秒 ({total_time/60:.1f} 分钟)")
    print("=" * 60)
    
    # 打印统计摘要
    print("\n统计摘要:")
    print(f"  总记录数: {stats['total']}")
    print(f"  成功处理: {stats['success']}")
    print(f"  LLM 成功率: {stats['llm_success']/max(1, stats['success'])*100:.1f}%")
    print(f"  异常记录: {len(stats.get('errors', []))}")
    print(f"\n输出文件:")
    print(f"  - {OUTPUT_CSV}")
    print(f"  - {OUTPUT_DIR / 'bank_trend.csv'}")
    print(f"  - {OUTPUT_DIR / 'year_comparison.csv'}")
    print(f"  - {LOGS_DIR / 'extract_errors.csv'}")
    print(f"  - {OUTPUT_DIR / 'sample_check.csv'}")
    print(f"  - {OUTPUT_DIR / 'data_quality_report.md'}")


if __name__ == "__main__":
    main()
