from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from core.exceptions import LLMConnectionError, LLMProviderError
from core.llm_client import FreeClaudeCodeClient


STATUS_OK = "ok"
STATUS_NEEDS_CLARIFICATION = "needs_clarification"
STATUS_PARTIAL = "partial"


@dataclass(frozen=True)
class TravelOpsRequest:
    conversation_id: str
    user_query: str
    context: dict[str, Any] | None = None


@dataclass
class TravelOpsResponse:
    status: str
    intent_summary: str
    recommendation: str
    alternatives: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TravelOpsSingleAgent:
    """Agente único del ejercicio 01 para recomendaciones de viaje."""

    def __init__(
        self,
        llm_callable: Callable[[str], str] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._llm_callable = llm_callable or self._default_llm_call
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    def run(self, request: TravelOpsRequest) -> TravelOpsResponse:
        query = request.user_query.strip()
        self._logger.info("TravelOps request received: conversation_id=%s", request.conversation_id)

        if not query:
            self._logger.warning("Empty query: conversation_id=%s", request.conversation_id)
            return TravelOpsResponse(
                status=STATUS_NEEDS_CLARIFICATION,
                intent_summary="Consulta vacía.",
                recommendation="No puedo generar una recomendación sin una consulta.",
                risks=["Falta información de la solicitud."],
                next_action="Indica destino, fecha aproximada y presupuesto.",
            )

        intent = self._extract_intent(query)
        destination = intent.get("destination")

        if not destination:
            self._logger.info("Clarification required: conversation_id=%s", request.conversation_id)
            return TravelOpsResponse(
                status=STATUS_NEEDS_CLARIFICATION,
                intent_summary="Consulta ambigua sin destino explícito.",
                recommendation=(
                    "Puedo ayudarte a planear el viaje, pero necesito un destino concreto para recomendarte."
                ),
                risks=["Sin destino no se puede consultar contexto confiable."],
                next_action="¿A qué ciudad o país quieres viajar?",
                evidence=[{"source": "user_query", "fact": query, "confidence": 1.0}],
            )

        prompt = self._build_prompt(query=query, intent=intent)
        try:
            recommendation = self._llm_callable(prompt).strip()
            if not recommendation:
                raise LLMProviderError("El LLM devolvió texto vacío.")
            status = STATUS_OK
            risks: list[str] = []
            self._logger.info("LLM recommendation generated: conversation_id=%s", request.conversation_id)
        except (RuntimeError, LLMConnectionError, LLMProviderError) as error:
            self._logger.error(
                "LLM unavailable, using fallback: conversation_id=%s error=%s",
                request.conversation_id,
                error,
            )
            recommendation = self._fallback_recommendation(intent=intent)
            status = STATUS_PARTIAL
            risks = ["Proveedor LLM no disponible; respuesta degradada con reglas base."]

        intent_summary = self._format_intent_summary(intent=intent)
        evidence = [
            {"source": "user_query", "fact": query, "confidence": 1.0},
            {"source": "intent_parser", "fact": intent_summary, "confidence": 0.8},
        ]

        return TravelOpsResponse(
            status=status,
            intent_summary=intent_summary,
            recommendation=recommendation,
            alternatives=self._alternatives(intent=intent),
            evidence=evidence,
            risks=risks,
            next_action="Confirma fechas exactas y cantidad de viajeros para afinar el plan.",
        )

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
    def _build_prompt(query: str, intent: dict[str, str | None]) -> str:
        return (
            "Eres TravelOps IA, asistente de viajes.\n"
            "Responde en español, breve y práctico.\n"
            "Incluye: recomendación principal, una advertencia y siguiente paso.\n"
            f"Destino detectado: {intent.get('destination') or 'no detectado'}\n"
            f"Presupuesto detectado: {intent.get('budget') or 'no detectado'}\n"
            f"Consulta: {query}\n"
        )

    @staticmethod
    def _format_intent_summary(intent: dict[str, str | None]) -> str:
        destination = intent.get("destination") or "sin destino"
        budget = intent.get("budget") or "sin presupuesto explícito"
        return f"Solicitud de viaje a {destination} con presupuesto {budget}."

    @staticmethod
    def _fallback_recommendation(intent: dict[str, str | None]) -> str:
        destination = intent.get("destination") or "el destino indicado"
        budget = intent.get("budget")
        budget_text = f" y presupuesto {budget}" if budget else ""
        return (
            f"Como base, te conviene planear un viaje a {destination}{budget_text}, "
            "priorizando fechas flexibles, alojamiento con cancelación y revisión previa del clima."
        )

    @staticmethod
    def _alternatives(intent: dict[str, str | None]) -> list[str]:
        budget = intent.get("budget")
        if budget == "bajo":
            return ["Viajar en temporada media para reducir costos."]
        if budget == "alto":
            return ["Agregar opción premium con seguro de viaje integral."]
        return ["Comparar dos ventanas de fechas para balancear costo y clima."]

    @staticmethod
    def _default_llm_call(prompt: str) -> str:
        client = FreeClaudeCodeClient()
        return client.ask(prompt)

