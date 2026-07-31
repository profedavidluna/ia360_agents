# 06 - Multiagente (3 Agentes)

## Objetivo

Extender a tres agentes para elevar calidad y control de riesgo.

## Diseño mínimo

- **Orquestador**: coordina el flujo completo
- **Investigador**: obtiene contexto y datos externos
- **Validador**: revisa consistencia, riesgo y formato final

## Tareas

1. Mantener contratos de mensajes por rol
2. Agregar etapa de validación obligatoria
3. Definir regla de aprobación/rechazo
4. Escalar al humano en casos críticos

## Escenarios de prueba

- flujo exitoso con aprobación
- inconsistencias detectadas por validador
- operación crítica que requiere confirmación humana

## Criterios de éxito

- cada agente con responsabilidad única
- orquestación clara de ida y vuelta
- salida final más robusta que en ejercicio 05

