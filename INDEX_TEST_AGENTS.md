# 📑 Index - Test Scenario Generator Agents

## 🗂️ Estructura de Archivos

```
Test Scenario Generators/
│
├─ 📊 DOCUMENTACIÓN
│  ├─ README_TEST_AGENTS.md                (← EMPIEZA AQUÍ)
│  ├─ RESUMEN_AGENTES_TEST.md              (qué es, por qué)
│  ├─ COMPARATIVA_AGENTES_TEST.md          (tabla comparativa)
│  ├─ GUIA_AGENTES_TEST.md                 (guía completa)
│  └─ INDEX_TEST_AGENTS.md                 (este archivo)
│
├─ 💻 CÓDIGO
│  ├─ test_scenario_agent_a.py             (~300 líneas, Simple)
│  ├─ test_scenario_agent_b.py             (~600 líneas, Professional)
│  ├─ test_scenario_agent_c.py             (~800 líneas, RAG)
│  └─ ejemplo_uso_agentes_test.py          (ejemplos de las 3)
│
└─ 🎯 ARCHIVOS GENERADOS (por el agent)
   ├─ test_calculate_discount.py           (ejemplo A)
   ├─ example_a_tests.py
   ├─ example_b_tests.py
   ├─ example_b_scenarios.json
   ├─ example_c_tests.py
   └─ ... (más archivos según uses)
```

---

## 🎓 Ruta de Aprendizaje

### Opción 1: Inicio Rápido (15 minutos)

```
1. Leer README_TEST_AGENTS.md (2 min)
   ↓ Entiendes qué es
2. Ejecutar ejemplo_uso_agentes_test.py (5 min)
   ↓ Ves en acción
3. Probar test_scenario_agent_a.py (5 min)
   ↓ Generas tu primer test
4. Decidir: ¿A, B o C?
```

### Opción 2: Comprensión Completa (45 minutos)

```
1. RESUMEN_AGENTES_TEST.md (10 min)
   ↓ Concepto general
2. COMPARATIVA_AGENTES_TEST.md (15 min)
   ↓ Diferencias claras
3. Ejecutar ejemplos (10 min)
   ↓ Ver en vivo
4. GUIA_AGENTES_TEST.md - read specific sections (10 min)
   ↓ Profundizar en elegida
5. Implementar en proyecto
```

### Opción 3: Deep Dive (2-3 horas)

```
1. README_TEST_AGENTS.md (5 min)
2. RESUMEN_AGENTES_TEST.md (10 min)
3. COMPARATIVA_AGENTES_TEST.md (20 min)
4. Código fuente (30 min)
   ├─ test_scenario_agent_a.py (10 min)
   ├─ test_scenario_agent_b.py (10 min)
   └─ test_scenario_agent_c.py (10 min)
5. GUIA_AGENTES_TEST.md (30 min)
6. ejemplo_uso_agentes_test.py (20 min)
7. Experimentar (60+ min)
```

---

## 📍 Navegación por Pregunta

### "¿Qué es esto?"
→ Empieza con `README_TEST_AGENTS.md`

### "¿Cuál uso?"
→ Lee `COMPARATIVA_AGENTES_TEST.md`

### "¿Cómo empiezo?"
→ `README_TEST_AGENTS.md` + ejecuta `ejemplo_uso_agentes_test.py`

### "¿Cuál es la diferencia?"
→ Ver tabla en `COMPARATIVA_AGENTES_TEST.md`

### "¿Cómo uso la Opción A?"
→ `test_scenario_agent_a.py` (es el código fuente)

### "Quiero entender todo"
→ Lee completo: `GUIA_AGENTES_TEST.md`

### "Necesito ejemplos"
→ `ejemplo_uso_agentes_test.py`

### "Tengo un error"
→ `GUIA_AGENTES_TEST.md` → Troubleshooting

### "Compara todas las opciones"
→ `COMPARATIVA_AGENTES_TEST.md`

---

## 📊 Comparación Rápida

### Por Tiempo de Lectura

| Doc | Tiempo | Propósito |
|-----|--------|----------|
| README_TEST_AGENTS.md | 2 min | Quick start |
| RESUMEN_AGENTES_TEST.md | 5 min | Overview |
| COMPARATIVA_AGENTES_TEST.md | 10 min | Decisión |
| GUIA_AGENTES_TEST.md | 30 min | Completo |

### Por Tipo de Usuario

