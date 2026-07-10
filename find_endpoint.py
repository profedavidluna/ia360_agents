#!/usr/bin/env python3
"""Descubre los endpoints disponibles en localhost:8082"""

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


def test_endpoint(path: str, method: str = "GET") -> tuple[bool, str]:
    """Prueba si un endpoint existe."""
    url = f"http://localhost:8082{path}"
    
    try:
        if method == "GET":
            with urlopen(url, timeout=2) as response:
                return True, f"✓ {response.status}"
        else:  # POST
            body = json.dumps({"test": "test"}).encode("utf-8")
            request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(request, timeout=2) as response:
                return True, f"✓ {response.status}"
    except HTTPError as e:
        return False, f"✗ {e.code} {e.reason}"
    except URLError as e:
        return False, f"✗ Connection Error"
    except Exception as e:
        return False, f"✗ {type(e).__name__}"


def main():
    print("\n" + "="*70)
    print("BUSCADOR DE ENDPOINTS - FREE CLAUDE CODE")
    print("="*70)
    print("\nBuscando endpoints disponibles en http://localhost:8082\n")
    
    # Endpoints a probar
    endpoints = [
        # Raíz
        ("/", "GET"),
        
        # Health checks
        ("/health", "GET"),
        ("/status", "GET"),
        ("/v1/health", "GET"),
        
        # Endpoints de mensajes Anthropic
        ("/messages", "POST"),
        ("/v1/messages", "POST"),
        ("/api/messages", "POST"),
        ("/chat/messages", "POST"),
        
        # Endpoints OpenAI
        ("/v1/chat/completions", "POST"),
        ("/chat/completions", "POST"),
        ("/completions", "POST"),
        ("/v1/completions", "POST"),
        
        # Otros endpoints comunes
        ("/api/chat", "POST"),  # Ollama
        ("/chat", "POST"),
        ("/models", "GET"),
        ("/v1/models", "GET"),
        
        # Raíz con POST
        ("/", "POST"),
    ]
    
    found_endpoints = []
    
    for path, method in endpoints:
        success, status = test_endpoint(path, method)
        symbol = "✓" if success else "✗"
        print(f"{symbol} {method:4s} {path:30s} {status}")
        if success:
            found_endpoints.append((path, method))
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    
    if found_endpoints:
        print(f"\n✓ Endpoints encontrados ({len(found_endpoints)}):\n")
        for path, method in found_endpoints:
            print(f"  {method:4s} http://localhost:8082{path}")
    else:
        print("\n✗ No se encontraron endpoints funcionando.")
        print("\nVerifica que:")
        print("  1. El servidor está corriendo: python -m free_claude_code")
        print("  2. Está en http://localhost:8082")
        print("  3. No hay firewall bloqueando la conexión")
        return 1
    
    print("\n" + "="*70)
    print("PRUEBA DEL ENDPOINT")
    print("="*70)
    
    # Intenta con el primer endpoint POST encontrado
    post_endpoints = [e for e in found_endpoints if e[1] == "POST"]
    if post_endpoints:
        path, _ = post_endpoints[0]
        print(f"\nProbando POST {path}...\n")
        
        try:
            body = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": "Hola"}]
            }
            
            url = f"http://localhost:8082{path}"
            data = json.dumps(body).encode("utf-8")
            request = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            
            with urlopen(request, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
                print("✓ Request exitoso!")
                print(f"\nRespuesta (primeros 300 caracteres):")
                print(json.dumps(result, indent=2)[:300])
                
                # Detectar formato
                if "content" in result:
                    print("\n✓ Formato: ANTHROPIC")
                    return 0
                elif "choices" in result:
                    print("\n✓ Formato: OPENAI")
                    return 0
                else:
                    print("\n⚠ Formato desconocido")
                    return 0
                    
        except Exception as e:
            print(f"✗ Error en el POST: {e}")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
