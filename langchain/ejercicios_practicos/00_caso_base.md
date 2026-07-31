# 00 - Caso Base: TravelOps IA (Versión Completa)

## Historia

Una agencia recibe consultas como:

> "¿Conviene viajar a Medellín la próxima semana con presupuesto medio y plan familiar?"

El sistema TravelOps IA debe:

1. entender intención y restricciones del usuario
2. obtener contexto externo (clima, políticas y restricciones)
3. construir una recomendación razonada de viaje
4. explicar evidencia y supuestos de la recomendación

---

## Objetivo de aprendizaje

Definir la base funcional, límites y métricas del producto antes de implementar agentes, para evitar retrabajo en ejercicios posteriores.

---

## Alcance funcional (sí hace)

TravelOps IA en esta ruta cubrirá:

1. **Interpretación de consulta**
   - destino(s), fechas aproximadas, tipo de viaje, presupuesto y preferencias
2. **Recuperación de contexto**
   - consulta de clima por destino/fecha
   - consulta de políticas/restricciones de viaje
3. **Generación de recomendación**
   - propuesta de plan de viaje con justificación
   - alternativas cuando falte información o existan riesgos
4. **Transparencia de respuesta**
   - indicar fuentes/herramientas usadas
   - separar hechos vs. supuestos
5. **Manejo de fallas**
   - degradación controlada cuando una tool no responda
   - mensaje claro de limitaciones

---

## No alcance (no hace)

Fuera de alcance para esta ruta:

1. Compra real de vuelos/hoteles
2. Integración con pagos o emisión de tiquetes
3. Acceso a datos personales sensibles o historiales financieros
4. Recomendaciones médicas o legales oficiales
5. Garantías de precio en tiempo real
6. Optimización multiobjetivo avanzada (yield management)

---

## Riesgos principales y mitigación

1. **Datos externos incompletos o desactualizados**
   - Mitigación: etiquetar frescura y nivel de confianza de cada dato
2. **Alucinación del LLM**
   - Mitigación: obligar cita de fuente por dato clave y fallback conservador
3. **Prompt injection en entradas de usuario**
   - Mitigación: validación de instrucciones, aislamiento de contexto y reglas de sistema
4. **Latencia alta por múltiples tools**
   - Mitigación: timeouts, retry limitado y respuesta parcial útil
5. **Recomendaciones inseguras en casos críticos**
   - Mitigación: regla de escalamiento a aprobación humana

---

## Métricas del sistema

### Calidad

- **Cobertura de campos extraídos** (destino, fecha, presupuesto, tipo): objetivo >= 95%
- **Tasa de respuestas con evidencia trazable**: objetivo >= 90%
- **Tasa de fallback correcto ante falla de tool**: objetivo >= 99%

### Latencia

- **p50 end-to-end** <= 4s
- **p95 end-to-end** <= 8s
- **Timeout por tool** <= 2s (con retry controlado)

### Costo

- **Costo promedio por consulta**: umbral configurable por entorno
- **Tokens promedio por respuesta**: seguimiento por versión de prompt

### Confiabilidad

- **Error rate total** <= 2%
- **Disponibilidad de flujo principal** >= 99%

---

## Lista inicial de herramientas externas

1. **Tool de clima** (forecast por ciudad/fecha)
2. **Tool de políticas/restricciones** (requisitos de entrada y reglas vigentes)
3. **(Opcional posterior) Tool de costos estimados** (rangos de presupuesto)

---

## Contrato funcional base (estable para ejercicios 01–09)

### Entrada lógica

- `conversation_id`: identificador de conversación
- `user_query`: texto libre del usuario
- `context` (opcional): historial resumido y preferencias persistidas

### Salida lógica

- `status`: `ok | needs_clarification | partial | error`
- `intent_summary`: interpretación breve de la solicitud
- `recommendation`: propuesta principal de viaje
- `alternatives`: opciones adicionales (si aplica)
- `evidence`: lista de hechos con `source` y `confidence`
- `risks`: riesgos detectados
- `next_action`: aclaración pedida o paso sugerido al usuario

### Reglas obligatorias

1. No afirmar datos externos sin fuente explícita.
2. Si falta información crítica, pedir aclaración concreta.
3. Si falla una tool, responder en modo degradado con transparencia.
4. En casos críticos, marcar necesidad de confirmación humana.

---

## Criterios de éxito del ejercicio 00

- Alcance y no alcance definidos y aprobables.
- Riesgos clave con mitigación inicial explícita.
- Métricas medibles de calidad/latencia/costo/confiabilidad.
- Contrato funcional estable para no rediseñar en cada ejercicio.
