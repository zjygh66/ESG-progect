
"""
字段抽取脚本 - 规则字段部分
输入：解析后的文本片段 + 页码 + 议题信息
输出：包含所有规则字段的字典
"""

import re
from typing import Dict, Any, Optional


# ========== 关键词库 ==========

POLICY_KEYWORDS = ["办法", "指引", "制度", "管理办法", "实施细则", "暂行规定"]
SCOPE_KEYWORDS = ["范围", "口径", "境内", "不含", "含/不含", "统计范围", "管理范围"]
CASE_KEYWORDS = ["案例", "专栏", "实践", "典型案例", "案例分享"]
YOY_KEYWORDS = ["同比", "较上年", "较年初", "环比", "较上期", "同比增长", "同比下降"]
METHOD_KEYWORDS = ["编制基础", "指标释义", "注：", "①", "②", "¹", "²", "附录", "指标说明"]
ASSURANCE_KEYWORDS = ["鉴证", "第三方", "独立验证", "审计", "审验", "保证声明"]
MATRIX_KEYWORDS = ["实质性议题", "重要性矩阵", "双重重要性", "实质性分析", "重要性评估"]


# ========== 正则模式 ==========

# 匹配数字+单位（如 386亿元、1,234.56万元、85%）
KPI_PATTERN = re.compile(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*[亿万千百十]?[元户人%个次条件]+')

# 匹配页码引用（如 见第45页、详见P23）
PAGE_REF_PATTERN = re.compile(r'(?:见|详见|参考|附)[第Pp]?\s*\d+\s*[页页码]')


def extract_rule_fields(text: str, issue_name: str, page: int, 
                       doc_id: str, company_code: str, report_year: int,
                       anchor_type: str) -> Dict[str, Any]:
    """
    从文本片段中抽取所有规则字段
    
    参数:
        text: 解析后的文本内容
        issue_name: 议题名称（6个之一）
        page: 页码
        doc_id: 文档ID
        company_code: 股票代码
        report_year: 报告年份
        anchor_type: 锚点类型（matrix/narrative/kpi）
    
    返回:
        包含所有字段的字典
    """
    
    # 清理文本（去除多余空格，方便匹配）
    clean_text = text.replace('\n', ' ').replace('\t', ' ')
    
    result = {
        # 基础字段（外部传入）
        "doc_id": doc_id,
        "company_code": company_code,
        "report_year": report_year,
        "issue_name": issue_name,
        "anchor_type": anchor_type,
        "source_page": page,
        "evidence_snippet": _extract_snippet(text, 150),  # 截取前150字作为证据
        
        # A. 矩阵字段
        "in_material_matrix": _check_keywords(clean_text, MATRIX_KEYWORDS),
        "matrix_importance": _determine_importance(clean_text, issue_name),
        
        # B. 正文字段
        "has_policy_ref": _check_keywords(clean_text, POLICY_KEYWORDS),
        "has_scope_statement": _check_keywords(clean_text, SCOPE_KEYWORDS),
        "has_case_study": _check_keywords(clean_text, CASE_KEYWORDS),
        # risk_tone 由 LLM 判断，这里先留空或标记
        "risk_tone": None,
        
        # C. 绩效表字段
        "has_kpi_value": _has_kpi_value(clean_text),
        "kpi_value": _extract_kpi_value(clean_text) if _has_kpi_value(clean_text) else None,
        "has_yoy_change": _check_keywords(clean_text, YOY_KEYWORDS),
        "has_method_note": _check_keywords(clean_text, METHOD_KEYWORDS),
        "has_assurance": _check_keywords(clean_text, ASSURANCE_KEYWORDS),
    }
    
    # D. 派生字段计算
    result["verifiability_score"] = _calculate_score(result)
    result["spotlight_bias_flag"] = _check_spotlight_bias(result)
    
    return result


# ========== 辅助函数 ==========

def _check_keywords(text: str, keywords: list) -> bool:
    """检查文本中是否包含任一关键词"""
    return any(kw in text for kw in keywords)


def _extract_snippet(text: str, max_length: int = 150) -> str:
    """截取文本片段作为证据，优先截取包含关键词的句子"""
    sentences = re.split(r'[。！？；]', text)
    for sent in sentences:
        if len(sent.strip()) > 10:  # 跳过太短的句子
            return sent.strip()[:max_length]
    return text[:max_length].strip()


def _has_kpi_value(text: str) -> bool:
    """检查是否有量化数据（数字+单位）"""
    return bool(KPI_PATTERN.search(text))


def _extract_kpi_value(text: str) -> Optional[str]:
    """抽取第一个匹配的数值+单位"""
    match = KPI_PATTERN.search(text)
    return match.group(0) if match else None


def _determine_importance(text: str, issue_name: str) -> str:
    """
    简单判断议题重要性（基于关键词位置）
    注意：这个很粗糙，准确判断需要 LLM 或更复杂的规则
    """
    # 如果议题名出现在"高"或"重要"附近，判断为高
    # 这里先做个简单版本，后续可以优化
    if issue_name in text:
        # 检查前后50字是否有"高"、"重要"、"优先"等词
        idx = text.find(issue_name)
        context = text[max(0, idx-50):min(len(text), idx+50)]
        if any(w in context for w in ["高", "重要", "优先", "核心", "关键"]):
            return "高"
        elif any(w in context for w in ["中", "一般", "关注"]):
            return "中"
        else:
            return "低"
    return "未出现"


def _calculate_score(record: Dict[str, Any]) -> int:
    """
    计算可核查性评分 (0-5)
    基于 B、C 组布尔字段
    """
    score = 0
    
    # B组字段（每个1分）
    if record.get("has_policy_ref"): score += 1
    if record.get("has_scope_statement"): score += 1
    if record.get("has_case_study"): score += 1
    
    # C组字段（每个1分，但总分不超过5）
    if record.get("has_kpi_value"): score += 1
    if record.get("has_yoy_change"): score += 1
    if record.get("has_method_note"): score += 1
    if record.get("has_assurance"): score += 1
    
    return min(score, 5)  # 最高5分


def _check_spotlight_bias(record: Dict[str, Any]) -> bool:
    """
    检查"言行偏离"：高重要性但低可核查性
    """
    importance = record.get("matrix_importance", "")
    score = record.get("verifiability_score", 0)
    return importance == "高" and score <= 2


# ========== 测试 ==========

if __name__ == "__main__":
    # 测试用例：模拟一段文本
    test_text = """
    我行制定《绿色金融管理办法》，明确绿色信贷统计范围涵盖境内分行。
    2023年绿色信贷余额达386亿元，较上年增长15%。
    详见编制基础说明（第45页）。
    """
    
    result = extract_rule_fields(
        text=test_text,
        issue_name="绿色信贷/绿色金融",
        page=45,
        doc_id="ICBC_2023_GreenCredit",
        company_code="601398",
        report_year=2023,
        anchor_type="narrative"
    )
    
    # 打印结果
    for key, value in result.items():
        print(f"{key}: {value}")
    
    # 验证关键字段
    assert result["has_policy_ref"] == True, "应该检测到管理办法"
    assert result["has_scope_statement"] == True, "应该检测到范围"
    assert result["has_kpi_value"] == True, "应该检测到386亿元"
    assert result["kpi_value"] == "386亿元", "应该提取出具体数值"
    assert result["has_yoy_change"] == True, "应该检测到较上年"
    assert result["verifiability_score"] >= 3, "分数应该较高"
    
    print("\n✅ 所有测试通过！")