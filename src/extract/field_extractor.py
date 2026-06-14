"""
字段抽取脚本 - 规则字段部分

输入：
  - section_locations.csv（B 同学提供）
  - metadata.csv（A 同学提供，但需注意无直接 doc_id 映射）
  - data/parsed/markdown/{stock_code}/{doc_id}.md（B 同学解析后的文本）

输出：
  - outputs/results/base_records.csv

作者：陈欣悦
日期：2026-06-14
"""

import csv
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ========== HTML 过滤函数 ==========
def filter_html_tags(text: str) -> str:
    """
    过滤 HTML 标签，只保留纯文本内容
    
    参数:
        text: 原始文本（可能包含 HTML 标签）
    
    返回:
        str: 过滤后的纯文本
    """
    if not text:
        return ""
    
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


# 导入 LLM 抽取模块
try:
    from .llm_extractor import extract_risk_tone, extract_matrix_importance
except ImportError:
    from llm_extractor import extract_risk_tone, extract_matrix_importance

# ========== 默认路径配置（相对于项目根目录） ==========
DEFAULT_SECTION_LOCATIONS = "project/project/outputs/reports/section_locations.csv"
DEFAULT_METADATA = "data/metadata.csv"
DEFAULT_PARSED_DIR = "project/project/data/parsed/markdown"
DEFAULT_OUTPUT = "outputs/results/base_records.csv"


# ========== 关键词库（按需求定义） ==========
# 关键词需要合理平衡：避免误检，但也要能匹配到实际存在的文本

# 政策参考：严格匹配政策类文件名称（中文书名号内）
POLICY_KEYWORDS = [
    "《ESG", "《绿色金融", "《社会责任", "《风险管理", "《公司治理",
    "《合规管理", "《数据安全", "《信息安全", "《消费者权益",
    "《普惠金融", "《乡村振兴", "《碳中和", "《碳达峰"
]

# 范围声明：严格匹配范围相关的短语
SCOPE_KEYWORDS = [
    "统计范围", "统计口径", "报告范围", "计量口径",
    "不包括", "不含", "剔除", "境内分行", "子公司",
    "范围包括", "范围涵盖"
]

# 案例研究：严格匹配案例相关词汇
CASE_KEYWORDS = [
    "案例", "案例分析", "案例一", "案例二", "案例三",
    "专栏", "实践案例", "典型案例", "【案例", "（案例",
    " BOX", "box"  # 英文案例框
]

# 同比变化：严格匹配同比相关词汇
YOY_KEYWORDS = [
    "同比", "同比增长", "同比增加", "同比下降", "同比减少",
    "较上年", "较上年末", "较年初", "比上年", "比去年同期",
    "较2020", "较2019", "较2018"  # 具体年份对比
]

# 方法说明：严格匹配方法说明相关词汇
METHOD_KEYWORDS = [
    "注：", "注:", "①", "¹", "²", "编制基础", 
    "指标释义", "数据来源说明", "计算方法说明", "口径说明"
]

# 鉴证声明：严格匹配鉴证相关词汇
ASSURANCE_KEYWORDS = [
    "鉴证", "第三方审计", "独立验证", "外部审计",
    "审计机构", "会计师事务所", "验证意见", "核查意见"
]

# 实质性矩阵
MATRIX_KEYWORDS = ["实质性议题", "重要性矩阵", "重大性议题", "重要议题矩阵"]


# ========== 正则模式 ==========
KPI_PATTERN = re.compile(r"\d+\.?\d*\s*[亿元万元户人%]")


# ========== issue_name 映射关系 ==========
ISSUE_NAME_MAPPING = {
    "风险管理": "公司治理/风险管理",
    "公司治理": "公司治理/风险管理",
    "绿色金融": "绿色信贷/绿色金融",
    "消费者权益保护": "消费者权益保护",
    "普惠金融": "普惠金融",
    "员工权益": "员工权益",
    "乡村振兴": "员工权益",
    "信息": "信息安全与隐私保护",
}


