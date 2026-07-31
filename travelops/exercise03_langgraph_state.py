from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from typing import Any, Callable

from core.exceptions import LLMConnectionError, LLMProviderError
from core.llm_client import FreeClaudeCodeClient
from travelops.exercise01_single_agent import (
    STATUS_NEEDS_CLARIFICATION,
    STATUS_OK,
    STATUS_PARTIAL,
    TravelOpsRequest,
    TravelOpsResponse,
)

# ---------------------------------------------------------------------------
# Nodos del grafo
# ---------------------------------------------------------------------------
NODE_INTENT = "intent"
NODE_CONTEXT = "context"
NODE_PROPOSAL = "proposal"
NODE_VALIDATION = "validation"
NODE_ERROR_RECOVERY = "error_recovery"
NODE_END = "end"

_MAX_PROPOSAL_RETRIES = 3
_GRAPH_ITERATION_LIMIT = 20  # protección contra loops infinitos


# ---------------------------------------------------------------------------
# Estado tipado del grafo (equivalente a TypedDict de LangGraph)
# ---------------------------------------------------------------------------

@dataclass
class TravelOpsGraphState:
    """Estado completo que fluye a través de los nodos del grafo."""

    conversation_id: str
    user_query: str

    # Salidas del nodo intención
    destination: str | None = None
    budget: str | None = None

    # Salidas del nodo contexto
    weather_data: dict[str, Any] | None = None
    policy_data: dict[str, Any] | None = None
    context_errors: list[str] = field(default_factory=list)

    # Salidas del nodo propuesta
    recommendation: str = ""
    proposal_attempts: int = 0

    # Salidas del nodo validación
    validation_passed: bool = False
    validation_notes: list[str] = field(default_factory=list)

    # Control de errores
    error_node: str | None = None
    error_message: str | None = None

    # Evidencia acumulada y riesgos
    evidence: list[dict[str, Any]] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    # Control de flujo
    current_node: str = NODE_INTENT
    status: str = STATUS_OK
    next_action: str = ""


# ---------------------------------------------------------------------------
# Agente con flujo de estado LangGraph-style
# ---------------------------------------------------------------------------

