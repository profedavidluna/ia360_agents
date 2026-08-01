"""
Tests — Ejercicio 07: Agente con Crítica y Auto-Mejora
======================================================

Cubre:
- EvaluationResult: validación de score
- parse_evaluation: extracción de puntuación y sugerencias
- TravelPlannerAgent.plan: generación de plan inicial y revisado
- TravelCriticAgent.evaluate: delegación al LLM y parseo
- EvaluatorAgent.run_cycle: ciclo completo, parada anticipada y por iteraciones
- EvaluatorAgent.chat: respuesta con resumen del ciclo
- EvaluatorAgent.reset: limpieza del historial

Cómo ejecutar:
    pytest test_exercise07_critic_evaluator.py -v
"""

from __future__ import annotations

import os
import sys
from unittest.mock import call, patch

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from travelops.exercise07_critic_evaluator import (
    EvaluationResult,
    EvaluatorAgent,
    RevisionRecord,
    TravelCriticAgent,
    TravelPlannerAgent,
    parse_evaluation,
)


class TestEvaluationResult:
    def test_score_is_clamped_to_0_10(self):
        result = EvaluationResult(score=15.0, critique="texto")
        assert result.score == 10.0

        result2 = EvaluationResult(score=-3.0, critique="texto")
        assert result2.score == 0.0

    def test_passed_is_set_correctly(self):
        result = EvaluationResult(score=8.0, critique="bien", passed=True)
        assert result.passed is True

        result2 = EvaluationResult(score=5.0, critique="regular", passed=False)
        assert result2.passed is False


class TestParseEvaluation:
    def test_extracts_score_with_out_of_ten(self):
        text = "Puntuación: 8/10\nEl plan es sólido."
        result = parse_evaluation(text, min_score=7.0)
        assert result.score == 8.0
        assert result.passed is True

    def test_extracts_score_keyword_only(self):
        text = "Score: 6\n- Agregar más actividades culturales"
        result = parse_evaluation(text, min_score=7.0)
        assert result.score == 6.0
        assert result.passed is False

    def test_extracts_x_slash_10_pattern(self):
        text = "Este plan merece un 9/10 por su detalle."
        result = parse_evaluation(text)
        assert result.score == 9.0

    def test_defaults_to_5_when_no_score_found(self):
        text = "El plan tiene algunos problemas."
        result = parse_evaluation(text, min_score=7.0)
        assert result.score == 5.0
        assert result.passed is False

    def test_extracts_suggestions_from_bullets(self):
        text = "Puntuación: 6/10\n- Añadir más restaurantes\n- Revisar presupuesto"
        result = parse_evaluation(text)
        assert len(result.suggestions) >= 2
        assert any("restaurantes" in s for s in result.suggestions)

    def test_extracts_suggestions_from_numbered_list(self):
        text = "Nota: 7/10\n1. Mejorar transporte\n2. Agregar día libre"
        result = parse_evaluation(text)
        assert len(result.suggestions) >= 2

    def test_passed_true_when_score_equals_min(self):
        text = "Puntuación: 7/10"
        result = parse_evaluation(text, min_score=7.0)
        assert result.passed is True


class TestTravelPlannerAgent:
    @patch("travelops.exercise07_critic_evaluator.call_llm")
    def test_plan_generates_initial_plan(self, mock_llm):
        mock_llm.return_value = "Día 1: Llegar a Tokio..."
        agent = TravelPlannerAgent()
        result = agent.plan(request="5 días en Tokio")
        assert "Tokio" in result
        mock_llm.assert_called_once()

    @patch("travelops.exercise07_critic_evaluator.call_llm")
    def test_plan_includes_feedback_in_revision(self, mock_llm):
        mock_llm.return_value = "Plan revisado con mejoras."
        agent = TravelPlannerAgent()
        agent.plan(
            request="5 días en Tokio",
            feedback="Falta actividad cultural",
            previous_plan="Plan inicial...",
        )
        args, kwargs = mock_llm.call_args
        messages = kwargs.get("messages") or args[0]
        content = messages[0]["content"]
        assert "Falta actividad cultural" in content
        assert "Plan inicial" in content

    @patch("travelops.exercise07_critic_evaluator.call_llm")
    def test_plan_raises_on_llm_failure(self, mock_llm):
        mock_llm.side_effect = RuntimeError("sin conexión")
        agent = TravelPlannerAgent()
        with pytest.raises(RuntimeError):
            agent.plan(request="viaje a París")