def normalize_issue_name(issue_name: str) -> str:
    """将 B 同学输出的 issue_name 映射为标准议题"""
    return ISSUE_NAME_MAPPING.get(issue_name, issue_name)


# ========== 辅助函数 ==========

def _check_keywords(text: str, keywords: List[str], field_name: str = "") -> tuple:
    """
    检查文本中是否包含任一关键词
    
    返回:
        tuple: (是否匹配, 匹配到的关键词列表)
    """
    matched_keywords = []
    for kw in keywords:
        if kw in text:
            matched_keywords.append(kw)
    
    return len(matched_keywords) > 0, matched_keywords


def _extract_evidence_snippet(text: str, issue_name: str = "", max_sentences: int = 3, max_chars_per_sentence: int = 100) -> str:
    """
    截取原文片段（1-3 句），优先保留包含关键词的句子
    
    参数:
        text: 原始文本
        issue_name: 议题名称（用于定制关键词）
        max_sentences: 最大句子数，默认 3
        max_chars_per_sentence: 每句最大字符数，默认 100
    
    返回:
        截取后的证据片段
    """
    # 按句号、感叹号、问号、分号分割句子
    raw_sentences = re.split(r"[。！？；\n]", text)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 10]

    if not sentences:
        return text[:200].strip()

    # 收集所有关键词
    all_keywords = (
        POLICY_KEYWORDS
        + SCOPE_KEYWORDS
        + CASE_KEYWORDS
        + YOY_KEYWORDS
        + METHOD_KEYWORDS
        + ASSURANCE_KEYWORDS
        + MATRIX_KEYWORDS
    )
    
    # 根据议题名称添加定制关键词
    issue_keywords = []
    if issue_name:
        # 将议题名称拆分成词作为关键词
        cleaned_issue = issue_name.replace("/", "").replace(" ", "").replace("（", "").replace("）", "")
        issue_keywords.append(cleaned_issue)
        # 添加议题名称的各个部分
        issue_parts = issue_name.replace("/", " ").replace("（", " ").replace("）", " ").split()
        issue_keywords += issue_parts
    
    all_keywords += issue_keywords
    
    # 优先选择包含关键词的句子
    priority_sentences = [
        s for s in sentences if any(kw in s for kw in all_keywords)
    ]

    # 选择句子：优先选择包含关键词的句子，最多 max_sentences 句
    selected = priority_sentences[:max_sentences]
    if not selected:
        selected = sentences[:max_sentences]

    # 截断每句话到 max_chars_per_sentence 字符
    truncated_sentences = [s[:max_chars_per_sentence] for s in selected]
    
    # 用分号连接
    result = "；".join(truncated_sentences)
    
    return result


