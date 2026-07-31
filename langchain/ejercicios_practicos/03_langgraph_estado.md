# 03 - Flujo con Estado usando LangGraph

## Objetivo

Migrar de flujo lineal a flujo por estados con ramas de decisión.

## Qué agregar al proyecto

- estado tipado del proceso
- nodos separados por responsabilidad
- transiciones por condiciones explícitas

## Tareas

1. Definir nodos: intención, contexto, propuesta, validación
2. Modelar ramas de error y recuperación
3. Limitar iteraciones para evitar loops
4. Guardar checkpoint por sesión

## Escenarios de prueba

- ruta feliz completa
- error en recuperación de contexto
- validación negativa y regeneración controlada

## Criterios de éxito

- flujo determinista y trazable
- errores manejados por rama definida
- estado persistente reanudable

