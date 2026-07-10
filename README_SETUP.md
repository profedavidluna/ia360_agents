# Configuración del Agente de Clima con Free Claude Code

## 🎯 Resumen

Tu agente ahora soporta **Free Claude Code** con el formato correcto **Anthropic Messages API**.

---

## ✅ Lo que cambió

1. **Endpoint actualizado** a `http://localhost:8082/messages` (Anthropic format)
2. **Soporte dual**: El agente puede usar tanto Anthropic como OpenAI
3. **Mejor detección de errores**: Mensajes más claros si algo falla
4. **Scripts de prueba incluidos**: Para verificar la conexión

---

## 🚀 Cómo Usar

### Paso 1: Iniciar el servidor Free Claude Code

En otra terminal (o antes de ejecutar el agente):

```bash
python -m free_claude_code
```

O si tienes instalado el paquete:

```bash
free-claude-code
```

Debería ver algo como:
```
INFO:     Uvicorn running on http://0.0.0.0:8082
```

### Paso 2: Verificar la conexión (Opcional)

```bash
.\Scripts\python.exe test_anthropic.py
```

Si funciona, verás:
```
✓ ÉXITO!
Status: 200

Response:
{
  "id": "...",
  "content": [{"type": "text", "text": "2+2 = 4"}],
  ...
}
```

### Paso 3: Ejecutar el agente

En PowerShell:

```powershell
$env:LLM_BASE_URL = "http://localhost:8082/messages"
$env:LLM_API_KEY = "freecc"
$env:LLM_MODEL = "claude-3-5-sonnet-20241022"

.\Scripts\python.exe main.py
```

O directamente (usa los defaults):

```bash
.\Scripts\python.exe main.py
```

### Paso 4: Usa el agente

```
============================================================
AGENTE DE CLIMA Y VIAJES
============================================================
✓ Modo LLM ACTIVO (ANTHROPIC)
  Servidor: http://localhost:8082/messages
  Modelo: claude-3-5-sonnet-20241022
  Respuestas más naturales y contextuales

Escribe una consulta natural o 'salir' para terminar.
Ejemplos: '¿Qué tal el clima en París?', 'Viajar a Medellín', 'Salir'
============================================================

Tú> ¿Conviene viajar a Madrid?
```

---

## 🔧 Variables de Entorno

Personaliza con estas variables (opcional, tienen defaults):

```powershell
$env:LLM_BASE_URL = "http://localhost:8082/messages"      # Endpoint
$env:LLM_API_KEY = "freecc"                               # API key (por defecto "freecc")
$env:LLM_MODEL = "claude-3-5-sonnet-20241022"             # Modelo a usar
$env:LLM_API_TYPE = "anthropic"                           # Tipo de API ("anthropic" o "openai")
```

---

## 📋 Modelos Disponibles

Free Claude Code puede usar diferentes modelos según tu configuración:

### Claude 3.5 Sonnet (Recomendado)
```
claude-3-5-sonnet-20241022
```
- Rápido y equilibrado
- Buen balance entre velocidad y calidad

### Claude 3 Opus
```
claude-3-opus-20250729
```
- Más potente pero más lento
- Para tareas complejas

### Claude 3 Haiku
```
claude-3-haiku-20250307
```
- Muy rápido
- Para tareas simples

---

## 🧪 Scripts Disponibles

### `test_anthropic.py`
Prueba la conexión directa al servidor:
```bash
.\Scripts\python.exe test_anthropic.py
```

### `discover_llm.py`
Prueba múltiples endpoints (si quieres experimentar):
```bash
.\Scripts\python.exe discover_llm.py
```

### `main.py`
El agente principal:
```bash
.\Scripts\python.exe main.py
```

---

## 🆘 Solución de Problemas

### Error: "Connection refused"
**Problema:** El servidor no está corriendo
```bash
python -m free_claude_code
```

### Error: "405 Method Not Allowed"
**Problema:** Endpoint incorrecto
```powershell
# Verifica:
$env:LLM_BASE_URL = "http://localhost:8082/messages"  # Correcto
# NO: http://localhost:8082/v1/chat/completions (es OpenAI)
```

### Error: "No content in response"
**Problema:** Respuesta vacía del servidor
- Verifica que el modelo existe
- Intenta con un modelo diferente
- Revisa los logs del servidor

### El agente responde con modo local
**Problema:** LLM falló, usando fallback
- Verifica que el servidor está corriendo
- Revisa el archivo de log del agente
- Ejecuta `test_anthropic.py` para diagnosticar

---

## 📝 Ejemplo de Sesión Completa

```powershell
# Terminal 1: Inicia el servidor
python -m free_claude_code

# Terminal 2 (después de ~5 segundos): Ejecuta el agente
cd c:\opt\cursos\2026\ia360\agentesPython\agentsCourse
$env:LLM_BASE_URL = "http://localhost:8082/messages"
$env:LLM_MODEL = "claude-3-5-sonnet-20241022"
.\Scripts\python.exe main.py
```

Interacción esperada:
```
============================================================
AGENTE DE CLIMA Y VIAJES
============================================================
✓ Modo LLM ACTIVO (ANTHROPIC)
  Servidor: http://localhost:8082/messages
  Modelo: claude-3-5-sonnet-20241022
  Respuestas más naturales y contextuales

Tú> ¿Conviene viajar a Nueva York?

Agente> Voy a consultar el clima actual de Nueva York para ti.

Clima en New York, United States of America:

Basándome en los datos meteorológicos actuales:
- Temperatura moderada
- Sin precipitaciones
- Viento ligero

Es un excelente momento para viajar a Nueva York. Las condiciones son 
ideales: clima templado, cielo despejado y sin lluvia. Perfecto para 
pasear por las calles y disfrutar de los puntos turísticos.

Tú> Gracias, ¿y París?
...
```

---

## 💡 Tips

1. **Usa Claude 3.5 Sonnet**: Es el mejor balance entre velocidad y calidad
2. **Deja el servidor corriendo**: No lo cierres mientras usas el agente
3. **Prueba primero con `test_anthropic.py`**: Para verificar que todo funciona
4. **Lee los logs**: Si algo falla, busca pistas en los logs del servidor

---

## 📚 Recursos

- [Free Claude Code - GitHub](https://github.com/Rishurajgautam24/free-claude-code)
- [Documentación Anthropic API](https://docs.anthropic.com/api/messages)
- [Modelos de Claude](https://docs.anthropic.com/claude/docs/models-overview)

---

## ✨ Características

- ✅ Consulta de clima en tiempo real vía Open-Meteo
- ✅ Análisis inteligente con Claude
- ✅ Respuestas naturales en español
- ✅ Conversación multi-turno con contexto
- ✅ Fallback automático a modo local si LLM falla
- ✅ Soporte para múltiples modelos de Claude
