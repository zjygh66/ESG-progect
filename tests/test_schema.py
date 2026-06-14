"""
tests/test_schema.py
Schema 验证测试
"""

import sys
from pathlib import Path

# 把项目根目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.esg import IssueRecord, calculate_verifiability_score, check_spotlight_bias


def test_schema_validation():
    """测试 Schema 能正常创建和验证"""
    
    # 模拟数据：工商银行2023年绿色信贷议题
    sample = {
        "doc_id": "ICBC_2023_GreenCredit",
        "company_code": "601398",
        "report_year": 2023,
        "issue_name": "绿色信贷/绿色金融",
        "anchor_type": "kpi",
        "source_page": 45,
        "evidence_snippet": "绿色信贷余额386亿元，较上年增长15%。详见《绿色金融管理办法》。",
        
        # A. 矩阵
        "in_material_matrix": True,
        "matrix_importance": "高",
        
        # B. 正文
        "has_policy_ref": True,
        "has_scope_statement": True,
        "has_case_study": False,
        "risk_tone": None,  # LLM字段预留
        
        # C. 绩效表
        "has_kpi_value": True,
        "kpi_value": "386亿元",
        "has_yoy_change": True,
        "has_method_note": True,
        "has_assurance": False,
        
        # D. 派生
        "verifiability_score": 4,
        "spotlight_bias_flag": False,
        "score_by_year": None,
        "trend_5yr": None
    }
    
    # 创建记录
    record = IssueRecord(**sample)
    
    # 验证关键字段
    assert record.company_code == "601398"
    assert record.source_page == 45
    assert record.evidence_snippet == "绿色信贷余额386亿元，较上年增长15%。详见《绿色金融管理办法》。"
    assert record.verifiability_score == 4
    assert record.spotlight_bias_flag == False
    
    print("✅ Schema 验证通过")
    print(f"   文档: {record.doc_id}")
    print(f"   页码: {record.source_page}")
    print(f"   证据: {record.evidence_snippet[:30]}...")
    print(f"   评分: {record.verifiability_score}/5")
    
    return record


def test_score_calculation():
    """测试评分计算函数"""
    
    # 创建一个低分记录
    low_record = IssueRecord(
        doc_id="TEST_001",
        company_code="000001",
        report_year=2023,
        issue_name="绿色信贷/绿色金融",
        anchor_type="narrative",
        source_page=10,
        evidence_snippet="测试文本",
        in_material_matrix=True,
        matrix_importance="高",
        has_policy_ref=False,
        has_scope_statement=False,
        has_case_study=False,
        has_kpi_value=False,
        has_yoy_change=False,
        has_method_note=False,
        has_assurance=False,
        verifiability_score=0,
        spotlight_bias_flag=True
    )
    
    # 验证 spotlight_bias
    assert check_spotlight_bias(low_record) == True
    print("✅ 言行偏离检测正确（高重要性+低评分）")
    
    # 验证评分计算
    calculated = calculate_verifiability_score(low_record)
    assert calculated == 0
    print(f"✅ 评分计算正确: {calculated}/5")


def test_error_validation():
    """测试错误数据会被拦截"""
    
    try:
        # 错误的年份
        bad_record = IssueRecord(
            doc_id="TEST",
            company_code="000001",
            report_year=2020,  # ❌ 超出范围
            issue_name="绿色信贷/绿色金融",
            anchor_type="kpi",
            source_page=1,
            evidence_snippet="测试",
            in_material_matrix=True,
            matrix_importance="高",
            has_policy_ref=True,
            has_scope_statement=True,
            has_case_study=True,
            has_kpi_value=True,
            has_yoy_change=True,
            has_method_note=True,
            has_assurance=True,
            verifiability_score=4,
            spotlight_bias_flag=False
        )
        assert False, "应该报错"
    except Exception as e:
        print(f"✅ 正确拦截错误数据: {type(e).__name__}")


if __name__ == "__main__":
    print("=" * 50)
    print("Schema 测试开始")
    print("=" * 50)
    
    test_schema_validation()
    print()
    test_score_calculation()
    print()
    test_error_validation()
    
    print()
    print("=" * 50)
    print("✅ 所有测试通过！")
    print("=" * 50)