from __future__ import annotations

import logging
import re
import uuid
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

WeatherTool = Callable[[str], dict[str, Any]]
PolicyTool = Callable[[str], dict[str, Any]]

MESSAGE_STATUS_OK = "ok"
MESSAGE_STATUS_ERROR = "error"


@dataclass(frozen=True)
class PlannerToSpecialistMessage:
    message_type: str
    request_id: str
    conversation_id: str
    destination: str
    budget: str | None
    user_query: str
    constraints: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SpecialistToPlannerMessage:
    message_type: str
    request_id: str
    status: str
    evidence: list[dict[str, Any]]
    risks: list[str] = field(default_factory=list)
    summary: str = ""


class TravelOpsSpecialistAgent:
    """Agente especialista que consulta herramientas y devuelve evidencia."""

    def __init__(
        self,
        weather_tool: WeatherTool | None = None,
        policy_tool: PolicyTool | None = None,
    ) -> None:
        self._weather_tool = weather_tool or self._default_weather_tool
        self._policy_tool = policy_tool or self._default_policy_tool

    def run(self, message: PlannerToSpecialistMessage) -> SpecialistToPlannerMessage:
        evidence: list[dict[str, Any]] = []
        risks: list[str] = []

        try:
            weather_data = self._weather_tool(message.destination)
            evidence.append(
                {
                    "source": "weather_tool",
                    "fact": f"Clima en {message.destination}: {weather_data.get('summary', 'sin resumen')}",
                    "confidence": 0.9,
                }
            )
        except Exception as error:  # noqa: BLE001
            risks.append(f"weather_tool falló ({error}).")

        try:
            policy_data = self._policy_tool(message.destination)
            evidence.append(
                {
                    "source": "policy_tool",
                    "fact": f"Política de viaje: {policy_data.get('entry_requirement', 'sin dato')}",
                    "confidence": 0.9,
                }
            )
        except Exception as error:  # noqa: BLE001
            risks.append(f"policy_tool falló ({error}).")

        status = MESSAGE_STATUS_OK if evidence else MESSAGE_STATUS_ERROR
        summary = (
            f"Evidencia recuperada para {message.destination}."
            if status == MESSAGE_STATUS_OK
            else f"No se logró recuperar evidencia para {message.destination}."
        )
        return SpecialistToPlannerMessage(
            message_type="specialist_result",
            request_id=message.request_id,
            status=status,
            evidence=evidence,
            risks=risks,
            summary=summary,
        )

    @staticmethod
    def _default_weather_tool(destination: str) -> dict[str, Any]:
        mock_weather = {
            "Medellín": {"summary": "templado con lluvias ligeras", "temperature_c": 23},
            "París": {"summary": "variable con probabilidad de lluvia", "temperature_c": 19},
            "Lima": {"summary": "templado y seco", "temperature_c": 21},
        }
        return mock_weather.get(destination, {"summary": "clima no verificado en tiempo real", "temperature_c": None})

    @staticmethod
    def _default_policy_tool(destination: str) -> dict[str, Any]:
        mock_policy = {
            "Medellín": {"entry_requirement": "documento de identidad vigente"},
            "París": {"entry_requirement": "pasaporte vigente"},
            "Lima": {"entry_requirement": "documento vigente"},
        }
        return mock_policy.get(destination, {"entry_requirement": "verificación manual requerida"})