class TravelOpsGraphAgent:
    """Ejercicio 03: Flujo con estado LangGraph-style para TravelOps.

    El flujo sigue esta topología de nodos:

        intent
          ├─(sin destino)──► error_recovery ──► end
          └─(con destino)──► context ──► proposal
                                              ├─(falla LLM)──► error_recovery ──► end
                                              └─(ok)──► validation
                                                            ├─(pasa)──► end
                                                            ├─(falla, reintentos disponibles)──► proposal
                                                            └─(falla, máx reintentos)──► error_recovery ──► end
    """

    def __init__(
        self,
        llm_callable: Callable[[str], str] | None = None,
        weather_tool: Callable[[str], dict[str, Any]] | None = None,
        policy_tool: Callable[[str], dict[str, Any]] | None = None,
        tool_timeout_seconds: float = 2.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self._llm_callable = llm_callable or self._default_llm_call
        self._weather_tool = weather_tool or self._default_weather_tool
        self._policy_tool = policy_tool or self._default_policy_tool
        self._tool_timeout_seconds = tool_timeout_seconds
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        # Checkpoint por sesión: persiste el estado entre llamadas
        self._checkpoints: dict[str, TravelOpsGraphState] = {}

    # ------------------------------------------------------------------
    # Punto de entrada público
    # ------------------------------------------------------------------

    def run(self, request: TravelOpsRequest) -> TravelOpsResponse:
        state = TravelOpsGraphState(
            conversation_id=request.conversation_id,
            user_query=request.user_query.strip(),
        )
        self._logger.info("Exercise03 graph start: conversation_id=%s", request.conversation_id)

        if not state.user_query:
            return TravelOpsResponse(
                status=STATUS_NEEDS_CLARIFICATION,
                intent_summary="Consulta vacía.",
                recommendation="Necesito una consulta de viaje para ayudarte.",
                risks=["Falta información de entrada."],
                next_action="Indica destino, fecha aproximada y presupuesto.",
            )

        state = self._execute_graph(state)
        self._save_checkpoint(state)
        return self._state_to_response(state)

    # ------------------------------------------------------------------
    # Motor del grafo (state machine loop)
    # ------------------------------------------------------------------

    def _execute_graph(self, state: TravelOpsGraphState) -> TravelOpsGraphState:
        iterations = 0
        while state.current_node != NODE_END:
            if iterations >= _GRAPH_ITERATION_LIMIT:
                self._logger.error(
                    "Graph iteration limit reached: conversation_id=%s",
                    state.conversation_id,
                )
                state.current_node = NODE_END
                state.status = STATUS_PARTIAL
                state.risks.append("Límite de iteraciones alcanzado; flujo detenido.")
                break
            iterations += 1
            self._logger.debug("Graph node=%s iteration=%d", state.current_node, iterations)

            if state.current_node == NODE_INTENT:
                state = self._node_intent(state)
            elif state.current_node == NODE_CONTEXT:
                state = self._node_context(state)
            elif state.current_node == NODE_PROPOSAL:
                state = self._node_proposal(state)
            elif state.current_node == NODE_VALIDATION:
                state = self._node_validation(state)
            elif state.current_node == NODE_ERROR_RECOVERY:
                state = self._node_error_recovery(state)
            else:
                self._logger.warning("Unknown node: %s", state.current_node)
                state.current_node = NODE_END

        return state

    # ------------------------------------------------------------------
    # Nodos
    # ------------------------------------------------------------------

    def _node_intent(self, state: TravelOpsGraphState) -> TravelOpsGraphState:
        """Extrae intención (destino, presupuesto) de la consulta."""
        destination_match = re.search(
            r"\b(?:a|en)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\b", state.user_query
        )
        state.destination = destination_match.group(1) if destination_match else None

        if re.search(r"\b(bajo|econ[oó]mico|barato)\b", state.user_query, re.IGNORECASE):
            state.budget = "bajo"
        elif re.search(r"\b(medio|moderado)\b", state.user_query, re.IGNORECASE):
            state.budget = "medio"
        elif re.search(r"\b(alto|premium|lujo)\b", state.user_query, re.IGNORECASE):
            state.budget = "alto"

        state.evidence.append(
            {"source": "user_query", "fact": state.user_query, "confidence": 1.0}
        )

        # Transición condicional
        if not state.destination:
            state.error_node = NODE_INTENT
            state.error_message = "No se detectó destino en la consulta."
            state.status = STATUS_NEEDS_CLARIFICATION
            state.current_node = NODE_ERROR_RECOVERY
        else:
            state.current_node = NODE_CONTEXT
        return state

    def _node_context(self, state: TravelOpsGraphState) -> TravelOpsGraphState:
        """Recupera clima y políticas para el destino detectado."""
        destination = state.destination  # guaranteed not None here

        weather_data, weather_error = self._run_tool_with_timeout(
            self._weather_tool, destination, "weather_tool"
        )
        if weather_data:
            state.weather_data = weather_data
            state.evidence.append(
                {
                    "source": "weather_tool",
                    "fact": f"Clima en {destination}: {weather_data.get('summary', 'sin resumen')}",
                    "confidence": 0.9,
                }
            )
        if weather_error:
            state.context_errors.append(weather_error)
            state.risks.append(weather_error)

        policy_data, policy_error = self._run_tool_with_timeout(
            self._policy_tool, destination, "policy_tool"
        )
        if policy_data:
            state.policy_data = policy_data
            state.evidence.append(
                {
                    "source": "policy_tool",
                    "fact": f"Política de viaje: {policy_data.get('entry_requirement', 'sin dato')}",
                    "confidence": 0.9,
                }
            )
        if policy_error:
            state.context_errors.append(policy_error)
            state.risks.append(policy_error)

        if state.context_errors:
            state.status = STATUS_PARTIAL

        # El contexto siempre avanza a propuesta (modo degradado si hay errores)
        state.current_node = NODE_PROPOSAL
        return state

    def _node_proposal(self, state: TravelOpsGraphState) -> TravelOpsGraphState:
        """Genera la recomendación de viaje usando el LLM."""
        state.proposal_attempts += 1
        prompt = (
            "Eres TravelOps IA.\n"
            "Responde en español con recomendación principal, advertencia y siguiente paso.\n"
            f"Destino: {state.destination}\n"
            f"Presupuesto: {state.budget or 'no especificado'}\n"
            f"Clima: {state.weather_data or 'no disponible'}\n"
            f"Políticas: {state.policy_data or 'no disponible'}\n"
            f"Consulta: {state.user_query}\n"
        )
        try:
            recommendation = self._llm_callable(prompt).strip()
            if not recommendation:
                raise LLMProviderError("El LLM devolvió respuesta vacía.")
            state.recommendation = recommendation
            state.current_node = NODE_VALIDATION
        except (RuntimeError, LLMConnectionError, LLMProviderError) as error:
            self._logger.error(
                "LLM failed in proposal node: conversation_id=%s error=%s",
                state.conversation_id,
                error,
            )
            state.error_node = NODE_PROPOSAL
            state.error_message = str(error)
            state.current_node = NODE_ERROR_RECOVERY
        return state

    def _node_validation(self, state: TravelOpsGraphState) -> TravelOpsGraphState:
        """Valida que la propuesta generada cumpla criterios mínimos de calidad."""
        notes: list[str] = []

        if not state.recommendation:
            notes.append("La propuesta está vacía.")
        if len(state.recommendation) < 20:
            notes.append("La propuesta es demasiado corta.")
        if state.destination and state.destination.lower() not in state.recommendation.lower():
            notes.append(f"La propuesta no menciona el destino ({state.destination}).")

        state.validation_notes = notes

        if not notes:
            state.validation_passed = True
            state.current_node = NODE_END
        elif state.proposal_attempts < _MAX_PROPOSAL_RETRIES:
            # Reintentar generación de propuesta
            self._logger.info(
                "Validation failed, retrying proposal: attempt=%d conversation_id=%s notes=%s",
                state.proposal_attempts,
                state.conversation_id,
                notes,
            )
            state.current_node = NODE_PROPOSAL
        else:
            # Máximo de reintentos alcanzado
            state.error_node = NODE_VALIDATION
            state.error_message = f"Validación fallida tras {state.proposal_attempts} intentos: {notes}"
            state.current_node = NODE_ERROR_RECOVERY
        return state

    def _node_error_recovery(self, state: TravelOpsGraphState) -> TravelOpsGraphState:
        """Gestiona errores con respuesta degradada según el nodo de origen."""
        self._logger.warning(
            "Error recovery activated: origin=%s message=%s conversation_id=%s",
            state.error_node,
            state.error_message,
            state.conversation_id,
        )

        if state.error_node == NODE_INTENT:
            state.recommendation = "Necesito un destino concreto para recomendarte un plan de viaje."
            state.next_action = "¿A qué ciudad o país quieres viajar?"
        elif state.error_node == NODE_PROPOSAL:
            state.recommendation = self._deterministic_fallback(state)
            state.risks.append("Proveedor LLM no disponible; se responde con fallback determinístico.")
            state.status = STATUS_PARTIAL
        elif state.error_node == NODE_VALIDATION:
            # Usar la última propuesta aunque no pasó validación
            if not state.recommendation:
                state.recommendation = self._deterministic_fallback(state)
            state.risks.append("Propuesta generada no superó validación completa; revisar recomendación.")
            state.status = STATUS_PARTIAL
        else:
            state.recommendation = self._deterministic_fallback(state)
            state.status = STATUS_PARTIAL

        state.current_node = NODE_END
        return state

    # ------------------------------------------------------------------
    # Checkpoint
    # ------------------------------------------------------------------

    def _save_checkpoint(self, state: TravelOpsGraphState) -> None:
        self._checkpoints[state.conversation_id] = state
        self._logger.info(
            "Checkpoint saved: conversation_id=%s status=%s",
            state.conversation_id,
            state.status,
        )

    def get_checkpoint(self, conversation_id: str) -> TravelOpsGraphState | None:
        """Devuelve el último estado guardado para la sesión, si existe."""
        return self._checkpoints.get(conversation_id)

    # ------------------------------------------------------------------
    # Conversión de estado a respuesta pública
    # ------------------------------------------------------------------

    @staticmethod
    def _state_to_response(state: TravelOpsGraphState) -> TravelOpsResponse:
        destination = state.destination or "sin destino"
        budget = state.budget or "sin presupuesto explícito"
        intent_summary = f"Solicitud de viaje a {destination} con presupuesto {budget}."

        next_action = state.next_action or (
            "Confirma fechas y cantidad de viajeros para afinar el plan."
            if state.status == STATUS_OK
            else "Revisa los riesgos indicados antes de continuar."
        )

        return TravelOpsResponse(
            status=state.status,
            intent_summary=intent_summary,
            recommendation=state.recommendation,
            alternatives=["Puedes comparar con otro destino en una nueva consulta."]
            if state.status == STATUS_OK
            else [],
            evidence=state.evidence,
            risks=state.risks,
            next_action=next_action,
        )

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _run_tool_with_timeout(
        self,
        tool_callable: Callable[[str], dict[str, Any]],
        destination: str,
        tool_name: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(tool_callable, destination)
                result = future.result(timeout=self._tool_timeout_seconds)
                if not isinstance(result, dict):
                    raise ValueError(f"{tool_name} devolvió formato inválido.")
                return result, None
        except FuturesTimeoutError:
            self._logger.warning("%s timed out for destination=%s", tool_name, destination)
            return None, f"{tool_name} no respondió a tiempo; se continúa en modo degradado."
        except Exception as error:  # noqa: BLE001
            self._logger.warning("%s failed for destination=%s error=%s", tool_name, destination, error)
            return None, f"{tool_name} falló ({error}); se continúa en modo degradado."

    @staticmethod
    def _deterministic_fallback(state: TravelOpsGraphState) -> str:
        destination = state.destination or "el destino indicado"
        weather_hint = (
            state.weather_data.get("summary") if state.weather_data else "sin datos de clima confirmados"
        )
        policy_hint = (
            state.policy_data.get("entry_requirement")
            if state.policy_data
            else "sin políticas confirmadas para la fecha"
        )
        return (
            f"Plan base para {destination}: valida clima ({weather_hint}) y requisitos de ingreso "
            f"({policy_hint}) antes de reservar."
        )

    @staticmethod
    def _default_weather_tool(destination: str) -> dict[str, Any]:
        mock_weather = {
            "Medellín": {"summary": "templado con lluvias ligeras", "temperature_c": 23, "risk_level": "medio"},
            "París": {"summary": "variable con probabilidad de lluvia", "temperature_c": 19, "risk_level": "medio"},
            "Lima": {"summary": "templado y seco", "temperature_c": 21, "risk_level": "bajo"},
        }
        return mock_weather.get(
            destination,
            {"summary": "clima no verificado en tiempo real", "temperature_c": None, "risk_level": "desconocido"},
        )

    @staticmethod
    def _default_policy_tool(destination: str) -> dict[str, Any]:
        mock_policy = {
            "Medellín": {"entry_requirement": "documento de identidad vigente", "notes": "revisar requisitos locales"},
            "París": {"entry_requirement": "pasaporte vigente", "notes": "verificar visa según nacionalidad"},
            "Lima": {"entry_requirement": "documento vigente", "notes": "confirmar restricciones sanitarias"},
        }
        return mock_policy.get(
            destination,
            {"entry_requirement": "verificación manual requerida", "notes": "fuente oficial recomendada"},
        )

    @staticmethod
    def _default_llm_call(prompt: str) -> str:
        client = FreeClaudeCodeClient()
        return client.ask(prompt)
