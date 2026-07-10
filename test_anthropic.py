#!/usr/bin/env python3
"""Test simple para verificar el endpoint Anthropic de free-claude-code."""

import os
import json
import sys
from urllib.request import urlopen, Request


def parse_sse_response(response_text: str) -> str:
    """Parsea respuesta Server-Sent Events (SSE) y extrae el contenido de texto."""
    
    text_content = ""
    
    for line in response_text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("event:"):
            continue
        
        if line.startswith("data:"):
            data_str = line[5:].strip()
            try:
                data_json = json.loads(data_str)
                
                # Buscar deltas de texto
                if data_json.get("type") == "content_block_delta":
                    delta = data_json.get("delta", {})
                    if "text" in delta:
                        text_content += delta["text"]
                
            except json.JSONDecodeError:
                pass
    
    return text_content


def test_anthropic_api():
    """Prueba el endpoint Anthropic."""
    
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:8082/v1/messages")
    api_key = os.getenv("LLM_API_KEY", "freecc")
    model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
    
    print("\n" + "="*70)
    print("TEST ANTHROPIC API - Free Claude Code")
    print("="*70)
    print(f"\nURL:    {base_url}")
    print(f"API Key: {api_key}")
    print(f"Modelo: {model}\n")
    
    # Request en formato Anthropic
    body = {
        "model": model,
        "max_tokens": 100,
        "system": "Responde de forma breve.",
        "messages": [
            {"role": "user", "content": "¿Cuál es 2+2?"}
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    print("Request body:")
    print(json.dumps(body, indent=2))
    print("\nEnviando...\n")
    
    try:
        data = json.dumps(body).encode("utf-8")
        request = Request(base_url, data=data, headers=headers, method="POST")
        
        with urlopen(request, timeout=30) as response:
            response_text = response.read().decode("utf-8")
            
            print(f"✓ Response Status: {response.status}\n")
            
            # Respuesta vacía
            if not response_text or not response_text.strip():
                print("⚠ Servidor devolvió respuesta vacía!")
                return 1
            
            # Detectar si es SSE (Server-Sent Events)
            if response_text.strip().startswith("event:"):
                print("✓ Formato detectado: Server-Sent Events (SSE)\n")
                print("Respuesta recibida (primeros 800 caracteres):")
                print(response_text[:800])
                print("\n" + "="*70)
                
                # Parsear SSE
                text_content = parse_sse_response(response_text)
                
                if text_content:
                    print(f"\n✅ Contenido extraído del SSE:")
                    print(f"   {text_content}")
                    return 0
                else:
                    print("\n⚠ No se encontró contenido de texto en la respuesta SSE")
                    return 1
            
            # Si no es SSE, intenta JSON normal
            else:
                print("Intentando parsear como JSON...\n")
                try:
                    result = json.loads(response_text)
                    print("✓ JSON válido!\n")
                    print("Response completo:")
                    print(json.dumps(result, indent=2)[:500])
                    
                    content = result.get("content", [])
                    if content:
                        text = content[0].get("text", "")
                        print(f"\n✅ Respuesta: {text}")
                        return 0
                    
                except json.JSONDecodeError as e:
                    print(f"✗ Error al parsear JSON: {e}")
                    print(f"Primeros 200 caracteres: {response_text[:200]}")
                    return 1
            
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(test_anthropic_api())
