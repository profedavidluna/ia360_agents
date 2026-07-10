# 🗂️ Explorador de Base de Datos RAG

Herramienta para visualizar, explorar y analizar la base de datos vectorial de Chroma como si fuera una BD relacional.

## 🚀 Inicio Rápido

### Modo Interactivo (recomendado)

```bash
python explore_rag.py --interactive

# O simplemente
python explore_rag.py
```

Te presentará un menú interactivo:

```
======================================================================
🗂️  EXPLORADOR DE RAG - MENÚ PRINCIPAL
======================================================================

1. Ver estadísticas
2. Listar documentos
3. Ver detalles de un documento
4. Buscar documentos
5. Exportar a JSON
6. Salir

Opción (1-6):
```

### Línea de comandos

```bash
# Ver estadísticas
python explore_rag.py --stats

# Listar primeros 20 documentos
python explore_rag.py --list 20

# Ver detalles de un documento específico
python explore_rag.py --detail "nombre_pdf_chunk_0"

# Buscar documentos
python explore_rag.py --search "política de vacaciones"

# Exportar a JSON
python explore_rag.py --export my_backup.json
```

---

## 📊 Opciones Disponibles

### 1️⃣ Ver Estadísticas

Muestra información general de la BD:

```bash
python explore_rag.py --stats
```

**Output:**
```
======================================================================
📊 ESTADÍSTICAS DE LA BASE DE DATOS
======================================================================

📁 Información General:
  Total de chunks: 77
  Archivos fuente: 2
  Tamaño de embeddings: 384 dimensiones (all-MiniLM-L6-v2)
  Ubicación: .chroma

📄 Distribución por archivo:
  • manual_empleado.pdf: 45 chunks
  • politicas.pdf: 32 chunks
```

### 2️⃣ Listar Documentos

Muestra todos los documentos en formato tabla:

```bash
python explore_rag.py --list 10
```

**Output:**
```
======================================================================
📋 DOCUMENTOS EN LA BASE DE DATOS
======================================================================

Mostrando 10 de 77 documentos:
+-----+----------+-----------------------------------+-------------------+
| #   | ID       | Texto (preview)                 | Fuente            |
+=====+==========+===================================+===================+
| 1   | manual_... | La empresa fue fundada en 2010   | manual_empleado   |
| 2   | manual_... | Tenemos 500 empleados           | manual_empleado   |
| 3   | politica..| Política de vacaciones: 20 días | politicas.pdf     |
+-----+----------+-----------------------------------+-------------------+
```

### 3️⃣ Ver Detalles

Muestra todo sobre un documento específico:

```bash
python explore_rag.py --detail "manual_empleado.pdf_chunk_0"
```

**Output:**
```
======================================================================
📄 DETALLES DEL DOCUMENTO
======================================================================

ID: manual_empleado.pdf_chunk_0
Fuente: manual_empleado.pdf

📝 Texto:
────────────────────────────────────────────────────────────────────
La empresa fue fundada en 2010 con la misión de revolucionar...
... (500 caracteres más)
────────────────────────────────────────────────────────────────────

🔢 Embedding:
  Dimensiones: 384
  Primeros 10 valores: [0.123, -0.456, 0.789, ...]
  Últimos 10 valores: [..., 0.234, -0.567]
```

### 4️⃣ Buscar Documentos

Busca documentos similares:

```bash
python explore_rag.py --search "vacaciones"
```

**Output:**
```
======================================================================
🔍 RESULTADOS DE BÚSQUEDA
======================================================================

Búsqueda: vacaciones

+-----+---------------+--------------------+-------------------+
| #   | Similaridad   | Texto (preview)    | Fuente            |
+=====+===============+====================+===================+
| 1   | 0.945         | Vacaciones: 20...  | politicas.pdf     |
| 2   | 0.812         | Días libres...     | manual_empleado   |
| 3   | 0.567         | Beneficios...      | politicas.pdf     |
+-----+---------------+--------------------+-------------------+
```

Los números de similaridad van de 0 (no relacionado) a 1 (idéntico).

### 5️⃣ Exportar a JSON

Descarga toda la BD en JSON:

```bash
python explore_rag.py --export backup.json
```

**Contenido del JSON:**
```json
{
  "config": {
    "collection": "company_documents",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "embedding_model": "all-MiniLM-L6-v2"
  },
  "documents": [
    {
      "id": "manual_empleado.pdf_chunk_0",
      "text": "La empresa fue fundada...",
      "source": "manual_empleado.pdf"
    },
    ...
  ]
}
```

