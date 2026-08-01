"""
Tests — Ejercicio 03: Sistema Multi-Agente de TravelOps
========================================================

Cubre:
- AgentRole enum
- SpecialistAgent: init, respond (con LLM mockeado), reset
- Especialistas concretos: create_flight_agent, create_hotel_agent, create_itinerary_agent
- route_query: retorna roles válidos, maneja fallo del LLM (fallback)
- OrchestratorAgent: init, chat, reset, síntesis de respuestas
- Flujos multi-especialista y de único especialista
- Manejo de errores en especialistas

Cómo ejecutar:
    pytest test_exercise03_multi_agent.py -v
"""

from __future__ import annotations

import json
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from travelops.exercise03_multi_agent import (
    AgentRole,
    OrchestratorAgent,
    SpecialistAgent,
    create_flight_agent,
    create_hotel_agent,
    create_itinerary_agent,
    get_llm_config,
    route_query,
)


# ---------------------------------------------------------------------------
# Tests de AgentRole
# ---------------------------------------------------------------------------

class TestAgentRole:
    def test_has_expected_roles(self):
        assert AgentRole.FLIGHT is not None
        assert AgentRole.HOTEL is not None
        assert AgentRole.ITINERARY is not None

    def test_values_are_strings(self):
        for role in [AgentRole.FLIGHT, AgentRole.HOTEL, AgentRole.ITINERARY]:
            assert isinstance(role.value, str)

    def test_flight_value(self):
        assert AgentRole.FLIGHT.value == "flight"

    def test_hotel_value(self):
        assert AgentRole.HOTEL.value == "hotel"

    def test_itinerary_value(self):
        assert AgentRole.ITINERARY.value == "itinerary"

    def test_from_string(self):
        assert AgentRole("flight") == AgentRole.FLIGHT
        assert AgentRole("hotel") == AgentRole.HOTEL
        assert AgentRole("itinerary") == AgentRole.ITINERARY


# ---------------------------------------------------------------------------
# Tests de SpecialistAgent
# ---------------------------------------------------------------------------

class TestSpecialistAgent:
    def test_init_with_role_and_prompt(self):
        agent = SpecialistAgent(
            role=AgentRole.FLIGHT,
            system_prompt="Eres experto en vuelos.",
        )
        assert agent.role == AgentRole.FLIGHT
        assert agent.system_prompt == "Eres experto en vuelos."
        assert agent.history == []

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_respond_returns_string(self, mock_llm):
        mock_llm.return_value = "Hay vuelos baratos en enero."
        agent = SpecialistAgent(role=AgentRole.FLIGHT, system_prompt="Experto en vuelos.")
        result = agent.respond("¿Cuándo hay vuelos baratos a Europa?")
        assert result == "Hay vuelos baratos en enero."

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_respond_adds_messages_to_history(self, mock_llm):
        mock_llm.return_value = "Respuesta del especialista."
        agent = SpecialistAgent(role=AgentRole.HOTEL, system_prompt="Experto en hoteles.")
        agent.respond("¿Qué hotel me recomiendas en Roma?")
        assert len(agent.history) == 2
        assert agent.history[0]["role"] == "user"
        assert agent.history[1]["role"] == "assistant"

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_respond_raises_on_empty_query(self, mock_llm):
        agent = SpecialistAgent(role=AgentRole.ITINERARY, system_prompt="Experto en itinerarios.")
        with pytest.raises(ValueError):
            agent.respond("")

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_respond_raises_on_whitespace_query(self, mock_llm):
        agent = SpecialistAgent(role=AgentRole.ITINERARY, system_prompt="Experto en itinerarios.")
        with pytest.raises(ValueError):
            agent.respond("   ")

    def test_reset_clears_history(self):
        agent = SpecialistAgent(role=AgentRole.FLIGHT, system_prompt="Experto en vuelos.")
        agent.history = [{"role": "user", "content": "Hola"}]
        agent.reset()
        assert agent.history == []

    def test_reset_preserves_prompt(self):
        agent = SpecialistAgent(role=AgentRole.FLIGHT, system_prompt="Mi prompt especial.")
        agent.reset()
        assert agent.system_prompt == "Mi prompt especial."

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_respond_accumulates_history_across_turns(self, mock_llm):
        mock_llm.side_effect = ["Respuesta 1.", "Respuesta 2."]
        agent = SpecialistAgent(role=AgentRole.HOTEL, system_prompt="Experto en hoteles.")
        agent.respond("Pregunta 1")
        agent.respond("Pregunta 2")
        assert len(agent.history) == 4

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_respond_passes_system_prompt_to_llm(self, mock_llm):
        mock_llm.return_value = "Respuesta."
        agent = SpecialistAgent(role=AgentRole.FLIGHT, system_prompt="Mi prompt de vuelos.")
        agent.respond("Pregunta de vuelos")
        _, kwargs = mock_llm.call_args
        assert kwargs.get("system_prompt") == "Mi prompt de vuelos."