def extract_rule_fields(
    text: str,
    issue_name: str,
    source_page: int,
    doc_id: str = "",
    stock_code: str = "",
    report_year: int = 0,
    matrix_importance: Optional[str] = None,
    debug: bool = False,
    use_llm: bool = False,  # 新增参数：是否调用 LLM
) -> Dict[str, Any]:
    """
    从文本片段中抽取所有规则字段和派生字段

    参数:
        text: 解析后的文本内容
        issue_name: 原始议题名称
        source_page: 证据页码（来自 section_locations）
        doc_id: 文档 ID
        stock_code: 股票代码
        report_year: 报告年份
        matrix_importance: 议题重要性（高/中/低），若未提供则留空
        debug: 是否打印调试信息

    返回:
        包含所有规则字段、派生字段和基础字段的字典
    """
    clean_text = text.replace("\n", " ").replace("\t", " ")

    # 规则字段提取（带调试输出）
    has_policy_ref, policy_kws = _check_keywords(clean_text, POLICY_KEYWORDS, "has_policy_ref")
    has_scope_statement, scope_kws = _check_keywords(clean_text, SCOPE_KEYWORDS, "has_scope_statement")
    has_case_study, case_kws = _check_keywords(clean_text, CASE_KEYWORDS, "has_case_study")
    has_method_note, method_kws = _check_keywords(clean_text, METHOD_KEYWORDS, "has_method_note")
    has_assurance, assurance_kws = _check_keywords(clean_text, ASSURANCE_KEYWORDS, "has_assurance")
    in_material_matrix, matrix_kws = _check_keywords(clean_text, MATRIX_KEYWORDS, "in_material_matrix")
    
    # KPI 检测
    has_kpi_value = bool(KPI_PATTERN.search(clean_text))
    kpi_match = KPI_PATTERN.search(clean_text)
    kpi_kws = [kpi_match.group()] if kpi_match else []
    
    # 同比变化检测
    has_yoy_change, yoy_kws = _check_keywords(clean_text, YOY_KEYWORDS, "has_yoy_change")

    # 调试输出
    if debug:
        print(f"\n[DEBUG] 字段提取调试信息 - doc_id: {doc_id}, issue: {issue_name}")
        print(f"  has_policy_ref: {has_policy_ref}, 匹配关键词: {policy_kws}")
        print(f"  has_scope_statement: {has_scope_statement}, 匹配关键词: {scope_kws}")
        print(f"  has_case_study: {has_case_study}, 匹配关键词: {case_kws}")
        print(f"  has_kpi_value: {has_kpi_value}, 匹配值: {kpi_kws}")
        print(f"  has_yoy_change: {has_yoy_change}, 匹配关键词: {yoy_kws}")
        print(f"  has_method_note: {has_method_note}, 匹配关键词: {method_kws}")
        print(f"  has_assurance: {has_assurance}, 匹配关键词: {assurance_kws}")
        print(f"  in_material_matrix: {in_material_matrix}, 匹配关键词: {matrix_kws}")

    # 可核查性评分：5 个布尔字段之和，上限 5 分
    # 注意：has_assurance 不计入可核查性评分
    verifiability_score = min(
        int(has_policy_ref)
        + int(has_scope_statement)
        + int(has_case_study)
        + int(has_kpi_value)
        + int(has_yoy_change),
        5,
    )

    # 议题标准化
    normalized_issue = normalize_issue_name(issue_name)

    # LLM 字段抽取
    # risk_tone: 如果文本长度 > 50 字，调用 LLM（截断到前1000字）；否则返回默认值"展示性"
    llm_success = False  # 追踪 LLM 是否成功调用
    if use_llm and len(text) > 50:
        risk_tone = extract_risk_tone(text[:1000])
        llm_success = True  # 如果调用了 LLM 且没有异常，标记为成功
    else:
        risk_tone = "展示性"
    
    # matrix_importance: 如果在实质性矩阵中，调用 LLM；否则返回 "未出现"
    extracted_matrix_importance = "未出现"
    if use_llm and in_material_matrix:
        extracted_matrix_importance = extract_matrix_importance(text[:1000], normalized_issue)
        llm_success = True  # 如果调用了 LLM 且没有异常，标记为成功

    # spotlight 偏差标志（高重要性但低可核查性时触发）
    spotlight_bias_flag = extracted_matrix_importance == "高" and verifiability_score <= 2

    # 证据片段截取
    evidence_snippet = _extract_evidence_snippet(text, normalized_issue)

    if debug:
        print(f"  verifiability_score: {verifiability_score}")
        print(f"  risk_tone: {risk_tone}")
        print(f"  matrix_importance: {extracted_matrix_importance}")
        print(f"  spotlight_bias_flag: {spotlight_bias_flag}")
        print(f"  evidence_snippet (前100字): {evidence_snippet[:100]}...")

    # 检查 source_page 是否可能不准确（封面/目录页）
    source_page_warning = ""
    try:
        page_num = int(source_page)
        if page_num in [1, 2]:
            source_page_warning = "页码可能不准确（封面/目录页）"
    except (ValueError, TypeError):
        pass

    return {
        # 基础字段
        "doc_id": doc_id,
        "stock_code": stock_code,
        "report_year": report_year,
        "issue_name": normalized_issue,
        "source_page": source_page,
        "source_page_warning": source_page_warning,
        "evidence_snippet": evidence_snippet,
        # 规则字段
        "has_policy_ref": has_policy_ref,
        "has_scope_statement": has_scope_statement,
        "has_case_study": has_case_study,
        "has_kpi_value": has_kpi_value,
        "has_yoy_change": has_yoy_change,
        "has_method_note": has_method_note,
        "has_assurance": has_assurance,
        "in_material_matrix": in_material_matrix,
        # LLM 字段
        "risk_tone": risk_tone,
        "matrix_importance": extracted_matrix_importance,
        # 派生字段
        "verifiability_score": verifiability_score,
        "spotlight_bias_flag": spotlight_bias_flag,
        # LLM 调用状态
        "llm_success": llm_success,
    }


