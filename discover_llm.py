#!/usr/bin/env python3
"""Script para descubrir la forma correcta de llamar al servidor LLM."""

import os
import json
import sys
from urllib.request import urlopen, Request
import urllib.request as urllib_request


def test_endpoint(url: str, body: dict, headers: dict = None, description: str = "") -> bool:
    """Prueba un endpoint y retorna True si funciona."""
    
    print(f"\n{'='*70}")
    print(f"PROBANDO: {description}")
    print(f"{'='*70}")
    print(f"URL: {url}")
    print(f"Body: {json.dumps(body, indent=2)}")
    
    if headers:
        print(f"Headers: {json.dumps(headers, indent=2)}")
    
    try:
        data = json.dumps(body).encode("utf-8")
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        
        request = Request(url, data=data, headers=request_headers, method="POST")
        print("\nEnviando request...")
        
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"\n✓ ÉXITO! Status: {response.status}")
            print(f"Respuesta:\n{json.dumps(result, indent=2)}")
            return True
            
    except Exception as e:
        print(f"\n✗ FALLO: {type(e).__name__}")
        print(f"Error: {e}")
        return False


def main():
    """Prueba diferentes endpoints."""
    
    base = os.getenv("LLM_BASE_URL", "http://localhost:8082")
    api_key = os.getenv("LLM_API_KEY", "freecc")
    model = os.getenv("LLM_MODEL", "claude")
    
    print("\n" + "="*70)
    print("DESCUBRIDOR DE ENDPOINTS - FREE CLAUDE CODE")
    print("="*70)
    print(f"\nBase URL: {base}")
    print(f"API Key: {api_key}")
    print(f"Modelo: {model}\n")
    
    test_message = {
        "role": "user",
        "content": "Hola, soy un test. ¿Puedes responder con 'OK'?"
    }
    
    tests = [
        # Formato OpenAI Chat Completions (estándar)
        {
            "url": f"{base}/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [test_message],
                "temperature": 0.2,
            },
            "description": "OpenAI Chat Completions API (estándar)"
        },
        
        # Sin el /v1
        {
            "url": f"{base}/chat/completions",
            "body": {
                "model": model,
                "messages": [test_message],
                "temperature": 0.2,
            },
            "description": "Sin /v1 (chat/completions)"
        },
        
        # Solo /completions
        {
            "url": f"{base}/completions",
            "body": {
                "model": model,
                "messages": [test_message],
                "temperature": 0.2,
            },
            "description": "Solo /completions"
        },
        
        # Formato alternativo: prompt en vez de messages
        {
            "url": f"{base}/v1/completions",
            "body": {
                "model": model,
                "prompt": "Hola, soy un test. ¿Puedes responder con 'OK'?",
                "temperature": 0.2,
                "max_tokens": 100,
            },
            "description": "OpenAI Completions API (con prompt en vez de messages)"
        },
        
        # Con API key en header
        {
            "url": f"{base}/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [test_message],
                "temperature": 0.2,
            },
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "X-API-Key": api_key,
            },
            "description": "Chat Completions con Authorization headers"
        },
        
        # Formato Ollama
        {
            "url": f"{base}/api/chat",
            "body": {
                "model": model,
                "messages": [test_message],
                "stream": False,
            },
            "description": "Formato Ollama (/api/chat)"
        },
        
        # Formato Anthropic (aunque probablemente no)
        {
            "url": f"{base}/messages",
            "body": {
                "model": model,
                "messages": [test_message],
                "max_tokens": 1024,
            },
            "headers": {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            "description": "Formato Anthropic Messages API"
        },
    ]
    
    results = []
    for test in tests:
        url = test["url"]
        body = test["body"]
        headers = test.get("headers")
        description = test["description"]
        
        success = test_endpoint(url, body, headers, description)
        results.append({
            "description": description,
            "url": url,
            "success": success
        })
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70 + "\n")
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    if successful:
        print(f"✓ ENDPOINTS QUE FUNCIONAN ({len(successful)}):\n")
        for r in successful:
            print(f"  • {r['description']}")
            print(f"    URL: {r['url']}\n")
    else:
        print("✗ Ningún endpoint funcionó.\n")
    
    print(f"\n✗ Endpoints que fallaron ({len(failed)}):\n")
    for r in failed[:3]:  # Mostrar solo los primeros 3
        print(f"  • {r['description']}")
        print(f"    URL: {r['url']}\n")


if __name__ == "__main__":
    main()
