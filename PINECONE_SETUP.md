# 🚀 Configuración de Pinecone para el Agente RAG

Guía paso a paso para usar Pinecone como base de datos vectorial en tu agente RAG.

## 📋 Requisitos Previos

- Cuenta de Pinecone (gratuita o de pago)
- API Key de Pinecone
- Python 3.8+
- Free Claude Code server corriendo

## 🔑 Paso 1: Obtener Credenciales de Pinecone

### Crear cuenta (si no tienes)

1. Ve a https://www.pinecone.io/
2. Click en "Sign Up"
3. Completa el formulario
4. Confirma email
5. Inicia sesión

### Obtener API Key

1. En el dashboard de Pinecone, ve a "API Keys" (izquierda)
2. Click en "Create API Key"
3. Dale un nombre (ej: "RAG-Agent")
4. Copia la API Key completa
5. Guárdala en un lugar seguro

**Aspecto de la API Key:**
```
pcsk_57CWgh_3q2KDbHf8yjpJZFrqgdcpG2LBMwckmgeGPLi5YUMy59oCsCYXAysF7mv1KxvbtG
```

### Obtener Environment

En el dashboard:
1. Mira la sección "Indexes"
2. El environment está en la parte superior (ej: "us-west-2-aws", "us-east-1")
3. Apunta el environment que uses

**Opciones de environment para tier gratuito:**
- `us-east-1` (recomendado)
- `us-west-2-aws`
- `us-west-4-aws`

## 🛠️ Paso 2: Instalar Dependencias

```bash
cd c:\opt\cursos\2026\ia360\agentesPython\agentsCourse

# Instalar dependencias
pip install -r requirements.txt

# O manualmente
pip install pinecone-client sentence-transformers PyPDF2
```

## 🔧 Paso 3: Configurar Variables de Entorno

### PowerShell

```powershell
$env:PINECONE_API_KEY = "pcsk_57CWgh_3q2KDbHf8yjpJZFrqgdcpG2LBMwckmgeGPLi5YUMy59oCsCYXAysF7mv1KxvbtG"
$env:PINECONE_INDEX_NAME = "company-documents"
$env:PINECONE_ENVIRONMENT = "us-east-1"

# LLM
$env:LLM_BASE_URL = "http://localhost:8082/v1/messages"
$env:LLM_MODEL = "claude-3-5-sonnet-20241022"
$env:LLM_API_KEY = "freecc"
```

### Cmd

```cmd
set PINECONE_API_KEY=pcsk_57CWgh_3q2KDbHf8yjpJZFrqgdcpG2LBMwckmgeGPLi5YUMy59oCsCYXAysF7mv1KxvbtG
set PINECONE_INDEX_NAME=company-documents
set PINECONE_ENVIRONMENT=us-east-1

set LLM_BASE_URL=http://localhost:8082/v1/messages
set LLM_MODEL=claude-3-5-sonnet-20241022
set LLM_API_KEY=freecc
```

**O crea un archivo `.env` (no incluir en git):**

```
PINECONE_API_KEY=tu_api_key_aqui
PINECONE_INDEX_NAME=company-documents
PINECONE_ENVIRONMENT=us-east-1
LLM_BASE_URL=http://localhost:8082/v1/messages
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_API_KEY=freecc
```

## 🎯 Paso 4: Usar el Agente

### Terminal 1: Inicia el LLM

```bash
python -m free_claude_code
```

### Terminal 2: Ejecuta el agente

```bash
# Modo interactivo
python main.py --chat

# Pregunta única
python main.py "¿Cuál es la política de vacaciones?"

# Re-indexar (borrar índice y empezar nuevo)
python main.py --reset --chat
```

## 📊 Características de Pinecone vs Chroma

| Característica | Pinecone | Chroma |
|---|---|---|
| **Ubicación** | Cloud | Local |
| **Escalabilidad** | Ilimitada | Limitada |
| **Coste** | Gratuito (con límites) | Gratis |
| **Acceso remoto** | ✓ Sí | ✗ No |
| **Compartir BD** | ✓ Fácil | ✗ Complicado |
| **Latencia** | ~100ms | <1ms |
| **Setup** | Requiere configuración | Plug & play |