# ========== 批量处理 ==========

def build_doc_id_to_stock_code_mapping(parsed_dir: str) -> Dict[str, str]:
    """
    扫描 parsed_dir，建立 doc_id -> stock_code 映射

    目录结构：parsed_dir/{stock_code}/{doc_id}.md
    """
    mapping: Dict[str, str] = {}
    if not os.path.exists(parsed_dir):
        return mapping

    for stock_code_dir in os.listdir(parsed_dir):
        stock_code_path = os.path.join(parsed_dir, stock_code_dir)
        if not os.path.isdir(stock_code_path):
            continue
        for filename in os.listdir(stock_code_path):
            if filename.endswith(".md"):
                doc_id = filename[:-3]  # 去掉 .md
                mapping[doc_id] = stock_code_dir
    return mapping


def extract_year_from_doc_id(doc_id: str) -> int:
    """从 doc_id（如 2021-1212533363）中提取年份"""
    try:
        return int(doc_id.split("-")[0])
    except (ValueError, IndexError):
        return 0


def load_section_locations(path: str) -> List[Dict[str, Any]]:
    """读取 section_locations.csv"""
    records = []
    if not os.path.exists(path):
        print(f"[WARN] 文件不存在: {path}")
        return records
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sp = row.get("start_page", "").strip()
            ep = row.get("end_page", "").strip()
            try:
                start_page = int(float(sp)) if sp and sp != "-" else None
            except ValueError:
                start_page = None
            try:
                end_page = int(float(ep)) if ep and ep != "-" else None
            except ValueError:
                end_page = None

            records.append(
                {
                    "doc_id": row.get("doc_id", "").strip(),
                    "issue_name": row.get("issue_name", "").strip(),
                    "section_title": row.get("section_title", "").strip(),
                    "start_page": start_page,
                    "end_page": end_page,
                    "confidence": row.get("confidence", "").strip(),
                }
            )
    return records


