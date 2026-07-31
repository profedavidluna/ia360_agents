# 05 - Multiagente (2 Agentes)

## Objetivo

Separar responsabilidades entre dos agentes colaborando.

## Diseño mínimo

- **Agente Planificador**: entiende solicitud y define plan
- **Agente Especialista**: consulta herramientas y devuelve evidencias

## Tareas

1. Definir contrato de mensajes entre agentes
2. Implementar delegación y retorno de resultados
3. Manejar timeout y retry de comunicación
4. Consolidar respuesta final al usuario

## Escenarios de prueba

- solicitud estándar
- especialista tarda y responde al retry
- especialista falla y planificador entra en fallback

## Criterios de éxito

- colaboración sin acoplamiento fuerte
- mensajes con formato consistente
- respuesta final incluye evidencia del especialista

