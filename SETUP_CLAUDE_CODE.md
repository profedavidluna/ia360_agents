# Configuración para Free Claude Code Server

## ✅ Información Importante

**Free Claude Code** es un servidor FastAPI que usa el **formato Anthropic Messages API**, NO OpenAI Chat Completions.

El servidor espera requests en formato Anthropic en `localhost:8082`.

---

## 📝 Formato Correcto para Llamadas

### ❌ NO FUNCIONA (OpenAI format):
```json
POST /v1/chat/completions
{
  "model": "claude-3-sonnet",
  "messages": [{"role": "user", "content": "..."}],
  "temperature": 0.2
}
```

### ✅ FUNCIONA (Anthropic format):
```json
POST /messages
{
  "model": "claude-3-sonnet-20250219",
  "max_tokens": 1024,
  "system": "Eres un asistente útil",
  "messages": [
    {"role": "user", "content": "Hola"}
  ]
}
```

---

## 🔧 Configuración para tu Agente

Tienes dos opciones:

### Opción A: Usar Formato Anthropic (Recomendado)

Actualiza `get_llm_config()` en `main.py`:

```python
def get_llm_config() -> dict[str, str]:
    return {
        "base_url": os.getenv(
            "LLM_BASE_URL",
            "http://localhost:8082/messages"  # ← Endpoint Anthropic
        ),
        "api_key": os.getenv(
            "LLM_API_KEY",
            "freecc"
        ),
        "model": os.getenv(
            "LLM_MODEL",
            "claude-3-sonnet-20250219"
        ),
    }
```

Luego actualiza `call_llm()` para usar formato Anthropic:

```python
def call_llm(messages: list[dict[str, str]], temperature: float = 0.2) -> str:
    config = get_llm_config()
    
    # Convertir messages OpenAI al formato Anthropic
    system_message = None
    user_messages = []
    
    for msg in messages:
        if msg["role"] == "system":
            system_message = msg["content"]
        else:
            user_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    body = {
        "model": config["model"],
        "max_tokens": 2048,
        "messages": user_messages,
        "temperature": temperature,
    }
    
    if system_message:
        body["system"] = system_message
    
    headers = {}
    if config["api_key"]:
        headers["x-api-key"] = config["api_key"]
    
    try:
        response = post_json(config["base_url"], body, headers=headers)
    except Exception as e:
        raise ValueError(f"Error al conectar con Anthropic API en {config['base_url']}: {e}")
    
    content = response.get("content") or []
    if not content:
        raise ValueError("El servidor no devolvió content. Respuesta: " + str(response))
    
    return str(content[0].get("text", ""))
```

### Opción B: Usar Adaptador OpenAI -> Anthropic

Si el servidor soporta ambos formatos (algunos adaptan automáticamente):

```python
base_url = os.getenv(
    "LLM_BASE_URL",
    "http://localhost:8082/v1/chat/completions"
)
```

---

## 📋 Referencias de Modelos

Modelos disponibles en Free Claude Code:

- `claude-3-5-sonnet-20241022` (recomendado, más rápido)
- `claude-3-sonnet-20250219` (última versión)
- `claude-3-opus-20250729` (más potente, más lento)
- `claude-3-haiku-20250307` (rápido, menos capaz)

---

## 🚀 Pasos Rápidos

### 1. Verifica que el servidor está corriendo:

```bash
curl -X POST http://localhost:8082/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: freecc" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hola"}]
  }'
```

### 2. Si funciona, actualiza tu agente:

En PowerShell:
```powershell
$env:LLM_BASE_URL = "http://localhost:8082/messages"
$env:LLM_API_KEY = "freecc"
$env:LLM_MODEL = "claude-3-5-sonnet-20241022"
.\Scripts\python.exe main.py
```

### 3. Usa el agente:

```
Tú> ¿Qué tal el clima en París?
```

---

## 🔍 Si Aún No Funciona

### Problema: "No messages in content"
**Solución:** El servidor retorna `{"content": []}`. Verifica:
1. El formato de messages es correcto
2. El modelo existe en el servidor
3. max_tokens > 0

### Problema: "x-api-key not allowed"
**Solución:** Algunos endpoints no requieren key, solo quita la validación:
```python
# No añadas headers si no es necesario
headers = {}  # Vacío
```

### Problema: "Endpoint not found"
**Solución:** Prueba estos endpoints:
```
http://localhost:8082/messages         ← Anthropic (recomendado)
http://localhost:8082/api/messages     ← Alternativo
http://localhost:8082/chat/messages    ← Otro alternativo
```

---

## 📚 Recursos Útiles

- Documentación Anthropic Messages API: https://docs.anthropic.com/api/messages
- Free Claude Code GitHub: https://github.com/Rishurajgautam24/free-claude-code
- Modelos disponibles: Depende de tu configuración de free-claude-code

---

## 💡 Resumen

- **Endpoint:** `http://localhost:8082/messages`
- **Formato:** Anthropic Messages API (no OpenAI)
- **Headers:** `x-api-key: freecc`
- **Modelos:** claude-3-5-sonnet-20241022 (recomendado)
