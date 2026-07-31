from __future__ import annotations

from travelops.exercise01_single_agent import STATUS_OK, STATUS_PARTIAL, TravelOpsRequest
from travelops.exercise02_tools_memory_agent import TravelOpsToolsMemoryAgent


def test_first_destination_query_uses_tools_and_returns_evidence() -> None:
    weather_calls = {"count": 0}
    policy_calls = {"count": 0}

    def weather_tool(destination: str) -> dict[str, object]:
        weather_calls["count"] += 1
        return {"summary": f"clima estable en {destination}", "temperature_c": 24}

    def policy_tool(destination: str) -> dict[str, object]:
        policy_calls["count"] += 1
        return {"entry_requirement": f"pasaporte vigente para {destination}"}

    agent = TravelOpsToolsMemoryAgent(
        llm_callable=lambda _prompt: "Recomiendo plan familiar con reservas flexibles.",
        weather_tool=weather_tool,
        policy_tool=policy_tool,
    )

    response = agent.run(
        TravelOpsRequest(
            conversation_id="conv-001",
            user_query="Quiero viajar a Medellín con presupuesto medio.",
        )
    )

    sources = {item["source"] for item in response.evidence}
    assert response.status == STATUS_OK
    assert "weather_tool" in sources
    assert "policy_tool" in sources
    assert weather_calls["count"] == 1
    assert policy_calls["count"] == 1


def test_followup_destination_change_updates_context() -> None:
    calls = {"weather": 0, "policy": 0}

    def weather_tool(destination: str) -> dict[str, object]:
        calls["weather"] += 1
        return {"summary": f"clima para {destination}", "temperature_c": 20}

    def policy_tool(destination: str) -> dict[str, object]:
        calls["policy"] += 1
        return {"entry_requirement": f"requisito para {destination}"}

    agent = TravelOpsToolsMemoryAgent(
        llm_callable=lambda _prompt: "Plan recomendado con validación de herramientas.",
        weather_tool=weather_tool,
        policy_tool=policy_tool,
    )

    first = agent.run(
        TravelOpsRequest(
            conversation_id="conv-002",
            user_query="Quiero viajar a Medellín.",
        )
    )
    second = agent.run(
        TravelOpsRequest(
            conversation_id="conv-002",
            user_query="¿y si cambio a París?",
        )
    )

    assert first.status == STATUS_OK
    assert second.status == STATUS_OK
    assert "París" in second.intent_summary
    assert calls["weather"] == 2
    assert calls["policy"] == 2


def test_tool_failure_returns_partial_with_warning() -> None:
    def weather_tool(_destination: str) -> dict[str, object]:
        raise RuntimeError("weather backend unavailable")

    def policy_tool(destination: str) -> dict[str, object]:
        return {"entry_requirement": f"documento vigente para {destination}"}

    agent = TravelOpsToolsMemoryAgent(
        llm_callable=lambda _prompt: "Respuesta con información parcial disponible.",
        weather_tool=weather_tool,
        policy_tool=policy_tool,
    )

    response = agent.run(
        TravelOpsRequest(
            conversation_id="conv-003",
            user_query="Viaje a Lima con presupuesto bajo.",
        )
    )

    assert response.status == STATUS_PARTIAL
    assert any("weather_tool" in risk for risk in response.risks)
    assert any(item["source"] == "policy_tool" for item in response.evidence)

