"""
Tests — Ejercicio 02: Agente con Herramientas (Tool Use / ReAct)
=================================================================

Cubre:
- Herramientas individuales (search_flights, search_hotels, get_weather, calculate_budget)
- ToolDefinition y TOOL_REGISTRY
- parse_tool_call: casos válidos e inválidos
- execute_tool: herramienta conocida, desconocida y con error de argumentos
- build_system_prompt_with_tools: contiene descripción de herramientas
- TravelAgentWithTools.chat: respuesta directa, con una herramienta, ciclo ReAct
- TravelAgentWithTools.reset
- Límite de rondas (max_tool_rounds)

Cómo ejecutar:
    pytest test_exercise02_agent_with_tools.py -v
"""

from __future__ import annotations

import json
import os
import sys
from unittest.mock import call, patch

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from travelops.exercise02_agent_with_tools import (
    TOOL_REGISTRY,
    ToolDefinition,
    TravelAgentWithTools,
    build_system_prompt_with_tools,
    calculate_budget,
    execute_tool,
    get_llm_config,
    get_weather,
    parse_tool_call,
    search_flights,
    search_hotels,
)


# ---------------------------------------------------------------------------
# Tests de herramientas individuales
# ---------------------------------------------------------------------------

class TestSearchFlights:
    def test_returns_string(self):
        result = search_flights("Lima", "Madrid", "15 de marzo")
        assert isinstance(result, str)

    def test_contains_origin_and_destination(self):
        result = search_flights("Bogotá", "París", "10 de junio")
        assert "Bogotá" in result
        assert "París" in result

    def test_contains_date(self):
        result = search_flights("Lima", "Madrid", "15 de marzo")
        assert "15 de marzo" in result

    def test_contains_flight_options(self):
        result = search_flights("Lima", "Madrid", "15 de marzo")
        assert "✈" in result or "vuelo" in result.lower() or "Vuelo" in result


class TestSearchHotels:
    def test_returns_string(self):
        result = search_hotels("París", "01/06", "07/06")
        assert isinstance(result, str)

    def test_contains_city(self):
        result = search_hotels("Tokio", "01/06", "07/06")
        assert "Tokio" in result

    def test_contains_dates(self):
        result = search_hotels("Tokio", "01/06", "07/06")
        assert "01/06" in result
        assert "07/06" in result

    def test_budget_parameter_reflected(self):
        result = search_hotels("Tokio", "01/06", "07/06", budget="bajo")
        assert "bajo" in result

    def test_default_budget_accepted(self):
        result = search_hotels("Tokio", "01/06", "07/06")
        assert isinstance(result, str) and len(result) > 0


class TestGetWeather:
    def test_returns_string(self):
        result = get_weather("Tokio", "marzo")
        assert isinstance(result, str)

    def test_contains_city_and_month(self):
        result = get_weather("Tokio", "marzo")
        assert "Tokio" in result
        assert "marzo" in result

    def test_contains_temperature_info(self):
        result = get_weather("Tokio", "marzo")
        assert "°C" in result or "temperatura" in result.lower()


class TestCalculateBudget:
    def test_single_item(self):
        items = json.dumps([{"name": "vuelo", "cost": 450}])
        result = calculate_budget(items)
        assert "450" in result
        assert "vuelo" in result

    def test_multiple_items_total(self):
        items = json.dumps([
            {"name": "vuelo", "cost": 400},
            {"name": "hotel", "cost": 300},
            {"name": "comida", "cost": 100},
        ])
        result = calculate_budget(items)
        assert "800" in result  # total = 800

    def test_zero_cost_item(self):
        items = json.dumps([{"name": "entrada gratuita", "cost": 0}])
        result = calculate_budget(items)
        assert "0" in result

    def test_invalid_json_returns_error_message(self):
        result = calculate_budget("esto no es json")
        assert "error" in result.lower() or "Error" in result

    def test_non_list_json_returns_error_message(self):
        result = calculate_budget('{"name": "vuelo", "cost": 100}')
        assert "error" in result.lower() or "Error" in result

    def test_item_with_non_numeric_cost(self):
        items = json.dumps([{"name": "vuelo", "cost": "no-number"}])
        result = calculate_budget(items)
        # Debe manejar el error de conversión sin explotar
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Tests de ToolDefinition y TOOL_REGISTRY
# ---------------------------------------------------------------------------

