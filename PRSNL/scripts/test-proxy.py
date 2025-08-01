#!/usr/bin/env python3
import requests
import json

# Test the proxy
url = "http://localhost:8002/v1/chat/completions"
data = {
    "messages": [{"role": "user", "content": "Test"}],
    "model": "gpt-4",
    "max_tokens": 10
}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")