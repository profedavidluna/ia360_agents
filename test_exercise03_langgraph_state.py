from __future__ import annotations

from travelops.exercise01_single_agent import STATUS_NEEDS_CLARIFICATION, STATUS_OK, STATUS_PARTIAL, TravelOpsRequest
from travelops.exercise03_langgraph_state import (
    NODE_CONTEXT,
    NODE_ERROR_RECOVERY,
    NODE_INTENT,
    NODE_PROPOSAL,
    NODE_VALIDATION,
    TravelOpsGraphAgent,
    TravelOpsGraphState,
)


# ---------------------------------------------------------------------------
# Escenario 1 – ruta feliz completa
# ---------------------------------------------------------------------------

def test_happy_path_all_nodes_succeed() -> None:
    """Flujo completo sin errores: intent → context → proposal → validation → end."""

    weather_calls: dict[str, int] = {"count": 0}
    policy_calls: dict[str, int] = {"count": 0}

    def weather_tool(destination: str) -> dict[str, object]:
        weather_calls["count"] += 1
        return {"summary": f"soleado en {destination}", "temperature_c": 25}

    def policy_tool(destination: str) -> dict[str, object]:
        policy_calls["count"] += 1
        return {"entry_requirement": f"pasaporte vigente para {destination}"}

    llm_responses: list[str] = [f"Recomiendo visitar Medellín en temporada seca."]

    def llm(prompt: str) -> str:
        return llm_responses[0]

    agent = TravelOpsGraphAgent(
        llm_callable=llm,
        weather_tool=weather_tool,
        policy_tool=policy_tool,
    )

    response = agent.run(
        TravelOpsRequest(
            conversation_id="conv-g001",
            user_query="Quiero viajar a Medellín con presupuesto medio.",
        )
    )

    assert response.status == STATUS_OK
    assert "Medellín" in response.intent_summary
    sources = {item["source"] for item in response.evidence}
    assert "weather_tool" in sources
    assert "policy_tool" in sources
    assert weather_calls["count"] == 1
    assert policy_calls["count"] == 1


def test_happy_path_saves_checkpoint() -> None:
    """El estado queda guardado en el checkpoint del agente tras la ejecución."""

    agent = TravelOpsGraphAgent(
        llm_callable=lambda _: "Plan de viaje a Lima confirmado con detalles.",
        weather_tool=lambda _: {"summary": "templado"},
        policy_tool=lambda _: {"entry_requirement": "documento vigente"},
    )

    agent.run(
        TravelOpsRequest(
            conversation_id="conv-g002",
            user_query="Quiero viajar a Lima con presupuesto bajo.",
        )
    )

    checkpoint = agent.get_checkpoint("conv-g002")
    assert checkpoint is not None
    assert isinstance(checkpoint, TravelOpsGraphState)
    assert checkpoint.destination == "Lima"
    assert checkpoint.status == STATUS_OK


# ---------------------------------------------------------------------------
# Escenario 2 – error en recuperación de contexto (tools fallan)
# ---------------------------------------------------------------------------

def test_context_error_both_tools_fail_returns_partial() -> None:
    """Cuando ambas tools fallan el nodo contexto registra errores y avanza en modo degradado."""

    def weather_tool(_destination: str) -> dict[str, object]:
        raise RuntimeError("weather service down")

    def policy_tool(_destination: str) -> dict[str, object]:
        raise RuntimeError("policy service down")

    agent = TravelOpsGraphAgent(
        llm_callable=lambda _: "Plan de viaje básico para París disponible.",
        weather_tool=weather_tool,
        policy_tool=policy_tool,
    )

    response = agent.run(
        TravelOpsRequest(
            conversation_id="conv-g003",
            user_query="Quiero ir a París con presupuesto alto.",
        )
    )

    assert response.status == STATUS_PARTIAL
    assert any("weather_tool" in r for r in response.risks)
    assert any("policy_tool" in r for r in response.risks)
    assert response.recommendation != ""


def test_context_error_partial_tool_failure_still_returns_ok() -> None:
    """Si sólo una tool falla el status puede ser partial pero se responde con datos disponibles."""

    def weather_tool(_destination: str) -> dict[str, object]:
        raise ConnectionError("timeout")

    def policy_tool(destination: str) -> dict[str, object]:
        return {"entry_requirement": f"documento vigente para {destination}"}

    agent = TravelOpsGraphAgent(
        llm_callable=lambda _: "Recomiendo viajar a Lima con seguro médico.",
        weather_tool=weather_tool,
        policy_tool=policy_tool,
    )

    response = agent.run(
        TravelOpsRequest(
            conversation_id="conv-g004",
            user_query="Viaje a Lima con presupuesto bajo.",
        )
    )

    assert response.status == STATUS_PARTIAL
    assert any("weather_tool" in r for r in response.risks)
    sources = {item["source"] for item in response.evidence}
    assert "policy_tool" in sources


# ---------------------------------------------------------------------------
# Escenario 3 – validación negativa y regeneración controlada
# ---------------------------------------------------------------------------

def test_validation_failure_triggers_retry_until_success() -> None:
    """La primera propuesta no menciona el destino; el grafo reintenta y la segunda pasa."""

    call_count: dict[str, int] = {"n": 0}

    def llm(_prompt: str) -> str:
        call_count["n"] += 1
        if call_count["n"] == 1:
            # Primera respuesta intencionalmente no menciona el destino → falla validación
            return "Es un buen momento para reservar con antelación."
        # Segunda respuesta menciona el destino → pasa validación
        return "Medellín es ideal en esta época; reserva con antelación."

    agent = TravelOpsGraphAgent(
        llm_callable=llm,
        weather_tool=lambda _: {"summary": "templado"},
        policy_tool=lambda _: {"entry_requirement": "documento vigente"},
    )

    response = agent.run(
        TravelOpsRequest(
            conversation_id="conv-g005",
            user_query="Quiero viajar a Medellín.",
        )
    )

    assert response.status in (STATUS_OK, STATUS_PARTIAL)
    assert call_count["n"] == 2  # se llamó al LLM dos veces


def test_validation_failure_max_retries_returns_partial() -> None:
    """Cuando el LLM nunca pasa validación se activa error_recovery y el estado es partial."""

    def llm(_prompt: str) -> str:
        # Siempre devuelve algo demasiado corto para pasar validación
        return "ok"

    agent = TravelOpsGraphAgent(
        llm_callable=llm,
        weather_tool=lambda _: {"summary": "templado"},
        policy_tool=lambda _: {"entry_requirement": "documento vigente"},
    )

    response = agent.run(
        TravelOpsRequest(
            conversation_id="conv-g006",
            user_query="Quiero viajar a Lima.",
        )
    )

    assert response.status == STATUS_PARTIAL
    assert any("validación" in r.lower() or "propuesta" in r.lower() for r in response.risks)


# ---------------------------------------------------------------------------
# Escenario 4 – sin destino activa error_recovery directamente
# ---------------------------------------------------------------------------

def test_no_destination_returns_needs_clarification() -> None:
    """Si la consulta no tiene destino el nodo intent enruta a error_recovery."""

    agent = TravelOpsGraphAgent(
        llm_callable=lambda _: "respuesta inesperada",
        weather_tool=lambda _: {},
        policy_tool=lambda _: {},
    )

    response = agent.run(
        TravelOpsRequest(
            conversation_id="conv-g007",
            user_query="Quiero hacer un viaje pronto.",
        )
    )

    assert response.status == STATUS_NEEDS_CLARIFICATION
    assert "destino" in response.recommendation.lower() or "destino" in response.next_action.lower()