# ---------------------------------------------------------------------------
# Tests de especialistas concretos
# ---------------------------------------------------------------------------

class TestSpecialistFactories:
    def test_create_flight_agent_role(self):
        agent = create_flight_agent()
        assert agent.role == AgentRole.FLIGHT

    def test_create_hotel_agent_role(self):
        agent = create_hotel_agent()
        assert agent.role == AgentRole.HOTEL

    def test_create_itinerary_agent_role(self):
        agent = create_itinerary_agent()
        assert agent.role == AgentRole.ITINERARY

    def test_flight_prompt_mentions_flights(self):
        agent = create_flight_agent()
        keywords = {"vuelo", "vuelos", "aerolínea", "aéreo", "flight"}
        assert any(k in agent.system_prompt.lower() for k in keywords)

    def test_hotel_prompt_mentions_hotels(self):
        agent = create_hotel_agent()
        keywords = {"hotel", "alojamiento", "hospedaje", "hostal"}
        assert any(k in agent.system_prompt.lower() for k in keywords)

    def test_itinerary_prompt_mentions_itinerary(self):
        agent = create_itinerary_agent()
        keywords = {"itinerario", "actividad", "planif", "día a día"}
        assert any(k in agent.system_prompt.lower() for k in keywords)

    def test_each_factory_creates_independent_instance(self):
        a1 = create_flight_agent()
        a2 = create_flight_agent()
        a1.history.append({"role": "user", "content": "Hola"})
        assert a2.history == []

    def test_all_prompts_in_spanish(self):
        for factory in [create_flight_agent, create_hotel_agent, create_itinerary_agent]:
            agent = factory()
            spanish_words = {"eres", "puedes", "experto", "responde"}
            assert any(w in agent.system_prompt.lower() for w in spanish_words), (
                f"El prompt de {agent.role} debe estar en español"
            )


# ---------------------------------------------------------------------------
# Tests de route_query
# ---------------------------------------------------------------------------

class TestRouteQuery:
    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_routes_to_flight_agent(self, mock_llm):
        mock_llm.return_value = '{"agents": ["flight"]}'
        roles = route_query("¿Hay vuelos directos a Roma?")
        assert AgentRole.FLIGHT in roles

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_routes_to_hotel_agent(self, mock_llm):
        mock_llm.return_value = '{"agents": ["hotel"]}'
        roles = route_query("¿Qué hotel me recomiendas en Barcelona?")
        assert AgentRole.HOTEL in roles

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_routes_to_itinerary_agent(self, mock_llm):
        mock_llm.return_value = '{"agents": ["itinerary"]}'
        roles = route_query("¿Qué hacer en París en 3 días?")
        assert AgentRole.ITINERARY in roles

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_routes_to_multiple_agents(self, mock_llm):
        mock_llm.return_value = '{"agents": ["flight", "hotel"]}'
        roles = route_query("Busca vuelos y hotel para Madrid")
        assert AgentRole.FLIGHT in roles
        assert AgentRole.HOTEL in roles

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_fallback_when_llm_fails(self, mock_llm):
        mock_llm.side_effect = RuntimeError("Servidor no disponible")
        roles = route_query("Viaje completo a Tokio")
        # Fallback: debe retornar algún rol (no lista vacía)
        assert len(roles) > 0

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_fallback_when_json_invalid(self, mock_llm):
        mock_llm.return_value = "Respuesta que no es JSON válido"
        roles = route_query("Viaje completo")
        assert len(roles) > 0

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_fallback_when_no_agents_in_response(self, mock_llm):
        mock_llm.return_value = '{"agents": []}'
        roles = route_query("Viaje completo")
        assert len(roles) > 0

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_ignores_unknown_agent_names(self, mock_llm):
        mock_llm.return_value = '{"agents": ["flight", "agente_desconocido"]}'
        roles = route_query("Busca vuelo")
        assert AgentRole.FLIGHT in roles
        # El rol desconocido no debe causar un error
        for role in roles:
            assert isinstance(role, AgentRole)

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_returns_list_of_agent_roles(self, mock_llm):
        mock_llm.return_value = '{"agents": ["hotel"]}'
        roles = route_query("Alojamiento en Miami")
        assert isinstance(roles, list)
        for role in roles:
            assert isinstance(role, AgentRole)


