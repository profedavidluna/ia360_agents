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


WeatherTool = Callable[[str], dict[str, Any]]
PolicyTool = Callable[[str], dict[str, Any]]


@dataclass
class ConversationMemory:
    last_destination: str | None = None
    recent_queries: list[str] = field(default_factory=list)
    response_cache: dict[str, str] = field(default_factory=dict)
    weather_cache: dict[str, dict[str, Any]] = field(default_factory=dict)
    policy_cache: dict[str, dict[str, Any]] = field(default_factory=dict)


class TravelOpsToolsMemoryAgent:
    """Ejercicio 02: Agente con tools y memoria conversacional corta."""

    def __init__(
        self,
        llm_callable: Callable[[str], str] | None = None,
        weather_tool: WeatherTool | None = None,
        policy_tool: PolicyTool | None = None,
        tool_timeout_seconds: float = 2.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self._llm_callable = llm_callable or self._default_llm_call
        self._weather_tool = weather_tool or self._default_weather_tool
        self._policy_tool = policy_tool or self._default_policy_tool
        self._tool_timeout_seconds = tool_timeout_seconds
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._memory_store: dict[str, ConversationMemory] = {}

    def run(self, request: TravelOpsRequest) -> TravelOpsResponse:
        query = request.user_query.strip()
        normalized_query = self._normalize_query(query)
        memory = self._memory_store.setdefault(request.conversation_id, ConversationMemory())
        self._logger.info("Exercise02 request: conversation_id=%s", request.conversation_id)

        if not query:
            return TravelOpsResponse(
                status=STATUS_NEEDS_CLARIFICATION,
                intent_summary="Consulta vacía.",
                recommendation="Necesito una consulta de viaje para ayudarte.",
                risks=["Falta información de entrada."],
                next_action="Indica destino, fecha aproximada y presupuesto.",
            )

        if normalized_query in memory.response_cache:
            self._logger.info("Reused cached response for query: conversation_id=%s", request.conversation_id)
            return TravelOpsResponse(
                status=STATUS_OK,
                intent_summary="Consulta repetida detectada; se reutiliza respuesta previa.",
                recommendation=memory.response_cache[normalized_query],
                alternatives=["Si cambias destino o presupuesto, te doy una propuesta actualizada."],
                evidence=[{"source": "conversation_memory", "fact": "respuesta previa reutilizada", "confidence": 1.0}],
                risks=[],
                next_action="Indica si deseas cambiar ciudad, fechas o presupuesto.",
            )

        intent = self._extract_intent(query)
        destination = intent.get("destination") or memory.last_destination
        if not destination:
            return TravelOpsResponse(
                status=STATUS_NEEDS_CLARIFICATION,
                intent_summary="Consulta ambigua sin destino explícito.",
                recommendation="Necesito un destino para consultar clima y políticas.",
                evidence=[{"source": "user_query", "fact": query, "confidence": 1.0}],
                risks=["Sin destino no se pueden consultar herramientas."],
                next_action="¿A qué ciudad o país quieres viajar?",
            )

        intent["destination"] = destination
        risks: list[str] = []
        evidence = [{"source": "user_query", "fact": query, "confidence": 1.0}]

        weather_data, weather_source, weather_error = self._get_weather_with_memory(destination, memory)
        if weather_data:
            evidence.append(
                {
                    "source": weather_source,
                    "fact": f"Clima en {destination}: {weather_data.get('summary', 'sin resumen')}",
                    "confidence": 0.9 if weather_source == "weather_tool" else 0.85,
                }
            )
        if weather_error:
            risks.append(weather_error)

        policy_data, policy_source, policy_error = self._get_policy_with_memory(destination, memory)
        if policy_data:
            evidence.append(
                {
                    "source": policy_source,
                    "fact": f"Política de viaje: {policy_data.get('entry_requirement', 'sin dato')}",
                    "confidence": 0.9 if policy_source == "policy_tool" else 0.85,
                }
            )
        if policy_error:
            risks.append(policy_error)

        prompt = self._build_prompt(
            query=query,
            intent=intent,
            weather_data=weather_data,
            policy_data=policy_data,
            memory=memory,
        )
        status = STATUS_OK if not risks else STATUS_PARTIAL
        try:
            recommendation = self._llm_callable(prompt).strip()
            if not recommendation:
                raise LLMProviderError("El LLM devolvió respuesta vacía.")
        except (RuntimeError, LLMConnectionError, LLMProviderError) as error:
            self._logger.error("LLM fallback activated: conversation_id=%s error=%s", request.conversation_id, error)
            recommendation = self._fallback_recommendation(intent, weather_data, policy_data)
            status = STATUS_PARTIAL
            risks.append("Proveedor LLM no disponible; se responde con fallback determinístico.")

        memory.last_destination = destination
        memory.recent_queries.append(normalized_query)
        memory.recent_queries = memory.recent_queries[-5:]
        memory.response_cache[normalized_query] = recommendation

        if "cached_weather" in weather_source or "cached_policy" in policy_source:
            alternatives = ["Ya tengo contexto previo: puedes pedir comparación con otro destino."]
        else:
            alternatives = ["Si cambias destino, puedo comparar clima y políticas en la misma conversación."]

        return TravelOpsResponse(
            status=status,
            intent_summary=self._format_intent_summary(intent),
            recommendation=recommendation,
            alternatives=alternatives,
            evidence=evidence,
            risks=risks,
            next_action="Indica si deseas mantener el destino o cambiarlo para comparar opciones.",
        )

    def _get_weather_with_memory(
        self, destination: str, memory: ConversationMemory
    ) -> tuple[dict[str, Any] | None, str, str | None]:
        if destination in memory.weather_cache:
            return memory.weather_cache[destination], "cached_weather", None
        data, error = self._run_tool_with_timeout(self._weather_tool, destination, "weather_tool")
        if data:
            memory.weather_cache[destination] = data
            return data, "weather_tool", None
        return None, "weather_tool", error

    def _get_policy_with_memory(
        self, destination: str, memory: ConversationMemory
    ) -> tuple[dict[str, Any] | None, str, str | None]:
        if destination in memory.policy_cache:
            return memory.policy_cache[destination], "cached_policy", None
        data, error = self._run_tool_with_timeout(self._policy_tool, destination, "policy_tool")
        if data:
            memory.policy_cache[destination] = data
            return data, "policy_tool", None
        return None, "policy_tool", error

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
    def _normalize_query(query: str) -> str:
        return " ".join(query.lower().split())

    @staticmethod
    def _build_prompt(
        query: str,
        intent: dict[str, str | None],
        weather_data: dict[str, Any] | None,
        policy_data: dict[str, Any] | None,
        memory: ConversationMemory,
    ) -> str:
        return (
            "Eres TravelOps IA.\n"
            "Responde en español con recomendación principal, advertencia y siguiente paso.\n"
            f"Destino: {intent.get('destination')}\n"
            f"Presupuesto: {intent.get('budget') or 'no especificado'}\n"
            f"Clima: {weather_data or 'no disponible'}\n"
            f"Políticas: {policy_data or 'no disponible'}\n"
            f"Consultas recientes: {memory.recent_queries[-3:]}\n"
            f"Consulta actual: {query}\n"
        )

    @staticmethod
    def _format_intent_summary(intent: dict[str, str | None]) -> str:
        destination = intent.get("destination") or "sin destino"
        budget = intent.get("budget") or "sin presupuesto explícito"
        return f"Solicitud de viaje a {destination} con presupuesto {budget}."

    @staticmethod
    def _fallback_recommendation(
        intent: dict[str, str | None],
        weather_data: dict[str, Any] | None,
        policy_data: dict[str, Any] | None,
    ) -> str:
        destination = intent.get("destination") or "el destino indicado"
        weather_hint = weather_data.get("summary") if weather_data else "sin datos de clima confirmados"
        policy_hint = (
            policy_data.get("entry_requirement") if policy_data else "sin políticas confirmadas para la fecha"
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

