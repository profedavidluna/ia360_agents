from __future__ import annotations

import time

from travelops.exercise01_single_agent import STATUS_OK, STATUS_PARTIAL, TravelOpsRequest
from travelops.exercise05_multiagent_two_agents import (
    MESSAGE_STATUS_OK,
    PlannerToSpecialistMessage,
    SpecialistToPlannerMessage,
    TravelOpsTwoAgentSystem,
)


def test_standard_request_delegates_and_returns_specialist_evidence() -> None:
    agent = TravelOpsTwoAgentSystem(
        llm_callable=lambda _prompt: "Recomiendo Medellín con reservas flexibles y revisión de clima previa.",
        communication_timeout_seconds=0.1,
    )

    response = agent.run(
        TravelOpsRequest(
            conversation_id="e05-001",
            user_query="Quiero viajar a Medellín con presupuesto medio.",
        )
    )

    assert response.status == STATUS_OK
    sources = {item["source"] for item in response.evidence}
    assert "weather_tool" in sources
    assert "policy_tool" in sources
    assert "planner_contract" in sources


def test_specialist_timeout_then_retry_success() -> None:
    calls = {"count": 0}

    def specialist_callable(message: PlannerToSpecialistMessage) -> SpecialistToPlannerMessage:
        calls["count"] += 1
        if calls["count"] == 1:
            time.sleep(0.1)
        return SpecialistToPlannerMessage(
            message_type="specialist_result",
            request_id=message.request_id,
            status=MESSAGE_STATUS_OK,
            evidence=[{"source": "weather_tool", "fact": "Clima estable en Lima", "confidence": 0.9}],
            risks=[],
            summary="Evidencia recuperada para Lima.",
        )

    agent = TravelOpsTwoAgentSystem(
        llm_callable=lambda _prompt: "Recomiendo Lima con itinerario ligero y monitoreo de clima.",
        specialist_callable=specialist_callable,
        communication_timeout_seconds=0.03,
        communication_max_retries=1,
    )

    response = agent.run(
        TravelOpsRequest(
            conversation_id="e05-002",
            user_query="Viaje a Lima con presupuesto bajo.",
        )
    )

    assert response.status == STATUS_OK
    assert calls["count"] == 2
    assert any(item["source"] == "weather_tool" for item in response.evidence)


def test_specialist_failure_triggers_planner_fallback_partial() -> None:
    def specialist_callable(_message: PlannerToSpecialistMessage) -> SpecialistToPlannerMessage:
        raise RuntimeError("specialist down")

    agent = TravelOpsTwoAgentSystem(
        llm_callable=lambda _prompt: "Respuesta no usada",
        specialist_callable=specialist_callable,
        communication_timeout_seconds=0.03,
        communication_max_retries=1,
    )

    response = agent.run(
        TravelOpsRequest(
            conversation_id="e05-003",
            user_query="Quiero viajar a París con presupuesto alto.",
        )
    )

    assert response.status == STATUS_PARTIAL
    assert any("especialista" in risk.lower() for risk in response.risks)
