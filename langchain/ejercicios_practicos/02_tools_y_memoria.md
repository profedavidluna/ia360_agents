# 02 - Tools + Memoria Conversacional

## Objetivo

Enriquecer el agente con herramientas y memoria de sesión.

## Qué agregar al proyecto

- tool de clima
- tool de políticas de viaje
- memoria corta por conversación

## Tareas

1. Conectar 2 tools con timeout y manejo de errores
2. Guardar contexto de la conversación
3. Evitar repetir preguntas ya respondidas
4. Citar qué tool aportó cada dato clave

## Escenarios de prueba

- primera consulta de destino
- pregunta de seguimiento ("¿y si cambio a París?")
- tool caída (debe degradar con aviso)

## Criterios de éxito

- usa tools de forma controlada
- mantiene contexto entre turnos
- responde aun cuando una tool falle

