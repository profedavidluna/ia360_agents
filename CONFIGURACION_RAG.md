# ⚙️ Configuración de Embeddings y Chunks en RAG

## 📚 Conceptos Básicos

### ¿Qué es un Chunk?

Un **chunk** es un fragmento de texto de un documento. El RAG divide los PDFs en chunks para:
- Hacer búsquedas más precisas
- Enviar contexto relevante al LLM
- Mejorar la recuperación de información

**Ejemplo:**
```
PDF original: "La empresa fue fundada en 2010. Tenemos 500 empleados..."

Chunks:
- Chunk 1: "La empresa fue fundada en 2010."
- Chunk 2: "Tenemos 500 empleados en total."
```

### ¿Qué es un Embedding?

Un **embedding** es una representación numérica de texto. Transforma palabras en números que una máquina puede entender.

**Ejemplo:**
```
Texto: "Política de vacaciones"
Embedding: [0.123, -0.456, 0.789, ..., 0.234]  (768 números típicamente)

Texto: "Días de descanso"
Embedding: [0.125, -0.450, 0.785, ..., 0.240]  (similar al anterior)
```

**Ventaja:** Embeddings similares = textos similares. Así busca Chroma.

---

## 🔧 Configuración de Chunks

### Localización en el código

En `main.py`, busca la clase `RAGConfig`:

```python
@dataclass
class RAGConfig:
    """Configuración del sistema RAG."""
    pdf_folder: str = "company_docs"
    chroma_db_path: str = ".chroma"
    collection_name: str = "company_documents"
    chunk_size: int = 1000          # ← AQUÍ: Tamaño en caracteres
    chunk_overlap: int = 200        # ← AQUÍ: Solapamiento
```

### Parámetros

#### `chunk_size` (Tamaño del chunk)
- **Rango recomendado:** 500 - 2000 caracteres
- **Default:** 1000
- **Unidad:** caracteres (no palabras)

**Impacto según tamaño:**

```
chunk_size = 500 (pequeño)
✓ Más chunks (búsquedas muy específicas)
✓ Menos contexto a la vez
✗ Puede perder contexto importante
✗ Más lento a procesar

chunk_size = 1000 (balance)
✓ Balance bueno
✓ Contexto relevante
✓ Procesamiento rápido

chunk_size = 2000 (grande)
✓ Más contexto en cada chunk
✓ Menos chunks totales
✗ Menos específico
✗ Puede incluir ruido
```

#### `chunk_overlap` (Solapamiento)
- **Rango recomendado:** 100 - 500
- **Default:** 200
- **Unidad:** caracteres

El solapamiento evita perder información entre chunks:

```
Sin solapamiento:
[Chunk 1: "La vacaciones son..."] [Chunk 2: "El salario es..."]
                              ↑ PIERDE CONTEXTO

Con solapamiento (200 chars):
[Chunk 1: "La vacaciones son...xxxxx]
                            [xxxxx El salario es..."]
                            ↑ CONSERVA CONTEXTO
```

### Cómo cambiar

#### Opción 1: Editar en el código

Abre `main.py` y modifica:

```python
@dataclass
class RAGConfig:
    chunk_size: int = 1500          # De 1000 a 1500
    chunk_overlap: int = 300        # De 200 a 300
```

#### Opción 2: Variables de entorno

```bash
# PowerShell
$env:RAG_CHUNK_SIZE = "1500"
$env:RAG_CHUNK_OVERLAP = "300"
python main.py --chat

# Cmd
set RAG_CHUNK_SIZE=1500
set RAG_CHUNK_OVERLAP=300
python main.py --chat
```

Para que esto funcione, actualiza `RAGConfig.__init__()` (ver abajo).

---

## 📊 Configuración de Embeddings

### ¿Quién genera los embeddings?

**Chroma** genera embeddings automáticamente usando modelos incluidos.

### Modelos disponibles

Chroma soporta varios modelos de embedding:

#### 1. **Default (all-MiniLM-L6-v2)**
```python
collection = client.get_or_create_collection(
    name="company_documents"
    # Sin especificar embedding_function = usa default
)

# Características:
# - 384 dimensiones
# - Rápido
# - Bueno para búsqueda general
```

#### 2. **all-mpnet-base-v2** (más grande, mejor precisión)
```python
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-mpnet-base-v2"
)

collection = client.get_or_create_collection(
    name="company_documents",
    embedding_function=embedding_function
)

# Características:
# - 768 dimensiones (mejor, más preciso)
# - Más lento
# - Mejor para búsqueda específica
```

#### 3. **Multilingual (para múltiples idiomas)**
```python
embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="multilingual-e5-small"
)

# Características:
# - Soporta 100+ idiomas
# - Bueno si mezclas español e inglés
```

### Cómo cambiar modelo de embedding

Edita la clase `VectorStore` en `main.py`:

```python
class VectorStore:
    def __init__(self, config: RAGConfig):
        if chromadb is None:
            raise ImportError("chromadb no está instalado...")
        
        self.config = config
        self.client = chromadb.PersistentClient(path=config.chroma_db_path)
        
        # OPCIÓN 1: Default (384 dims)
        self.collection = self.client.get_or_create_collection(
            name=config.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # OPCIÓN 2: Cambiar a all-mpnet-base-v2 (768 dims, más preciso)
        # from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        # embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")
        # self.collection = self.client.get_or_create_collection(
        #     name=config.collection_name,
        #     embedding_function=embedding_fn,
        #     metadata={"hnsw:space": "cosine"}
        # )
```

