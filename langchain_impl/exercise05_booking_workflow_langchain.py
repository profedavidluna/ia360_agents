from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    from .common import get_llm_config, invoke_with_history
except ImportError:
    from common import get_llm_config, invoke_with_history


class WorkflowStatus(str, Enum):
    COLLECTING = "collecting"
    READY_TO_CONFIRM = "ready_to_confirm"
    CONFIRMED = "confirmed"


@dataclass
class TravelRequest:
    origin: str | None = None
    destination: str | None = None
    departure_date: str | None = None
    return_date: str | None = None
    travelers: int | None = None
    budget_usd: int | None = None
    notes: str | None = None

    def update(self, data: dict[str, Any]) -> None:
        for field_name, value in data.items():
            if value is None:
                continue
            setattr(self, field_name, value)

    def missing_fields(self) -> list[str]:
        required = [
            "origin",
            "destination",
            "departure_date",
            "return_date",
            "travelers",
            "budget_usd",
        ]
        return [name for name in required if getattr(self, name) in (None, "")]

    def is_complete(self) -> bool:
        return not self.missing_fields()

    def to_summary(self) -> str:
        lines = [
            f"Origen: {self.origin or 'pendiente'}",
            f"Destino: {self.destination or 'pendiente'}",
            f"Salida: {self.departure_date or 'pendiente'}",
            f"Regreso: {self.return_date or 'pendiente'}",
            f"Viajeros: {self.travelers if self.travelers is not None else 'pendiente'}",
            f"Presupuesto: {self.budget_usd if self.budget_usd is not None else 'pendiente'} USD",
        ]
        if self.notes:
            lines.append(f"Notas: {self.notes}")
        return "\n".join(lines)


def _extract_json_block(text: str) -> dict[str, Any] | None:
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None

    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _regex_extract_trip_details(message: str) -> dict[str, Any]:
    details: dict[str, Any] = {}
    text = " ".join(message.strip().split())

    route_match = re.search(
        r"\bde\s+([A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?)\s+a\s+([A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?)(?=(?:\s+(?:del|para|con|y)\b|$))",
        text,
        flags=re.IGNORECASE,
    )
    if route_match:
        details["origin"] = route_match.group(1).strip(" ,.")
        details["destination"] = route_match.group(2).strip(" ,.")

    range_match = re.search(
        r"\bdel\s+(\d{4}-\d{2}-\d{2})\s+al\s+(\d{4}-\d{2}-\d{2})\b",
        text,
        flags=re.IGNORECASE,
    )
    if range_match:
        details["departure_date"] = range_match.group(1)
        details["return_date"] = range_match.group(2)

    departure_match = re.search(r"\b(?:salida|ida)\s+(?:el\s+)?(\d{4}-\d{2}-\d{2})\b", text, flags=re.IGNORECASE)
    if departure_match:
        details["departure_date"] = departure_match.group(1)

    return_match = re.search(r"\b(?:regreso|vuelta)\s+(?:el\s+)?(\d{4}-\d{2}-\d{2})\b", text, flags=re.IGNORECASE)
    if return_match:
        details["return_date"] = return_match.group(1)

    travelers_match = re.search(
        r"\b(\d+)\s+(?:persona|personas|viajero|viajeros|pasajero|pasajeros)\b",
        text,
        flags=re.IGNORECASE,
    )
    if travelers_match:
        details["travelers"] = int(travelers_match.group(1))

    budget_match = re.search(r"\b(?:presupuesto|budget)(?:\s+de)?\s+\$?([\d.,]+)\b", text, flags=re.IGNORECASE)
    if budget_match:
        numeric_budget = budget_match.group(1).replace(".", "").replace(",", "")
        details["budget_usd"] = int(numeric_budget)

    note_match = re.search(r"\b(?:preferencias|notas|detalle)\s*:\s*(.+)$", text, flags=re.IGNORECASE)
    if note_match:
        details["notes"] = note_match.group(1).strip()

    return details


def extract_trip_details(message: str) -> dict[str, Any]:
    extraction_prompt = (
        "Extrae datos de solicitud de viaje y responde SOLO JSON con estas claves: "
        "origin, destination, departure_date, return_date, travelers, budget_usd, notes. "
        "Si falta un dato, usa null. Fechas en formato YYYY-MM-DD."
    )

    try:
        raw = invoke_with_history(extraction_prompt, [{"role": "user", "content": message}], temperature=0.0)
        parsed = _extract_json_block(raw)
        if parsed:
            clean: dict[str, Any] = {}
            for key in [
                "origin",
                "destination",
                "departure_date",
                "return_date",
                "travelers",
                "budget_usd",
                "notes",
            ]:
                value = parsed.get(key)
                if value in (None, "", "null"):
                    continue
                if key in {"travelers", "budget_usd"}:
                    try:
                        clean[key] = int(str(value).replace(".", "").replace(",", ""))
                    except ValueError:
                        continue
                else:
                    clean[key] = str(value).strip()
            if clean:
                return clean
    except Exception:
        pass

    return _regex_extract_trip_details(message)