class TestToolDefinition:
    def test_has_required_fields(self):
        tool = TOOL_REGISTRY["search_flights"]
        assert tool.name == "search_flights"
        assert isinstance(tool.description, str) and len(tool.description) > 0
        assert isinstance(tool.parameters, dict) and len(tool.parameters) > 0
        assert callable(tool.fn)

    def test_all_expected_tools_present(self):
        expected = {"search_flights", "search_hotels", "get_weather", "calculate_budget"}
        assert expected.issubset(set(TOOL_REGISTRY.keys()))

    def test_tool_fn_is_callable(self):
        for name, tool in TOOL_REGISTRY.items():
            assert callable(tool.fn), f"La herramienta '{name}' debe tener fn callable"


# ---------------------------------------------------------------------------
# Tests de build_system_prompt_with_tools
# ---------------------------------------------------------------------------

class TestBuildSystemPromptWithTools:
    def test_returns_non_empty_string(self):
        prompt = build_system_prompt_with_tools()
        assert isinstance(prompt, str) and len(prompt) > 0

    def test_contains_all_tool_names(self):
        prompt = build_system_prompt_with_tools()
        for tool_name in TOOL_REGISTRY:
            assert tool_name in prompt, f"'{tool_name}' debe aparecer en el prompt"

    def test_contains_json_format_instructions(self):
        prompt = build_system_prompt_with_tools()
        assert '"tool"' in prompt or "tool" in prompt

    def test_prompt_is_in_spanish(self):
        prompt = build_system_prompt_with_tools()
        spanish_words = {"eres", "puedes", "herramienta", "responde", "viaje"}
        assert any(w in prompt.lower() for w in spanish_words)


# ---------------------------------------------------------------------------
# Tests de parse_tool_call
# ---------------------------------------------------------------------------

class TestParseToolCall:
    def test_valid_tool_call(self):
        response = '{"tool": "search_flights", "args": {"origin": "Lima", "destination": "Madrid", "date": "15 de marzo"}}'
        result = parse_tool_call(response)
        assert result is not None
        assert result["tool"] == "search_flights"
        assert result["args"]["origin"] == "Lima"

    def test_tool_call_embedded_in_text(self):
        response = 'Voy a buscar los vuelos ahora. {"tool": "search_flights", "args": {"origin": "Lima", "destination": "Madrid", "date": "15/03"}} Espera los resultados.'
        result = parse_tool_call(response)
        assert result is not None
        assert result["tool"] == "search_flights"

    def test_plain_text_returns_none(self):
        response = "Te recomiendo visitar Japón en primavera, cuando florecen los cerezos."
        result = parse_tool_call(response)
        assert result is None

    def test_json_without_tool_key_returns_none(self):
        response = '{"message": "hola", "status": "ok"}'
        result = parse_tool_call(response)
        assert result is None

    def test_invalid_json_returns_none(self):
        response = "{esto no es json válido}"
        result = parse_tool_call(response)
        assert result is None

    def test_empty_string_returns_none(self):
        result = parse_tool_call("")
        assert result is None

    def test_extracts_args_correctly(self):
        response = '{"tool": "get_weather", "args": {"city": "Tokio", "month": "abril"}}'
        result = parse_tool_call(response)
        assert result["args"]["city"] == "Tokio"
        assert result["args"]["month"] == "abril"

    def test_empty_args(self):
        response = '{"tool": "search_flights", "args": {}}'
        result = parse_tool_call(response)
        assert result is not None
        assert result["args"] == {}


# ---------------------------------------------------------------------------
# Tests de execute_tool
# ---------------------------------------------------------------------------

