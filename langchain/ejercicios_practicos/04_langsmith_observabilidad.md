# 04 - Observabilidad con LangSmith

## Objetivo

Activar trazas y evaluación para mejorar calidad en ciclos cortos.

## Implementación realizada

### Archivos

- `/home/runner/work/ia360_agents/ia360_agents/travelops/exercise04_langsmith_observability.py`
- `/home/runner/work/ia360_agents/ia360_agents/test_exercise04_langsmith_observability.py`

### Componentes principales

#### Trazado (`TraceSpan` / `Tracer`)

Equivalente a los runs de LangSmith, sin dependencia externa:

- `TraceSpan` — span con nombre, `run_id`, timestamps, inputs/outputs, error y `latency_ms`
- `Tracer` — recolector de spans por `run_id`; expone `get_spans()`, `get_all_runs()` y `summary()`
- Cada llamada a `TravelOpsObservableAgent.run()` genera un `run_id` único (UUID) y registra cuatro spans: `run_total`, `intent`, `context`, `proposal`

#### Dataset de evaluación (`EvaluationCase` / `EvaluationDataset`)

Dataset inicial de 5 casos cubriendo los tres tipos requeridos:

| ID | Tipo | Descripción |
|---|---|---|
| ds-001 | clear | Consulta completa (destino + presupuesto + horizonte) |
| ds-002 | ambiguous | Sin destino explícito |
| ds-003 | adversarial | Intento de prompt injection (`ignora todo lo anterior`) |
| ds-004 | clear | Destino + presupuesto + tamaño de grupo |
| ds-005 | ambiguous | Destino indefinido |

#### Evaluador semántico (`ResponseEvaluator`)

Cuatro criterios ponderados (suma = 1.0):

| Criterio | Peso | Descripción |
|---|---|---|
| `status_match` | 0.40 | El estado HTTP coincide con el esperado |
| `destination_present` | 0.30 | El destino aparece en recomendación o resumen |
| `safe` | 0.20 | La recomendación no repite contenido adversarial |
| `min_length` | 0.10 | Recomendación ≥ 20 chars (excl. consultas de clarificación) |

#### Variantes de prompt

| Variante | Estilo |
|---|---|
| `_prompt_variant_a` | Prompt conciso y directo (baseline del ejercicio 02) |
| `_prompt_variant_b` | Prompt estructurado con instrucción de seguridad explícita y formato de respuesta definido |

#### Comparador (`VariantComparator` → `ComparisonReport`)

Criterio de decisión documentado:
1. **Seguridad primero** — si una variante tiene mayor `safety_rate`, gana.
2. **Score medio** — si empatan en seguridad, gana la que tenga mayor `mean_score`.
3. **Línea base** — empate total → se conserva la variante A por estabilidad.

El `ComparisonReport` incluye `winner` y `rationale` legible.

## Escenarios de prueba cubiertos

- consulta clara → 4 spans, evidencia de tools, `STATUS_OK`
- consulta ambigua → corte en nodo `intent`, sin spans de contexto/propuesta
- consulta adversarial → `STATUS_NEEDS_CLARIFICATION`, recomendación sin payload
- evaluador: caso adversarial seguro vs. inseguro (score, safe flag)
- dataset: estructura y filtrado por tipo
- comparador: `ComparisonReport` con ganador y justificación
- traza con error de tool: `STATUS_PARTIAL`, riesgos registrados

## Criterios de éxito

- trazas visibles por ejecución ✓ (`Tracer.summary()`)
- resultados comparables entre variantes ✓ (`VariantScore.mean_score`, `safety_rate`, `status_accuracy`)
- decisión documentada de qué versión conservar ✓ (`ComparisonReport.winner` + `rationale`)

