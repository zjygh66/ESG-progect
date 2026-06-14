"""
LLM 字段抽取测试脚本

测试 extract_risk_tone 和 extract_matrix_importance 函数的功能正确性。

作者：C 同学
日期：2026-06-14
"""

import sys
import os

# 添加 src/extract 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'extract'))

from llm_extractor import extract_risk_tone, extract_matrix_importance


def test_risk_tone():
    """
    测试风险语调抽取函数
    """
    print("=" * 60)
    print("测试 1：风险语调抽取 (extract_risk_tone)")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "展示性文本",
            "text": "我行绿色信贷余额达386亿元，较上年增长15%，实现了预期目标。",
            "expected": "展示性",
        },
        {
            "name": "平衡性文本",
            "text": "虽然绿色信贷增长15%，但部分项目环境效益评估仍不完善，需加强管理。",
            "expected": "平衡（含挑战）",
        },
        {
            "name": "风险透明文本",
            "text": "报告期内，我行因消费者权益保护问题收到监管罚单3张，已制定整改方案。",
            "expected": "风险透明（含负面）",
        },
    ]
    
    passed = 0
    for i, case in enumerate(test_cases, 1):
        result = extract_risk_tone(case["text"])
        status = "PASS" if result == case["expected"] else f"FAIL (期望: {case['expected']}, 实际: {result})"
        print(f"\n[{i}] {case['name']}:")
        print(f"   文本: {case['text']}")
        print(f"   结果: {result}")
        print(f"   状态: {status}")
        if result == case["expected"]:
            passed += 1
    
    print(f"\n风险语调测试: {passed}/{len(test_cases)} 通过")
    return passed == len(test_cases)


def test_matrix_importance():
    """
    测试矩阵重要性抽取函数
    """
    print("\n" + "=" * 60)
    print("测试 2：矩阵重要性抽取 (extract_matrix_importance)")
    print("=" * 60)
    
    # 矩阵描述文本
    matrix_text = """
    根据实质性评估结果，我行确定了以下重要议题：
    
    【高度重要议题】（矩阵右上角区域）
    - 绿色金融：对公司战略和利益相关方都至关重要，列为优先关注领域
    - 风险管理：作为银行核心竞争力，需要持续强化
    
    【中等重要议题】（矩阵中部区域）
    - 消费者权益保护：重要但优先级相对较低
    - 普惠金融：关注但资源有限
    
    【低度重要议题】（矩阵左下角区域）
    - 员工权益：一般关注
    """
    
    test_cases = [
        {"name": "绿色金融", "issue": "绿色金融", "expected": "高"},
        {"name": "风险管理", "issue": "风险管理", "expected": "高"},
        {"name": "消费者权益保护", "issue": "消费者权益保护", "expected": "中"},
        {"name": "普惠金融", "issue": "普惠金融", "expected": "中"},
        {"name": "员工权益", "issue": "员工权益", "expected": "低"},
        {"name": "未提及议题", "issue": "信息安全", "expected": "未出现"},
    ]
    
    passed = 0
    for i, case in enumerate(test_cases, 1):
        result = extract_matrix_importance(matrix_text, case["issue"])
        status = "PASS" if result == case["expected"] else f"FAIL (期望: {case['expected']}, 实际: {result})"
        print(f"\n[{i}] {case['name']}:")
        print(f"   议题: {case['issue']}")
        print(f"   结果: {result}")
        print(f"   状态: {status}")
        if result == case["expected"]:
            passed += 1
    
    print(f"\n矩阵重要性测试: {passed}/{len(test_cases)} 通过")
    return passed == len(test_cases)


def test_edge_cases():
    """
    测试边界情况
    """
    print("\n" + "=" * 60)
    print("测试 3：边界情况测试")
    print("=" * 60)
    
    # 空文本测试
    print("\n[1] 空文本测试:")
    result = extract_risk_tone("")
    print(f"   风险语调(空文本): {result}")
    
    # 短文本测试
    print("\n[2] 短文本测试:")
    result = extract_risk_tone("简短文本")
    print(f"   风险语调(短文本): {result}")
    
    # 超长文本测试（应该被截断）
    print("\n[3] 超长文本测试:")
    long_text = "测试" * 5000
    result = extract_risk_tone(long_text)
    print(f"   风险语调(超长文本): {result}")
    
    # 议题名称为空
    print("\n[4] 空议题名称测试:")
    result = extract_matrix_importance("测试文本", "")
    print(f"   矩阵重要性(空议题): {result}")
    
    print("\n边界情况测试完成")
    return True


def main():
    """
    主测试函数
    """
    print("\n" + "=" * 60)
    print("LLM 字段抽取模块测试")
    print("=" * 60)
    print("\n注意：如果 Ollama 服务未启动，将使用规则保底模式")
    print("=" * 60)
    
    # 运行所有测试
    results = [
        test_risk_tone(),
        test_matrix_importance(),
        test_edge_cases(),
    ]
    
    print("\n" + "=" * 60)
    if all(results):
        print("所有测试通过！")
    else:
        print("部分测试未通过！")
    print("=" * 60)


if __name__ == "__main__":
    main()
