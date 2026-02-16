#!/usr/bin/env python3
"""Test Ollama integration"""
import main

print('Testing Ollama connection...')
models = main.query_ollama_models()
print(f'Found {len(models)} models\n')

if models:
    for m in models:
        name = m.get('name', 'unknown')
        size = m.get('size', 0)
        size_gb = size / (1024 * 1024 * 1024)
        print(f'  - {name:30} {size_gb:.1f}GB')
        if 'gemma3:4b' in name.lower():
            print(f'    ^ Found recommended model!')
else:
    print('No models found or Ollama not running')
