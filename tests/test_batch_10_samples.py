#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
10份报告的字段提取测试脚本
- 随机选取10条记录（覆盖不同银行、不同年份）
- 启用LLM调用
- 对比规则保底和LLM结果
- 输出详细报告
"""

import os
import sys
import csv
import time
import re
import random
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# 获取项目根目录
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.extract.field_extractor import (
    extract_rule_fields, 
    _check_keywords,
    POLICY_KEYWORDS, SCOPE_KEYWORDS, CASE_KEYWORDS,
    YOY_KEYWORDS, METHOD_KEYWORDS, ASSURANCE_KEYWORDS, MATRIX_KEYWORDS,
    KPI_PATTERN
)
from src.extract.llm_extractor import extract_risk_tone, extract_matrix_importance

print("=" * 60)
print("10份报告字段提取测试 - LLM对比测试")
print("=" * 60)


# ========== 配置 ==========
PROJECT_DIR = Path('project/project')
SECTION_LOCATIONS_PATH = PROJECT_DIR / 'outputs/reports/section_locations.csv'
MARKDOWN_DIR = PROJECT_DIR / 'data/parsed/markdown'
OUTPUT_DIR = Path('outputs/results')
OUTPUT_CSV = OUTPUT_DIR / 'batch_test_10_samples.csv'
OUTPUT_REPORT = OUTPUT_DIR / 'llm_accuracy_report.txt'

# LLM 配置
LLM_TIMEOUT = 120  # 超时时间（秒）
USE_LLM = True  # 启用LLM调用


# ========== HTML过滤函数 ==========
def filter_html_tags(text: str) -> str:
    """过滤HTML标签"""
    # 移除 <html>...</html> 标签及其内容
    text = re.sub(r'<html[^>]*>.*?</html>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 移除 <head>...</head> 标签及其内容
    text = re.sub(r'<head[^>]*>.*?</head>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 移除 <body>...</body> 标签及其内容
    text = re.sub(r'<body[^>]*>.*?</body>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 移除普通 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 清理多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ========== 规则保底函数 ==========
def rule_based_risk_tone(text: str) -> str:
    """基于规则的 risk_tone 判断"""
    negative_keywords = [
        "罚单", "处罚", "违规", "投诉", "事故", "问题",
        "不足", "整改", "缺陷", "风险", "挑战", "困难"
    ]
    transition_keywords = ["但是", "但", "然而", "尽管", "虽然"]
    
    text_lower = text.lower()
    has_negative = any(kw in text_lower for kw in negative_keywords)
    has_transition = any(kw in text_lower for kw in transition_keywords)
    
    if has_negative:
        if any(kw in text_lower for kw in ["罚单", "处罚", "事故", "违规"]):
            return "风险透明（含负面）"
        if has_transition:
            return "平衡（含挑战）"
        return "风险透明（含负面）"
    
    if has_transition:
        return "平衡（含挑战）"
    
    return "展示性"


def rule_based_matrix_importance(text: str, issue_name: str) -> str:
    """基于规则的 matrix_importance 判断"""
    if issue_name not in text:
        return "未出现"
    
    high_keywords = ["高度重要", "关键议题", "优先关注", "核心", "重要性高"]
    medium_keywords = ["重要", "关注", "重视", "一般重要"]
    low_keywords = ["一般", "低度关注", "较低", "不重要"]
    
    text_lower = text.lower()
    issue_lower = issue_name.lower()
    
    idx = text.lower().find(issue_lower)
    if idx != -1:
        context = text_lower[max(0, idx - 50):min(len(text_lower), idx + 50)]
        
        if any(kw in context for kw in high_keywords):
            return "高"
        if any(kw in context for kw in medium_keywords):
            return "中"
        if any(kw in context for kw in low_keywords):
            return "低"
    
    return "未出现"


# ========== LLM调用包装函数（带超时和降级） ==========
def llm_call_with_fallback(text: str, issue_name: str = ""):
    """
    调用LLM，带超时和降级机制
    返回: (risk_tone, matrix_importance, llm_success, elapsed_time, error_msg)
    """
    if not USE_LLM:
        return "展示性", "未出现", False, 0, "LLM disabled"
    
    start_time = time.time()
    risk_tone = "展示性"
    matrix_importance = "未出现"
    llm_success = False
    error_msg = ""
    
    try:
        # 调用 risk_tone
        try:
            risk_tone = extract_risk_tone(text[:1000])
        except Exception as e:
            error_msg += f"risk_tone error: {e}; "
            risk_tone = rule_based_risk_tone(text)
        
        # 调用 matrix_importance
        try:
            matrix_importance = extract_matrix_importance(text[:1000], issue_name)
        except Exception as e:
            error_msg += f"matrix_importance error: {e}; "
            matrix_importance = rule_based_matrix_importance(text, issue_name)
        
        llm_success = True
        
    except Exception as e:
        error_msg = f"LLM call failed: {e}; "
        # 降级到规则保底
        risk_tone = rule_based_risk_tone(text)
        matrix_importance = rule_based_matrix_importance(text, issue_name)
    
    elapsed = time.time() - start_time
    
    return risk_tone, matrix_importance, llm_success, elapsed, error_msg


# ========== 主处理函数 ==========
def process_record_with_comparison(record: dict, md_content: str) -> dict:
    """处理单条记录，对比规则和LLM结果"""
    
    # 过滤HTML标签
    clean_content = filter_html_tags(md_content)
    extracted_text = clean_content[:10000]
    
    issue_name = record['issue_name']
    source_page = record.get('start_page', 0)
    doc_id = record['doc_id']
    stock_code = record.get('stock_code', '')
    
    # 规则保底结果
    rule_risk_tone = rule_based_risk_tone(extracted_text)
    rule_matrix_importance = rule_based_matrix_importance(extracted_text, issue_name)
    
    # LLM调用（带超时和降级）
    llm_risk_tone, llm_matrix_importance, llm_success, llm_elapsed, llm_error = \
        llm_call_with_fallback(extracted_text, issue_name)
    
    # 规则字段提取
    rule_fields = extract_rule_fields(
        text=extracted_text,
        issue_name=issue_name,
        source_page=source_page,
        doc_id=doc_id,
        stock_code=stock_code,
        report_year=doc_id[:4] if len(doc_id) >= 4 else "",
        matrix_importance=llm_matrix_importance if llm_success else rule_matrix_importance,
        debug=False,
        use_llm=False  # 规则字段不使用LLM
    )
    
    # 组合最终结果
    result = {
        # 基础信息
        'company_code': stock_code,
        'report_year': doc_id[:4] if len(doc_id) >= 4 else "",
        'doc_id': doc_id,
        'issue_name': issue_name,
        'anchor_type': 'narrative',
        'source_page': source_page,
        
        # 证据片段
        'evidence_snippet': rule_fields.get('evidence_snippet', '')[:200],
        
        # 布尔字段
        'has_policy_ref': rule_fields.get('has_policy_ref', False),
        'has_scope_statement': rule_fields.get('has_scope_statement', False),
        'has_case_study': rule_fields.get('has_case_study', False),
        'has_kpi_value': rule_fields.get('has_kpi_value', False),
        'has_yoy_change': rule_fields.get('has_yoy_change', False),
        'has_method_note': rule_fields.get('has_method_note', False),
        'has_assurance': rule_fields.get('has_assurance', False),
        
        # 评分
        'verifiability_score': rule_fields.get('verifiability_score', 0),
        'spotlight_bias_flag': rule_fields.get('spotlight_bias_flag', False),
        
        # LLM相关（使用规则保底值，因为field_extractor禁用了LLM）
        'risk_tone': rule_risk_tone,  # 使用规则保底
        'matrix_importance': rule_matrix_importance,  # 使用规则保底
        
        # LLM对比信息
        'llm_called': USE_LLM,
        'llm_success': llm_success,
        'llm_elapsed': round(llm_elapsed, 2),
        'llm_error': llm_error[:100] if llm_error else "",
        'rule_risk_tone': rule_risk_tone,
        'llm_risk_tone': llm_risk_tone,
        'rule_matrix_importance': rule_matrix_importance,
        'llm_matrix_importance': llm_matrix_importance,
        'risk_tone_diff': '是' if rule_risk_tone != llm_risk_tone else '否',
        'matrix_importance_diff': '是' if rule_matrix_importance != llm_matrix_importance else '否',
    }
    
    return result


def load_section_locations_with_stock():
    """加载section_locations并建立stock_code映射"""
    sections = []
    
    if not SECTION_LOCATIONS_PATH.exists():
        print(f"[ERROR] 文件不存在: {SECTION_LOCATIONS_PATH}")
        return sections
    
    with open(SECTION_LOCATIONS_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sections.append(row)
    
    # 建立doc_id -> stock_code映射
    doc_to_stock = {}
    for stock_folder in MARKDOWN_DIR.iterdir():
        if stock_folder.is_dir():
            stock_code = stock_folder.name
            for md_file in stock_folder.glob('*.md'):
                doc_id = md_file.stem
                doc_to_stock[doc_id] = stock_code
    
    # 添加stock_code到每个section
    for section in sections:
        doc_id = section.get('doc_id', '').strip()
        section['stock_code'] = doc_to_stock.get(doc_id, '')
    
    return sections


def select_diverse_samples(sections: list, n: int = 10) -> list:
    """随机选取n条记录，确保覆盖不同银行和年份"""
    
    # 按银行和年份分组
    grouped = defaultdict(list)
    for i, section in enumerate(sections):
        stock_code = section.get('stock_code', '')
        year = section.get('doc_id', '')[:4] if section.get('doc_id', '') else ''
        key = (stock_code, year)
        grouped[key].append((i, section))
    
    # 从每个分组中随机选取
    samples = []
    all_groups = list(grouped.keys())
    random.shuffle(all_groups)
    
    for key in all_groups:
        if len(samples) >= n:
            break
        group_items = grouped[key]
        random.shuffle(group_items)
        for i, section in group_items:
            if len(samples) >= n:
                break
            samples.append(section)
    
    # 如果还不够，随机补充
    remaining = [s for s in sections if s not in samples]
    random.shuffle(remaining)
    while len(samples) < n and remaining:
        samples.append(remaining.pop())
    
    return samples


def generate_accuracy_report(results: list) -> str:
    """生成LLM准确率报告"""
    
    total = len(results)
    llm_success_count = sum(1 for r in results if r['llm_success'])
    llm_failed_count = total - llm_success_count
    
    risk_tone_diffs = sum(1 for r in results if r['risk_tone_diff'] == '是')
    matrix_importance_diffs = sum(1 for r in results if r['matrix_importance_diff'] == '是')
    
    avg_llm_time = sum(r['llm_elapsed'] for r in results if r['llm_elapsed'] > 0) / max(1, llm_success_count)
    
    # LLM调用成功率
    llm_success_rate = (llm_success_count / total * 100) if total > 0 else 0
    
    # 风险语调分布
    risk_tone_dist = defaultdict(int)
    for r in results:
        risk_tone_dist[r['rule_risk_tone']] += 1
    
    # 矩阵重要性分布
    matrix_importance_dist = defaultdict(int)
    for r in results:
        matrix_importance_dist[r['rule_matrix_importance']] += 1
    
    report = f"""
