# Configuración del LLM para el Agente de Clima

## Problema: HTTP Error 405 (Method Not Allowed)

Esto significa que la URL del endpoint no es correcta. El servidor esperaba una URL con el path `/v1/chat/completions`.

## Solución

### 1. **URL Correcta**
La URL base debe ser **completa**, incluyendo el path:

```
http://localhost:8082/v1/chat/completions
```

### 2. **Variables de Entorno (Windows Cmd)**

```cmd
set LLM_BASE_URL=http://localhost:8082/v1/chat/completions
set LLM_API_KEY=freecc
set LLM_MODEL=nvidia_nim/minimaxai/minimax-m2.5
```

### 3. **Variables de Entorno (PowerShell)**

```powershell
$env:LLM_BASE_URL = "http://localhost:8082/v1/chat/completions"
$env:LLM_API_KEY = "freecc"
$env:LLM_MODEL = "nvidia_nim/minimaxai/minimax-m2.5"
```

### 4. **Ejecutar el Programa**

```bash
.\Scripts\python.exe main.py
```

## Verificación

Si el LLM está configurado correctamente, verás:

```
============================================================
AGENTE DE CLIMA Y VIAJES
============================================================
✓ Modo LLM ACTIVO - Usando inteligencia artificial para análisis
  Respuestas más naturales y contextuales
```

Si hay un error, verás:

```
⚠ Error de LLM: Error al conectar con LLM en http://localhost:8082/v1/chat/completions: [details]
  Usando modo local como fallback...
```

## Endpoints Comunes

### OpenAI
```
https://api.openai.com/v1/chat/completions
```

### Ollama (local)
```
http://localhost:11434/api/chat
```

### LM Studio (local)
```
http://localhost:1234/v1/chat/completions
```

### Servidor Local personalizado
```
http://localhost:8082/v1/chat/completions
```

## Requisitos del Servidor LLM

El servidor debe:
1. Aceptar POST requests en el endpoint
2. Devolver JSON con estructura:
```json
{
  "choices": [
    {
      "message": {
        "content": "respuesta del modelo"
      }
    }
  ]
}
```
3. Aceptar el header `Authorization: Bearer {api_key}` (opcional)
4. Soportar el formato de mensajes OpenAI Chat API

## Solución de Problemas

### Error 405: Method Not Allowed
- ✓ Verifica que `LLM_BASE_URL` tenga el path completo `/v1/chat/completions`
- ✓ Asegúrate que es un POST request (el código ya lo hace)

### Error de conexión
- ✓ Verifica que el servidor está corriendo en `localhost:8082`
- ✓ Prueba con `curl -X POST http://localhost:8082/v1/chat/completions`

### Error 401: Unauthorized
- ✓ Verifica que `LLM_API_KEY` es correcta
- ✓ Algunos servidores pueden no requerir key (usa "freecc" como default)

### Timeout
- ✓ El servidor tarda demasiado en responder
- ✓ Aumenta el timeout en `post_json` (actualmente 60 segundos)
