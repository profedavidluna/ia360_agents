# 03 - Flujo con Estado usando LangGraph

## Objetivo

Migrar de flujo lineal a flujo por estados con ramas de decisión.

## Implementación realizada

### Archivos

- `/home/runner/work/ia360_agents/ia360_agents/travelops/exercise03_langgraph_state.py`
- `/home/runner/work/ia360_agents/ia360_agents/test_exercise03_langgraph_state.py`

### Estado tipado (`TravelOpsGraphState`)

Dataclass que fluye a través de todos los nodos:

- `destination`, `budget` — salidas del nodo de intención
- `weather_data`, `policy_data`, `context_errors` — salidas del nodo de contexto
- `recommendation`, `proposal_attempts` — salidas del nodo de propuesta
- `validation_passed`, `validation_notes` — salidas del nodo de validación
- `error_node`, `error_message` — control de errores
- `evidence`, `risks`, `status`, `current_node` — acumuladores y control de flujo

### Nodos y topología del grafo

```
intent
  ├─(sin destino)──► error_recovery ──► end
  └─(con destino)──► context ──► proposal
                                     ├─(falla LLM)──► error_recovery ──► end
                                     └─(ok)──► validation
                                                   ├─(pasa)──► end
                                                   ├─(falla, reintentos disponibles)──► proposal
                                                   └─(falla, máx reintentos)──► error_recovery ──► end
```

1. **intent** — extrae destino y presupuesto; enruta a `error_recovery` si no hay destino
2. **context** — consulta `weather_tool` y `policy_tool` con timeout; siempre avanza (modo degradado si hay errores)
3. **proposal** — genera recomendación con el LLM; ante falla de LLM enruta a `error_recovery`
4. **validation** — verifica que la propuesta no esté vacía, no sea muy corta y mencione el destino; reintenta hasta `MAX_PROPOSAL_RETRIES = 3`
5. **error_recovery** — genera respuesta degradada según el nodo de origen y cierra el flujo

### Límite de iteraciones

El motor del grafo corta a los 20 ciclos (`_GRAPH_ITERATION_LIMIT`) para prevenir loops infinitos.

### Checkpoint por sesión

`TravelOpsGraphAgent._checkpoints` almacena el último `TravelOpsGraphState` por `conversation_id`, recuperable con `get_checkpoint(conversation_id)`.

## Escenarios de prueba cubiertos

- ruta feliz completa (todos los nodos exitosos, checkpoint guardado)
- ambas tools fallan → modo degradado con `STATUS_PARTIAL`
- sólo una tool falla → evidencia parcial, riesgos registrados
- validación falla en primer intento, pasa en segundo (retry controlado)
- validación falla en todos los intentos → `error_recovery`, `STATUS_PARTIAL`
- consulta sin destino → `error_recovery`, `STATUS_NEEDS_CLARIFICATION`

## Criterios de éxito

- flujo determinista y trazable ✓
- errores manejados por rama definida ✓
- estado persistente reanudable ✓