def extract_from_sections(
    section_locations_path: str,
    parsed_dir: str,
    output_path: str,
) -> None:
    """
    主处理流程：
    section_locations.csv + markdown 文件 -> 规则匹配 -> 评分计算 -> base_records.csv
    """
    sections = load_section_locations(section_locations_path)
    doc_id_to_stock = build_doc_id_to_stock_code_mapping(parsed_dir)

    print(f"[INFO] 加载 {len(sections)} 条 section_locations 记录")
    print(f"[INFO] 建立 {len(doc_id_to_stock)} 个 doc_id -> stock_code 映射")

    results: List[Dict[str, Any]] = []
    processed_count = 0

    for sec in sections:
        doc_id = sec["doc_id"]
        issue_name = sec["issue_name"]
        start_page = sec["start_page"]
        end_page = sec["end_page"]

        if not doc_id:
            continue

        # 查找 stock_code
        stock_code = doc_id_to_stock.get(doc_id, "")
        report_year = extract_year_from_doc_id(doc_id)

        # 读取 markdown 文件
        if stock_code:
            md_path = os.path.join(parsed_dir, stock_code, f"{doc_id}.md")
        else:
            md_path = None

        if md_path and os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            # markdown 文件不存在，跳过
            continue

        # 截取页码范围的文本（如果 content 中有页码标记则截取，否则用整篇）
        # 注意：当前 markdown 文件没有页码标记，因此直接用整篇
        page_text = content

        # 提取字段（source_page 使用 start_page）
        source_page = start_page if start_page is not None else 0

        record = extract_rule_fields(
            text=page_text,
            issue_name=issue_name,
            source_page=source_page,
            doc_id=doc_id,
            stock_code=stock_code,
            report_year=report_year,
            matrix_importance=None,  # 预留，待 LLM 补充
        )
        results.append(record)
        processed_count += 1

    print(f"[INFO] 成功处理 {processed_count} 条记录")

    # 输出结果
    if results:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 定义用户要求的输出字段顺序
        output_fieldnames = [
            'company_code', 'report_year', 'issue_name', 'anchor_type', 
            'source_page', 'evidence_snippet',
            'has_policy_ref', 'has_scope_statement', 'has_case_study',
            'risk_tone', 'has_kpi_value', 'has_yoy_change', 
            'has_method_note', 'has_assurance',
            'verifiability_score', 'spotlight_bias_flag'
        ]
        
        # 转换结果格式
        output_results = []
        for record in results:
            output_record = {
                'company_code': record['stock_code'],
                'report_year': record['report_year'],
                'issue_name': record['issue_name'],
                'anchor_type': 'narrative',  # 默认为 narrative
                'source_page': record['source_page'],
                'evidence_snippet': record['evidence_snippet'],
                'has_policy_ref': record['has_policy_ref'],
                'has_scope_statement': record['has_scope_statement'],
                'has_case_study': record['has_case_study'],
                'risk_tone': record['risk_tone'],
                'has_kpi_value': record['has_kpi_value'],
                'has_yoy_change': record['has_yoy_change'],
                'has_method_note': record['has_method_note'],
                'has_assurance': record['has_assurance'],
                'verifiability_score': record['verifiability_score'],
                'spotlight_bias_flag': record['spotlight_bias_flag']
            }
            output_results.append(output_record)
        
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerows(output_results)
        print(f"[OK] 已生成 {len(output_results)} 条记录 -> {output_path}")
    else:
        print("[WARN] 未生成任何记录，请检查输入数据路径是否正确。")


# ========== 测试代码 ==========

