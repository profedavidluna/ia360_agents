"""
Tests — Ejercicio 04: Agente RAG de TravelOps
=============================================

Cubre:
- split_text y validaciones básicas
- TravelKnowledgeBase: indexación y recuperación
- build_rag_system_prompt
- TravelRAGAgent: inicialización, chat, reset y fallback sin contexto

Cómo ejecutar:
    pytest test_exercise04_rag.py -v
"""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from travelops.exercise04_rag import (
    TravelKnowledgeBase,
    TravelRAGAgent,
    build_default_documents,
    build_rag_system_prompt,
    split_text,
)


class TestSplitText:
    def test_returns_chunks_for_long_text(self):
        text = " ".join(f"palabra{i}" for i in range(25))
        chunks = split_text(text, chunk_size=10, overlap=2)
        assert len(chunks) >= 3

    def test_empty_text_returns_empty_list(self):
        assert split_text("") == []

    def test_invalid_chunk_size_raises(self):
        with pytest.raises(ValueError):
            split_text("hola mundo", chunk_size=0)

    def test_invalid_overlap_raises(self):
        with pytest.raises(ValueError):
            split_text("hola mundo", chunk_size=5, overlap=5)


class TestTravelKnowledgeBase:
    def test_add_documents_creates_chunks(self):
        kb = TravelKnowledgeBase(chunk_size=20, overlap=5)
        kb.add_documents(build_default_documents())
        assert len(kb.chunks) > 0

    def test_search_returns_relevant_chunk(self):
        kb = TravelKnowledgeBase(chunk_size=30, overlap=5)
        kb.add_documents(build_default_documents())
        results = kb.search("Kioto templos cerezos", top_k=2)
        assert len(results) >= 1
        assert "Kioto" in results[0].chunk.content or "Kioto" in results[0].chunk.source_title

    def test_search_returns_empty_for_irrelevant_query(self):
        kb = TravelKnowledgeBase()
        kb.add_documents(build_default_documents())
        assert kb.search("xylophone quantum broccoli", top_k=3) == []

    def test_format_context_mentions_source(self):
        kb = TravelKnowledgeBase(chunk_size=30, overlap=5)
        kb.add_documents(build_default_documents())
        results = kb.search("París metro museo", top_k=1)
        context = kb.format_context(results)
        assert "Fuente:" in context


class TestBuildRagSystemPrompt:
    def test_returns_non_empty_string(self):
        prompt = build_rag_system_prompt()
        assert isinstance(prompt, str) and len(prompt) > 0

    def test_prompt_mentions_context(self):
        prompt = build_rag_system_prompt().lower()
        assert "contexto" in prompt


class TestTravelRagAgent:
    def test_agent_loads_default_knowledge_base(self):
        agent = TravelRAGAgent()
        assert len(agent.knowledge_base.chunks) > 0

    @patch("travelops.exercise04_rag.call_llm")
    def test_chat_uses_retrieved_context(self, mock_llm):
        mock_llm.return_value = "Kioto es ideal en primavera por los cerezos."
        agent = TravelRAGAgent()
        result = agent.chat("¿Cuál es la mejor época para visitar Kioto?")
        assert result == "Kioto es ideal en primavera por los cerezos."
        _, kwargs = mock_llm.call_args
        messages = kwargs["messages"]
        assert "Contexto recuperado" in messages[-1]["content"]
        assert "Kioto" in messages[-1]["content"]

    @patch("travelops.exercise04_rag.call_llm")
    def test_chat_appends_history(self, mock_llm):
        mock_llm.return_value = "Respuesta RAG."
        agent = TravelRAGAgent()
        agent.chat("¿Cómo moverse en Tokio?")
        assert len(agent.history) == 2
        assert agent.history[0]["role"] == "user"
        assert agent.history[1]["role"] == "assistant"

    def test_chat_returns_fallback_without_context(self):
        agent = TravelRAGAgent()
        result = agent.chat("xylophone quantum broccoli")
        assert "No encontré contexto suficiente" in result

    def test_chat_raises_on_empty_message(self):
        agent = TravelRAGAgent()
        with pytest.raises(ValueError):
            agent.chat("   ")

    @patch("travelops.exercise04_rag.call_llm")
    def test_reset_clears_history(self, mock_llm):
        mock_llm.return_value = "Respuesta."
        agent = TravelRAGAgent()
        agent.chat("¿Qué zona conviene en París?")
        agent.reset()
        assert agent.history == []