class TravelOpsTwoAgentSystem:
    """Ejercicio 05: Sistema multiagente con planificador y especialista."""

    def __init__(
        self,
        llm_callable: Callable[[str], str] | None = None,
        specialist_agent: TravelOpsSpecialistAgent | None = None,
        specialist_callable: Callable[[PlannerToSpecialistMessage], SpecialistToPlannerMessage] | None = None,
        communication_timeout_seconds: float = 1.0,
        communication_max_retries: int = 1,
        logger: logging.Logger | None = None,
    ) -> None:
        self._llm_callable = llm_callable or self._default_llm_call
        self._specialist_agent = specialist_agent or TravelOpsSpecialistAgent()
        self._specialist_callable = specialist_callable or self._specialist_agent.run
        self._communication_timeout_seconds = communication_timeout_seconds
        self._communication_max_retries = communication_max_retries
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    def run(self, request: TravelOpsRequest) -> TravelOpsResponse:
        query = request.user_query.strip()
        if not query:
            return TravelOpsResponse(
                status=STATUS_NEEDS_CLARIFICATION,
                intent_summary="Consulta vacía.",
                recommendation="Necesito una consulta de viaje para ayudarte.",
                risks=["Falta información de entrada."],
                next_action="Indica destino, fecha aproximada y presupuesto.",
            )

        intent = self._extract_intent(query)
        destination = intent.get("destination")
        if not destination:
            return TravelOpsResponse(
                status=STATUS_NEEDS_CLARIFICATION,
                intent_summary="Consulta ambigua sin destino explícito.",
                recommendation="Necesito un destino para delegar la consulta al especialista.",
                evidence=[{"source": "planner_intent", "fact": query, "confidence": 1.0}],
                risks=["Sin destino no se puede activar la colaboración multiagente."],
                next_action="¿A qué ciudad o país quieres viajar?",
            )

        request_id = f"{request.conversation_id}-{uuid.uuid4().hex[:8]}"
        planner_message = PlannerToSpecialistMessage(
            message_type="specialist_context_request",
            request_id=request_id,
            conversation_id=request.conversation_id,
            destination=destination,
            budget=intent.get("budget"),
            user_query=query,
            constraints=["priorizar evidencia verificable", "responder en formato estructurado"],
        )
        specialist_result = self._delegate_with_retry(planner_message)

        evidence = [
            {"source": "planner_intent", "fact": self._format_intent_summary(intent), "confidence": 0.85},
            {"source": "planner_contract", "fact": planner_message.message_type, "confidence": 1.0},
        ]
        risks: list[str] = []

        if specialist_result is not None:
            evidence.extend(specialist_result.evidence)
            risks.extend(specialist_result.risks)
            if specialist_result.status == MESSAGE_STATUS_ERROR:
                risks.append("El especialista no devolvió evidencia suficiente.")
        else:
            risks.append("No hubo respuesta del especialista tras reintentos; se aplica fallback del planificador.")

        status = STATUS_OK if specialist_result is not None and specialist_result.status == MESSAGE_STATUS_OK else STATUS_PARTIAL

        try:
            recommendation = self._llm_callable(
                self._build_planner_prompt(query=query, intent=intent, specialist_result=specialist_result)
            ).strip()
            if not recommendation:
                raise LLMProviderError("El LLM devolvió respuesta vacía.")
        except (RuntimeError, LLMConnectionError, LLMProviderError):
            recommendation = self._fallback_recommendation(intent, specialist_result)
            status = STATUS_PARTIAL
            risks.append("Proveedor LLM no disponible; se responde con fallback determinístico del planificador.")

        return TravelOpsResponse(
            status=status,
            intent_summary=self._format_intent_summary(intent),
            recommendation=recommendation,
            alternatives=["Puedo comparar con otro destino usando el mismo flujo multiagente."],
            evidence=evidence,
            risks=risks,
            next_action="Confirma fechas exactas y número de viajeros para cerrar la propuesta.",
        )

    def _delegate_with_retry(
        self,
        message: PlannerToSpecialistMessage,
    ) -> SpecialistToPlannerMessage | None:
        attempts = self._communication_max_retries + 1
        last_error: str | None = None

        for attempt in range(1, attempts + 1):
            result, error = self._call_specialist_with_timeout(message)
            if result is not None:
                if attempt > 1:
                    self._logger.info(
                        "Specialist responded after retry: conversation_id=%s attempt=%s",
                        message.conversation_id,
                        attempt,
                    )
                return result
            last_error = error
            self._logger.warning(
                "Specialist communication failed: conversation_id=%s attempt=%s error=%s",
                message.conversation_id,
                attempt,
                error,
            )

        self._logger.error(
            "Specialist unavailable after retries: conversation_id=%s error=%s",
            message.conversation_id,
            last_error,
        )
        return None

    def _call_specialist_with_timeout(
        self,
        message: PlannerToSpecialistMessage,
    ) -> tuple[SpecialistToPlannerMessage | None, str | None]:
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self._specialist_callable, message)
        try:
            result = future.result(timeout=self._communication_timeout_seconds)
            if result.request_id != message.request_id:
                return None, "request_id inconsistente en respuesta del especialista."
            return result, None
        except FuturesTimeoutError:
            future.cancel()
            return None, "timeout de comunicación con especialista."
        except Exception as error:  # noqa: BLE001
            return None, f"error del especialista ({error})."
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _extract_intent(query: str) -> dict[str, str | None]:
        destination_match = re.search(r"\b(?:a|en)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\b", query)
        destination = destination_match.group(1) if destination_match else None
        budget = None
        if re.search(r"\b(bajo|econ[oó]mico|barato)\b", query, re.IGNORECASE):
            budget = "bajo"
        elif re.search(r"\b(medio|moderado)\b", query, re.IGNORECASE):
            budget = "medio"
        elif re.search(r"\b(alto|premium|lujo)\b", query, re.IGNORECASE):
            budget = "alto"
        return {"destination": destination, "budget": budget}

    @staticmethod
    def _format_intent_summary(intent: dict[str, str | None]) -> str:
        destination = intent.get("destination") or "sin destino"
        budget = intent.get("budget") or "sin presupuesto explícito"
        return f"Solicitud de viaje a {destination} con presupuesto {budget}."

    @staticmethod
    def _build_planner_prompt(
        query: str,
        intent: dict[str, str | None],
        specialist_result: SpecialistToPlannerMessage | None,
    ) -> str:
        return (
            "Eres el Agente Planificador de TravelOps IA.\n"
            "Consolida una respuesta corta en español con recomendación y siguiente paso.\n"
            f"Destino: {intent.get('destination')}\n"
            f"Presupuesto: {intent.get('budget') or 'no especificado'}\n"
            f"Consulta del usuario: {query}\n"
            f"Respuesta del especialista: {specialist_result.summary if specialist_result else 'sin respuesta'}\n"
            f"Evidencia del especialista: {specialist_result.evidence if specialist_result else []}\n"
        )

    @staticmethod
    def _fallback_recommendation(
        intent: dict[str, str | None],
        specialist_result: SpecialistToPlannerMessage | None,
    ) -> str:
        destination = intent.get("destination") or "el destino indicado"
        summary = specialist_result.summary if specialist_result else "sin evidencia confirmada"
        return (
            f"Plan base para {destination}: prioriza reserva flexible y validación de requisitos. "
            f"Estado de evidencia del especialista: {summary}."
        )

    @staticmethod
    def _default_llm_call(prompt: str) -> str:
        client = FreeClaudeCodeClient()
        return client.ask(prompt)
