# ⚡ Inicio Rápido - Agente RAG con Pinecone

## 🚀 En 3 Pasos

### Paso 1: Instalar dependencias

```bash
cd c:\opt\cursos\2026\ia360\agentesPython\agentsCourse

pip install pinecone-client sentence-transformers PyPDF2
```

O simplemente ejecuta:
```bash
start_pinecone.bat
```

### Paso 2: Inicia el servidor LLM (Terminal 1)

```bash
python -m free_claude_code
```

Espera a ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8082
```

### Paso 3: Ejecuta el agente (Terminal 2)

```bash
# Ya está configurado con tu API Key de Pinecone

# Modo interactivo (recomendado)
python main.py --chat

# O pregunta única
python main.py "¿Cuál es la política de vacaciones?"
```

## ✅ Verificar que Todo Funciona

### Primera ejecución

```
======================================================================
AGENTE RAG - INFORMACIÓN DE LA EMPRESA (Pinecone)
======================================================================

✓ LLM configurado correctamente
✓ Pinecone Index: company-documents

📄 Procesando 2 PDF(s)...
  • Prueba_Tecnica_CryptoWatch_Microservicios.docx.pdf... ✓ (45 chunks)
  • Prueba_Tecnica_Tienda_Virtual_Microservicios.docx.pdf... ✓ (32 chunks)

🤖 Cargando modelo de embeddings... ✓ (384 dimensiones)
📦 Creando índice 'company-documents'... ✓
📤 Generando embeddings para 77 chunks... ✓
   Enviando a Pinecone... ✓
   Indexados: 77 chunks

Modo interactivo. Escribe 'salir' para terminar.

Tu pregunta> ¿Qué es microservicios?
🔍 Buscando documentos relevantes... ✓
🤖 Consultando LLM... ✓

Agente> Los microservicios son una arquitectura de software...
```

## 📁 Estructura de Archivos

```
agentsCourse/
├── main.py                           # Agente RAG (Pinecone)
├── main_chroma_backup.py            # Backup antiguo (Chroma)
├── .env                             # Tu API Key (cargado automáticamente)
├── start_pinecone.bat               # Script de inicio rápido
├── company_docs/                    # Tus PDFs
│   ├── documento1.pdf
│   └── documento2.pdf
└── PINECONE_SETUP.md               # Documentación completa
```

## 💡 Comandos Básicos

```bash
# Modo interactivo
python main.py --chat

# Pregunta única
python main.py "¿Cuál es la estructura?"

# Re-indexar (borrar índice y empezar nuevo)
python main.py --reset --chat

# Ver que está en .env
cat .env
```

## 🔍 Diferencias con Chroma

### Chroma (antes)
```bash
# BD local
# Sin configuración necesaria
python main.py --chat
```

### Pinecone (ahora)
```bash
# BD en cloud
# API Key configurada en .env
python main.py --chat
```

## 🎯 Flujo de Datos

```
PDFs en company_docs/
    ↓
Procesamiento (PyPDF2)
    ↓
Dividir en chunks (1000 caracteres)
    ↓
Generar embeddings (sentence-transformers)
    ↓
Enviar a Pinecone (cloud)
    ↓
Almacenar en índice "company-documents"
```

## 📋 Configuración

Tu `.env` ya tiene:

```
PINECONE_API_KEY=pcsk_57CWgh_...        ← Tu clave
PINECONE_INDEX_NAME=company-documents   ← Nombre del índice
PINECONE_ENVIRONMENT=us-east-1          ← Región

LLM_BASE_URL=http://localhost:8082/v1/messages
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_API_KEY=freecc
```

**No necesitas hacer nada más**, se carga automáticamente.

## 🐛 Si Algo Falla

### Error: "PINECONE_API_KEY not found"

```bash
# Verifica que .env existe
ls -la .env

# Si existe, verifica su contenido
cat .env
```

### Error: "Connection timeout"

Verifica:
1. Internet está funcionando
2. Pinecone está online (raro que no lo esté)
3. Intenta de nuevo en unos minutos

### Error: "Index not found"

El índice se crea automáticamente. Si no funciona:
```bash
# Re-indexa todo
python main.py --reset --chat
```

### LLM no responde

Verifica:
1. Que `python -m free_claude_code` está corriendo
2. `http://localhost:8082` es accesible
3. Intenta de nuevo

## 📈 Monitoreo

Puedes ver en el dashboard de Pinecone:
- Número de vectores indexados (77 en tu caso)
- Uso de API
- Latencia de consultas

## 🔐 Seguridad

⚠️ **IMPORTANTE:**

1. **No commitees `.env` a git**
   - Crea `.gitignore`:
   ```
   .env
   *.log
   __pycache__/
   ```

2. **Tu API Key está segura aquí**
   - Solo se usa localmente
   - No se envía a nadie

3. **Si accidentalmente la compartiste**
   - Ve a Pinecone dashboard
   - Crea una nueva API Key
   - Borra la vieja

## 📚 Próximos Pasos

1. ✅ Agente RAG listo
2. Lee `PINECONE_SETUP.md` para más detalles
3. Lee `CONFIGURACION_RAG.md` para ajustar embeddings/chunks
4. Usa `explore_rag.py` para ver qué hay indexado

## 🎉 Resumen

✅ API Key configurada
✅ Dependencias instaladas
✅ Agente listo para usar
✅ PDFs procesados

**¡Puedes empezar a hacer preguntas!** 🚀

```bash
python main.py --chat
```
