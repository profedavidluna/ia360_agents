# 🧪 Test Scenario Generator Agents

> Generadores de tests automáticos usando IA (LLM + opcional RAG)

## ⚡ Quick Start (2 minutos)

### 1. Configura variables de entorno
```bash
export LLM_BASE_URL="http://localhost:8082/v1/messages"
export LLM_API_KEY="tu_api_key"
export LLM_MODEL="claude-3-5-sonnet-20241022"
```

### 2. Ejecuta un ejemplo
```bash
python test_scenario_agent_a.py
# o
python test_scenario_agent_b.py
```

### 3. ¡Listo! 🎉

---

## 📦 Archivos Principales

| Archivo | Descripción | Líneas |
|---------|-------------|--------|
| `test_scenario_agent_a.py` | Opción Quick (fácil) | ~300 |
| `test_scenario_agent_b.py` | Opción Professional (producción) | ~600 |
| `test_scenario_agent_c.py` | Opción RAG (enterprise) | ~800 |
| `ejemplo_uso_agentes_test.py` | Ejemplos de las 3 opciones | ~400 |

---

## 📚 Documentación

| Documento | Propósito | Tiempo |
|-----------|-----------|--------|
| `RESUMEN_AGENTES_TEST.md` | Qué es, por qué, cómo | 5 min |
| `README_TEST_AGENTS.md` | Este archivo (quick start) | 2 min |
| `COMPARATIVA_AGENTES_TEST.md` | Tabla comparativa visual | 10 min |
| `GUIA_AGENTES_TEST.md` | Guía completa con ejemplos | 30 min |

---

## 🎯 ¿Cuál opción es para mí?

```
Aprendo Testing        → Opción A (Simple)
Desarrollo real        → Opción B (Professional)
Equipo grande + tests viejos → Opción C (RAG)
```

**→ Ver `COMPARATIVA_AGENTES_TEST.md` para decisión más informada**

---

## 💡 Ejemplo en 30 segundos

```python
from test_scenario_agent_a import TestScenarioGenerator

# 1. Especificar función
spec = """
Función: is_prime
Parámetros: n (int)
Retorna: True si es primo, False sino
"""

# 2. Generar
generator = TestScenarioGenerator()
scenarios = generator.analyze_function(spec)
test_code = generator.generate_test_code("is_prime", "math_utils")

# 3. Usar
print(test_code)  # pytest ready!
```

---

## 🚀 Próximos Pasos

1. **Leer** `RESUMEN_AGENTES_TEST.md` (5 min)
2. **Ejecutar** `python ejemplo_uso_agentes_test.py` (2 min)
3. **Elegir** qué opción usarás
4. **Probar** con tu propia función
5. **Documentarte** en `GUIA_AGENTES_TEST.md` si tienes dudas

---

## 🔧 Troubleshooting

### Error: "No module named chromadb"
```bash
pip install chromadb  # Solo para Opción C
```

### Error: "LLM_BASE_URL not configured"
```bash
export LLM_BASE_URL="http://localhost:8082/v1/messages"
export LLM_API_KEY="tu_api_key"
```

### Error: Tests no compilan
- Verifica que la función existe
- Verifica tipos de datos en inputs
- Revisa logs del LLM

→ Ver `GUIA_AGENTES_TEST.md` sección Troubleshooting

---

## 📖 Recursos

- [RESUMEN_AGENTES_TEST.md](RESUMEN_AGENTES_TEST.md) - Introducción
- [COMPARATIVA_AGENTES_TEST.md](COMPARATIVA_AGENTES_TEST.md) - Tabla comparativa
- [GUIA_AGENTES_TEST.md](GUIA_AGENTES_TEST.md) - Guía completa
- [ejemplo_uso_agentes_test.py](ejemplo_uso_agentes_test.py) - Ejemplos ejecutables

---

## 📊 Casos de Uso

✅ Automatizar generación de tests  
✅ Enseñar testing patterns  
✅ Acelerar desarrollo  
✅ Mejorar cobertura de tests  
✅ CI/CD automation  

---

## 🎓 Flujo de Aprendizaje

```
Semana 1: Conceptos
├─ Leer RESUMEN
├─ Ejecutar ejemplos
└─ Entender flujo

Semana 2: Práctica
├─ Usar Opción A en tu código
├─ Generar tests simples
└─ Validar resultado

Semana 3: Producción
├─ Opción B para equipo
├─ Integrar CI/CD
└─ Medir impacto

Mes 2: Avanzado (opcional)
├─ Opción C con RAG
├─ Indexar histórico
└─ ML learning
```

---

## ⏱️ Tiempo Típico

| Tarea | Tiempo |
|-------|--------|
| Leer esta intro | 2 min |
| Ver RESUMEN | 5 min |
| Ejecutar ejemplos | 5 min |
| Probar Opción A | 5 min |
| **Total inicial** | **17 min** |
| Aprender Opción B | 15 min |
| Implementar en proyecto | 30 min |
| **Total día 1** | **1 hora** |

---

## 🌟 Resultados Típicos

**Entrada:** 1 especificación de función
**Salida (Opción B):**
- 8-12 escenarios generados
- 150-300 líneas de test code
- Coverage analysis
- JSON export

**Tiempo:** 1-2 minutos
**vs. Manual:** 30-60 minutos
**Ahorro:** 95%+

---

## ❓ FAQ

**P: ¿Necesito LLM para funcionar?**
R: Sí, todos los agents usan LLM. Configura `.env`

**P: ¿Cuál recomiendan para empezar?**
R: Opción A para aprender, Opción B para producción

**P: ¿Funciona con otros lenguajes?**
R: Actualmente Python. Fácil adaptar para Java, C#, etc.

**P: ¿Qué pasa si mi especificación es vaga?**
R: El LLM hará lo mejor que puede. Especificaciones claras = mejores resultados

**P: ¿Puedo usar con unittest en lugar de pytest?**
R: Sí, modifica generate_test_code() para tu framework

---

## 💬 Community

- Pregunta en issues
- Comparte mejoras
- Contribuye ejemplos

---

## 📝 Licencia

Educational use. Libre para aprender y enseñar.

---

**¿Listo? Comienza:**
```bash
python ejemplo_uso_agentes_test.py --opcion todas
```

**O lee primero:**
- [RESUMEN_AGENTES_TEST.md](RESUMEN_AGENTES_TEST.md)

---

Última actualización: 2026-07-09  
Versión: 1.0.0  
Estado: ✅ Production Ready
