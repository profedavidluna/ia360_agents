"""
Tests — Ejercicio 05: Workflow de Reserva de TravelOps
======================================================

Cubre:
- TravelRequest y validación de campos faltantes
- extract_trip_details
- mensajes de guía del workflow
- BookingWorkflowAgent: recopilación, confirmación, reset y fallback

Cómo ejecutar:
    pytest test_exercise05_booking_workflow.py -v
"""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from travelops.exercise05_booking_workflow import (
    BookingWorkflowAgent,
    TravelRequest,
    WorkflowStatus,
    build_missing_fields_message,
    build_ready_to_confirm_message,
    extract_trip_details,
)


class TestTravelRequest:
    def test_missing_fields_detects_required_data(self):
        request = TravelRequest(origin="Lima", destination="Madrid")
        assert "departure_date" in request.missing_fields()
        assert "budget_usd" in request.missing_fields()

    def test_is_complete_when_all_fields_exist(self):
        request = TravelRequest(
            origin="Lima",
            destination="Madrid",
            departure_date="2026-09-10",
            return_date="2026-09-18",
            travelers=2,
            budget_usd=2400,
        )
        assert request.is_complete() is True

    def test_update_ignores_none_values(self):
        request = TravelRequest(origin="Lima")
        request.update({"destination": "Madrid", "budget_usd": None})
        assert request.destination == "Madrid"
        assert request.budget_usd is None


class TestExtractTripDetails:
    def test_extracts_route_dates_travelers_and_budget(self):
        details = extract_trip_details(
            "Quiero viajar de Lima a Madrid del 2026-09-10 al 2026-09-18 para 2 personas con presupuesto 2400"
        )
        assert details["origin"] == "Lima"
        assert details["destination"] == "Madrid"
        assert details["departure_date"] == "2026-09-10"
        assert details["return_date"] == "2026-09-18"
        assert details["travelers"] == 2
        assert details["budget_usd"] == 2400

    def test_extracts_individual_dates(self):
        details = extract_trip_details("Salida 2026-10-02 y regreso 2026-10-12")
        assert details["departure_date"] == "2026-10-02"
        assert details["return_date"] == "2026-10-12"

    def test_extracts_notes_when_present(self):
        details = extract_trip_details("Notas: prefiero hotel céntrico")
        assert details["notes"] == "prefiero hotel céntrico"


class TestWorkflowMessages:
    def test_missing_fields_message_mentions_needed_data(self):
        request = TravelRequest(origin="Lima")
        message = build_missing_fields_message(request)
        assert "destino" in message
        assert "presupuesto" in message

    def test_ready_message_contains_summary(self):
        request = TravelRequest(
            origin="Lima",
            destination="Madrid",
            departure_date="2026-09-10",
            return_date="2026-09-18",
            travelers=2,
            budget_usd=2400,
        )
        message = build_ready_to_confirm_message(request)
        assert "confirmar" in message.lower()
        assert "Madrid" in message


class TestBookingWorkflowAgent:
    def test_initial_status_is_collecting(self):
        agent = BookingWorkflowAgent()
        assert agent.status == WorkflowStatus.COLLECTING

    def test_chat_raises_on_empty_message(self):
        agent = BookingWorkflowAgent()
        with pytest.raises(ValueError):
            agent.chat(" ")

    def test_chat_collects_partial_information(self):
        agent = BookingWorkflowAgent()
        response = agent.chat("Quiero viajar de Lima a Madrid")
        assert agent.request.origin == "Lima"
        assert agent.request.destination == "Madrid"
        assert "fecha" in response.lower()

    def test_chat_accumulates_information_across_turns(self):
        agent = BookingWorkflowAgent()
        agent.chat("Quiero viajar de Lima a Madrid")
        response = agent.chat("Del 2026-09-10 al 2026-09-18 para 2 personas con presupuesto 2400")
        assert agent.request.is_complete() is True
        assert agent.status == WorkflowStatus.READY_TO_CONFIRM
        assert "confirmar" in response.lower()

    @patch("travelops.exercise05_booking_workflow.call_llm")
    def test_confirmation_calls_llm(self, mock_llm):
        mock_llm.return_value = "Reserva lista. Considera comprar el seguro de viaje."
        agent = BookingWorkflowAgent()
        agent.chat(
            "Quiero viajar de Lima a Madrid del 2026-09-10 al 2026-09-18 para 2 personas con presupuesto 2400"
        )
        result = agent.chat("confirmar")
        assert result == "Reserva lista. Considera comprar el seguro de viaje."
        assert agent.status == WorkflowStatus.CONFIRMED

    @patch("travelops.exercise05_booking_workflow.call_llm")
    def test_confirmation_falls_back_when_llm_fails(self, mock_llm):
        mock_llm.side_effect = RuntimeError("Servidor caído")
        agent = BookingWorkflowAgent()
        agent.chat(
            "Quiero viajar de Lima a Madrid del 2026-09-10 al 2026-09-18 para 2 personas con presupuesto 2400"
        )
        result = agent.chat("confirmar")
        assert "solicitud quedó confirmada" in result.lower()
        assert agent.status == WorkflowStatus.CONFIRMED

    def test_reset_clears_request_and_history(self):
        agent = BookingWorkflowAgent()
        agent.chat("Quiero viajar de Lima a Madrid")
        message = agent.chat("reiniciar")
        assert "reiniciado" in message.lower()
        assert agent.request.origin is None
        assert agent.history[-1]["role"] == "assistant"