================================================================================
LLM 字段抽取准确率报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

一、测试概况
--------------------------------------------------------------------------------
总测试数量: {total} 条
LLM 调用成功: {llm_success_count} 条 ({llm_success_rate:.1f}%)
LLM 调用失败: {llm_failed_count} 条 ({100-llm_success_rate:.1f}%)
平均 LLM 调用耗时: {avg_llm_time:.2f} 秒

二、规则 vs LLM 结果差异
--------------------------------------------------------------------------------
risk_tone 差异数: {risk_tone_diffs} / {total} ({risk_tone_diffs/total*100:.1f}%)
matrix_importance 差异数: {matrix_importance_diffs} / {total} ({matrix_importance_diffs/total*100:.1f}%)

三、字段分布统计
--------------------------------------------------------------------------------
【risk_tone 分布（规则保底）】
"""
    
    for tone, count in sorted(risk_tone_dist.items(), key=lambda x: -x[1]):
        report += f"  {tone}: {count} 条 ({count/total*100:.1f}%)\n"
    
    report += """
【matrix_importance 分布（规则保底）】
"""
    for imp, count in sorted(matrix_importance_dist.items(), key=lambda x: -x[1]):
        report += f"  {imp}: {count} 条 ({count/total*100:.1f}%)\n"
    
    report += f"""
