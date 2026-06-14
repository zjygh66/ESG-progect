#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""快速 LLM 测试"""

import requests
import time
import sys

print("测试 Ollama LLM...", flush=True)

try:
    start = time.time()
    r = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'huihui_ai/deepseek-r1-abliterated:1.5b',
            'prompt': 'Hi',
            'stream': False
        },
        timeout=30
    )
    elapsed = time.time() - start

    print(f"耗时: {elapsed:.1f}秒", flush=True)
    print(f"状态: {r.status_code}", flush=True)
    print(f"响应: {r.json().get('response', '')[:50]}", flush=True)
except Exception as e:
    print(f"失败: {e}", flush=True)
    sys.exit(1)