## 🆓 Tier Gratuito de Pinecone

**Incluye:**
- 1 índice
- 100k vectores
- 10 consultas por segundo
- 1GB almacenamiento

**Perfecto para:**
- Desarrollo y testing
- Pequeños RAGs (< 50 PDFs)
- Aprendizaje

**Cuando actualizar a pago:**
- Más de 100k vectores
- Múltiples índices
- Producción

## 🧪 Pruebas Rápidas

### Test 1: Verificar conexión

```bash
python -c "from pinecone import Pinecone; pc = Pinecone(api_key='tu_key'); print('✓ Conectado')"
```

### Test 2: Ejecutar agente

```bash
python main.py --chat

# Luego escribe una pregunta
Tu pregunta> ¿Cuál es la estructura del proyecto?
```

### Test 3: Ver índices

```bash
python -c "
from pinecone import Pinecone
import os
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
indexes = pc.list_indexes()
print(f'Índices: {indexes}')
"
```

## 🐛 Solución de Problemas

### Error: "PINECONE_API_KEY not found"

```bash
# Verifica que la variable de entorno está configurada
echo %PINECONE_API_KEY%    # CMD
echo $env:PINECONE_API_KEY # PowerShell

# Si está vacía, configúrala de nuevo
```

### Error: "Index not found"

El índice se crea automáticamente la primera vez. Si falla:
1. Verifica que PINECONE_INDEX_NAME es correcto
2. Verifica que PINECONE_ENVIRONMENT es válido
3. Intenta con un nombre diferente

### Error: "Connection timeout"

- Verifica conexión a internet
- Pinecone puede estar caído (raro)
- Intenta de nuevo en unos minutos

### Error: "Invalid API Key"

- Copia la API Key exacta de Pinecone
- No incluyas espacios
- Verifica que no esté expirada

### El agente tarda mucho en responder

- Pinecone tarda ~100ms en buscar
- Los embeddings tardan tiempo (depende del modelo)
- Primera búsqueda es más lenta (carga de modelo)

### No indexa los PDFs

1. Verifica que están en `company_docs/`
2. Extensión debe ser `.pdf` (minúsculas)
3. Intenta: `python main.py --reset --chat`

## 📈 Monitoreo de Pinecone

En el dashboard de Pinecone puedes ver:
- Número de vectores indexados
- Uso de la API
- Latencia de consultas
- Costes (si eres de pago)

## 🔒 Seguridad

### Buenas prácticas

1. **Nunca commits tu API Key**
   - Usa `.env` con `.gitignore`
   - O variables de entorno del sistema

2. **Rota tu API Key periódicamente**
   - En Pinecone dashboard
   - Crea una nueva y borra la vieja

3. **Usa HTTPS**
   - Pinecone siempre usa HTTPS
   - No necesitas preocuparte

4. **Diferencia de APIs**
   - LLM API Key (freecc) ≠ Pinecone API Key
   - No las mezcles

## 📚 Diferencias en el Código

Si vienes de Chroma:

**Chroma (antes):**
```python
from chromadb import PersistentClient
client = PersistentClient(path=".chroma")
collection = client.get_or_create_collection()
```

**Pinecone (ahora):**
```python
from pinecone import Pinecone
pc = Pinecone(api_key=key)
index = pc.Index(index_name)
```

## 🚀 Próximos Pasos

1. **Configurar Pinecone** (ahora)
2. **Instalar dependencias** (`pip install -r requirements.txt`)
3. **Ejecutar agente** (`python main.py --chat`)
4. **Hacer preguntas** sobre tus PDFs

## 💬 Referencia Rápida

```bash
# Instalación
pip install pinecone-client sentence-transformers PyPDF2

# Configuración (PowerShell)
$env:PINECONE_API_KEY = "tu_key"
$env:PINECONE_INDEX_NAME = "company-documents"
$env:PINECONE_ENVIRONMENT = "us-east-1"

# Ejecución
python main.py --chat              # Interactivo
python main.py "tu pregunta"       # Pregunta única
python main.py --reset --chat      # Re-indexar
```

---

¡Listo! Tu agente RAG ahora usa Pinecone como base de datos vectorial en la nube. 🎉