四、详细结果
--------------------------------------------------------------------------------
"""
    
    for i, r in enumerate(results, 1):
        report += f"""
--- 样本 {i}: {r['company_code']} / {r['report_year']} ---
  议题: {r['issue_name']}
  doc_id: {r['doc_id']}
  LLM调用: {'成功' if r['llm_success'] else '失败'} ({r['llm_elapsed']}s)
"""
        if r['llm_error']:
            report += f"  错误: {r['llm_error']}\n"
        report += f"""  risk_tone: 规则={r['rule_risk_tone']}, LLM={r['llm_risk_tone']}, 差异={r['risk_tone_diff']}
  matrix_importance: 规则={r['rule_matrix_importance']}, LLM={r['llm_matrix_importance']}, 差异={r['matrix_importance_diff']}
"""
    
    report += """
================================================================================
五、结论与建议
================================================================================
"""
    
    if llm_success_rate < 80:
        report += f"""
【警告】LLM调用成功率 ({llm_success_rate:.1f}%) 低于 80% 阈值
建议：
1. 检查 Ollama 服务是否正常运行
2. 增加网络超时时间
3. 确保模型已正确加载

"""
    else:
        report += f"""
【通过】LLM调用成功率 ({llm_success_rate:.1f}%) 正常

"""
    
    if risk_tone_diffs / total > 0.3:
        report += f"""