def _run_tests():
    """使用模拟文本验证抽取逻辑"""
    print("=" * 50)
    print("开始运行测试...")
    print("=" * 50)

    # 测试用例 1：包含多个规则字段
    test_text_1 = """
    我行制定《绿色金融管理办法》，明确绿色信贷统计范围涵盖境内分行。
    2023年绿色信贷余额达386亿元，较上年增长15%。详见编制基础说明（第45页）。
    """

    result_1 = extract_rule_fields(
        text=test_text_1,
        issue_name="绿色金融",
        source_page=45,
        doc_id="TEST_001",
        stock_code="601398",
        report_year=2023,
        matrix_importance="高",
    )

    assert result_1["has_policy_ref"] is True, "应检测到管理办法"
    assert result_1["has_scope_statement"] is True, "应检测到范围/境内分行"
    assert result_1["has_kpi_value"] is True, "应检测到 386亿元"
    assert result_1["has_yoy_change"] is True, "应检测到较上年"
    assert result_1["has_method_note"] is True, "应检测到编制基础"
    assert result_1["has_assurance"] is False, "不应检测到鉴证"
    assert result_1["in_material_matrix"] is False, "不应检测到矩阵"
    assert result_1["verifiability_score"] == 5, f"分数应为5，实际{result_1['verifiability_score']}"
    assert result_1["spotlight_bias_flag"] is False, "高重要性但5分不应触发偏差"
    assert result_1["issue_name"] == "绿色信贷/绿色金融", f"议题映射错误: {result_1['issue_name']}"
    assert result_1["source_page"] == 45, "页码应保留"
    assert len(result_1["evidence_snippet"]) > 0, "应有证据片段"
    print("[PASS] 测试用例 1 通过（高可核查性）")

    # 测试用例 2：低可核查性但无矩阵信息 -> spotlight_bias_flag 应为 False
    test_text_2 = "本行高度重视绿色金融发展，积极推动绿色转型。"

    result_2 = extract_rule_fields(
        text=test_text_2,
        issue_name="绿色金融",
        source_page=3,
        doc_id="TEST_002",
        stock_code="600000",
        report_year=2022,
        matrix_importance="高",
    )

    assert result_2["has_policy_ref"] is False
    assert result_2["has_scope_statement"] is False
    assert result_2["has_case_study"] is False
    assert result_2["has_kpi_value"] is False
    assert result_2["has_yoy_change"] is False
    assert result_2["has_method_note"] is False
    assert result_2["verifiability_score"] == 0
    assert result_2["in_material_matrix"] is False, "文本不含矩阵关键词"
    assert result_2["matrix_importance"] == "未出现", "无矩阵信息时应为未出现"
    assert result_2["spotlight_bias_flag"] is False, "矩阵重要性为未出现时不应触发偏差"
    print("[PASS] 测试用例 2 通过（无矩阵信息）")

    # 测试用例 3：包含案例与矩阵
    test_text_3 = """
    专栏：绿色金融创新实践
    本行将绿色金融列为实质性议题，纳入重要性矩阵评估。
    第三方审计机构对数据进行了鉴证。
    """

    result_3 = extract_rule_fields(
        text=test_text_3,
        issue_name="公司治理",
        source_page=12,
        doc_id="TEST_003",
        stock_code="601988",
        report_year=2024,
        matrix_importance="中",
    )

    assert result_3["has_case_study"] is True, "应检测到专栏/实践"
    assert result_3["in_material_matrix"] is True, "应检测到实质性议题/重要性矩阵"
    assert result_3["has_assurance"] is True, "应检测到鉴证"
    assert result_3["issue_name"] == "公司治理/风险管理", "议题映射应为 公司治理/风险管理"
    assert result_3["matrix_importance"] == "未出现", "LLM 未实现时返回未出现"
    print("[PASS] 测试用例 3 通过（案例与矩阵）")

    # 测试用例 4：KPI 正则匹配多种单位
    test_text_4 = "服务小微企业 12.5 万户，贷款余额 3,000 万元，占比 15%。"
    result_4 = extract_rule_fields(
        text=test_text_4,
        issue_name="普惠金融",
        source_page=20,
        doc_id="TEST_004",
        stock_code="601169",
        report_year=2023,
    )
    assert result_4["has_kpi_value"] is True, "应匹配到 12.5 万户 / 3,000 万元 / 15%"
    print("[PASS] 测试用例 4 通过（KPI 正则匹配）")

    # 测试用例 5：issue_name 映射
    test_cases = [
        ("风险管理", "公司治理/风险管理"),
        ("绿色金融", "绿色信贷/绿色金融"),
        ("消费者权益保护", "消费者权益保护"),
        ("普惠金融", "普惠金融"),
        ("员工权益", "员工权益"),
        ("乡村振兴", "员工权益"),
        ("信息", "信息安全与隐私保护"),
    ]
    for raw, expected in test_cases:
        assert normalize_issue_name(raw) == expected, f"映射错误: {raw} -> {normalize_issue_name(raw)}"
    print("[PASS] 测试用例 5 通过（issue_name 映射）")

    print("=" * 50)
    print("[DONE] 全部测试通过！")
    print("=" * 50)


def main():
    """
    命令行入口
    用法:
      python src/extract/field_extractor.py
      python src/extract/field_extractor.py --test
    """
    import argparse

    parser = argparse.ArgumentParser(description="银行 ESG 报告规则字段抽取")
    parser.add_argument(
        "--sections",
        default=DEFAULT_SECTION_LOCATIONS,
        help="section_locations.csv 路径",
    )
    parser.add_argument(
        "--parsed-dir", default=DEFAULT_PARSED_DIR, help="markdown 文件所在目录",
    )
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT, help="输出 CSV 路径",
    )
    parser.add_argument("--test", action="store_true", help="运行测试")
    args = parser.parse_args()

    if args.test:
        _run_tests()
        return

    # 默认也先运行测试
    _run_tests()

    # 然后执行批量抽取
    extract_from_sections(
        section_locations_path=args.sections,
        parsed_dir=args.parsed_dir,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
