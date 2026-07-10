# ✅ Solución: Error en main_chroma_backup.py

## Problema
```
✗ Error: VectorStore.search() got an unexpected keyword argument 'top_k'
```

## Causa
En la línea 357 se estaba pasando `top_k=5` a `search()`:

```python
# ❌ ANTES (Incorrecto)
relevant_docs = self.vector_store.search(question, top_k=5)
```

El método `search()` en Chroma NO acepta `top_k` como parámetro. Usa `n_results` internamente.

## Solución (Ya Aplicada)
```python
# ✅ DESPUÉS (Correcto)
relevant_docs = self.vector_store.search(question)
```

El método ya usa `self.config.top_k` internamente (línea 226).

## Cambio Exacto
**Archivo**: `main_chroma_backup.py`
**Línea**: 357
**De**: `self.vector_store.search(question, top_k=5)`
**A**: `self.vector_store.search(question)`

## Estado
✅ **ARREGLADO** - El archivo ya fue corregido automáticamente

## Prueba
```bash
python main_chroma_backup.py --chat
```

Si queda colgado en la carga inicial, es normal (cargando modelos de embeddings).
Espera 30-60 segundos en la primera ejecución.

## Nota sobre Chroma vs Pinecone
```
Chroma:
├─ Búsqueda: collection.query(query_texts=[...], n_results=k)
└─ Top k se pasa como: n_results

Pinecone:
├─ Búsqueda: index.query(vector=..., top_k=k)
└─ Top k se pasa como: top_k

LangChain abstrae esto:
├─ .as_retriever(search_kwargs={"k": 5})
└─ Funciona igual para ambos
```

## Por qué main_langchain.py no tiene este problema
```python
# main_langchain.py usa LangChain
retriever = vector_store.as_retriever(
    search_kwargs={"k": self.top_k}
)
```

LangChain maneja los detalles de cada vector store automáticamente. ✅
