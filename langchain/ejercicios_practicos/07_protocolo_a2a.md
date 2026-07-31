# 07 - Protocolo Agent-to-Agent (A2A)

## Objetivo

Estandarizar la comunicación entre agentes con contratos interoperables.

## Qué agregar al proyecto

- esquema de mensaje A2A
- control de correlación por `conversation_id`
- idempotencia por `message_id`

## Tareas

1. Definir campos obligatorios del mensaje
2. Tipificar intents y respuestas esperadas
3. Implementar timeout, retry y deduplicación
4. Auditar eventos clave de comunicación

## Escenarios de prueba

- mensaje válido end-to-end
- mensaje duplicado (debe ignorarse o consolidarse)
- mensaje inválido (debe rechazarse con error claro)

## Criterios de éxito

- protocolo claro y reusable
- trazabilidad completa por conversación
- recuperación robusta ante fallas de red/latencia

