# 02 - Tools + Memoria Conversacional (Versión Completa)

## Objetivo

Extender TravelOps IA con dos tools (clima y políticas), memoria corta por conversación, control de timeout y degradación robusta.

## Implementación realizada

### Archivos

- `/home/runner/work/ia360_agents/ia360_agents/travelops/exercise02_tools_memory_agent.py`
- `/home/runner/work/ia360_agents/ia360_agents/test_exercise02_tools_memory_agent.py`

### Componentes incorporados

1. **Tool de clima** (`weather_tool`)
   - invocado con timeout configurable
   - cacheado por destino en memoria de conversación
2. **Tool de políticas** (`policy_tool`)
   - invocado con timeout configurable
   - cacheado por destino en memoria de conversación
3. **Memoria corta**
   - `last_destination`
   - `recent_queries` (últimas 5)
   - `response_cache` para consultas repetidas
   - caches de weather/policy por destino
4. **Manejo de errores y degradación**
   - timeout/falla de tool → riesgo explícito + modo `partial`
   - falla de LLM → fallback determinístico con datos de tools disponibles
5. **Trazabilidad de evidencia**
   - cada dato clave incluye fuente (`weather_tool`, `policy_tool`, `cached_*`)

## Escenarios de prueba cubiertos

- primera consulta de destino (invoca tools y evidencia de fuentes)
- pregunta de seguimiento (`¿y si cambio a París?`) manteniendo contexto conversacional
- caída de tool (respuesta degradada con aviso y continuidad)

## Resultado esperado

- uso controlado de tools con timeout y fallback
- continuidad de contexto entre turnos
- no repetición de consultas idénticas (reutilización de memoria)
- evidencia explícita de qué tool aportó cada dato
