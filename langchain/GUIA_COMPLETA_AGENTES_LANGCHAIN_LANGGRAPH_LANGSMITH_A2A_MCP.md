# Guía Paso a Paso: Programación de Agentes de IA con LangChain, LangGraph, LangSmith, A2A y MCP

## 0) Objetivo de esta guía

Esta guía está diseñada para estudiantes que **ya saben crear agentes con Python** y ahora necesitan dar el salto a:

- Arquitecturas más robustas con **LangChain**
- Orquestación de flujos con **LangGraph**
- Observabilidad, trazas y evaluación con **LangSmith**
- Comunicación entre agentes con **Agent-to-Agent (A2A)**
- Integración estándar de herramientas con **MCP (Model Context Protocol)**

---

## 1) Ruta de aprendizaje recomendada

1. Fundamentos de arquitectura de agentes modernos
2. Configuración de entorno profesional
3. Agente base con LangChain
4. Memoria y herramientas
5. Flujos de estado con LangGraph
6. Trazabilidad y evaluación con LangSmith
7. Diseño Multiagente
8. Protocolo A2A
9. Protocolo MCP
10. Seguridad, testing, despliegue y operación
11. Proyecto final integrador

---

## 2) Prerrequisitos técnicos

Debes dominar al menos:

- Python 3.10+
- Funciones, clases, typing, async básico
- API REST básica (FastAPI recomendado)
- JSON, HTTP, WebSockets (deseable)
- Git y manejo de ramas

Conocimientos recomendados:

- Docker
- pytest
- Pydantic
- conceptos de RAG

---

## 3) Stack sugerido

### Core
- **LangChain**: construcción de cadenas, agentes, herramientas y prompts
- **LangGraph**: grafos de estado para flujos determinísticos + agentes
- **LangSmith**: tracing, datasets, evaluaciones y monitoreo

### Complementarios importantes
- **FastAPI**: exponer agentes por API
- **Pydantic**: contratos de entrada/salida
- **Redis o DB**: memoria persistente y estado
- **Vector DB** (Chroma/Pinecone/FAISS): RAG
- **pytest**: pruebas unitarias e integración
- **Docker**: empaquetado reproducible

---

## 4) Diseño de arquitectura antes de programar

Antes de escribir código, define:

1. **Caso de uso** (qué problema resuelve el agente)
2. **Fronteras** (qué decide el agente y qué no)
3. **Herramientas disponibles** (APIs, DB, búsquedas, acciones)
4. **Riesgo** (acciones críticas requieren validación humana)
5. **Métricas** (latencia, costo, tasa de éxito, alucinación)

Salida mínima de diseño (documento breve):
- Objetivo
- Inputs/outputs
- Lista de tools
- Criterios de éxito
- Política de fallback

---

## 5) Paso a paso con LangChain (base sólida)

### Paso 5.1: Crear entorno aislado
1. Crear entorno virtual
2. Instalar dependencias base
3. Configurar variables de entorno (`.env`)
4. Definir proveedor LLM y modelo por defecto

### Paso 5.2: Definir contratos de datos
1. Crear modelos Pydantic para requests y responses
2. Validar entradas temprano
3. Normalizar errores en formato estándar

### Paso 5.3: Diseñar prompts por capas
1. Prompt de sistema (rol, reglas, límites)
2. Prompt de tarea (objetivo puntual)
3. Prompt de contexto (datos de negocio/RAG)
4. Prompt de salida (estructura JSON requerida)

### Paso 5.4: Añadir herramientas (tools)
1. Cada tool con interfaz clara
2. Timeout y manejo de excepciones
3. Logs de entrada/salida
4. Reintentos controlados

### Paso 5.5: Construir agente inicial
1. Agente con 1–2 tools
2. Flujo simple: pregunta → decisión → tool → respuesta
3. Registrar trazas desde el inicio

### Paso 5.6: Endurecer el agente
1. Guardrails de contenido
2. Restricción de herramientas peligrosas
3. Validación de salida estructurada
4. Modo degradado cuando falla el LLM

---

## 6) Cuándo pasar de LangChain a LangGraph

Usa **LangGraph** cuando necesites:

- Estado explícito entre pasos
- Ramas condicionales complejas
- Reintentos por nodo
- Ciclos de reflexión/revisión
- Human-in-the-loop en puntos críticos

