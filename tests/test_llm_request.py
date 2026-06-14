#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 LLM 调用"""
import requests
import time

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "huihui_ai/deepseek-r1-abliterated:1.5b"
TIMEOUT = 120

# 测试用 prompt
prompt = """你是一位资深的ESG（环境、社会、治理）报告分析专家。你的任务是判断银行ESG报告中某段文字的风险语调。

## 分类标准

【展示性】
- 只描述成绩、目标、承诺、正面数据
- 不提及任何困难、风险、挑战或改进空间
- 例子："我行绿色信贷余额达386亿元，较上年增长15%"

## 输出要求

请只输出以下JSON格式，不要任何解释：
{"risk_tone": "展示性", "reason": "简要说明理由"}

## 待分析段落

我行绿色信贷余额达386亿元，较上年增长15%"""

print(f"Prompt length: {len(prompt)} chars")

data = {
    "model": OLLAMA_MODEL,
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.1,
        "max_tokens": 500,
    },
}

print("Making request...")
start = time.time()
try:
    response = requests.post(OLLAMA_API_URL, json=data, timeout=TIMEOUT)
    elapsed = time.time() - start
    print(f"Response received! Status: {response.status_code}, Time: {elapsed:.1f}s")
    if response.status_code == 200:
        result = response.json()
        print(f"Response text: {result.get('response', '')[:200]}")
except Exception as e:
    print(f"Request failed: {e}")