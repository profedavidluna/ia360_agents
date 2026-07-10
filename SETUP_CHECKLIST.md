# ✅ Setup Checklist - Test Scenario Generator Agents

## 🚀 Pre-Requisitos (5 minutos)

### Sistema
- [ ] Python 3.8+ instalado
  ```bash
  python --version  # Debe ser 3.8+
  ```
- [ ] pip funcionando
  ```bash
  pip --version
  ```
- [ ] Acceso a terminal/cmd
- [ ] Editor de código (VS Code, PyCharm, etc.)

### LLM (Requerido)
- [ ] LLM service corriendo (ej: Claude API)
  ```bash
  # Verifica que responde
  curl -X POST http://localhost:8082/v1/messages \
    -H "Content-Type: application/json" \
    -d '{"model": "claude-3-5-sonnet-20241022", "messages": [{"role": "user", "content": "test"}]}'
  ```

---

## 📦 Instalación (5 minutos)

### Paso 1: Descarga los archivos
```bash
# Estos 4 archivos deben estar en el mismo directorio:
ls -la test_scenario_agent_*.py
ls -la ejemplo_uso_agentes_test.py
```

### Paso 2: Verifica instalación de Python
```bash
python -m pip --version
```

### Paso 3: (Opcional) Crea venv
```bash
# Recomendado pero no requerido
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### Paso 4: Instala dependencias (si faltan)
```bash
# Mínimo requerido
pip install requests  # Si no está

# Para Opción C solamente
pip install chromadb
```

### Paso 5: Verifica instalación
```bash
python -c "import sys; print(f'Python {sys.version}')"
```

---

## 🔧 Configuración (5 minutos)

### Paso 1: Configura LLM (REQUERIDO)

#### Opción A: Variables de entorno
```bash
# Linux/Mac
export LLM_BASE_URL="http://localhost:8082/v1/messages"
export LLM_API_KEY="tu_api_key"
export LLM_MODEL="claude-3-5-sonnet-20241022"

# Windows (CMD)
set LLM_BASE_URL=http://localhost:8082/v1/messages
set LLM_API_KEY=tu_api_key
set LLM_MODEL=claude-3-5-sonnet-20241022

# Windows (PowerShell)
$env:LLM_BASE_URL = "http://localhost:8082/v1/messages"
$env:LLM_API_KEY = "tu_api_key"
$env:LLM_MODEL = "claude-3-5-sonnet-20241022"
```

#### Opción B: Archivo .env (en el directorio)
```bash
# .env
LLM_BASE_URL=http://localhost:8082/v1/messages
LLM_API_KEY=tu_api_key
LLM_MODEL=claude-3-5-sonnet-20241022
```

#### Opción C: Modifica el código (último recurso)
```python
# En test_scenario_agent_a.py, línea ~30
def get_llm_config() -> dict[str, str]:
    return {
        "base_url": "tu_url",  # ← Aquí
        "api_key": "tu_api_key",  # ← Aquí
        "model": "tu_modelo",  # ← Aquí
    }
```

### Paso 2: Verifica configuración
```bash
# Ejecuta script de test
python -c "
import os
print('LLM_BASE_URL:', os.getenv('LLM_BASE_URL'))
print('LLM_API_KEY:', 'configurado' if os.getenv('LLM_API_KEY') else 'NO configurado')
print('LLM_MODEL:', os.getenv('LLM_MODEL'))
"
```

---

## ✅ Verificación de Setup (10 minutos)

### Paso 1: Test de importación

```bash
# Opción A
python -c "from test_scenario_agent_a import TestScenarioGenerator; print('✓ Opción A OK')"

# Opción B
python -c "from test_scenario_agent_b import TestScenarioGenerator; print('✓ Opción B OK')"

# Opción C
python -c "from test_scenario_agent_c import TestScenarioGeneratorWithRAG; print('✓ Opción C OK')"
```

**Esperado:** ✓ Todos OK

### Paso 2: Test de LLM

```bash
python << 'EOF'
import os
import json
from urllib.request import urlopen
import urllib.request as urllib_request