# ---------------------------------------------------------------------------
# Tests de OrchestratorAgent — inicialización
# ---------------------------------------------------------------------------

class TestOrchestratorAgentInit:
    def test_has_all_three_specialists(self):
        orch = OrchestratorAgent()
        assert AgentRole.FLIGHT in orch.specialists
        assert AgentRole.HOTEL in orch.specialists
        assert AgentRole.ITINERARY in orch.specialists

    def test_history_starts_empty(self):
        orch = OrchestratorAgent()
        assert orch.history == []

    def test_specialists_are_specialist_agents(self):
        orch = OrchestratorAgent()
        for role, specialist in orch.specialists.items():
            assert isinstance(specialist, SpecialistAgent), (
                f"El especialista {role} debe ser SpecialistAgent"
            )

    def test_each_specialist_has_correct_role(self):
        orch = OrchestratorAgent()
        for role, specialist in orch.specialists.items():
            assert specialist.role == role


# ---------------------------------------------------------------------------
# Tests de OrchestratorAgent.reset
# ---------------------------------------------------------------------------

class TestOrchestratorAgentReset:
    def test_reset_clears_orchestrator_history(self):
        orch = OrchestratorAgent()
        orch.history = [{"role": "user", "content": "Hola"}]
        orch.reset()
        assert orch.history == []

    def test_reset_clears_all_specialist_histories(self):
        orch = OrchestratorAgent()
        for specialist in orch.specialists.values():
            specialist.history = [{"role": "user", "content": "Datos anteriores"}]
        orch.reset()
        for role, specialist in orch.specialists.items():
            assert specialist.history == [], (
                f"El historial del especialista {role} debe estar vacío tras reset()"
            )

    def test_reset_preserves_specialists_dict(self):
        orch = OrchestratorAgent()
        original_keys = set(orch.specialists.keys())
        orch.reset()
        assert set(orch.specialists.keys()) == original_keys


# ---------------------------------------------------------------------------
# Tests de OrchestratorAgent.chat — con LLM mockeado
# ---------------------------------------------------------------------------

