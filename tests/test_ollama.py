#!/usr/bin/env python
"""测试 Ollama 连接"""
import requests
import time
import sys

print("测试 Ollama 连接...")
print(f"URL: http://localhost:11434")

try:
    start = time.time()
    r = requests.get('http://localhost:11434/api/tags', timeout=10)
    elapsed = time.time() - start
    print(f"状态码: {r.status_code}")
    print(f"耗时: {elapsed:.1f}秒")
    print(f"响应: {r.text[:300]}")
except Exception as e:
    print(f"请求失败: {e}")
    sys.exit(1)

print("\n测试 LLM 生成...")
try:
    start = time.time()
    r = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'huihui_ai/deepseek-r1-abliterated:1.5b',
            'prompt': 'Say hello in 3 words',
            'stream': False
        },
        timeout=60
    )
    elapsed = time.time() - start
    print(f"状态码: {r.status_code}")
    print(f"耗时: {elapsed:.1f}秒")
    if r.status_code == 200:
        resp = r.json()
        print(f"响应: {resp.get('response', '')[:200]}")
    else:
        print(f"错误: {r.text[:200]}")
except Exception as e:
    print(f"生成失败: {e}")
    sys.exit(1)

print("\n全部测试通过!")