| Usuario | Ruta |
|---------|------|
| Estudiante | README → ejemplos → A → B → C |
| Developer | README → B → proyecto |
| Architect | COMPARATIVA → B o C → GUIA |
| Manager | RESUMEN → COMPARATIVA |

### Por Objetivo

| Objetivo | Documento |
|----------|-----------|
| Entender concepto | RESUMEN_AGENTES_TEST.md |
| Decidir opción | COMPARATIVA_AGENTES_TEST.md |
| Aprender a usar | GUIA_AGENTES_TEST.md |
| Ver código | test_scenario_agent_*.py |
| Ejecutar ejemplo | ejemplo_uso_agentes_test.py |

---

## 🚀 Guía Paso a Paso

### Paso 1: Configuración (5 minutos)

```bash
# 1. Verifica que tienes Python 3.8+
python --version

# 2. Configura LLM
export LLM_BASE_URL="http://localhost:8082/v1/messages"
export LLM_API_KEY="tu_api_key"
export LLM_MODEL="claude-3-5-sonnet-20241022"

# 3. (Opcional) Instala chromadb para Opción C
pip install chromadb
```

### Paso 2: Primer Test (5 minutos)

```bash
# Ejecuta el ejemplo simple
python test_scenario_agent_a.py
```

### Paso 3: Elige tu Opción (10 minutos)

- Lee `COMPARATIVA_AGENTES_TEST.md`
- Elige A, B o C
- Lee la sección relevante en `GUIA_AGENTES_TEST.md`

### Paso 4: Implementa (20+ minutos)

```python
# Usa la opción que elegiste
from test_scenario_agent_b import TestScenarioGenerator

generator = TestScenarioGenerator()
scenarios = generator.analyze_function("tu_spec")
test_code = generator.generate_test_code("tu_funcion")
```

### Paso 5: Integra en Proyecto (30+ minutos)

- Adapta a tu flujo
- Agrega a CI/CD si quieres
- Entrena al equipo

---

## 📖 Contenido por Documento

### README_TEST_AGENTS.md
```
✓ Quick start
✓ Configuración (2 min)
✓ Ejemplo mínimo
✓ FAQ rápido
✓ Troubleshooting básico
```

### RESUMEN_AGENTES_TEST.md
```
✓ Qué es
✓ Por qué lo necesitas
✓ Las 3 opciones (tabla)
✓ Ventajas/limitaciones
✓ Casos de uso
✓ Métricas de éxito
```

### COMPARATIVA_AGENTES_TEST.md
```
✓ Tabla comparativa visual
✓ Funcionalidades lado a lado
✓ Análisis por caso de uso
✓ ROI por opción
✓ Recomendaciones por contexto
✓ Matriz de decisión
```

### GUIA_AGENTES_TEST.md
```
✓ Instalación completa
✓ API Reference
✓ Ejemplos detallados
✓ Casos de uso en profundidad
✓ Troubleshooting exhaustivo
✓ Patterns avanzados
```

### test_scenario_agent_a.py
```python
✓ ~300 líneas
✓ Código funcional
✓ TestScenarioGenerator
✓ Ejemplo main()
✓ Documentación inline
```

### test_scenario_agent_b.py
```python
✓ ~600 líneas
✓ Validación completa
✓ Análisis de cobertura
✓ Export JSON
✓ Reportes
```

### test_scenario_agent_c.py
```python
✓ ~800 líneas
✓ RAG con Chroma
✓ Búsqueda semántica
✓ Confidence scores
✓ Learning report
```

### ejemplo_uso_agentes_test.py
```python
✓ Ejemplo A
✓ Ejemplo B
✓ Ejemplo C
✓ Tabla comparativa
✓ Ejecutable directamente
```

---

## 🎯 Matriz de Decisión

```
Pregunta                        Respuesta           Documento
────────────────────────────────────────────────────────────
¿Qué debo leer primero?         README              README_TEST_AGENTS.md
¿Por qué lo necesito?           Overview            RESUMEN_AGENTES_TEST.md
¿Qué opción elijo?              Comparar            COMPARATIVA_AGENTES_TEST.md
¿Cómo lo uso?                   Aprender            GUIA_AGENTES_TEST.md
¿Cómo veo código?               Fuente              test_scenario_agent_*.py
¿Dónde hay ejemplos?            Ejecutar            ejemplo_uso_agentes_test.py
¿Tengo un error?                Solucionar          GUIA_AGENTES_TEST.md
¿Comparar funcionalmente?       Tabla               COMPARATIVA_AGENTES_TEST.md
```

