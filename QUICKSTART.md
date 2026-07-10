# 🚀 Inicio Rápido - Agente RAG

## ⚡ En 3 pasos

### Paso 1: Instalar dependencias

```bash
# Windows - ejecuta
install_dependencies.bat

# O manualmente
pip install chromadb PyPDF2
```

### Paso 2: Inicia el servidor LLM (en otra terminal)

```bash
python -m free_claude_code
```

Espera a ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8082
```

### Paso 3: Ejecuta el agente

```bash
# Modo interactivo (recomendado)
python main.py --chat

# O pregunta única
python main.py "¿Cuál es la política de vacaciones?"
```

## 📁 Estructura de carpetas

```
agentsCourse/
├── main.py                      # Agente RAG
├── requirements.txt             # Dependencias
├── README_RAG.md               # Documentación completa
├── company_docs/               # Tus PDFs aquí
│   ├── manual_empleado.pdf
│   └── politicas.pdf
└── .chroma/                    # BD vectorial (se crea automáticamente)
```

## 💡 Ejemplos de uso

### Modo interactivo
```bash
$ python main.py --chat

======================================================================
AGENTE RAG - INFORMACIÓN DE LA EMPRESA
======================================================================

✓ LLM configurado correctamente

📄 Procesando 2 PDF(s)...
  • manual_empleado.pdf... ✓ (45 chunks)
  • politicas.pdf... ✓ (32 chunks)

🗂️  Indexando 77 chunks en Chroma...
✓ Indexación completada

Modo interactivo. Escribe 'salir' para terminar.

Tu pregunta> ¿Cuántos días de vacaciones tengo?
🔍 Buscando documentos relevantes... ✓
🤖 Consultando LLM... ✓

Agente> Según el manual de empleado, tienes 20 días de vacaciones 
anuales, más 5 días adicionales si trabajas más de 3 años en la empresa.

Tu pregunta> ¿Cuál es la política de teletrabajo?
...
```

### Pregunta única
```bash
$ python main.py "¿Qué beneficios ofrece la empresa?"

======================================================================
AGENTE RAG - INFORMACIÓN DE LA EMPRESA
======================================================================
[Procesamiento...]

Agente> La empresa ofrece los siguientes beneficios:
- Seguro médico para ti y tu familia
- Plan de pensión
- Flexibilidad de horario
- Acceso a cursos de capacitación
- Bonificación anual basada en desempeño

```

### Limpiar BD (re-indexar)
```bash
python main.py --reset --chat
```

## 🔧 Configuración

### Variables de entorno (opcional)

```powershell
# PowerShell
$env:LLM_BASE_URL = "http://localhost:8082/v1/messages"
$env:LLM_MODEL = "claude-3-5-sonnet-20241022"
$env:RAG_PDF_FOLDER = "company_docs"

python main.py --chat
```

## 🎯 Flujo

```
1. Usuario pregunta
   ↓
2. Búsqueda vectorial en Chroma
   ↓
3. Obtiene top-5 documentos relevantes
   ↓
4. Envía a Claude con contexto
   ↓
5. Claude responde
   ↓
6. Usuario ve respuesta
```

## ❓ Preguntas frecuentes

**P: ¿Dónde coloco los PDFs?**
R: En la carpeta `company_docs/`

**P: ¿Puedo usar otros formatos?**
R: Por ahora solo PDF. Puedes convertir DOCX a PDF con herramientas online.

**P: ¿Cuánto tarda en indexar?**
R: Depende del tamaño. Típicamente 10-30 segundos para 3-5 PDFs.

**P: ¿Se guardan las respuestas?**
R: No. Pero puedes copiar y guardar en un archivo.

**P: ¿Necesito internet?**
R: No. Todo funciona localmente (Chroma + Free Claude Code local).

## 🚨 Si algo falla

### "Chromadb no encontrado"
```bash
pip install chromadb
```

### "PDFs no procesados"
1. Verifica que los PDFs estén en `company_docs/`
2. Los archivos deben terminar en `.pdf` (minúsculas)
3. Intenta: `python main.py --reset --chat`

### "LLM no responde"
1. Verifica que `python -m free_claude_code` está corriendo
2. Abre `http://localhost:8082` en el navegador para verificar

### "Respuestas genéricas"
1. Usa términos más específicos
2. Verifica que los PDFs tienen contenido relevante
3. Intenta: `python main.py --reset --chat`

## 📚 Más info

- Documentación completa: `README_RAG.md`
- Código: `main.py`
- Dependencias: `requirements.txt`

---

¡Listo! Ya puedes usar tu agente RAG. 🎉