class TestExecuteTool:
    def test_execute_search_flights(self):
        result = execute_tool(
            "search_flights",
            {"origin": "Lima", "destination": "Madrid", "date": "15 de marzo"},
        )
        assert isinstance(result, str)
        assert "Lima" in result

    def test_execute_search_hotels(self):
        result = execute_tool(
            "search_hotels",
            {"city": "París", "check_in": "01/06", "check_out": "07/06"},
        )
        assert isinstance(result, str)
        assert "París" in result

    def test_execute_get_weather(self):
        result = execute_tool("get_weather", {"city": "Tokio", "month": "marzo"})
        assert isinstance(result, str)
        assert "Tokio" in result

    def test_execute_calculate_budget(self):
        items = json.dumps([{"name": "vuelo", "cost": 300}])
        result = execute_tool("calculate_budget", {"items": items})
        assert "300" in result

    def test_unknown_tool_raises_key_error(self):
        with pytest.raises(KeyError, match="no encontrada"):
            execute_tool("herramienta_inexistente", {})

    def test_wrong_args_raises_type_error(self):
        with pytest.raises(TypeError):
            execute_tool("search_flights", {"wrong_param": "value"})


# ---------------------------------------------------------------------------
# Tests de TravelAgentWithTools — inicialización y reset
# ---------------------------------------------------------------------------

class TestTravelAgentWithToolsInit:
    def test_history_starts_empty(self):
        agent = TravelAgentWithTools()
        assert agent.history == []

    def test_system_prompt_contains_tool_names(self):
        agent = TravelAgentWithTools()
        for tool_name in TOOL_REGISTRY:
            assert tool_name in agent.system_prompt

    def test_default_max_tool_rounds(self):
        agent = TravelAgentWithTools()
        assert agent.max_tool_rounds >= 1

    def test_custom_max_tool_rounds(self):
        agent = TravelAgentWithTools(max_tool_rounds=3)
        assert agent.max_tool_rounds == 3

    def test_reset_clears_history(self):
        agent = TravelAgentWithTools()
        agent.history = [{"role": "user", "content": "Hola"}]
        agent.reset()
        assert agent.history == []

    def test_reset_preserves_system_prompt(self):
        agent = TravelAgentWithTools()
        original = agent.system_prompt
        agent.reset()
        assert agent.system_prompt == original


# ---------------------------------------------------------------------------
# Tests de TravelAgentWithTools.chat — con LLM mockeado
# ---------------------------------------------------------------------------