---

## 📚 Lectura Recomendada

### En 5 minutos
1. README_TEST_AGENTS.md

### En 15 minutos
1. README_TEST_AGENTS.md
2. RESUMEN_AGENTES_TEST.md

### En 30 minutos
1. README_TEST_AGENTS.md
2. RESUMEN_AGENTES_TEST.md
3. COMPARATIVA_AGENTES_TEST.md
4. Ver ejemplos en vivo

### En 2 horas
- Todo lo anterior
- GUIA_AGENTES_TEST.md completo
- Código fuente
- Experimentar

---

## 🔗 Referencias Cruzadas

### Desde README_TEST_AGENTS.md
- "¿Cuál opción?" → COMPARATIVA_AGENTES_TEST.md
- "Troubleshooting" → GUIA_AGENTES_TEST.md
- "Ejemplos" → ejemplo_uso_agentes_test.py

### Desde RESUMEN_AGENTES_TEST.md
- "Diferencias" → COMPARATIVA_AGENTES_TEST.md
- "Cómo empezar" → README_TEST_AGENTS.md
- "Más detalles" → GUIA_AGENTES_TEST.md

### Desde COMPARATIVA_AGENTES_TEST.md
- "Cómo usar" → GUIA_AGENTES_TEST.md
- "Quick start" → README_TEST_AGENTS.md
- "Ver código" → test_scenario_agent_*.py

### Desde GUIA_AGENTES_TEST.md
- "Comparación" → COMPARATIVA_AGENTES_TEST.md
- "Ejemplos" → ejemplo_uso_agentes_test.py
- "API" → test_scenario_agent_*.py

---

## ⚡ Quick Links

```
Empezar                      → README_TEST_AGENTS.md
Decidir opción               → COMPARATIVA_AGENTES_TEST.md
Aprender a usar              → GUIA_AGENTES_TEST.md
Ver ejemplos                 → ejemplo_uso_agentes_test.py
Leer resumen                 → RESUMEN_AGENTES_TEST.md
Ver índice                   → INDEX_TEST_AGENTS.md
```

---

## 🎓 Certificado de Aprendizaje

Si completaste esto ✅:

- [ ] Leí README_TEST_AGENTS.md
- [ ] Entiendo las 3 opciones
- [ ] Ejecuté los ejemplos
- [ ] Elegí una opción
- [ ] Generé mi primer test
- [ ] Lo integré en mi proyecto

**Si hiciste todo → Felicitaciones! 🎉 Ya eres experto en Test Scenario Generators**

---

## 📞 Soporte

```
Problema                    Solución
────────────────────────────────────────────
No entiendo               Leer RESUMEN
Debo elegir               Ver COMPARATIVA
Necesito aprender         Leer GUIA
Tengo error               Ver Troubleshooting
Quiero ver código         Ver test_scenario_*.py
Quiero ejemplo            Ejecutar ejemplo_uso
No funciona LLM           Ver GUIA - Config
No genera tests           Ver GUIA - Troubleshooting
```

---

## 📈 Roadmap de Lectura

```
Día 1: Introducción
├─ README (2 min)
├─ RESUMEN (5 min)
└─ Ver ejemplos (5 min)

Día 2: Decisión
├─ COMPARATIVA (15 min)
├─ Sección relevante GUIA (10 min)
└─ Probar opción elegida (20 min)

Día 3-5: Implementación
├─ GUIA completa (30 min)
├─ Integrar en proyecto (60+ min)
└─ Entrenar equipo

Semana 2: Avanzado (opcional)
├─ Explorar otras opciones
├─ Optimizaciones
└─ Contribuir mejoras
```

---

## 🌟 Puntos Clave

```
TEST SCENARIO GENERATORS
├─ 3 opciones: A (fácil), B (pro), C (enterprise)
├─ Generan tests automáticamente
├─ 10-15x más rápido que manual
├─ Requieren especificación clara
└─ Mejores resultados con LLM bien configurado

LECTURA RECOMENDADA
├─ Start: README (2 min)
├─ Decide: COMPARATIVA (10 min)
├─ Learn: GUIA (30 min)
└─ Do: Implementar (60+ min)

DOCUMENTOS
├─ Rápido: README
├─ Visual: COMPARATIVA
├─ Completo: GUIA
└─ Código: test_scenario_agent_*.py
```

---

**Este es tu mapa. ¡Comienza donde quieras!** 🚀

---

Última actualización: 2026-07-09
Versión: 1.0.0
