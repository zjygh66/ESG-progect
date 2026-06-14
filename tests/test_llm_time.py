#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 LLM 响应时间"""

import requests
import time

print("测试 Ollama LLM 响应时间...")
print(f"开始时间: {time.strftime('%H:%M:%S')}")

try:
    start = time.time()
    r = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'huihui_ai/deepseek-r1-abliterated:1.5b',
            'prompt': 'Say hello in 5 words',
            'stream': False
        },
        timeout=60
    )
    elapsed = time.time() - start
    
    print(f"耗时: {elapsed:.1f}秒")
    print(f"状态: {r.status_code}")
    print(f"响应: {r.json().get('response', '')[:100]}")
except requests.exceptions.Timeout:
    print("请求超时！")
except Exception as e:
    print(f"请求失败: {e}")
