# 01 - Agente Único con LangChain (Versión Completa)

## Objetivo

Crear un agente único de TravelOps IA que entregue recomendaciones de viaje con contrato estable, manejo de errores del proveedor LLM y logging básico.

## Implementación realizada

### Archivos

- `/home/runner/work/ia360_agents/ia360_agents/travelops/exercise01_single_agent.py`
- `/home/runner/work/ia360_agents/ia360_agents/test_exercise01_single_agent.py`

### Capacidades incluidas

1. **Contrato de entrada/salida**
   - `TravelOpsRequest`: `conversation_id`, `user_query`, `context`
   - `TravelOpsResponse`: `status`, `intent_summary`, `recommendation`, `alternatives`, `evidence`, `risks`, `next_action`
2. **Responsabilidad única**
   - agente enfocado en interpretar la consulta y devolver recomendación de viaje
3. **Manejo de errores LLM**
   - captura errores de conexión/proveedor
   - fallback determinístico con estado `partial`
4. **Logs básicos**
   - inicio de request
   - caso de aclaración
   - respuesta con LLM
   - degradación por falla del proveedor

## Escenarios de prueba cubiertos

- consulta simple de destino
- consulta con presupuesto
- consulta ambigua (pide aclaración)
- falla del LLM con fallback degradado

## Resultado esperado

- respuestas coherentes en escenarios base
- formato de salida estable (`to_dict`)
- fallback funcional cuando falle el proveedor LLM
