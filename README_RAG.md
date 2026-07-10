# 🤖 Agente RAG - Consulta de Documentos de la Empresa

Un agente inteligente que usa embeddings vectoriales y LLM para responder preguntas sobre documentos PDF de tu empresa.

## ✨ Características

- 📄 Procesa múltiples PDFs automáticamente
- 🔍 Búsqueda semántica usando embeddings
- 💬 Respuestas contextualizadas con Claude
- 💾 Base de datos vectorial persistente (Chroma)
- 🎯 Modo interactivo y consultas únicas

## 📋 Requisitos

- Python 3.8+
- Free Claude Code server corriendo en `localhost:8082`
- Dependencias: `chroma-client`, `PyPDF2`

## 🚀 Instalación

### 1. Instala las dependencias

```bash
pip install -r requirements.txt
```

O manualmente:
```bash
pip install chroma-client PyPDF2
```

### 2. Inicia el servidor LLM

En otra terminal:
```bash
python -m free_claude_code
```

### 3. Prepara los PDFs

Crea una carpeta `company_docs/` en el directorio del agente:
```bash
mkdir company_docs
```

Coloca tus PDFs de la empresa en esta carpeta:
```
company_docs/
├── manual_empleado.pdf
├── politicas.pdf
├── estrategia_2024.pdf
└── ...
```

## 💡 Uso

### Modo interactivo (recomendado)

```bash
python main.py --chat
```

El agente cargará automáticamente todos los PDFs e indexará su contenido:

```
======================================================================
AGENTE RAG - INFORMACIÓN DE LA EMPRESA
======================================================================

✓ LLM configurado correctamente

📄 Procesando 3 PDF(s)...

  • manual_empleado.pdf... ✓ (45 chunks)
  • politicas.pdf... ✓ (32 chunks)
  • estrategia_2024.pdf... ✓ (28 chunks)

🗂️  Indexando 105 chunks en Chroma...
✓ Indexación completada

Modo interactivo. Escribe 'salir' para terminar.

Tu pregunta> ¿Cuál es la política de vacaciones?
```

El agente buscará documentos relevantes y responderá basándose en ellos.

### Pregunta única

```bash
python main.py "¿Cuál es la política de teletrabajo?"
```

Responde la pregunta y sale.

### Limpiar la base de datos vectorial

```bash
python main.py --reset --chat
```

Borra todos los embeddings almacenados y reindexca desde cero.

## 🔧 Configuración

### Variables de entorno

```bash
# LLM
set LLM_BASE_URL=http://localhost:8082/v1/messages
set LLM_MODEL=claude-3-5-sonnet-20241022
set LLM_API_KEY=freecc

# RAG (opcional)
set RAG_PDF_FOLDER=company_docs
set RAG_CHUNK_SIZE=1000
```

### Personalizar en el código

Edita `RAGConfig` en `main.py`:
```python
@dataclass
class RAGConfig:
    pdf_folder: str = "company_docs"        # Dónde están los PDFs
    chroma_db_path: str = ".chroma"         # Dónde se almacenan embeddings
    collection_name: str = "company_documents"
    chunk_size: int = 1000                  # Tamaño de chunks (caracteres)
    chunk_overlap: int = 200                # Solapamiento entre chunks
```

## 📊 Arquitectura

```
┌─────────────────┐
│   PDFs (*.pdf)  │
└────────┬────────┘
         │
    ┌────▼─────┐
    │PDF Parser │  Extrae texto
    └────┬─────┘
         │
    ┌────▼─────────┐
    │Text Chunks   │  Divide en trozos
    └────┬─────────┘
         │
    ┌────▼──────────────┐
    │Chroma (Embeddings)│  Genera vectores
    └────┬──────────────┘
         │
    ┌────▼──────────┐
    │Vector Store   │  Almacena indexado
    └────┬──────────┘
         │
         │ Búsqueda semántica
         │
    ┌────▼──────────┐
    │  Top-5 Docs   │
    └────┬──────────┘
         │
    ┌────▼────────────────┐
    │ LLM (Claude)        │  Responde con contexto
    └─────────────────────┘
```

## 🎯 Flujo de una consulta

1. **Usuario pregunta**: "¿Cuántos días de vacaciones tengo?"
2. **Búsqueda vectorial**: Encuentra chunks relevantes
3. **Contexto**: Selecciona los 5 más relevantes
4. **LLM**: Recibe pregunta + contexto
5. **Respuesta**: Claude responde basándose en documentos

## 📝 Ejemplos de preguntas

```
✓ ¿Cuál es la política de vacaciones?
✓ ¿Qué beneficios tiene la empresa?
✓ ¿Cuáles son los objetivos estratégicos?
✓ ¿Cómo funciona el proceso de reembolsos?
✓ Explícame el plan de compensación
✓ ¿Cuántos días de enfermedad tengo?
```

## 🐛 Solución de problemas

### Error: "Carpeta company_docs no existe"
```bash
mkdir company_docs
# Coloca tus PDFs aquí
```

### Error: "No se encontraron PDFs"
Asegúrate que:
1. Los archivos terminan en `.pdf`
2. Están en la carpeta `company_docs/`
3. No están comprimidos

### Error: "Chroma no está instalado"
```bash
pip install chromadb
```

### Error: "LLM no está configurado"
Asegúrate que:
1. Free Claude Code está corriendo: `python -m free_claude_code`
2. Variables de entorno están configuradas
3. `localhost:8082` es accesible

### El agente da respuestas genéricas
- Los PDFs tienen contenido relevante?
- Aumenta `chunk_size` si el contenido está fragmentado
- Usa términos más específicos en tus preguntas

## 📚 Mejoras futuras

- [ ] Soporte para más formatos (DOCX, TXT, etc.)
- [ ] Búsqueda híbrida (vectorial + keyword)
- [ ] Caché de respuestas
- [ ] Exportar respuestas a PDF
- [ ] Multi-lenguaje
- [ ] Feedback de usuario para mejorar

## 📄 Licencia

MIT

## 💬 Preguntas?

Revisa los logs del agente para más detalles sobre qué está pasando.