class TestTravelCriticAgent:
    @patch("travelops.exercise07_critic_evaluator.call_llm")
    def test_evaluate_returns_evaluation_result(self, mock_llm):
        mock_llm.return_value = "Puntuación: 8/10\n- Buen itinerario"
        agent = TravelCriticAgent(min_score=7.0)
        result = agent.evaluate(plan="Plan de ejemplo", request="5 días en Roma")
        assert isinstance(result, EvaluationResult)
        assert result.score == 8.0
        assert result.passed is True

    @patch("travelops.exercise07_critic_evaluator.call_llm")
    def test_evaluate_marks_failed_when_score_below_min(self, mock_llm):
        mock_llm.return_value = "Score: 5/10\n- Necesita más detalles"
        agent = TravelCriticAgent(min_score=7.0)
        result = agent.evaluate(plan="Plan básico", request="viaje corto")
        assert result.passed is False

    @patch("travelops.exercise07_critic_evaluator.call_llm")
    def test_evaluate_raises_on_llm_failure(self, mock_llm):
        mock_llm.side_effect = RuntimeError("LLM no disponible")
        agent = TravelCriticAgent()
        with pytest.raises(RuntimeError):
            agent.evaluate(plan="plan", request="viaje")


class TestEvaluatorAgent:
    def _make_agent(self, min_score: float = 7.0, max_iter: int = 3) -> EvaluatorAgent:
        planner = TravelPlannerAgent()
        critic = TravelCriticAgent(min_score=min_score)
        return EvaluatorAgent(
            planner=planner,
            critic=critic,
            min_score=min_score,
            max_iterations=max_iter,
        )

    def test_chat_raises_on_empty_message(self):
        agent = self._make_agent()
        with pytest.raises(ValueError):
            agent.chat("  ")

    @patch("travelops.exercise07_critic_evaluator.call_llm")
    def test_cycle_stops_early_when_score_passes(self, mock_llm):
        # Primera llamada: planificador genera plan
        # Segunda llamada: crítico da 8/10 (pasa)
        mock_llm.side_effect = [
            "Plan de viaje detallado...",
            "Puntuación: 8/10\n- Todo bien",
        ]
        agent = self._make_agent(min_score=7.0, max_iter=3)
        agent.run_cycle("5 días en Madrid")
        assert len(agent.revisions) == 1
        assert agent.revisions[0].evaluation.passed is True

    @patch("travelops.exercise07_critic_evaluator.call_llm")
    def test_cycle_runs_max_iterations_when_score_never_passes(self, mock_llm):
        # Planificador: plan en iteraciones 1, 2, 3
        # Crítico: puntuación baja en cada una
        mock_llm.side_effect = [
            "Plan v1", "Puntuación: 4/10\n- Mejorar presupuesto",
            "Plan v2", "Puntuación: 5/10\n- Añadir actividades",
            "Plan v3", "Puntuación: 6/10\n- Revisar logística",
        ]
        agent = self._make_agent(min_score=7.0, max_iter=3)
        agent.run_cycle("viaje a Buenos Aires")
        assert len(agent.revisions) == 3

    @patch("travelops.exercise07_critic_evaluator.call_llm")
    def test_chat_returns_summary_with_score(self, mock_llm):
        mock_llm.side_effect = [
            "Itinerario completo...",
            "Puntuación: 9/10\n- Excelente plan",
        ]
        agent = self._make_agent()
        result = agent.chat("3 días en Lima")
        assert "9.0/10" in result
        assert "iteración" in result.lower()

    @patch("travelops.exercise07_critic_evaluator.call_llm")
    def test_reset_clears_revisions(self, mock_llm):
        mock_llm.side_effect = [
            "Plan de viaje",
            "Puntuación: 8/10",
        ]
        agent = self._make_agent()
        agent.run_cycle("viaje")
        assert len(agent.revisions) == 1
        agent.reset()
        assert agent.revisions == []

    @patch("travelops.exercise07_critic_evaluator.call_llm")
    def test_revisions_contain_plan_and_evaluation(self, mock_llm):
        mock_llm.side_effect = [
            "Plan detallado de Tokio",
            "Puntuación: 7/10\n- Buen trabajo",
        ]
        agent = self._make_agent(min_score=7.0, max_iter=1)
        agent.run_cycle("Tokio 5 días")
        rev = agent.revisions[0]
        assert isinstance(rev, RevisionRecord)
        assert rev.iteration == 1
        assert "Tokio" in rev.plan
        assert rev.evaluation.score == 7.0

    @patch("travelops.exercise07_critic_evaluator.call_llm")
    def test_second_iteration_receives_first_plan_as_context(self, mock_llm):
        mock_llm.side_effect = [
            "Plan inicial v1",
            "Puntuación: 5/10\n- Falta detalle",
            "Plan revisado v2",
            "Puntuación: 8/10\n- Mucho mejor",
        ]
        agent = self._make_agent(min_score=7.0, max_iter=3)
        agent.run_cycle("viaje a Santiago")
        assert len(agent.revisions) == 2
        # En la segunda llamada al planificador, el mensaje debe incluir el plan anterior
        second_planner_call = mock_llm.call_args_list[2]
        args, kwargs = second_planner_call
        messages = kwargs.get("messages") or args[0]
        content = messages[0]["content"]
        assert "Plan inicial v1" in content
