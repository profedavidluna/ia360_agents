from __future__ import annotations

from travelops.exercise01_single_agent import (
    STATUS_NEEDS_CLARIFICATION,
    STATUS_OK,
    STATUS_PARTIAL,
    TravelOpsRequest,
    TravelOpsSingleAgent,
)


def test_single_destination_query_returns_ok_status() -> None:
    agent = TravelOpsSingleAgent(
        llm_callable=lambda _prompt: "Te recomiendo Medellín con actividades familiares y revisión climática."
    )
    response = agent.run(
        TravelOpsRequest(
            conversation_id="c-001",
            user_query="Quiero viajar a Medellín la próxima semana con mi familia.",
        )
    )

    assert response.status == STATUS_OK
    assert "Medellín" in response.intent_summary
    assert "recomiendo" in response.recommendation.lower()
    assert response.next_action


def test_budget_query_keeps_stable_output_contract() -> None:
    agent = TravelOpsSingleAgent(
        llm_callable=lambda _prompt: "París es viable con presupuesto medio si priorizas reservas anticipadas."
    )
    response = agent.run(
        TravelOpsRequest(
            conversation_id="c-002",
            user_query="Necesito un plan para viajar a París con presupuesto medio.",
        )
    )

    payload = response.to_dict()
    assert response.status == STATUS_OK
    assert "presupuesto medio" in response.intent_summary.lower()
    assert isinstance(payload["evidence"], list)
    assert {"status", "intent_summary", "recommendation", "alternatives", "evidence", "risks", "next_action"} <= set(
        payload.keys()
    )


def test_ambiguous_query_requests_clarification() -> None:
    agent = TravelOpsSingleAgent(llm_callable=lambda _prompt: "No debería llamarse")
    response = agent.run(
        TravelOpsRequest(
            conversation_id="c-003",
            user_query="Quiero viajar pronto, ¿qué me recomiendas?",
        )
    )

    assert response.status == STATUS_NEEDS_CLARIFICATION
    assert "destino" in response.next_action.lower()


def test_llm_failure_falls_back_to_partial_response() -> None:
    def failing_llm(_prompt: str) -> str:
        raise RuntimeError("provider down")

    agent = TravelOpsSingleAgent(llm_callable=failing_llm)
    response = agent.run(
        TravelOpsRequest(
            conversation_id="c-004",
            user_query="Quiero viajar a Lima con presupuesto bajo.",
        )
    )

    assert response.status == STATUS_PARTIAL
    assert "degradada" in response.risks[0].lower()
    assert "Lima" in response.recommendation