---

## 💡 Casos de Uso

### Verificar que los PDFs se indexaron correctamente

```bash
python explore_rag.py --stats
```

Verifica que los archivos aparecen y tienen chunks.

### Inspeccionar un chunk específico

```bash
python explore_rag.py --detail "archivo.pdf_chunk_42"
```

Ver exactamente qué texto contiene un chunk.

### Verificar la calidad de búsqueda

```bash
python explore_rag.py --search "tu pregunta"
```

Ver qué documentos son recuperados y cuán similares son.

### Hacer backup de los datos

```bash
python explore_rag.py --export backup_2024.json
```

Guardar todos los datos para importar después o analizar.

### Debugging de RAG

Si el agente no responde bien, usa explore_rag para:

1. Verificar que los PDFs están indexados: `--stats`
2. Ver los chunks: `--list 50`
3. Probar la búsqueda: `--search "tu pregunta"`
4. Inspeccionar chunks individuales: `--detail ID`

---

## 🔄 Flujo Típico de Uso

### Después de indexar nuevos PDFs:

```bash
# 1. Ver estadísticas
python explore_rag.py --stats
✓ Ves cuántos chunks hay

# 2. Listar documentos
python explore_rag.py --list 5
✓ Ves qué se indexó

# 3. Probar búsqueda
python explore_rag.py --search "tema importante"
✓ Ves si la búsqueda funciona

# 4. Hacer backup
python explore_rag.py --export backup.json
✓ Guardas los datos
```

### Modo interactivo para exploración

```bash
python explore_rag.py

# Menú interactivo con todas las opciones
# Puedes experimentar sin escribir comandos
```

---

## 📚 Entendiendo los Resultados

### Similaridad (en búsquedas)

```
Similaridad = 1 - Distance (en cosine similarity)

0.95 = Muy similar (muy relevante)
0.80 = Similar (relevante)
0.60 = Moderadamente similar
0.40 = Poco relacionado
0.10 = No relacionado
```

### Chunks

Un chunk es un fragmento de texto. Por ejemplo:

```
"manual_empleado.pdf_chunk_0"   ← Primer chunk de manual_empleado.pdf
"manual_empleado.pdf_chunk_45"  ← Chunk número 45 del mismo archivo
"politicas.pdf_chunk_3"         ← Tercer chunk de politicas.pdf
```

### Embeddings

Un embedding es un vector numérico:

```
"Dimensiones: 384"
→ El texto se representa como 384 números

[0.123, -0.456, 0.789, ..., 0.234]  ← 384 números
```

Dos textos similares tendrán embeddings similares.

---

## 🐛 Solución de Problemas

### Error: "No se encontró la colección"

Significa que no hay datos indexados.

```bash
# Primero indexa datos
python main.py --chat

# Luego explora
python explore_rag.py --stats
```

### Error: "Documento no encontrado"

El ID del documento no existe. Primero lista para obtener IDs válidos:

```bash
python explore_rag.py --list 5
# Copia un ID de la tabla
python explore_rag.py --detail "ID_copiado"
```

### La búsqueda devuelve resultados irrelevantes

Puede ser que:
1. El PDF no tiene el contenido relevante
2. El embedding model no es el correcto
3. Los chunks son demasiado pequeños

```bash
# Intenta re-indexar con configuración diferente
python main.py --reset --chat
```

---

## 📈 Análisis Avanzado

### Analizar la distribución de chunks

```bash
python explore_rag.py --stats

# Verifica:
# - Archivos con pocos chunks = posible problema
# - Archivos con muchos chunks = probablemente bien
```

### Encontrar los mejores chunks para una consulta

```bash
python explore_rag.py --search "tu consulta"

# Mira los chunks con similaridad > 0.80
# Esos son los que el agente usará
```

### Exportar y analizar con Excel

```bash
python explore_rag.py --export data.json

# Abre data.json en un editor de texto o Excel
# Analiza el contenido de los chunks
```

---

## 🎯 Resumen de Comandos

```bash
# Interactivo
python explore_rag.py

# Estadísticas
python explore_rag.py --stats

# Listar 20 documentos
python explore_rag.py --list 20

# Detalles de documento
python explore_rag.py --detail "documento_id"

# Buscar
python explore_rag.py --search "texto"

# Exportar
python explore_rag.py --export archivo.json
```

---

¡Usa este explorador para entender cómo funciona tu RAG! 🔍
