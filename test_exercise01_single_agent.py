"""
Tests — Ejercicio 01: Agente Único de TravelOps
================================================

Cubre:
- Configuración del LLM (get_llm_config)
- Prompt del sistema (build_system_prompt)
- Clase TravelAgent: init, chat (con LLM mockeado), reset
- Manejo de entradas inválidas y errores del LLM
- Acumulación correcta del historial de conversación

Cómo ejecutar:
    pytest test_exercise01_single_agent.py -v
"""

from __future__ import annotations

import sys
import os
from unittest.mock import patch, MagicMock

import pytest

# Asegurar que el paquete raíz esté en el path
sys.path.insert(0, os.path.dirname(__file__))

from travelops.exercise01_single_agent import (
    TravelAgent,
    build_system_prompt,
    call_llm,
    get_llm_config,
)


# ---------------------------------------------------------------------------
# Tests de get_llm_config
# ---------------------------------------------------------------------------

class TestGetLlmConfig:
    """Verifica que la configuración del LLM se lea correctamente."""

    def test_returns_dict_with_required_keys(self):
        config = get_llm_config()
        assert "base_url" in config
        assert "api_key" in config
        assert "model" in config

    def test_default_base_url_contains_localhost(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LLM_BASE_URL", None)
            config = get_llm_config()
        assert "localhost" in config["base_url"]

    def test_env_overrides_base_url(self):
        with patch.dict(os.environ, {"LLM_BASE_URL": "http://myserver:9000/v1/messages"}):
            config = get_llm_config()
        assert config["base_url"] == "http://myserver:9000/v1/messages"

    def test_env_overrides_model(self):
        with patch.dict(os.environ, {"LLM_MODEL": "claude-3-opus-20240229"}):
            config = get_llm_config()
        assert config["model"] == "claude-3-opus-20240229"

    def test_all_values_are_strings(self):
        config = get_llm_config()
        for key, value in config.items():
            assert isinstance(value, str), f"El valor de '{key}' debe ser str"


# ---------------------------------------------------------------------------
# Tests de build_system_prompt
# ---------------------------------------------------------------------------

class TestBuildSystemPrompt:
    """Verifica que el prompt del sistema sea adecuado para un agente de viajes."""

    def test_returns_non_empty_string(self):
        prompt = build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_mentions_travel_domain(self):
        prompt = build_system_prompt().lower()
        # Debe contener al menos una palabra clave de viajes
        travel_keywords = {"viaje", "viajes", "destino", "turismo", "travel"}
        assert any(kw in prompt for kw in travel_keywords), (
            "El prompt debe mencionar conceptos de viajes"
        )

    def test_prompt_is_in_spanish(self):
        prompt = build_system_prompt()
        spanish_words = {"eres", "puedes", "ayudar", "responde", "siempre"}
        assert any(word in prompt.lower() for word in spanish_words), (
            "El prompt debe estar en español"
        )

    def test_prompt_is_deterministic(self):
        """Llamadas sucesivas deben devolver el mismo prompt."""
        assert build_system_prompt() == build_system_prompt()


# ---------------------------------------------------------------------------
# Tests de TravelAgent — inicialización
# ---------------------------------------------------------------------------

class TestTravelAgentInit:
    """Verifica el estado inicial del agente."""

    def test_history_starts_empty(self):
        agent = TravelAgent()
        assert agent.history == []

    def test_system_prompt_is_set(self):
        agent = TravelAgent()
        assert isinstance(agent.system_prompt, str)
        assert len(agent.system_prompt) > 0

    def test_custom_system_prompt(self):
        custom = "Eres un agente de prueba."
        agent = TravelAgent(system_prompt=custom)
        assert agent.system_prompt == custom

    def test_different_agents_have_independent_histories(self):
        agent_a = TravelAgent()
        agent_b = TravelAgent()
        # Modificar la historia de uno no debe afectar al otro
        agent_a.history.append({"role": "user", "content": "Hola"})
        assert agent_b.history == []


# ---------------------------------------------------------------------------
# Tests de TravelAgent.reset
# ---------------------------------------------------------------------------

class TestTravelAgentReset:
    """Verifica que reset() limpia correctamente el historial."""

    def test_reset_clears_history(self):
        agent = TravelAgent()
        agent.history = [
            {"role": "user", "content": "¿Qué llevar a París?"},
            {"role": "assistant", "content": "Lleva un paraguas..."},
        ]
        agent.reset()
        assert agent.history == []

    def test_reset_preserves_system_prompt(self):
        agent = TravelAgent()
        original_prompt = agent.system_prompt
        agent.reset()
        assert agent.system_prompt == original_prompt

    def test_reset_on_empty_history_is_safe(self):
        agent = TravelAgent()
        agent.reset()  # No debe lanzar excepción
        assert agent.history == []


# ---------------------------------------------------------------------------
# Tests de TravelAgent.chat — con LLM mockeado
# ---------------------------------------------------------------------------

class TestTravelAgentChat:
    """Verifica el comportamiento de chat() sin requerir un LLM real."""

    @patch("travelops.exercise01_single_agent.call_llm")
    def test_chat_returns_string(self, mock_call_llm):
        mock_call_llm.return_value = "París es una ciudad maravillosa."
        agent = TravelAgent()
        result = agent.chat("¿Qué me recomiendas de París?")
        assert isinstance(result, str)
        assert result == "París es una ciudad maravillosa."

    @patch("travelops.exercise01_single_agent.call_llm")
    def test_chat_adds_user_message_to_history(self, mock_call_llm):
        mock_call_llm.return_value = "Respuesta de prueba."
        agent = TravelAgent()
        agent.chat("¿Cuándo viajar a Japón?")
        assert len(agent.history) >= 1
        assert agent.history[0]["role"] == "user"
        assert agent.history[0]["content"] == "¿Cuándo viajar a Japón?"

    @patch("travelops.exercise01_single_agent.call_llm")
    def test_chat_adds_assistant_response_to_history(self, mock_call_llm):
        mock_call_llm.return_value = "La mejor época es primavera (marzo-mayo)."
        agent = TravelAgent()
        agent.chat("¿Cuándo viajar a Japón?")
        assert len(agent.history) == 2
        assert agent.history[1]["role"] == "assistant"
        assert agent.history[1]["content"] == "La mejor época es primavera (marzo-mayo)."

    @patch("travelops.exercise01_single_agent.call_llm")
    def test_chat_accumulates_history_across_turns(self, mock_call_llm):
        mock_call_llm.side_effect = [
            "Tailandia es ideal para tu presupuesto.",
            "Bangkok tiene muchos templos y mercados nocturnos.",
        ]
        agent = TravelAgent()
        agent.chat("¿Qué destino económico me recomiendas?")
        agent.chat("¿Qué hacer en Bangkok?")
        # 2 turnos × 2 mensajes por turno = 4 mensajes en el historial
        assert len(agent.history) == 4
        assert agent.history[2]["role"] == "user"
        assert agent.history[3]["role"] == "assistant"

    @patch("travelops.exercise01_single_agent.call_llm")
    def test_chat_strips_whitespace_from_user_message(self, mock_call_llm):
        mock_call_llm.return_value = "Respuesta."
        agent = TravelAgent()
        agent.chat("  ¿Cuánto cuesta volar a Roma?  ")
        assert agent.history[0]["content"] == "¿Cuánto cuesta volar a Roma?"

    @patch("travelops.exercise01_single_agent.call_llm")
    def test_chat_passes_system_prompt_to_llm(self, mock_call_llm):
        mock_call_llm.return_value = "Respuesta."
        agent = TravelAgent(system_prompt="Eres un experto en visados.")
        agent.chat("¿Necesito visa para Canadá?")
        _, kwargs = mock_call_llm.call_args
        assert kwargs.get("system_prompt") == "Eres un experto en visados."

    @patch("travelops.exercise01_single_agent.call_llm")
    def test_chat_passes_full_history_to_llm(self, mock_call_llm):
        mock_call_llm.return_value = "Respuesta."
        agent = TravelAgent()
        agent.chat("Primer mensaje")
        mock_call_llm.reset_mock()

        agent.chat("Segundo mensaje")
        args, kwargs = mock_call_llm.call_args
        messages_sent = args[0] if args else kwargs.get("messages", [])
        # El historial enviado debe incluir los dos turnos anteriores más el nuevo
        assert len(messages_sent) == 3

    def test_chat_raises_on_empty_message(self):
        agent = TravelAgent()
        with pytest.raises(ValueError):
            agent.chat("")

    def test_chat_raises_on_whitespace_only_message(self):
        agent = TravelAgent()
        with pytest.raises(ValueError):
            agent.chat("   ")

    @patch("travelops.exercise01_single_agent.call_llm")
    def test_chat_propagates_llm_runtime_error(self, mock_call_llm):
        mock_call_llm.side_effect = RuntimeError("Servidor no disponible.")
        agent = TravelAgent()
        with pytest.raises(RuntimeError, match="Servidor no disponible."):
            agent.chat("¿Qué ver en Roma?")

    @patch("travelops.exercise01_single_agent.call_llm")
    def test_history_not_updated_when_llm_fails(self, mock_call_llm):
        mock_call_llm.side_effect = RuntimeError("Error de red.")
        agent = TravelAgent()
        try:
            agent.chat("¿Qué ver en Roma?")
        except RuntimeError:
            pass
        # El mensaje del usuario sí se agrega antes de llamar al LLM;
        # la respuesta del asistente NO debe estar en el historial.
        assistant_messages = [m for m in agent.history if m["role"] == "assistant"]
        assert len(assistant_messages) == 0


# ---------------------------------------------------------------------------
# Tests de integración del historial
# ---------------------------------------------------------------------------

class TestConversationHistory:
    """Verifica la coherencia del historial después de varios turnos."""

    @patch("travelops.exercise01_single_agent.call_llm")
    def test_history_alternates_roles(self, mock_call_llm):
        mock_call_llm.side_effect = [f"Respuesta {i}" for i in range(5)]
        agent = TravelAgent()
        for i in range(5):
            agent.chat(f"Pregunta {i}")

        for i, msg in enumerate(agent.history):
            expected_role = "user" if i % 2 == 0 else "assistant"
            assert msg["role"] == expected_role, (
                f"Mensaje {i}: se esperaba '{expected_role}', se obtuvo '{msg['role']}'"
            )

    @patch("travelops.exercise01_single_agent.call_llm")
    def test_reset_then_chat_starts_fresh(self, mock_call_llm):
        mock_call_llm.return_value = "Nueva respuesta."
        agent = TravelAgent()

        # Primer turno
        mock_call_llm.return_value = "Respuesta inicial."
        agent.chat("Hola")

        # Limpiar historial
        agent.reset()
        assert agent.history == []

        # Nuevo turno — el historial enviado al LLM solo debe tener 1 mensaje
        mock_call_llm.return_value = "Respuesta nueva."
        agent.chat("Nuevo inicio")
        args, kwargs = mock_call_llm.call_args
        messages_sent = args[0] if args else kwargs.get("messages", [])
        assert len(messages_sent) == 1
