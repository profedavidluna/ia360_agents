# 🎯 INICIO AQUÍ - Test Scenario Generators

**Bienvenido. Este archivo te llevará por el camino correcto en 2 minutos.**

---

## ⚡ 3 Preguntas para Encontrar tu Ruta

### Pregunta 1: ¿Cuál es tu objetivo?

- [ ] **Aprender** cómo funcionan → Ve a [RUTA 1](#ruta-1-estudiante)
- [ ] **Usar en producción** → Ve a [RUTA 2](#ruta-2-desarrollador)
- [ ] **Entender todo** → Ve a [RUTA 3](#ruta-3-experto)

---

## 🚀 RUTA 1: Estudiante (Aprender)

### Tu Objetivo
Entender cómo funcionan los Test Scenario Generators

### Tiempo Total
15 minutos

### Pasos

#### Paso 1: Lee esto (2 min)
Este archivo es suficiente para entender qué son.

#### Paso 2: Ver ejemplo (5 min)
```bash
python test_scenario_agent_a.py
```
→ Verás escenarios generados en tiempo real

#### Paso 3: Leer documentación (5 min)
- [RESUMEN_AGENTES_TEST.md](RESUMEN_AGENTES_TEST.md) - Qué es

#### Paso 4: Decidir (3 min)
- Haz esto → Empieza con [RUTA 2](#ruta-2-desarrollador)

---

## 💻 RUTA 2: Desarrollador (Producción)

### Tu Objetivo
Usar Test Scenario Generators en tu proyecto

### Tiempo Total
30 minutos (setup + primera generación)

### Pasos

#### Paso 1: Setup (5 min)
Sigue [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)

```bash
# 1. Configura LLM
export LLM_BASE_URL="http://localhost:8082/v1/messages"
export LLM_API_KEY="tu_api_key"
export LLM_MODEL="claude-3-5-sonnet-20241022"

# 2. Verifica
python -c "from test_scenario_agent_b import TestScenarioGenerator; print('✓ OK')"
```

#### Paso 2: Decide qué opción usar (5 min)
- [COMPARATIVA_AGENTES_TEST.md](COMPARATIVA_AGENTES_TEST.md)
- **Recomendación:** Opción B para producción

#### Paso 3: Aprende tu opción (10 min)
- [GUIA_AGENTES_TEST.md](GUIA_AGENTES_TEST.md) - Sección relevante

#### Paso 4: Implementa (10 min)
```python
from test_scenario_agent_b import TestScenarioGenerator

spec = """
Función: mi_funcion
Parámetros: x (int), y (str)
Retorna: combinación de x e y
"""

generator = TestScenarioGenerator()
scenarios = generator.analyze_function(spec)
test_code = generator.generate_test_code("mi_funcion", "mi_modulo")

print(test_code)  # ¡Tests generados!
```

#### ✅ Listo
Ahora tienes tests automáticos

---

## 🎓 RUTA 3: Experto (Todo)

### Tu Objetivo
Entender completamente y posiblemente contribuir

### Tiempo Total
2-3 horas

### Pasos

#### Paso 1: Setup (10 min)
- [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)

#### Paso 2: Entender concepto (20 min)
- [README_TEST_AGENTS.md](README_TEST_AGENTS.md)
- [RESUMEN_AGENTES_TEST.md](RESUMEN_AGENTES_TEST.md)

#### Paso 3: Comparar opciones (20 min)
- [COMPARATIVA_AGENTES_TEST.md](COMPARATIVA_AGENTES_TEST.md)

#### Paso 4: Guía completa (30 min)
- [GUIA_AGENTES_TEST.md](GUIA_AGENTES_TEST.md)

#### Paso 5: Código fuente (45 min)
- Lee `test_scenario_agent_a.py`
- Lee `test_scenario_agent_b.py`
- Lee `test_scenario_agent_c.py`

#### Paso 6: Ejemplos (30 min)
- [ejemplo_uso_agentes_test.py](ejemplo_uso_agentes_test.py)

#### Paso 7: Experimentar (60 min)
- Crea tus propias funciones
- Genera tests para todas
- Valida cobertura

#### ✅ Eres experto
Ahora puedes:
- Explicar cómo funcionan
- Usar cualquier opción
- Resolver problemas
- Posiblemente contribuir

---

## 🎯 ¿Cuál es tu situación?

### "Acabo de llegar aquí"
→ [RUTA 1](#ruta-1-estudiante) (15 min)

### "Quiero usar esto en mi proyecto"
→ [RUTA 2](#ruta-2-desarrollador) (30 min)

### "Quiero entender todo"
→ [RUTA 3](#ruta-3-experto) (2-3 horas)

### "Solo dame la respuesta rápida"
→ [Quick Answer](#respuesta-rápida) (60 segundos)

---

## 💡 Respuesta Rápida

### ¿Qué es?
**Herramienta de IA que genera tests automáticamente**

### ¿Cómo funciona?
1. Describes una función
2. El agent analiza
3. Genera escenarios
4. Crea código de tests

### ¿Cuánto ahorras?
- **Manual:** 30-60 minutos por función
- **Con esto:** 1-2 minutos
- **Ahorro:** 95%+

### ¿Cuáles son mis opciones?
- **A (Simple):** Opción rápida, ideal para aprender
- **B (Pro):** Opción recomendada, para producción
- **C (Enterprise):** Opción avanzada, con AI learning

### ¿Cuál elijo?
**Recomendación:** 
- Estudiante → **A**
- Producción → **B**
- Empresa grande → **C**

### ¿Dónde empiezo?
```bash
python test_scenario_agent_b.py  # ← Comienza aquí
```

---

## 📊 Mapa Visual

```
TÚ ESTÁS AQUÍ
     ↓
   ¿NUEVO?
   ├─ SÍ → RUTA 1 (15 min)
   │        ↓
   │    RESUMEN
   │        ↓
   │    EJEMPLOS
   │        ↓
   └─→ RUTA 2 o 3
   │
   ├─ NO, QUIERO USAR → RUTA 2 (30 min)
   │                     ↓
   │                 SETUP
   │                     ↓
   │                 COMPARATIVA
   │                     ↓
   │                 GUIA
   │                     ↓
   │                 IMPLEMENTAR
   │
   └─ QUIERO TODO → RUTA 3 (2-3 horas)
                    ↓
                  TODO
```

---

## 🎬 Comienza Ahora

### Opción 1: Rápido (60 segundos)
```bash
python test_scenario_agent_a.py
```
→ Verás escenarios generados

### Opción 2: Completo (5 minutos)
```bash
python ejemplo_uso_agentes_test.py --opcion todas
```
→ Verás todas las opciones en acción

### Opción 3: Personalizado (10 minutos)
```bash
# Edita test_scenario_agent_a.py
# Cambia la especificación (línea ~200)
python test_scenario_agent_a.py
```
→ Genera tests para tu función

---

## 📚 Documentos Ordenados por Urgencia

```
URGENCIA ALTA (necesitas ahora)
├─ Este archivo (INICIO_AQUI)
├─ README_TEST_AGENTS.md (2 min)
└─ SETUP_CHECKLIST.md (5 min)

URGENCIA MEDIA (necesitas hoy)
├─ COMPARATIVA_AGENTES_TEST.md (10 min)
├─ GUIA_AGENTES_TEST.md (30 min)
└─ test_scenario_agent_b.py (código)

URGENCIA BAJA (si tienes tiempo)
├─ test_scenario_agent_a.py (learning)
├─ test_scenario_agent_c.py (advanced)
├─ RESUMEN_AGENTES_TEST.md (context)
├─ INDEX_TEST_AGENTS.md (navigation)
└─ MANIFEST_AGENTES_TEST.md (reference)
```

---

## ✅ Verificación Rápida

¿Funciona todo?

```bash
# 1. ¿Existen los archivos?
ls test_scenario_agent_*.py

# 2. ¿LLM está configurado?
echo $LLM_BASE_URL

# 3. ¿Genera tests?
python -c "
from test_scenario_agent_a import TestScenarioGenerator
gen = TestScenarioGenerator()
gen.analyze_function('Función: test\nRetorna: 42')
"
```

Si todo es ✅ → **¡Estás listo!**

---

## 🆘 Si Algo Falla

1. **Error de importación:**
   - Ve a [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md) → Troubleshooting

2. **LLM no responde:**
   - Verifica que LLM service está corriendo
   - Verifica variables de entorno

3. **No sé qué hacer:**
   - Sigue [RUTA 1](#ruta-1-estudiante) (15 min)

4. **Tengo un error específico:**
   - Ve a [GUIA_AGENTES_TEST.md](GUIA_AGENTES_TEST.md) → Troubleshooting

---

## 🎯 Próximos Pasos

### Si elegiste Ruta 1 (Estudiante)
```
1. RESUMEN_AGENTES_TEST.md (5 min) ← AHORA
2. ejemplo_uso_agentes_test.py --opcion a (5 min)
3. Decide qué opción aprender
```

### Si elegiste Ruta 2 (Desarrollador)
```
1. SETUP_CHECKLIST.md (5 min) ← AHORA
2. Ejecuta python -c "verificación"
3. COMPARATIVA_AGENTES_TEST.md (10 min)
4. test_scenario_agent_b.py (usar)
```

### Si elegiste Ruta 3 (Experto)
```
1. SETUP_CHECKLIST.md (5 min)
2. README_TEST_AGENTS.md (2 min)
3. GUIA_AGENTES_TEST.md (30 min) ← AHORA
4. Código fuente (lee y experimenta)
```

---

## 🎉 Bienvenida

**Ahora sabes:**
✅ Qué es esto  
✅ Cómo funciona  
✅ Por dónde empezar  
✅ Cuál es tu ruta  

**Próximo paso:**
→ Elige tu ruta arriba  
→ Haz clic en el documento  
→ ¡Aprende!

---

## 💬 TL;DR (Demasiado Largo; No Leí)

```
QUÉ:      Generador automático de tests con IA
POR QUÉ:  10-15x más rápido que manual
CÓMO:     Describe función → recibe tests
OPCIONES: A (fácil), B (pro), C (enterprise)
EMPIEZA:  python test_scenario_agent_b.py
```

---

**Cualquiera sea tu ruta, ¡bienvenido! 🚀**

---

Última actualización: 2026-07-09  
Versión: 1.0.0

📌 **Siguiente paso: Elige tu ruta arriba** ⬆️