Regla práctica:
- Flujo lineal simple → LangChain
- Flujo con estados y decisiones múltiples → LangGraph

---

## 7) Paso a paso con LangGraph

### Paso 7.1: Modelar estado global
Define un estado tipado con:
- input del usuario
- contexto acumulado
- resultados intermedios
- errores
- decisión final

### Paso 7.2: Diseñar nodos
Ejemplo de nodos típicos:
1. `classify_intent`
2. `retrieve_context`
3. `plan_actions`
4. `execute_tools`
5. `validate_output`
6. `finalize_response`

### Paso 7.3: Definir transiciones
- Transiciones por condición explícita
- Ramas de error
- Límite de iteraciones para evitar loops infinitos

### Paso 7.4: Checkpointing y persistencia
- Guardar estado por sesión
- Permitir reanudar ejecuciones
- Auditar decisiones críticas

### Paso 7.5: Human-in-the-loop
Insertar nodos de aprobación humana para:
- gastos
- cambios en sistemas productivos
- operaciones irreversibles

---

## 8) LangSmith: trazabilidad, evaluación y mejora continua

### Paso 8.1: Activar tracing
1. Conectar proyecto con clave y nombre de entorno
2. Trazar cada ejecución de cadena/grafo
3. Ver latencia por nodo y costo por interacción

### Paso 8.2: Crear datasets de evaluación
Construir dataset con:
- consultas reales
- respuestas esperadas o criterios de calidad
- casos límite y casos adversarios

### Paso 8.3: Definir evaluadores
Métricas útiles:
- exactitud factual
- relevancia
- groundedness
- completitud
- cumplimiento de formato

### Paso 8.4: Cierre de ciclo
1. Ejecutar experimentos
2. Comparar versiones de prompts/modelos
3. Promover versión ganadora
4. Repetir en cada cambio importante

---

## 9) Multiagente: patrón recomendado para estudiantes avanzados

Patrón simple y potente:

- **Orquestador**: recibe objetivo y divide trabajo
- **Agente investigador**: busca datos/contexto
- **Agente ejecutor**: usa herramientas externas
- **Agente verificador**: revisa consistencia y riesgos

Buenas prácticas:
1. Responsabilidad única por agente
2. Contratos de mensaje claros
3. Presupuesto de tokens por agente
4. Política de escalamiento al humano

---

## 10) Protocolo Agent-to-Agent (A2A)

> Objetivo: que agentes heterogéneos colaboren con contratos interoperables.

### Paso 10.1: Define el contrato de mensajes
Campos mínimos sugeridos:
- `message_id`
- `conversation_id`
- `sender_agent`
- `receiver_agent`
- `intent`
- `payload`
- `context_refs`
- `priority`
- `timestamp`

### Paso 10.2: Tipos de interacción
1. Solicitud/respuesta
2. Delegación de subtarea
3. Publicación de eventos
4. Confirmación o rechazo

### Paso 10.3: Reglas de coordinación
- timeouts por mensaje
- retries con backoff
- deduplicación por `message_id`
- idempotencia en acciones críticas

### Paso 10.4: Seguridad en A2A
- autenticación entre agentes
- firma/verificación de mensajes
- autorización por capacidades
- auditoría de eventos

### Paso 10.5: Patrón práctico
1. Orquestador recibe petición
2. Delega investigación al agente especializado
3. Recibe resultado estructurado
4. Solicita validación al verificador
5. Emite respuesta final con evidencia

---

## 11) Protocolo MCP (Model Context Protocol)

> Objetivo: estandarizar cómo el modelo descubre y usa herramientas/contexto de servidores externos.

### Paso 11.1: Conceptos clave MCP
- **MCP Host**: runtime del agente/cliente
- **MCP Server**: expone recursos, herramientas y prompts
- **Tool**: operación invocable por el modelo
- **Resource**: datos consultables

### Paso 11.2: Cuándo usar MCP
Úsalo cuando quieras:
- conectar múltiples herramientas de forma uniforme
- desacoplar agentes de integraciones concretas
- reutilizar servidores para distintos agentes

### Paso 11.3: Diseño de un MCP Server
1. Definir catálogo de tools
2. Definir esquema de inputs/outputs
3. Validar parámetros estrictamente
4. Implementar errores consistentes
5. Incluir límites de tasa y permisos