def build_booking_system_prompt() -> str:
    return (
        "Eres TravelOps BookingBot con LangChain. "
        "Recibirás una solicitud de viaje completa y debes generar un resumen final "
        "claro, útil y profesional en español."
    )


def build_missing_fields_message(request: TravelRequest) -> str:
    labels = {
        "origin": "ciudad de origen",
        "destination": "destino",
        "departure_date": "fecha de salida (YYYY-MM-DD)",
        "return_date": "fecha de regreso (YYYY-MM-DD)",
        "travelers": "cantidad de viajeros",
        "budget_usd": "presupuesto estimado en USD",
    }
    pending = [labels[field] for field in request.missing_fields()]
    return f"Perfecto, ya registré parte de tu solicitud. Aún necesito: {', '.join(pending)}."


def build_ready_to_confirm_message(request: TravelRequest) -> str:
    return (
        "Ya tengo todos los datos:\n\n"
        f"{request.to_summary()}\n\n"
        "Si todo está correcto, responde 'confirmar' para generar el resumen final."
    )


def build_fallback_confirmation(request: TravelRequest) -> str:
    return (
        "Tu solicitud quedó confirmada.\n\n"
        f"{request.to_summary()}\n\n"
        "Siguiente paso: validar disponibilidad real de vuelo y hotel dentro del presupuesto."
    )


@dataclass
class BookingWorkflowAgent:
    system_prompt: str = field(default_factory=build_booking_system_prompt)
    request: TravelRequest = field(default_factory=TravelRequest)
    history: list[dict[str, str]] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.COLLECTING

    def _looks_like_confirmation(self, message: str) -> bool:
        return message.strip().lower() in {"confirmar", "confirmo", "si", "sí", "ok", "listo"}

    def _looks_like_reset(self, message: str) -> bool:
        return message.strip().lower() in {"reset", "reiniciar", "nuevo", "clear", "empezar de nuevo"}

    def _confirm_request(self) -> str:
        prompt = (
            "Genera un resumen final de reserva para esta solicitud:\n\n"
            f"{self.request.to_summary()}"
        )
        try:
            response = invoke_with_history(
                self.system_prompt,
                [{"role": "user", "content": prompt}],
                temperature=0.2,
            )
        except Exception:
            response = build_fallback_confirmation(self.request)

        self.status = WorkflowStatus.CONFIRMED
        return response

    def chat(self, user_message: str) -> str:
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        self.history.append({"role": "user", "content": user_message})

        if self._looks_like_reset(user_message):
            self.reset()
            response = (
                "He reiniciado la solicitud. Indícame origen, destino, fechas, viajeros "
                "y presupuesto para comenzar de nuevo."
            )
            self.history.append({"role": "assistant", "content": response})
            return response

        extracted = extract_trip_details(user_message)
        if extracted:
            self.request.update(extracted)

        if self.request.is_complete():
            if self._looks_like_confirmation(user_message):
                response = self._confirm_request()
            else:
                self.status = WorkflowStatus.READY_TO_CONFIRM
                response = build_ready_to_confirm_message(self.request)
        else:
            self.status = WorkflowStatus.COLLECTING
            response = build_missing_fields_message(self.request)

        self.history.append({"role": "assistant", "content": response})
        return response

    def reset(self) -> None:
        self.request = TravelRequest()
        self.status = WorkflowStatus.COLLECTING
        self.history = []

    def run_interactive(self) -> None:
        config = get_llm_config()
        print("=" * 66)
        print("TRAVELOPS LANGCHAIN — Ejercicio 05 (Workflow)")
        print("=" * 66)
        print(f"Modelo : {config['model']}")
        print(f"Servidor: {config['base_url']}")
        print("Escribe 'salir' para terminar o 'reiniciar' para comenzar otra solicitud.\n")

        while True:
            try:
                user_input = input("Tú> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nHasta pronto. ✈️")
                return

            if not user_input:
                continue
            if user_input.lower() in {"salir", "exit", "quit", "q"}:
                print("¡Hasta pronto!")
                return

            try:
                answer = self.chat(user_input)
                print(f"\nTravelOps Workflow> {answer}\n")
            except RuntimeError as exc:
                print(f"\nError> {exc}\n")


def main() -> int:
    agent = BookingWorkflowAgent()
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:]).strip()
        try:
            print(agent.chat(query))
            return 0
        except (RuntimeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    agent.run_interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main())