class TestTravelAgentWithToolsChat:

    @patch("travelops.exercise02_agent_with_tools.call_llm")
    def test_direct_response_no_tool(self, mock_llm):
        """Cuando el LLM responde con texto, no llama herramientas."""
        mock_llm.return_value = "Te recomiendo visitar Japón en primavera."
        agent = TravelAgentWithTools()
        result = agent.chat("¿Cuándo visitar Japón?")
        assert result == "Te recomiendo visitar Japón en primavera."
        assert mock_llm.call_count == 1

    @patch("travelops.exercise02_agent_with_tools.call_llm")
    def test_chat_adds_user_message_to_history(self, mock_llm):
        mock_llm.return_value = "Respuesta directa."
        agent = TravelAgentWithTools()
        agent.chat("¿Cuál es el clima en París?")
        assert agent.history[0]["role"] == "user"
        assert agent.history[0]["content"] == "¿Cuál es el clima en París?"

    @patch("travelops.exercise02_agent_with_tools.call_llm")
    def test_chat_with_tool_call_executes_tool(self, mock_llm):
        """El agente detecta una tool call, ejecuta la herramienta y llama al LLM de nuevo."""
        tool_call_json = '{"tool": "get_weather", "args": {"city": "París", "month": "junio"}}'
        final_response = "En junio, París tiene buen clima con temperaturas de 18-25°C."

        mock_llm.side_effect = [tool_call_json, final_response]

        agent = TravelAgentWithTools()
        result = agent.chat("¿Qué clima hace en París en junio?")

        assert result == final_response
        assert mock_llm.call_count == 2

    @patch("travelops.exercise02_agent_with_tools.call_llm")
    def test_tool_result_injected_in_history(self, mock_llm):
        """El resultado de la herramienta debe aparecer en el historial."""
        tool_call_json = '{"tool": "get_weather", "args": {"city": "París", "month": "junio"}}'
        final_response = "El clima en París en junio es agradable."

        mock_llm.side_effect = [tool_call_json, final_response]

        agent = TravelAgentWithTools()
        agent.chat("¿Clima en París en junio?")

        # El historial debe contener el mensaje de resultado de herramienta
        tool_result_messages = [
            m for m in agent.history
            if "Resultado de herramienta" in m.get("content", "")
        ]
        assert len(tool_result_messages) == 1

    @patch("travelops.exercise02_agent_with_tools.call_llm")
    def test_chat_raises_on_empty_message(self, mock_llm):
        agent = TravelAgentWithTools()
        with pytest.raises(ValueError):
            agent.chat("")

    @patch("travelops.exercise02_agent_with_tools.call_llm")
    def test_chat_raises_on_whitespace_message(self, mock_llm):
        agent = TravelAgentWithTools()
        with pytest.raises(ValueError):
            agent.chat("   ")

    @patch("travelops.exercise02_agent_with_tools.call_llm")
    def test_max_tool_rounds_respected(self, mock_llm):
        """El agente no entra en un bucle infinito si el LLM siempre llama herramientas."""
        tool_call_json = '{"tool": "get_weather", "args": {"city": "Lima", "month": "enero"}}'
        # El LLM siempre devuelve una tool call: se debe respetar max_tool_rounds
        # y al final hacer una llamada extra para la respuesta final
        mock_llm.return_value = tool_call_json

        agent = TravelAgentWithTools(max_tool_rounds=2)
        # No debe entrar en bucle infinito; termina después de max_tool_rounds + 1 llamadas al LLM
        result = agent.chat("¿Clima?")
        # El LLM fue llamado max_tool_rounds veces + 1 llamada final (guardrail)
        assert mock_llm.call_count == agent.max_tool_rounds + 1
        assert isinstance(result, str)

    @patch("travelops.exercise02_agent_with_tools.call_llm")
    def test_unknown_tool_error_is_handled(self, mock_llm):
        """Si el LLM llama a una herramienta inexistente, el error se captura."""
        bad_tool_call = '{"tool": "herramienta_inexistente", "args": {}}'
        final_response = "Lo siento, no pude ejecutar esa herramienta."

        mock_llm.side_effect = [bad_tool_call, final_response]

        agent = TravelAgentWithTools()
        result = agent.chat("Usa la herramienta inexistente")

        # El agente no debe explotar; el error se inyecta en el historial y se continúa
        assert isinstance(result, str)

    @patch("travelops.exercise02_agent_with_tools.call_llm")
    def test_history_accumulates_across_turns(self, mock_llm):
        mock_llm.side_effect = ["Respuesta 1.", "Respuesta 2."]
        agent = TravelAgentWithTools()
        agent.chat("Pregunta 1")
        agent.chat("Pregunta 2")
        # Al menos 4 mensajes: user1, assistant1, user2, assistant2
        assert len(agent.history) >= 4

    @patch("travelops.exercise02_agent_with_tools.call_llm")
    def test_reset_then_chat_starts_fresh(self, mock_llm):
        mock_llm.return_value = "Respuesta fresca."
        agent = TravelAgentWithTools()

        mock_llm.return_value = "Primera respuesta."
        agent.chat("Hola")
        agent.reset()

        mock_llm.return_value = "Segunda respuesta."
        agent.chat("Nuevo inicio")

        args, kwargs = mock_llm.call_args
        messages_sent = args[0] if args else kwargs.get("messages", [])
        # Después del reset, solo debe haber 1 mensaje (el nuevo) en el historial enviado
        assert len(messages_sent) == 1

    @patch("travelops.exercise02_agent_with_tools.call_llm")
    def test_flight_search_react_cycle(self, mock_llm):
        """Ciclo completo: el agente busca vuelos y formula respuesta con los datos."""
        tool_call = '{"tool": "search_flights", "args": {"origin": "Lima", "destination": "Madrid", "date": "15 de marzo"}}'
        final = "Encontré varios vuelos. El más económico sale a las 22:00 por $320."

        mock_llm.side_effect = [tool_call, final]

        agent = TravelAgentWithTools()
        result = agent.chat("Busca vuelos de Lima a Madrid para el 15 de marzo")

        assert result == final
        # Verificar que el resultado del vuelo esté en el historial
        history_contents = " ".join(m["content"] for m in agent.history)
        assert "Lima" in history_contents
        assert "Madrid" in history_contents
