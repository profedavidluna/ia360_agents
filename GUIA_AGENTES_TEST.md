# 🧪 Test Scenario Generator Agents - Guía Completa

## 📚 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Las 3 Opciones](#las-3-opciones)
3. [Instalación](#instalación)
4. [Uso Rápido](#uso-rápido)
5. [Ejemplos Detallados](#ejemplos-detallados)
6. [API Reference](#api-reference)
7. [Casos de Uso](#casos-de-uso)
8. [Troubleshooting](#troubleshooting)

---

## Introducción

Los **Test Scenario Generator Agents** son herramientas que usan LLM (Large Language Models) para:

1. **Analizar especificaciones** de funciones
2. **Generar escenarios de prueba** automáticamente
3. **Crear código de tests** listo para ejecutar
4. **Validar cobertura** de pruebas
5. **Aprender de tests históricos** (opción avanzada)

### ¿Por qué es útil?

```
Antes (manual):
- Leer especificación
- Pensar en casos de prueba
- Escribir código de test
- Tiempo: 30-60 minutos por función
- Riesgo: Olvidar casos importantes

Con Test Scenario Generator:
- Especificar función
- Generar escenarios
- Generar tests
- Tiempo: 2-5 minutos
- Mejor: Cobertura completa + patrones consistentes
```

---

## Las 3 Opciones

### 📦 Opción A: Quick & Simple

**Mejor para:** Aprendizaje y prototipado rápido

```
Características:
✓ ~300 líneas de código
✓ Sin dependencias pesadas
✓ Genración rápida
✓ Ideal para comenzar
✗ Sin validación completa
✗ Sin análisis de cobertura
✗ Sin exportación de datos
```

**Estructura básica:**
```python
from test_scenario_agent_a import TestScenarioGenerator

generator = TestScenarioGenerator()
scenarios = generator.analyze_function(spec)
test_code = generator.generate_test_code("function_name")
```

**Uso:**
```bash
python test_scenario_agent_a.py
```

---

### 🏢 Opción B: Complete & Professional

**Mejor para:** Desarrollo en equipo y producción

```
Características:
✓ ~600 líneas de código
✓ Validación completa
✓ Análisis de cobertura
✓ Exportación JSON
✓ Reportes detallados
✓ Metadatos completos
✗ Más líneas de código
✗ Más lento que A
```

**Estructura profesional:**
```python
from test_scenario_agent_b import TestScenarioGenerator, TestType

generator = TestScenarioGenerator()
scenarios = generator.analyze_function(spec)

# Análisis de cobertura
coverage = generator.analyze_coverage()

# Validación
for scenario in scenarios:
    if scenario.validate():
        print(f"✓ {scenario.name}")

# Exportación
generator.save_to_file("scenarios.json")
```

**Uso:**
```bash
python test_scenario_agent_b.py
```

---

### 🚀 Opción C: With RAG Learning

**Mejor para:** Empresas con base de tests histórica

```
Características:
✓ ~800 líneas de código
✓ Aprende de tests históricos
✓ Vectorización con Chroma
✓ Confidence scores
✓ Análisis semántico
✓ Mejora iterativa
✗ Requiere chromadb
✗ Más lento (indexación)
✗ Requiere carpeta de tests
```

**Estructura avanzada con RAG:**
```python
from test_scenario_agent_c import TestScenarioGeneratorWithRAG

# Indexar tests existentes
generator = TestScenarioGeneratorWithRAG("ruta/a/tests")

# Analizar y aprender
scenarios = generator.analyze_function(spec)

# Ver lo que aprendió
report = generator.generate_learning_report()
print(report)
```

**Uso:**
```bash
python test_scenario_agent_c.py
```

---

## Instalación

### Requisitos base (todas las opciones)
```bash
pip install requests
```

### Opción B (recomendado)
No requiere instalación adicional

### Opción C (con RAG)
```bash
pip install chromadb
```

### Verificar instalación
```bash
python -c "from test_scenario_agent_a import TestScenarioGenerator; print('✓ Opción A OK')"
python -c "from test_scenario_agent_b import TestScenarioGenerator; print('✓ Opción B OK')"
python -c "from test_scenario_agent_c import TestScenarioGeneratorWithRAG; print('✓ Opción C OK')"
```

---

## Uso Rápido

### 1️⃣ Opción A (30 segundos)

```python
from test_scenario_agent_a import TestScenarioGenerator

# Especificar función
spec = """
Función: is_even
Parámetros:
- n (int): número
Retorna: True si n es par, False si es impar
"""

# Generar
generator = TestScenarioGenerator()
scenarios = generator.analyze_function(spec)
test_code = generator.generate_test_code("is_even")

# Ver resultado
print(test_code)
```

### 2️⃣ Opción B (1 minuto)

```python
from test_scenario_agent_b import TestScenarioGenerator

spec = """..."""

generator = TestScenarioGenerator()
scenarios = generator.analyze_function(spec)

# Análisis completo
print(generator.generate_report())
print(generator.generate_test_code("is_even"))

# Guardar
generator.save_to_file("scenarios.json")
```

### 3️⃣ Opción C (2 minutos con indexación)

```python
from test_scenario_agent_c import TestScenarioGeneratorWithRAG

spec = """..."""

# Indexar tests existentes
generator = TestScenarioGeneratorWithRAG("tests/")
scenarios = generator.analyze_function(spec)

# Ver aprendizaje
print(generator.generate_learning_report())
print(generator.generate_test_code("is_even"))
```

---

## Ejemplos Detallados

### Ejemplo 1: Función Simple (calculate_discount)

**Especificación:**
```python
spec = """
Función: calculate_discount
Parámetros:
- price (float): Precio del producto
- customer_type (str): Tipo ('regular', 'vip', 'corporate')
Comportamiento:
- Si price < 0: ValueError
- regular: sin descuento
- vip: 10% descuento
- corporate: 15% descuento
"""
```

**Ejecución:**
```python
from test_scenario_agent_b import TestScenarioGenerator

generator = TestScenarioGenerator()
scenarios = generator.analyze_function(spec)
generator.display_scenarios()
print(generator.generate_report())

test_code = generator.generate_test_code("calculate_discount", "commerce")
with open("test_discount.py", "w") as f:
    f.write(test_code)
```

**Salida esperada:**
```
📋 [1] happy_path_regular_customer (⭐)
    Tipo: happy_path
    Entrada: {'price': 100.0, 'customer_type': 'regular'}
    Esperado: 100.0

📋 [2] happy_path_vip_customer (⭐)
    Tipo: happy_path
    Entrada: {'price': 100.0, 'customer_type': 'vip'}
    Esperado: 90.0

📋 [3] error_negative_price (⭐⭐⭐⭐⭐)
    Tipo: error
    Entrada: {'price': -10.0, 'customer_type': 'regular'}
    Esperado: ValueError
```

### Ejemplo 2: Función Compleja (payment_processing)

**Con Opción B:**
```python
spec = """
Función: process_payment
Parámetros:
- amount (float): Monto (> 0)
- currency (str): 'USD', 'EUR', 'COP'
- card_number (str): 16 dígitos
- card_cvv (str): 3 dígitos
"""

generator = TestScenarioGenerator()
scenarios = generator.analyze_function(spec)
coverage = generator.analyze_coverage()

print(f"Total escenarios: {coverage.total_scenarios}")
print(f"Happy paths: {coverage.happy_path_count}")
print(f"Error cases: {coverage.error_cases_count}")
print(f"Cobertura: {coverage.coverage_percentage:.1f}%")
```

### Ejemplo 3: Con Aprendizaje RAG

**Opción C:**
```python
generator = TestScenarioGeneratorWithRAG("tests_historicos/")

spec = """Función: validate_user_input..."""

scenarios = generator.analyze_function(spec)

# Ver qué aprendió
for scenario in scenarios:
    print(f"{scenario.name}")
    print(f"  Confianza: {scenario.confidence_score:.2f}")
    if scenario.learned_from:
        print(f"  Aprendido de: {scenario.learned_from}")

print(generator.generate_learning_report())
```

---

## API Reference

### Opción A: TestScenarioGenerator

#### Métodos principales

**`analyze_function(function_spec: str) -> List[TestScenario]`**
```python
# Analiza especificación y retorna escenarios
scenarios = generator.analyze_function("""
    Función: my_func
    Parámetros: x (int)
    Comportamiento: retorna x * 2
""")
```

**`generate_test_code(function_name: str, module_name: str) -> str`**
```python
# Genera código de tests
code = generator.generate_test_code("my_func", "my_module")
```

**`display_scenarios() -> None`**
```python
# Muestra escenarios en formato legible
generator.display_scenarios()
```

---

### Opción B: TestScenarioGenerator (profesional)

#### Métodos adicionales

**`analyze_coverage() -> CoverageAnalysis`**
```python
coverage = generator.analyze_coverage()
print(coverage.total_scenarios)
print(coverage.happy_path_count)
print(coverage.coverage_percentage)
```

**`generate_report() -> str`**
```python
report = generator.generate_report()
print(report)
```

**`save_to_file(filename: str) -> None`**
```python
generator.save_to_file("escenarios.json")
```

---

### Opción C: TestScenarioGeneratorWithRAG

#### Métodos adicionales

**`__init__(test_folder: str)`**
```python
# Indexa tests existentes automáticamente
generator = TestScenarioGeneratorWithRAG("tests/")
```

**`generate_learning_report() -> str`**
```python
report = generator.generate_learning_report()
# Muestra lo que aprendió de tests históricos
```

**Attributes de TestScenario (con RAG):**
```python
scenario.learned_from      # Lista de tests similares
scenario.confidence_score  # 0.0-1.0, qué tan seguro está
```

---

## Casos de Uso

### 📖 Caso 1: Testing de módulo de autenticación

```python
from test_scenario_agent_b import TestScenarioGenerator

spec = """
Función: authenticate_user
Parámetros:
- username (str): nombre de usuario
- password (str): contraseña
- mfa_code (str, opcional): código MFA
Retorna:
- dict con user_id si es exitoso
- raises AuthenticationError si falla
"""

generator = TestScenarioGenerator()
scenarios = generator.analyze_function(spec)

# Validar cada escenario
valid_count = 0
for scenario in scenarios:
    if scenario.validate():
        valid_count += 1

print(f"✓ {valid_count}/{len(scenarios)} escenarios válidos")

# Exportar
generator.save_to_file("auth_tests.json")
test_code = generator.generate_test_code("authenticate_user", "auth")

with open("test_authentication.py", "w") as f:
    f.write(test_code)
```

### 🔄 Caso 2: Testing iterativo con RAG

```python
from test_scenario_agent_c import TestScenarioGeneratorWithRAG

# Generar tests base
generator = TestScenarioGeneratorWithRAG("empresa_tests/")

specs = [
    "Función A: ...",
    "Función B: ...",
    "Función C: ..."
]

for spec in specs:
    scenarios = generator.analyze_function(spec)
    
    # Generar con aprendizaje previo
    test_code = generator.generate_test_code("func_name")
    
    print(generator.generate_learning_report())
```

### 🚀 Caso 3: CI/CD Integration

```bash
#!/bin/bash
# generate_tests.sh

cd project/

# Generar tests automáticamente
python test_scenario_agent_b.py \
    --spec functions/ \
    --output tests/generated/

# Validar
pytest tests/generated/ -v

# Guardar reporte
python -c "
from test_scenario_agent_b import TestScenarioGenerator
import json

with open('scenarios.json') as f:
    data = json.load(f)

print(f'Generated {len(data)} scenarios')
"
```

---

## Troubleshooting

### ❌ Error: "No module named 'test_scenario_agent_a'"

**Solución:**
```bash
# Asegúrate que estén en el mismo directorio
ls test_scenario_agent_*.py

# O agrega a PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python tu_script.py
```

### ❌ Error: "LLM_BASE_URL not configured"

**Solución:**
```bash
export LLM_BASE_URL="http://localhost:8082/v1/messages"
export LLM_API_KEY="tu_api_key"
export LLM_MODEL="claude-3-5-sonnet-20241022"
python test_scenario_agent_a.py
```

### ❌ Error: "chromadb not installed" (Opción C)

**Solución:**
```bash
pip install chromadb
python test_scenario_agent_c.py
```

### ⚠️ Los tests generados no compilan

**Verifica:**
1. El nombre de la función es correcto
2. El módulo existe e importa correctamente
3. Los tipos de datos son válidos

```python
# Debug
generator.display_scenarios()

# Ver cada escenario
for scenario in generator.scenarios:
    print(f"Scenario: {scenario.name}")
    print(f"  Inputs: {scenario.inputs}")
    print(f"  Expected: {scenario.expected_output}")
```

### 🔧 Performance lento (Opción C)

**Optimizaciones:**
```python
# Limitar búsquedas
generator = TestScenarioGeneratorWithRAG("tests/")

# No indexar todos los archivos
# Modificar el código para limitar a últimos 100 tests

# O aumentar timeout
import urllib.request
urllib.request.socket.setdefaulttimeout(120)
```

---

## 📊 Comparativa Técnica

```
OPCIÓN A vs OPCIÓN B vs OPCIÓN C
───────────────────────────────────────────────

                      A           B           C
Imports             3           4           6+
Dependencies        0           0           chromadb
Métodos             5           8           10+
Complejidad ciclom. 2-3         4-5         6-7
Tiempo generación   <1s         1-2s        5-10s
Líneas código       300         600         800

Tipo TestScenario   Básico      Completo    +RAG
├─ name             ✓           ✓           ✓
├─ description      ✓           ✓           ✓
├─ inputs           ✓           ✓           ✓
├─ expected_output  ✓           ✓           ✓
├─ test_type        ✓           ✓           ✓
├─ priority         ✗           ✓           ✓
├─ tags             ✗           ✓           ✓
├─ preconditions    ✗           ✓           ✓
├─ postconditions   ✗           ✓           ✓
├─ learned_from     ✗           ✗           ✓
└─ confidence_score ✗           ✗           ✓

Análisis
├─ Cobertura        ✗           ✓           ✓
├─ Validación       ✗           ✓           ✓
├─ Reportes         ✗           ✓           ✓
├─ JSON export      ✗           ✓           ✓
└─ RAG learning     ✗           ✗           ✓
```

---

## 🎓 Próximos Pasos

1. **Comienza con Opción A** para entender los conceptos
2. **Pasa a Opción B** para desarrollo profesional
3. **Explora Opción C** si tu empresa tiene base de datos de tests

---

## 📝 Licencia y Créditos

Estos agentes fueron creados con propósito educativo para enseñar:
- Generación de tests con IA
- Integración de LLMs
- Análisis de código
- RAG (Retrieval Augmented Generation)

---

**¿Preguntas o sugerencias?** Consulta la sección [Troubleshooting](#troubleshooting) o revisa los ejemplos en `ejemplo_uso_agentes_test.py`
