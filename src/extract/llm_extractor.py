"""
LLM 字段抽取模块 - 基于本地 Ollama 模型

调用本地 Ollama HTTP API 抽取风险语调(risk_tone)和矩阵重要性(matrix_importance)字段。
支持 JSON 和纯文本两种输出格式解析，失败时返回规则保底值。

作者：陈欣悦
日期：2026-06-14
"""

import json
import re
import requests
from typing import Optional


# ========== Ollama 配置常量 ==========
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "huihui_ai/deepseek-r1-abliterated:1.5b"
TIMEOUT = 120  # 请求超时时间（秒）
MAX_RETRIES = 2  # 最大重试次数


# ========== Prompt 模板路径 ==========
PROMPTS_DIR = "prompts"
RISK_TONE_PROMPT_FILE = f"{PROMPTS_DIR}/risk_tone.txt"
MATRIX_IMPORTANCE_PROMPT_FILE = f"{PROMPTS_DIR}/matrix_importance.txt"


def _load_prompt_template(filepath: str) -> str:
    """
    加载 prompt 模板文件
    
    参数:
        filepath: 模板文件路径
    
    返回:
        str: 模板内容，失败返回空字符串
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[WARN] 无法加载模板文件 {filepath}: {e}")
        return ""


def _call_ollama(prompt: str, model: str = OLLAMA_MODEL) -> Optional[str]:
    """
    调用 Ollama HTTP API
    
    参数:
        prompt: 输入提示词
        model: 模型名称
    
    返回:
        str: 模型响应内容，失败返回 None
    """
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,  # 非流式输出
        "options": {
            "temperature": 0.1,  # 低温度，更确定性输出
            "max_tokens": 500,
        },
    }
    
    print(f"[DEBUG] Calling Ollama with model: {model}", flush=True)
    print(f"[DEBUG] Prompt length: {len(prompt)} chars", flush=True)
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(OLLAMA_API_URL, json=data, timeout=TIMEOUT)
            print(f"[DEBUG] Ollama response status: {response.status_code}", flush=True)
            
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get("response", "").strip()
            print(f"[DEBUG] Ollama response received: {len(response_text)} chars", flush=True)
            
            return response_text
        
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] Ollama ConnectionError on attempt {attempt + 1}", flush=True)
            if attempt < MAX_RETRIES:
                print(f"[WARN] Ollama 连接失败，重试 {attempt + 1}/{MAX_RETRIES}", flush=True)
                continue
            print("[ERROR] Ollama 服务未启动或无法连接", flush=True)
            return None
        
        except requests.exceptions.Timeout:
            print(f"[ERROR] Ollama Timeout on attempt {attempt + 1}", flush=True)
            if attempt < MAX_RETRIES:
                print(f"[WARN] 请求超时，重试 {attempt + 1}/{MAX_RETRIES}", flush=True)
                continue
            print("[ERROR] 请求超时", flush=True)
            return None
        
        except Exception as e:
            print(f"[ERROR] 调用 Ollama 失败: {e}", flush=True)
            return None


def _parse_json_output(output: str) -> Optional[dict]:
    """
    解析模型输出，提取 JSON 内容
    
    参数:
        output: 模型原始输出
    
    返回:
        dict: 解析后的 JSON 对象，失败返回 None
    """
    # 尝试提取 JSON 对象
    json_pattern = r"\{.*?\}"
    matches = re.findall(json_pattern, output, re.DOTALL)
    
    if matches:
        # 取最后一个匹配的 JSON（可能前面有多余内容）
        for match in reversed(matches):
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    
    return None


def _fallback_risk_tone(text: str) -> str:
    """
    规则保底：基于关键词判断风险语调
    
    参数:
        text: 待分析文本
    
    返回:
        str: "展示性" / "平衡（含挑战）" / "风险透明（含负面）"
    """
    # 负面关键词列表
    negative_keywords = [
        "罚单", "处罚", "违规", "投诉", "事故", "问题",
        "不足", "整改", "缺陷", "风险", "挑战", "困难"
    ]
    
    # 转折关键词
    transition_keywords = ["但是", "但", "然而", "尽管", "虽然"]
    
    text_lower = text.lower()
    
    # 检查是否有负面内容
    has_negative = any(kw in text_lower for kw in negative_keywords)
    has_transition = any(kw in text_lower for kw in transition_keywords)
    
    if has_negative:
        # 如果明确提到负面事件（罚单、处罚、事故等），归为风险透明
        if any(kw in text_lower for kw in ["罚单", "处罚", "事故", "违规"]):
            return "风险透明（含负面）"
        # 如果有负面词但也有转折，归为平衡
        if has_transition:
            return "平衡（含挑战）"
        return "风险透明（含负面）"
    
    if has_transition:
        return "平衡（含挑战）"
    
    return "展示性"


def _fallback_matrix_importance(text: str, issue_name: str) -> str:
    """
    规则保底：基于关键词判断矩阵重要性
    
    参数:
        text: 矩阵描述文本
        issue_name: 议题名称
    
    返回:
        str: "高" / "中" / "低" / "未出现"
    """
    # 检查议题是否在文本中出现
    if issue_name not in text:
        return "未出现"
    
    # 高重要性关键词
    high_keywords = ["高度重要", "关键议题", "优先关注", "核心", "重要性高"]
    # 中等重要性关键词
    medium_keywords = ["重要", "关注", "重视", "一般重要"]
    # 低重要性关键词
    low_keywords = ["一般", "低度关注", "较低", "不重要"]
    
    text_lower = text.lower()
    issue_lower = issue_name.lower()
    
    # 在议题附近查找关键词（前后各50字）
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


def extract_risk_tone(text: str) -> str:
    """
    抽取风险语调字段
    
    调用 Ollama 模型进行分类，失败时使用规则保底。
    
    参数:
        text: 待分析文本
    
    返回:
        "展示性" / "平衡（含挑战）" / "风险透明（含负面）"
    """
    # 文本预处理：截断到合理长度
    text = text[:2000].strip()
    if not text:
        return "展示性"
    
    # 加载 prompt 模板
    template = _load_prompt_template(RISK_TONE_PROMPT_FILE)
    if not template:
        print("[WARN] 无法加载风险语调模板，使用规则保底")
        return _fallback_risk_tone(text)
    
    # 填充模板
    prompt = template.replace("{text}", text)
    
    # 调用 Ollama
    response = _call_ollama(prompt)
    if not response:
        print("[WARN] Ollama 调用失败，使用规则保底")
        return _fallback_risk_tone(text)
    
    # 有效值列表
    valid_values = ["展示性", "平衡（含挑战）", "风险透明（含负面）"]
    
    # 解析输出
    result = _parse_json_output(response)
    if result and "risk_tone" in result:
        risk_tone = result["risk_tone"]
        # 验证返回值是否有效
        if risk_tone in valid_values:
            return risk_tone
    
    # 解析失败，尝试从纯文本中提取
    for valid in valid_values:
        if valid in response:
            return valid
    
    # 最终保底
    print("[WARN] 解析失败，使用规则保底")
    return _fallback_risk_tone(text)


def extract_matrix_importance(text: str, issue_name: str) -> str:
    """
    抽取议题重要性（实质性矩阵重要性）
    
    调用 Ollama 模型进行分类，失败时使用规则保底。
    
    参数:
        text: 矩阵描述文本
        issue_name: 议题名称
    
    返回:
        "高" / "中" / "低" / "未出现"
    """
    # 文本预处理：截断到合理长度
    text = text[:2000].strip()
    if not text or not issue_name:
        return "未出现"
    
    # 检查是否为目录页或封面页（不调用LLM，直接返回"未出现"）
    cover_page_keywords = ["目录", "CONTENTS", "关于本报告", "报告说明", "报告概述", "报告简介"]
    for keyword in cover_page_keywords:
        if keyword in text:
            print(f"[DEBUG] 检测到目录/封面页关键词 '{keyword}'，直接返回 '未出现'")
            return "未出现"
    
    # 加载 prompt 模板
    template = _load_prompt_template(MATRIX_IMPORTANCE_PROMPT_FILE)
    if not template:
        print("[WARN] 无法加载矩阵重要性模板，使用规则保底")
        return _fallback_matrix_importance(text, issue_name)
    
    # 填充模板
    prompt = template.replace("{issue}", issue_name).replace("{text}", text)
    
    # 调用 Ollama
    response = _call_ollama(prompt)
    if not response:
        print("[WARN] Ollama 调用失败，使用规则保底")
        return _fallback_matrix_importance(text, issue_name)
    
    # 验证返回值是否有效
    valid_values = ["高", "中", "低", "未出现"]
    
    # 解析输出
    result = _parse_json_output(response)
    if result and "importance" in result:
        importance = result["importance"]
        if importance in valid_values:
            return importance
    
    # 解析失败，尝试从纯文本中提取
    for valid in valid_values:
        if valid in response:
            return valid
    
    # 最终保底
    print("[WARN] 解析失败，使用规则保底")
    return _fallback_matrix_importance(text, issue_name)


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("LLM Extractor 测试")
    print("=" * 50)
    
    # 测试风险语调
    test_texts = [
        ("展示性测试", "我行绿色信贷余额达386亿元，较上年增长15%，实现了预期目标。"),
        ("平衡性测试", "虽然绿色信贷增长15%，但部分项目环境效益评估仍不完善，需加强管理。"),
        ("风险透明测试", "报告期内，我行因消费者权益保护问题收到监管罚单3张，已制定整改方案。"),
    ]
    
    print("\n--- 风险语调测试 ---")
    for name, text in test_texts:
        result = extract_risk_tone(text)
        print(f"{name}: {result}")
    
    # 测试矩阵重要性
    matrix_text = """
    根据实质性评估结果，绿色金融被列为高度重要议题，位于矩阵右上角区域。
    风险管理被列为中等重要议题。
    员工权益关注度较低。
    """
    
    print("\n--- 矩阵重要性测试 ---")
    test_issues = ["绿色金融", "风险管理", "员工权益", "信息安全"]
    for issue in test_issues:
        result = extract_matrix_importance(matrix_text, issue)
        print(f"{issue}: {result}")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