### Paso 11.4: Integración MCP con agentes LangChain/LangGraph
1. Registrar servidores MCP en tu host
2. Exponer herramientas MCP al agente
3. Registrar telemetría por invocación
4. Gestionar fallback si el server no responde

### Paso 11.5: Seguridad MCP
- autenticación de cliente-servidor
- scopes por herramienta
- sanitización de entradas
- bloqueo de herramientas peligrosas por entorno
- segregación dev/staging/prod

---

## 12) RAG + Agentes: cuándo y cómo

Usa RAG si el agente necesita datos actualizados o privados.

Pasos:
1. Ingesta y chunking de documentos
2. Embeddings
3. Indexado en vector DB
4. Recuperación top-k con filtros
5. Re-ranking (opcional)
6. Respuesta con citas/evidencias

Controles clave:
- versionado de documentos
- filtros por tenant/usuario
- evaluación de groundedness

---

## 13) Testing serio para agentes

### Capas de prueba
1. **Unitarias**: tools, parsers, validadores
2. **Integración**: cadena/grafo completo
3. **Contrato**: esquema de mensajes A2A/MCP
4. **Evaluación LLM**: calidad semántica
5. **Stress/latencia**: carga concurrente

### Casos obligatorios
- input ambiguo
- tool caída
- timeout LLM
- respuesta fuera de formato
- prompt injection
- datos contradictorios

---

## 14) Seguridad y gobernanza (indispensable)

Checklist mínimo:

- secrets en gestor seguro (no hardcode)
- control de permisos por herramienta
- auditoría de acciones
- límites de gasto/token
- red-team prompts adversarios
- validación fuerte de salida antes de ejecutar acciones

Para producción:
- RBAC
- cifrado en tránsito y reposo
- políticas de retención
- cumplimiento normativo aplicable

---

## 15) Operación y despliegue

### Entornos
- local
- staging
- producción

### Recomendaciones
1. Contenerizar con Docker
2. Health checks
3. Logging estructurado
4. Métricas (latencia, errores, costo)
5. Alertas por degradación
6. Rollback rápido de prompts/modelos

---

## 16) Roadmap didáctico para tus estudiantes

### Módulo 1: Base profesional de agentes
- LangChain base + tools + memoria

### Módulo 2: Flujos robustos
- LangGraph con estado, ramas y retries

### Módulo 3: Observabilidad
- LangSmith + evaluación continua

### Módulo 4: Multiagente
- orquestación, contratos y trazabilidad

### Módulo 5: Protocolos
- A2A + MCP con prácticas reales

### Módulo 6: Producción
- seguridad, testing, despliegue y operación

---

## 17) Proyecto final sugerido (integrador)

Construir un sistema con:

- Agente orquestador (LangGraph)
- 2 agentes especializados (investigación y ejecución)
- Comunicación A2A con contratos definidos
- Integración de herramientas vía MCP server
- Observabilidad completa con LangSmith
- Suite de pruebas y criterios de aceptación

Entregables:
1. Arquitectura documentada
2. API funcional
3. Trazas y evaluaciones
4. Informe de seguridad
5. Métricas de calidad/costo

---

## 18) Errores comunes y cómo evitarlos

1. **Empezar por código sin arquitectura**
   - Solución: documento de diseño mínimo antes de programar

2. **Demasiadas tools sin control**
   - Solución: catálogo limitado y versionado

3. **No medir calidad**
   - Solución: LangSmith + datasets + evaluación recurrente

4. **Ignorar seguridad**
   - Solución: permisos, validación, auditoría, red-team

5. **No definir contratos A2A/MCP**
   - Solución: esquemas formales y tests de contrato

---

## 19) Checklist de implementación real

- [ ] Caso de uso y métricas definidos
- [ ] Agente base en LangChain operativo
- [ ] Grafo LangGraph con estado y errores
- [ ] Trazas y evaluación en LangSmith activas
- [ ] Comunicación A2A definida y probada
- [ ] Integración MCP implementada y securizada
- [ ] Pruebas unitarias + integración + contrato
- [ ] Controles de seguridad y costos
- [ ] Despliegue en staging con observabilidad
- [ ] Paso a producción con rollback preparado

---

## 20) Siguiente paso inmediato

Empieza por un caso de uso concreto y recorre esta guía en orden. Si necesitas, puedes convertir cada sección en una práctica de laboratorio con criterio de aprobación por módulo.