config = {
    "base_url": os.getenv("LLM_BASE_URL", "http://localhost:8082/v1/messages"),
    "api_key": os.getenv("LLM_API_KEY", "freecc"),
    "model": os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022"),
}

body = {
    "model": config["model"],
    "max_tokens": 50,
    "messages": [{"role": "user", "content": "say ok"}],
    "temperature": 0.3,
}

headers = {
    "Content-Type": "application/json",
    "x-api-key": config["api_key"]
}

try:
    data = json.dumps(body).encode("utf-8")
    request = urllib_request.Request(config["base_url"], data=data, headers=headers, method="POST")
    with urlopen(request, timeout=10) as response:
        print("✓ LLM conectado exitosamente")
except Exception as e:
    print(f"✗ Error conectando LLM: {e}")
    print("  Verifica: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL")
EOF
```

**Esperado:** ✓ LLM conectado exitosamente

### Paso 3: Test de generación

```bash
python << 'EOF'
from test_scenario_agent_a import TestScenarioGenerator

spec = """
Función: add(a, b)
Retorna: suma de dos números
"""

try:
    generator = TestScenarioGenerator()
    scenarios = generator.analyze_function(spec)
    if scenarios:
        print(f"✓ Generación exitosa: {len(scenarios)} escenarios")
    else:
        print("⚠ No se generaron escenarios (verifica LLM)")
except Exception as e:
    print(f"✗ Error en generación: {e}")
EOF
```

**Esperado:** ✓ Generación exitosa

---

## 🎯 Verificación Final (5 minutos)

### Checklist Completo

```
SISTEMA
─────
✓ Python 3.8+
✓ pip funcionando
✓ Terminal/CMD accesible
✓ Editor de código listo

ARCHIVOS
─────
✓ test_scenario_agent_a.py (300 líneas)
✓ test_scenario_agent_b.py (600 líneas)
✓ test_scenario_agent_c.py (800 líneas)
✓ ejemplo_uso_agentes_test.py (400 líneas)

CONFIGURACIÓN
─────
✓ LLM_BASE_URL configurado
✓ LLM_API_KEY configurado
✓ LLM_MODEL configurado
✓ LLM responde

DEPENDENCIAS
─────
✓ requests (presente)
✓ chromadb (si usas C)

TESTS
─────
✓ Importación A
✓ Importación B
✓ Importación C
✓ Conexión LLM
✓ Generación básica
```

---

## 🚀 Primer Uso (5 minutos)

Si todo pasó ✅, estás listo!

### Opción 1: Ver ejemplos
```bash
python ejemplo_uso_agentes_test.py --opcion todas
```

### Opción 2: Usar Opción A
```bash
python test_scenario_agent_a.py
```

### Opción 3: Usar Opción B
```bash
python test_scenario_agent_b.py
```

### Opción 4: Usar Opción C
```bash
python test_scenario_agent_c.py
```

---

## ❌ Troubleshooting Setup

### Error: "No module named 'test_scenario_agent_a'"

**Causa:** Archivo no existe o está en otro directorio

**Solución:**
```bash
# Verifica que los archivos están donde ejecutas
ls test_scenario_agent_a.py

# Si no, cópialos
cp /ruta/correcta/test_scenario_agent_a.py .

# O agrega a PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

### Error: "LLM_BASE_URL not set"

**Causa:** Variables de entorno no configuradas

**Solución:**
```bash
# Verifica
echo $LLM_BASE_URL  # Linux/Mac
echo %LLM_BASE_URL%  # Windows

# Si no aparece, configura
export LLM_BASE_URL="http://localhost:8082/v1/messages"
export LLM_API_KEY="tu_api_key"
export LLM_MODEL="claude-3-5-sonnet-20241022"

# Verifica de nuevo
echo $LLM_BASE_URL
```

---

### Error: "Connection refused" (LLM)

**Causa:** LLM service no está corriendo

**Solución:**
```bash
# Verifica que LLM está corriendo
ping localhost
curl http://localhost:8082/v1/messages

# Si no responde:
# 1. Inicia el LLM service
# 2. Espera a que esté listo
# 3. Intenta de nuevo
```

---

### Error: "No module named 'chromadb'"