### Comparación de modelos

```
                    | Dimensiones | Velocidad | Precisión | Memoria
--------------------|------------|-----------|-----------|----------
all-MiniLM-L6-v2    | 384        | ✓ Rápido  | Buena     | 22 MB
all-mpnet-base-v2   | 768        | Media     | ✓ Mejor   | 420 MB
multilingual-e5     | 384        | ✓ Rápido  | Buena     | 150 MB
```

---

## 📈 Recomendaciones por caso

### Pequeña empresa (< 100 documentos)
```python
chunk_size: int = 1000
chunk_overlap: int = 200
# Default embedding (all-MiniLM-L6-v2)
```

### Mediana empresa (100-1000 documentos)
```python
chunk_size: int = 1500
chunk_overlap: int = 300
# Considera cambiar a all-mpnet-base-v2 para más precisión
```

### Grandes corporaciones (> 1000 documentos)
```python
chunk_size: int = 2000
chunk_overlap: int = 400
# Usa all-mpnet-base-v2 para mejor precisión
# Considera aumentar top_k en búsquedas
```

### Documentos técnicos (code, specs)
```python
chunk_size: int = 800    # Más pequeños para ser específicos
chunk_overlap: int = 150
# Usa all-mpnet-base-v2
```

### Documentos narrativos (políticas, guías)
```python
chunk_size: int = 1500   # Más grandes para contexto
chunk_overlap: int = 300
# Default embedding es suficiente
```

---

## 🧮 Matemáticas detrás

### Cosine Similarity (cómo busca Chroma)

```
Pregunta: "¿Cuántos días de vacaciones?"
Embedding: [0.1, 0.2, 0.3, ..., 0.9]

Documento 1: "Tenemos 20 días de vacaciones"
Embedding:   [0.11, 0.21, 0.31, ..., 0.91]  ← Muy similar!
Similarity: 0.98 (escala 0-1)

Documento 2: "El salario se paga mensualmente"
Embedding:   [0.5, 0.6, 0.7, ..., 0.2]     ← No relacionado
Similarity: 0.15
```

Chroma retorna los documentos con mayor similaridad.

---

## 🔧 Código de ejemplo personalizado

### Crear configuración personalizada

```python
# En main.py, modifica RAGConfig:

@dataclass
class RAGConfig:
    """Configuración del sistema RAG."""
    pdf_folder: str = "company_docs"
    chroma_db_path: str = ".chroma"
    collection_name: str = "company_documents"
    chunk_size: int = 1500          # Aumentado de 1000
    chunk_overlap: int = 300        # Aumentado de 200
    top_k: int = 5                  # Nuevos parámetros
    embedding_model: str = "all-mpnet-base-v2"  # Modelo de embedding
```

### Aplicar en VectorStore

```python
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

class VectorStore:
    def __init__(self, config: RAGConfig):
        if chromadb is None:
            raise ImportError("chromadb...")
        
        self.config = config
        self.client = chromadb.PersistentClient(path=config.chroma_db_path)
        
        # Usar modelo de embedding personalizado
        embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=config.embedding_model
        )
        
        self.collection = self.client.get_or_create_collection(
            name=config.collection_name,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
```

### Aplicar top_k en búsquedas

```python
def search(self, query: str) -> list[dict[str, str]]:
    results = self.collection.query(
        query_texts=[query],
        n_results=self.config.top_k  # Usar configuración
    )
    # ...
```

---

## 📝 Tabla de referencia rápida

| Parámetro | Rango | Default | Afecta |
|-----------|-------|---------|--------|
| chunk_size | 500-2000 | 1000 | Precisión, velocidad |
| chunk_overlap | 100-500 | 200 | Conservación de contexto |
| top_k | 3-10 | 5 | Cantidad de documentos recuperados |
| embedding_model | varios | all-MiniLM-L6-v2 | Precisión, velocidad, memoria |

---

## 🚀 Testing

### Probar diferentes configuraciones

```bash
# Test 1: Chunks pequeños
# Edita main.py: chunk_size = 500, chunk_overlap = 100
python main.py --reset --chat

# Test 2: Chunks grandes
# Edita main.py: chunk_size = 2000, chunk_overlap = 400
python main.py --reset --chat

# Compara resultados y elige la mejor
```

### Medir rendimiento

```python
import time

def test_config():
    agent = RAGAgent()
    
    start = time.time()
    agent.initialize()
    index_time = time.time() - start
    
    start = time.time()
    reply = agent.answer_question("¿Cuántos días de vacaciones?")
    query_time = time.time() - start
    
    print(f"Indexación: {index_time:.2f}s")
    print(f"Consulta: {query_time:.2f}s")
```

---

## 📚 Resumen

1. **Chunks**: Divide documentos en piezas manejables
   - `chunk_size`: Tamaño de cada pieza (1000 default)
   - `chunk_overlap`: Solapamiento para conservar contexto (200 default)

2. **Embeddings**: Convierte texto a números
   - Default: `all-MiniLM-L6-v2` (384 dims, rápido)
   - Premium: `all-mpnet-base-v2` (768 dims, preciso)

3. **Búsqueda**: Usa cosine similarity para encontrar documentos similares
   - `top_k`: Cantidad de resultados (5 default)

4. **Recomendación**: Para empezar está bien el default, ajusta según resultados
