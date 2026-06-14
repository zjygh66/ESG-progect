import requests
import time

data = {
    'model': 'huihui_ai/deepseek-r1-abliterated:1.5b',
    'prompt': 'Say hello',
    'stream': False
}

print("Testing Ollama API...")
start = time.time()
r = requests.post('http://localhost:11434/api/generate', json=data, timeout=30)
elapsed = time.time() - start

print(f"Status: {r.status_code}")
print(f"Time: {elapsed:.1f}s")
print(f"Response: {r.json().get('response', '')[:100]}")