**Causa:** chromadb no instalado (solo si usas Opción C)

**Solución:**
```bash
pip install chromadb
python -c "import chromadb; print('✓ chromadb OK')"
```

---

### Error: "JSON decode error" (LLM response)

**Causa:** LLM devuelve respuesta inesperada

**Solución:**
```bash
# Debug: verifica respuesta LLM
curl -X POST http://localhost:8082/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: tu_api_key" \
  -d '{"model": "claude-3-5-sonnet-20241022", "max_tokens": 50, "messages": [{"role": "user", "content": "test"}]}'

# Debería retornar JSON válido
# Si no, verifica configuración del LLM
```

---

## 📊 Verificación Estado

### Script de diagnóstico completo
```bash
python << 'EOF'
import os
import sys

print("=" * 60)
print("DIAGNÓSTICO - Test Scenario Generators")
print("=" * 60)

# 1. Python
print(f"\n1. Python: {sys.version}")

# 2. Archivos
import pathlib
files = [
    "test_scenario_agent_a.py",
    "test_scenario_agent_b.py",
    "test_scenario_agent_c.py",
    "ejemplo_uso_agentes_test.py"
]
print(f"\n2. Archivos:")
for f in files:
    exists = "✓" if pathlib.Path(f).exists() else "✗"
    print(f"   {exists} {f}")

# 3. Configuración
print(f"\n3. LLM Configuration:")
print(f"   LLM_BASE_URL: {os.getenv('LLM_BASE_URL', '✗ NO SET')}")
print(f"   LLM_API_KEY: {'✓ SET' if os.getenv('LLM_API_KEY') else '✗ NO SET'}")
print(f"   LLM_MODEL: {os.getenv('LLM_MODEL', '✗ NO SET')}")

# 4. Dependencias
print(f"\n4. Dependencies:")
try:
    import requests
    print(f"   ✓ requests")
except:
    print(f"   ✗ requests (pip install requests)")

try:
    import chromadb
    print(f"   ✓ chromadb")
except:
    print(f"   ⚠ chromadb (solo para Opción C)")

# 5. Imports
print(f"\n5. Imports:")
try:
    from test_scenario_agent_a import TestScenarioGenerator
    print(f"   ✓ Opción A")
except Exception as e:
    print(f"   ✗ Opción A: {e}")

try:
    from test_scenario_agent_b import TestScenarioGenerator
    print(f"   ✓ Opción B")
except Exception as e:
    print(f"   ✗ Opción B: {e}")

try:
    from test_scenario_agent_c import TestScenarioGeneratorWithRAG
    print(f"   ✓ Opción C")
except Exception as e:
    print(f"   ⚠ Opción C: {e}")

print(f"\n{'=' * 60}")
EOF
```

---

## ✨ Setup Exitoso

Si todo está ✅:

```
✓ Python 3.8+
✓ Archivos presentes
✓ LLM configurado
✓ Dependencias OK
✓ Imports OK
→ ¡LISTO PARA USAR!
```

---

## 🎯 Próximos Pasos

Después del setup:

1. **Lee** README_TEST_AGENTS.md (2 min)
2. **Ejecuta** ejemplo_uso_agentes_test.py (5 min)
3. **Elige** opción A, B o C (COMPARATIVA_AGENTES_TEST.md)
4. **Practica** con tu propia función
5. **Integra** en tu proyecto

---

## 📞 Ayuda

```
Problema                    Archivo
──────────────────────────────────────
Setup no funciona           Este archivo
No puedo decidir opción     COMPARATIVA_AGENTES_TEST.md
Error en generación         GUIA_AGENTES_TEST.md
Quiero ver código           test_scenario_agent_*.py
Necesito ejemplo            ejemplo_uso_agentes_test.py
```

---

## 🎉 Completado!

Si llegaste aquí y todo funciona → **¡Felicitaciones!**

Estás listo para:
- ✅ Generar tests automáticamente
- ✅ Ahorrar tiempo en testing
- ✅ Mejorar cobertura de tests
- ✅ Enseñar testing patterns

**¡A generar tests! 🚀**

---

Última actualización: 2026-07-09  
Versión: 1.0.0
