# 08 - Integración con MCP

## Objetivo

Conectar el sistema de agentes a herramientas externas mediante MCP.

## Qué agregar al proyecto

- definición de MCP servers necesarios
- mapeo de tools MCP por rol de agente
- controles de seguridad por permisos

## Tareas

1. Diseñar catálogo de herramientas MCP para TravelOps IA
2. Definir contratos de entrada/salida por tool
3. Implementar manejo de errores y fallback
4. Registrar telemetría de uso de tools MCP

## Escenarios de prueba

- invocación correcta de tool MCP
- tool con parámetros inválidos
- MCP server no disponible

## Criterios de éxito

- herramientas externas desacopladas del agente
- políticas de permisos activas por entorno
- trazabilidad de cada invocación MCP

