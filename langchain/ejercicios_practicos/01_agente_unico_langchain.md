# 01 - Agente Único con LangChain

## Objetivo

Crear un agente básico que responda consultas de viaje con prompt estructurado.

## Qué agregar al proyecto

- estructura mínima del agente
- prompt de sistema con reglas
- salida en formato consistente

## Tareas

1. Definir contrato de entrada/salida
2. Implementar agente de una sola responsabilidad
3. Manejar errores comunes del LLM
4. Registrar logs básicos

## Escenarios de prueba

- consulta simple de destino
- consulta con presupuesto
- consulta ambigua (debe pedir aclaración)

## Criterios de éxito

- respuestas coherentes en los 3 escenarios
- formato de salida estable
- fallback cuando falle el proveedor LLM

