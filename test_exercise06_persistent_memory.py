"""
Tests — Ejercicio 06: Agente con Memoria Persistente
=====================================================

Cubre:
- MemoryEntry: creación y categoría por defecto
- MemoryStore: add, forget, search, clear, load/save, to_context_string
- extract_memories: parseo de respuesta JSON del LLM
- PersistentTravelAgent: chat, reset, clear_memory, actualización de memoria

Cómo ejecutar:
    pytest test_exercise06_persistent_memory.py -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from travelops.exercise06_persistent_memory import (
    MemoryEntry,
    MemoryStore,
    PersistentTravelAgent,
    extract_memories,
)


class TestMemoryEntry:
    def test_default_category_is_otro(self):
        entry = MemoryEntry(key="k", value="v")
        assert entry.category == "otro"

    def test_invalid_category_falls_back_to_otro(self):
        entry = MemoryEntry(key="k", value="v", category="desconocido")
        assert entry.category == "otro"

    def test_valid_category_is_preserved(self):
        entry = MemoryEntry(key="nombre_usuario", value="Ana", category="nombre")
        assert entry.category == "nombre"


class TestMemoryStore:
    def _make_store(self, tmp_path: str) -> MemoryStore:
        file_path = os.path.join(tmp_path, "memory.json")
        return MemoryStore(file_path)

    def test_starts_empty(self, tmp_path):
        store = self._make_store(str(tmp_path))
        assert len(store) == 0
        assert store.all() == []

    def test_add_creates_entry(self, tmp_path):
        store = self._make_store(str(tmp_path))
        entry = store.add("nombre_usuario", "Ana", "nombre")
        assert entry.key == "nombre_usuario"
        assert entry.value == "Ana"
        assert len(store) == 1

    def test_add_updates_existing_key(self, tmp_path):
        store = self._make_store(str(tmp_path))
        store.add("nombre_usuario", "Ana", "nombre")
        store.add("nombre_usuario", "María", "nombre")
        assert len(store) == 1
        assert store.all()[0].value == "María"

    def test_forget_removes_entry(self, tmp_path):
        store = self._make_store(str(tmp_path))
        store.add("k", "v")
        assert store.forget("k") is True
        assert len(store) == 0

    def test_forget_returns_false_for_missing_key(self, tmp_path):
        store = self._make_store(str(tmp_path))
        assert store.forget("nonexistent") is False

    def test_clear_removes_all_entries(self, tmp_path):
        store = self._make_store(str(tmp_path))
        store.add("a", "1")
        store.add("b", "2")
        store.clear()
        assert len(store) == 0

    def test_search_by_text(self, tmp_path):
        store = self._make_store(str(tmp_path))
        store.add("destino_favorito", "Japón", "destino_deseado")
        store.add("nombre_usuario", "Pedro", "nombre")
        results = store.search(query="Japón")
        assert len(results) == 1
        assert results[0].value == "Japón"

    def test_search_by_category(self, tmp_path):
        store = self._make_store(str(tmp_path))
        store.add("destino_favorito", "Japón", "destino_deseado")
        store.add("nombre_usuario", "Pedro", "nombre")
        results = store.search(category="nombre")
        assert len(results) == 1
        assert results[0].key == "nombre_usuario"

    def test_persistence_across_instances(self, tmp_path):
        file_path = str(tmp_path / "mem.json")
        store1 = MemoryStore(file_path)
        store1.add("clave", "valor")

        store2 = MemoryStore(file_path)
        assert len(store2) == 1
        assert store2.all()[0].value == "valor"

    def test_to_context_string_empty(self, tmp_path):
        store = self._make_store(str(tmp_path))
        assert "sin memoria" in store.to_context_string()

    def test_to_context_string_with_entries(self, tmp_path):
        store = self._make_store(str(tmp_path))
        store.add("nombre_usuario", "Ana", "nombre")
        ctx = store.to_context_string()
        assert "Ana" in ctx
        assert "nombre" in ctx

    def test_load_ignores_corrupt_file(self, tmp_path):
        file_path = str(tmp_path / "bad.json")
        with open(file_path, "w") as f:
            f.write("not-json{{{")
        store = MemoryStore(file_path)
        assert len(store) == 0


class TestExtractMemories:
    def test_returns_empty_list_on_llm_failure(self):
        with patch(
            "travelops.exercise06_persistent_memory.call_llm",
            side_effect=RuntimeError("sin conexión"),
        ):
            result = extract_memories("Hola, me llamo Juan")
            assert result == []

    def test_parses_valid_json_array(self):
        llm_response = json.dumps(
            [{"key": "nombre_usuario", "value": "Ana", "category": "nombre"}]
        )
        with patch(
            "travelops.exercise06_persistent_memory.call_llm",
            return_value=llm_response,
        ):
            result = extract_memories("Me llamo Ana")
            assert len(result) == 1
            assert result[0]["key"] == "nombre_usuario"
            assert result[0]["value"] == "Ana"

    def test_handles_json_with_surrounding_text(self):
        llm_response = (
            'Aquí está el resultado:\n'
            '[{"key": "preferencia_viaje", "value": "senderismo", "category": "preferencia"}]'
        )
        with patch(
            "travelops.exercise06_persistent_memory.call_llm",
            return_value=llm_response,
        ):
            result = extract_memories("Me encanta el senderismo")
            assert len(result) == 1
            assert result[0]["key"] == "preferencia_viaje"

    def test_returns_empty_list_for_no_facts(self):
        with patch(
            "travelops.exercise06_persistent_memory.call_llm",
            return_value="[]",
        ):
            result = extract_memories("¿Qué tiempo hace en París?")
            assert result == []


class TestPersistentTravelAgent:
    def _make_agent(self, tmp_path) -> PersistentTravelAgent:
        file_path = str(tmp_path / "test_memory.json")
        store = MemoryStore(file_path)
        return PersistentTravelAgent(memory=store)

    def test_chat_raises_on_empty_message(self, tmp_path):
        agent = self._make_agent(tmp_path)
        with pytest.raises(ValueError):
            agent.chat("   ")

    @patch("travelops.exercise06_persistent_memory.call_llm")
    def test_chat_returns_llm_response(self, mock_llm, tmp_path):
        mock_llm.return_value = "¡Hola! ¿En qué puedo ayudarte?"
        agent = self._make_agent(tmp_path)
        response = agent.chat("Hola")
        assert response == "¡Hola! ¿En qué puedo ayudarte?"

    @patch("travelops.exercise06_persistent_memory.call_llm")
    def test_chat_adds_messages_to_history(self, mock_llm, tmp_path):
        mock_llm.return_value = "Respuesta"
        agent = self._make_agent(tmp_path)
        agent.chat("Mensaje de prueba")
        assert len(agent.history) == 2
        assert agent.history[0]["role"] == "user"
        assert agent.history[1]["role"] == "assistant"

    @patch("travelops.exercise06_persistent_memory.call_llm")
    def test_memory_is_updated_from_chat(self, mock_llm, tmp_path):
        # Primera llamada: extract_memories (retorna un hecho)
        # Segunda llamada: respuesta del agente
        fact_json = '[{"key": "nombre_usuario", "value": "Ana", "category": "nombre"}]'
        mock_llm.side_effect = [fact_json, "Hola Ana, ¿en qué puedo ayudarte?"]
        agent = self._make_agent(tmp_path)
        agent.chat("Me llamo Ana")
        assert agent.memory.search(query="Ana") != []

    def test_reset_clears_history_but_keeps_memory(self, tmp_path):
        agent = self._make_agent(tmp_path)
        agent.memory.add("nombre_usuario", "Ana", "nombre")

        with patch(
            "travelops.exercise06_persistent_memory.call_llm",
            return_value="Respuesta",
        ):
            agent.chat("Hola")

        agent.reset()
        assert agent.history == []
        assert len(agent.memory) == 1

    def test_clear_memory_removes_all_entries(self, tmp_path):
        agent = self._make_agent(tmp_path)
        agent.memory.add("nombre_usuario", "Ana", "nombre")
        agent.clear_memory()
        assert len(agent.memory) == 0

    @patch("travelops.exercise06_persistent_memory.call_llm")
    def test_system_prompt_includes_memory_context(self, mock_llm, tmp_path):
        mock_llm.return_value = "OK"
        agent = self._make_agent(tmp_path)
        agent.memory.add("nombre_usuario", "Ana", "nombre")

        agent.chat("hola")

        # Verificar que el system prompt enviado al LLM contiene la memoria
        _, kwargs = mock_llm.call_args
        system = kwargs.get("system_prompt", "")
        assert "Ana" in system