class TestOrchestratorAgentChat:

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_chat_raises_on_empty_message(self, mock_llm):
        orch = OrchestratorAgent()
        with pytest.raises(ValueError):
            orch.chat("")

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_chat_raises_on_whitespace_message(self, mock_llm):
        orch = OrchestratorAgent()
        with pytest.raises(ValueError):
            orch.chat("   ")

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_chat_adds_user_message_to_history(self, mock_llm):
        # route_query → '{"agents": ["flight"]}', specialist → "Resp esp.", synthesis → "Resp final"
        mock_llm.side_effect = [
            '{"agents": ["flight"]}',
            "Hay vuelos disponibles.",
        ]
        orch = OrchestratorAgent()
        orch.chat("¿Hay vuelos a Roma?")
        assert orch.history[0]["role"] == "user"
        assert orch.history[0]["content"] == "¿Hay vuelos a Roma?"

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_chat_adds_response_to_history(self, mock_llm):
        mock_llm.side_effect = [
            '{"agents": ["hotel"]}',
            "Te recomiendo el Hotel Coliseo.",
        ]
        orch = OrchestratorAgent()
        result = orch.chat("¿Qué hotel me recomiendas en Roma?")
        assert orch.history[-1]["role"] == "assistant"
        assert orch.history[-1]["content"] == result

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_single_specialist_response_returned_directly(self, mock_llm):
        """Con un solo especialista, su respuesta es la respuesta final."""
        specialist_response = "El mejor hotel en Roma es el Hotel Coliseo."
        mock_llm.side_effect = [
            '{"agents": ["hotel"]}',
            specialist_response,
        ]
        orch = OrchestratorAgent()
        result = orch.chat("¿Qué hotel en Roma?")
        assert result == specialist_response

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_multiple_specialists_triggers_synthesis(self, mock_llm):
        """Con múltiples especialistas, se hace una llamada extra al LLM para sintetizar."""
        mock_llm.side_effect = [
            '{"agents": ["flight", "hotel"]}',  # routing
            "Hay vuelos desde $300.",            # flight specialist
            "Hoteles desde $80/noche.",          # hotel specialist
            "Para tu viaje a Roma encontré vuelos desde $300 y hoteles desde $80/noche.",  # synthesis
        ]
        orch = OrchestratorAgent()
        result = orch.chat("Planifica vuelo y hotel para Roma")
        # Debe haber llamado al LLM 4 veces: routing + 2 especialistas + síntesis
        assert mock_llm.call_count == 4
        assert isinstance(result, str) and len(result) > 0

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_specialist_error_does_not_crash_orchestrator(self, mock_llm):
        """Si un especialista falla, el orquestador continúa y produce alguna respuesta."""
        mock_llm.side_effect = [
            '{"agents": ["flight"]}',    # routing
            RuntimeError("LLM error"),   # specialist falla
            "Lo siento, hubo un problema con los vuelos.",  # synthesis/fallback
        ]
        orch = OrchestratorAgent()
        result = orch.chat("¿Hay vuelos baratos?")
        assert isinstance(result, str)

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_chat_returns_string(self, mock_llm):
        mock_llm.side_effect = [
            '{"agents": ["itinerary"]}',
            "Día 1: Visita el Coliseo...",
        ]
        orch = OrchestratorAgent()
        result = orch.chat("¿Qué hacer en Roma en 3 días?")
        assert isinstance(result, str) and len(result) > 0

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_specialists_receive_the_user_query(self, mock_llm):
        """Los especialistas deben recibir exactamente el mensaje del usuario."""
        mock_llm.side_effect = [
            '{"agents": ["hotel"]}',
            "Te recomiendo el Hotel Central.",
        ]
        orch = OrchestratorAgent()
        orch.chat("¿Qué hotel recomiendas en Barcelona?")

        # El especialista de hoteles debe tener el mensaje del usuario en su historial
        hotel_specialist = orch.specialists[AgentRole.HOTEL]
        user_messages = [m for m in hotel_specialist.history if m["role"] == "user"]
        assert any("Barcelona" in m["content"] for m in user_messages)

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_history_accumulates_across_turns(self, mock_llm):
        mock_llm.side_effect = [
            '{"agents": ["flight"]}',
            "Vuelos disponibles.",
            '{"agents": ["hotel"]}',
            "Hoteles disponibles.",
        ]
        orch = OrchestratorAgent()
        orch.chat("Vuelos a Madrid")
        orch.chat("Hoteles en Madrid")
        # Orquestador debe tener 4 mensajes: user1, assistant1, user2, assistant2
        assert len(orch.history) == 4

    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_reset_then_fresh_start(self, mock_llm):
        mock_llm.side_effect = [
            '{"agents": ["flight"]}',
            "Vuelos disponibles.",
            '{"agents": ["hotel"]}',
            "Hoteles disponibles.",
        ]
        orch = OrchestratorAgent()
        orch.chat("Primera consulta")
        orch.reset()

        # Después del reset, el historial del orquestador y especialistas está limpio
        assert orch.history == []
        for specialist in orch.specialists.values():
            assert specialist.history == []

        orch.chat("Segunda consulta")
        assert len(orch.history) == 2  # solo la segunda consulta


# ---------------------------------------------------------------------------
# Tests de integración: flujo completo de 3 especialistas
# ---------------------------------------------------------------------------

class TestFullTripPlanning:
    @patch("travelops.exercise03_multi_agent.call_llm")
    def test_full_trip_uses_all_three_specialists(self, mock_llm):
        """Una consulta de viaje completo debe activar los 3 especialistas."""
        mock_llm.side_effect = [
            '{"agents": ["flight", "hotel", "itinerary"]}',  # routing
            "Vuelos desde $350.",                             # flight
            "Hoteles desde $70/noche.",                       # hotel
            "Itinerario de 5 días en Roma.",                  # itinerary
            "Plan completo para tu viaje a Roma de 5 días.",  # synthesis
        ]
        orch = OrchestratorAgent()
        result = orch.chat("Planifica un viaje completo de 5 días a Roma")

        assert mock_llm.call_count == 5
        assert isinstance(result, str) and len(result) > 0

        # Los tres especialistas deben tener historial
        for role in [AgentRole.FLIGHT, AgentRole.HOTEL, AgentRole.ITINERARY]:
            assert len(orch.specialists[role].history) > 0
