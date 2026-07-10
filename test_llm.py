#!/usr/bin/env python3
"""Script para verificar la conexión al LLM."""

import os
import json
import sys
from urllib.parse import quote_plus
from urllib.request import urlopen
import urllib.request as urllib_request


def post_json(url: str, body: dict, headers: dict = None):
    """POST request simple."""
    data = json.dumps(body).encode("utf-8")
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    request = urllib_request.Request(url, data=data, headers=request_headers, method="POST")
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def test_llm():
    """Prueba la conexión al LLM."""
    
    print("\n" + "="*60)
    print("PRUEBA DE CONEXIÓN AL LLM")
    print("="*60 + "\n")
    
    # Configuración
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:8082/v1/chat/completions")
    api_key = os.getenv("LLM_API_KEY", "freecc")
    model = os.getenv("LLM_MODEL", "nvidia_nim/minimaxai/minimax-m2.5")
    
    print(f"URL:     {base_url}")
    print(f"API Key: {api_key}")
    print(f"Modelo:  {model}\n")
    
    # Preparar request
    body = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hola, ¿cuál es 2+2?"}
        ],
        "temperature": 0.2,
    }
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    print("Enviando request...")
    
    try:
        response = post_json(base_url, body, headers=headers)
        print("✓ Conexión exitosa!\n")
        
        # Mostrar respuesta
        choices = response.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            print(f"Respuesta del LLM:\n{content}\n")
        else:
            print("⚠ Respuesta sin choices:")
            print(json.dumps(response, indent=2))
        
        return 0
        
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}\n")
        
        # Sugerencias
        if "405" in str(e):
            print("Sugerencia: Error 405 - La URL debe incluir /v1/chat/completions")
            print("Ejemplo correcto: http://localhost:8082/v1/chat/completions")
        elif "refused" in str(e).lower() or "connection" in str(e).lower():
            print("Sugerencia: No hay conexión. Verifica que:")
            print("  1. El servidor está corriendo en localhost:8082")
            print("  2. El puerto es correcto")
        elif "timeout" in str(e).lower():
            print("Sugerencia: Timeout - El servidor tardó demasiado en responder")
        
        return 1


if __name__ == "__main__":
    sys.exit(test_llm())
