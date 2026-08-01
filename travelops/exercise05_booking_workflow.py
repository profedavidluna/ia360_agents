"""
Ejercicio 05: Workflow de Reserva de TravelOps
==============================================

Enunciado
---------
Construye un agente de workflow para gestionar solicitudes de viaje que cumpla
con los siguientes requisitos:

1. Mantenga un estado estructurado con los datos clave de una solicitud:
   origen, destino, fechas, cantidad de viajeros y presupuesto.
2. Extraiga información parcial desde mensajes en lenguaje natural y la acumule
   a lo largo de varios turnos.
3. Guíe al usuario pidiendo los datos faltantes hasta completar la solicitud.
4. Cuando la solicitud esté completa, pida confirmación y genere un resumen
   final del itinerario.
5. Permita reiniciar el flujo en cualquier momento.

Tareas implementadas
--------------------
- [x] ``TravelRequest`` — modelo de datos de la solicitud
- [x] ``extract_trip_details()`` — extracción ligera de datos desde texto
- [x] ``build_missing_fields_message()`` — guía conversacional del workflow
- [x] ``BookingWorkflowAgent.chat()`` — ciclo completo de recopilación y confirmación
- [x] ``BookingWorkflowAgent.reset()`` — reinicia el estado
- [x] ``BookingWorkflowAgent.run_interactive()`` — modo terminal

Conceptos que aprenderás
------------------------
- Agentes con estado explícito y validación de datos
- Workflows conversacionales guiados
- Extracción incremental de información
- Confirmación final antes de ejecutar una acción

Cómo ejecutar
-------------
    python travelops/exercise05_booking_workflow.py
    python travelops/exercise05_booking_workflow.py "Quiero viajar de Lima a Madrid del 2026-09-10 al 2026-09-18 para 2 personas con presupuesto 2400"

Variables de entorno (opcionales)
---------------------------------
    LLM_BASE_URL  — URL del servidor LLM  (default: http://localhost:8082/v1/messages)
    LLM_API_KEY   — clave de API           (default: freecc)
    LLM_MODEL     — modelo a usar          (default: claude-3-5-sonnet-20241022)
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get_llm_config() -> dict[str, str]:
    """Retorna la configuración del LLM leyendo variables de entorno."""
    return {
        "base_url": os.getenv(
            "LLM_BASE_URL",
            "http://localhost:8082/v1/messages",
        ),
        "api_key": os.getenv("LLM_API_KEY", "freecc"),
        "model": os.getenv(
            "LLM_MODEL",
            "claude-3-5-sonnet-20241022",
        ),
    }


def call_llm(
    messages: list[dict[str, str]],
    system_prompt: str = "",
    temperature: float = 0.2,
) -> str:
    """Envía mensajes al LLM y retorna el texto de la respuesta."""
    config = get_llm_config()

    body: dict[str, Any] = {
        "model": config["model"],
        "max_tokens": 2048,
        "messages": messages,
        "temperature": temperature,
    }
    if system_prompt:
        body["system"] = system_prompt

    headers = {
        "Content-Type": "application/json",
        "x-api-key": config["api_key"],
    }

    request = Request(
        url=config["base_url"],
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    fragments: list[str] = []

    try:
        with urlopen(request, timeout=120) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()

                if not line or line.startswith("event:"):
                    continue

                if not line.startswith("data:"):
                    continue

                data_text = line[5:].strip()

                if not data_text or data_text == "[DONE]":
                    continue

                try:
                    event_data: dict[str, Any] = json.loads(data_text)
                except json.JSONDecodeError:
                    continue

                event_type = event_data.get("type")

                if event_type == "content_block_delta":
                    delta = event_data.get("delta", {})
                    if isinstance(delta, dict):
                        text = delta.get("text", "")
                        if text:
                            fragments.append(str(text))

                elif event_type == "error":
                    error = event_data.get("error", {})
                    message = (
                        error.get("message", "Error desconocido del LLM.")
                        if isinstance(error, dict)
                        else str(error)
                    )
                    raise RuntimeError(message)

                elif event_type == "message_stop":
                    break

    except HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Error HTTP {exc.code}: {body_text}") from exc

    except URLError as exc:
        raise RuntimeError(
            f"No se pudo conectar con {config['base_url']}: {exc.reason}"
        ) from exc

    answer = "".join(fragments).strip()

    if not answer:
        raise RuntimeError("El LLM finalizó la respuesta sin devolver texto.")

    return answer


class WorkflowStatus(str, Enum):
    COLLECTING = "collecting"
    READY_TO_CONFIRM = "ready_to_confirm"
    CONFIRMED = "confirmed"


@dataclass
class TravelRequest:
    """Representa una solicitud de viaje estructurada."""

    origin: str | None = None
    destination: str | None = None
    departure_date: str | None = None
    return_date: str | None = None
    travelers: int | None = None
    budget_usd: int | None = None
    notes: str | None = None

    def update(self, data: dict[str, Any]) -> None:
        """Actualiza solo los campos presentes en ``data``."""
        for field_name, value in data.items():
            if value is None:
                continue
            setattr(self, field_name, value)

    def missing_fields(self) -> list[str]:
        """Retorna la lista de campos requeridos faltantes."""
        required_fields = [
            "origin",
            "destination",
            "departure_date",
            "return_date",
            "travelers",
            "budget_usd",
        ]
        return [
            field_name
            for field_name in required_fields
            if getattr(self, field_name) in (None, "")
        ]

    def is_complete(self) -> bool:
        """Indica si la solicitud ya tiene todos los campos requeridos."""
        return not self.missing_fields()

    def to_summary(self) -> str:
        """Genera un resumen legible de la solicitud."""
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


def extract_trip_details(message: str) -> dict[str, Any]:
    """Extrae datos estructurados desde un mensaje en lenguaje natural."""
    details: dict[str, Any] = {}
    text = " ".join(message.strip().split())

    route_match = re.search(
        r"\bde\s+([A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?)\s+a\s+([A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?)(?=\s+(?:del|para|con|y|$))",
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

    departure_match = re.search(
        r"\b(?:salida|ida)\s+(?:el\s+)?(\d{4}-\d{2}-\d{2})\b",
        text,
        flags=re.IGNORECASE,
    )
    if departure_match:
        details["departure_date"] = departure_match.group(1)

    return_match = re.search(
        r"\b(?:regreso|vuelta)\s+(?:el\s+)?(\d{4}-\d{2}-\d{2})\b",
        text,
        flags=re.IGNORECASE,
    )
    if return_match:
        details["return_date"] = return_match.group(1)

    travelers_match = re.search(
        r"\b(\d+)\s+(?:persona|personas|viajero|viajeros|pasajero|pasajeros)\b",
        text,
        flags=re.IGNORECASE,
    )
    if travelers_match:
        details["travelers"] = int(travelers_match.group(1))

    budget_match = re.search(
        r"\b(?:presupuesto|budget)(?:\s+de)?\s+\$?([\d.,]+)\b",
        text,
        flags=re.IGNORECASE,
    )
    if budget_match:
        numeric_budget = budget_match.group(1).replace(".", "").replace(",", "")
        details["budget_usd"] = int(numeric_budget)

    note_match = re.search(
        r"\b(?:preferencias|notas|detalle adicional|detalle)\s*:\s*(.+)$",
        text,
        flags=re.IGNORECASE,
    )
    if note_match:
        details["notes"] = note_match.group(1).strip()

    return details


def build_booking_system_prompt() -> str:
    """Construye el prompt del sistema del agente de workflow."""
    return (
        "Eres TravelOps BookingBot, un coordinador de reservas. Recibirás una "
        "solicitud de viaje ya validada y debes devolver un resumen final breve, "
        "ordenado y profesional en español. Incluye recomendaciones prácticas y "
        "aclara que los precios son estimados si no hay inventario en tiempo real."
    )


def build_missing_fields_message(request: TravelRequest) -> str:
    """Genera una respuesta pidiendo los datos faltantes."""
    field_labels = {
        "origin": "ciudad de origen",
        "destination": "destino",
        "departure_date": "fecha de salida (YYYY-MM-DD)",
        "return_date": "fecha de regreso (YYYY-MM-DD)",
        "travelers": "cantidad de viajeros",
        "budget_usd": "presupuesto estimado en USD",
    }
    missing = [field_labels[name] for name in request.missing_fields()]
    missing_text = ", ".join(missing)
    return (
        "Perfecto, ya registré parte de tu solicitud. "
        f"Aún necesito: {missing_text}."
    )


def build_ready_to_confirm_message(request: TravelRequest) -> str:
    """Genera el mensaje cuando la solicitud está lista para confirmarse."""
    return (
        "Ya tengo todos los datos de tu solicitud:\n\n"
        f"{request.to_summary()}\n\n"
        "Si todo está correcto, responde 'confirmar' para generar el resumen final. "
        "Si quieres cambiar algo, solo envíame el dato actualizado."
    )


def build_fallback_confirmation(request: TravelRequest) -> str:
    """Genera una confirmación determinista si el LLM falla."""
    return (
        "Tu solicitud quedó confirmada.\n\n"
        f"{request.to_summary()}\n\n"
        "Siguiente paso sugerido: validar disponibilidad de vuelos y hotel dentro del "
        "presupuesto antes de emitir la reserva."
    )


@dataclass
class BookingWorkflowAgent:
    """Agente con estado para recopilar y confirmar solicitudes de viaje."""

    system_prompt: str = field(default_factory=build_booking_system_prompt)
    request: TravelRequest = field(default_factory=TravelRequest)
    history: list[dict[str, str]] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.COLLECTING

    def _looks_like_confirmation(self, message: str) -> bool:
        normalized = message.strip().lower()
        return normalized in {"confirmar", "confirmo", "sí", "si", "ok", "listo"}

    def _looks_like_reset(self, message: str) -> bool:
        normalized = message.strip().lower()
        return normalized in {"reset", "reiniciar", "nuevo", "empezar de nuevo", "clear"}

    def _confirm_request(self) -> str:
        confirmation_message = {
            "role": "user",
            "content": (
                "Genera un resumen final de reserva para esta solicitud:\n\n"
                f"{self.request.to_summary()}"
            ),
        }

        try:
            response = call_llm(
                messages=[confirmation_message],
                system_prompt=self.system_prompt,
            )
        except RuntimeError:
            response = build_fallback_confirmation(self.request)

        self.status = WorkflowStatus.CONFIRMED
        return response

    def chat(self, user_message: str) -> str:
        """Procesa un turno del workflow conversacional."""
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
        """Reinicia el estado del workflow."""
        self.request = TravelRequest()
        self.status = WorkflowStatus.COLLECTING
        self.history = []

    def run_interactive(self) -> None:
        """Inicia un bucle de conversación interactiva en la terminal."""
        config = get_llm_config()

        print("=" * 66)
        print("TRAVELOPS WORKFLOW — Coordinador de Solicitudes de Viaje")
        print("=" * 66)
        print(f"Modelo : {config['model']}")
        print(f"Servidor: {config['base_url']}")
        print("Escribe 'salir' para terminar o 'reiniciar' para comenzar otra solicitud.\n")

        while True:
            try:
                user_input = input("Tú> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nHasta pronto. ¡Buen viaje!")
                return

            if not user_input:
                continue

            if user_input.lower() in {"salir", "exit", "quit", "q"}:
                print("¡Hasta pronto! Que tengas un excelente viaje. 🧳")
                return

            try:
                answer = self.chat(user_input)
                print(f"\nTravelOps Workflow> {answer}\n")
            except RuntimeError as exc:
                print(f"\nError> {exc}\n")


def main() -> int:
    """Función principal."""
    agent = BookingWorkflowAgent()

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:]).strip()
        try:
            answer = agent.chat(question)
            print(answer)
            return 0
        except (RuntimeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    agent.run_interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main())
