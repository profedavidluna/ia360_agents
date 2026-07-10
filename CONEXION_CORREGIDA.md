# ✅ Conexión Corregida - Free Claude Code

## 🎯 Endpoint Correcto Identificado

```
URL: http://localhost:8082/v1/messages
Formato: Anthropic Messages API
```

---

## 📋 Pasos para Usar

### 1. **Terminal 1 - Inicia el servidor**

```bash
python -m free_claude_code
```

Espera a ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8082
```

### 2. **Terminal 2 - Verifica la conexión (opcional)**

```bash
cd c:\opt\cursos\2026\ia360\agentesPython\agentsCourse
.\Scripts\python.exe test_anthropic.py
```

Debería ver:
```
✓ Response Status: 200
✓ JSON válido!
✅ Respuesta del LLM: 2+2 = 4
```

### 3. **Terminal 2 - Ejecuta el agente**

```bash
.\Scripts\python.exe main.py
```

¡Y listo! Ahora puedes usar el agente normalmente.

---

## 🧪 Si test_anthropic.py falla

### Error: "respuesta vacía"
- El servidor puede estar configurado mal
- Verifica que `/v1/messages` existe
- Intenta reiniciar el servidor

### Error: "No JSON válido"
- El servidor devuelve HTML o texto
- Verifica el endpoint
- Mira los logs del servidor

### Error: "Connection refused"
- El servidor no está corriendo
- Ejecuta: `python -m free_claude_code`

---

## 🚀 Uso del Agente

Una vez iniciado, el agente te pedirá que escribas:

```
============================================================
AGENTE DE CLIMA Y VIAJES
============================================================
✓ Modo LLM ACTIVO (ANTHROPIC)
  Servidor: http://localhost:8082/v1/messages
  Modelo: claude-3-5-sonnet-20241022

Tú> ¿Conviene viajar a París?

Agente> Voy a revisar el clima para ti...

[Respuesta inteligente del agente]
```

---

## 📝 Variables de Entorno (todas tienen defaults)

Si quieres personalizar:

```powershell
$env:LLM_BASE_URL = "http://localhost:8082/v1/messages"
$env:LLM_MODEL = "claude-3-5-sonnet-20241022"
$env:LLM_API_KEY = "freecc"
$env:LLM_API_TYPE = "anthropic"

.\Scripts\python.exe main.py
```

---

## ✨ Lo que cambió en el código

1. **Endpoint actualizado** a `/v1/messages` (era `/messages`)
2. **Mejor manejo de errores** en `post_json()`
3. **Mejor parseo de respuesta** en `call_llm()`
4. **Script de prueba mejorado** para diagnosticar problemas

---

## 💡 Tips

- Deja el servidor (`python -m free_claude_code`) corriendo en una terminal separada
- Si algo falla, ejecuta `test_anthropic.py` para diagnosticar
- Lee los logs del servidor si tienes problemas
- El agente funciona con o sin LLM (fallback automático)

¡Disfruta tu agente de clima inteligente! 🌤️