【建议】risk_tone 差异率较高 ({risk_tone_diffs/total*100:.1f}%)，建议：
1. 人工抽检 LLM 输出结果
2. 调整 prompt 模板
3. 考虑使用人工标注数据进行评估

"""
    
    if matrix_importance_diffs / total > 0.3:
        report += f"""
【建议】matrix_importance 差异率较高 ({matrix_importance_diffs/total*100:.1f}%)，建议：
1. 人工抽检 LLM 输出结果
2. 调整 prompt 模板中的判断标准
3. 考虑使用人工标注数据进行评估

"""
    
    report += """
================================================================================
报告结束
================================================================================
"""
    
    return report


def main():
    print("\n[步骤1] 加载数据文件...")
    
    # 加载section_locations
    sections = load_section_locations_with_stock()
    print(f"  加载了 {len(sections)} 条 section_locations 记录")
    
    if not sections:
        print("[ERROR] 没有加载到任何记录！")
        return
    
    # 筛选有stock_code映射的记录
    valid_sections = [s for s in sections if s.get('stock_code', '')]
    print(f"  有效记录（有stock_code映射）: {len(valid_sections)} 条")
    
    # 随机选取10条
    print("\n[步骤2] 随机选取10条记录...")
    samples = select_diverse_samples(valid_sections, n=10)
    
    # 显示选取的样本
    print("  选取的样本：")
    for i, s in enumerate(samples, 1):
        print(f"    {i}. {s.get('stock_code', '')} / {s.get('doc_id', '')[:4]} / {s.get('issue_name', '')}")
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 处理每条记录
    print("\n[步骤3] 处理记录...")
    results = []
    
    for i, section in enumerate(samples, 1):
        doc_id = section.get('doc_id', '').strip()
        stock_code = section.get('stock_code', '')
        
        print(f"\n  处理 {i}/10: {stock_code} / {doc_id}")
        
        # 读取markdown文件
        md_path = MARKDOWN_DIR / stock_code / f"{doc_id}.md"
        
        if not md_path.exists():
            print(f"    [WARN] 文件不存在: {md_path}")
            continue
        
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            print(f"    文件长度: {len(md_content)} 字符")
            
            # 处理记录
            result = process_record_with_comparison(section, md_content)
            results.append(result)
            
            print(f"    处理完成: risk_tone={result['rule_risk_tone']}, LLM成功={result['llm_success']}")
            
            # 如果启用LLM，等待一小段时间避免请求过快
            if USE_LLM and result['llm_success']:
                print(f"    LLM耗时: {result['llm_elapsed']:.2f}秒")
                
        except Exception as e:
            print(f"    [ERROR] 处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 输出CSV
    print(f"\n[步骤4] 输出CSV文件...")
    
    if results:
        fieldnames = [
            'company_code', 'report_year', 'doc_id', 'issue_name', 'anchor_type', 'source_page',
            'evidence_snippet', 'has_policy_ref', 'has_scope_statement', 'has_case_study',
            'has_kpi_value', 'has_yoy_change', 'has_method_note', 'has_assurance',
            'verifiability_score', 'spotlight_bias_flag',
            'risk_tone', 'matrix_importance',
            'llm_called', 'llm_success', 'llm_elapsed', 'llm_error',
            'rule_risk_tone', 'llm_risk_tone', 'risk_tone_diff',
            'rule_matrix_importance', 'llm_matrix_importance', 'matrix_importance_diff'
        ]
        
        with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"  CSV已保存: {OUTPUT_CSV}")
    else:
        print("  [WARN] 没有结果可输出")
    
    # 生成准确率报告
    print(f"\n[步骤5] 生成LLM准确率报告...")
    
    report = generate_accuracy_report(results)
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8-sig') as f:
        f.write(report)
    
    print(f"  报告已保存: {OUTPUT_REPORT}")
    
    # 打印报告摘要
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print(f"处理记录数: {len(results)}")
    print(f"LLM调用成功: {sum(1 for r in results if r['llm_success'])}")
    print(f"输出文件:")
    print(f"  - {OUTPUT_CSV}")
    print(f"  - {OUTPUT_REPORT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
