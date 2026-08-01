from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum

try:
    from .common import get_llm_config, invoke_with_history
except ImportError:
    from common import get_llm_config, invoke_with_history


class AgentRole(str, Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    ITINERARY = "itinerary"


@dataclass
class SpecialistAgent:
    role: AgentRole
    system_prompt: str
    history: list[dict[str, str]] = field(default_factory=list)

    def respond(self, query: str) -> str:
        query = query.strip()
        if not query:
            raise ValueError("La consulta no puede estar vacía.")

        self.history.append({"role": "user", "content": query})
        answer = invoke_with_history(self.system_prompt, self.history, temperature=0.2)
        self.history.append({"role": "assistant", "content": answer})
        return answer

    def reset(self) -> None:
        self.history = []


def create_flight_agent() -> SpecialistAgent:
    return SpecialistAgent(
        role=AgentRole.FLIGHT,
        system_prompt=(
            "Eres especialista en vuelos. Recomienda rutas, escalas, ventanas de precio "
            "y consejos para ahorrar. Responde en español y con foco práctico."
        ),
    )


def create_hotel_agent() -> SpecialistAgent:
    return SpecialistAgent(
        role=AgentRole.HOTEL,
        system_prompt=(
            "Eres especialista en alojamiento. Sugiere zonas, tipos de hotel, "
            "rango de precios y criterios de selección. Responde en español."
        ),
    )


def create_itinerary_agent() -> SpecialistAgent:
    return SpecialistAgent(
        role=AgentRole.ITINERARY,
        system_prompt=(
            "Eres especialista en itinerarios. Construye planes día a día, "
            "equilibrando logística, tiempos y experiencia. Responde en español."
        ),
    )


def _fallback_route(query: str) -> list[AgentRole]:
    text = query.lower()
    roles: list[AgentRole] = []

    if any(k in text for k in ["vuelo", "vuelos", "aeropuerto", "aerolinea", "aerolínea"]):
        roles.append(AgentRole.FLIGHT)
    if any(k in text for k in ["hotel", "alojamiento", "hostal", "hospedaje"]):
        roles.append(AgentRole.HOTEL)
    if any(k in text for k in ["itinerario", "día", "dias", "actividades", "plan"]):
        roles.append(AgentRole.ITINERARY)

    if not roles:
        return [AgentRole.ITINERARY]
    return roles


def route_query(query: str) -> list[AgentRole]:
    router_prompt = (
        "Eres un router de consultas para un sistema multi-agente de viajes. "
        "Elige los especialistas necesarios entre: flight, hotel, itinerary. "
        "Responde SOLO JSON estricto con formato: {\"agents\": [\"flight\", ...]}"
    )

    try:
        raw = invoke_with_history(router_prompt, [{"role": "user", "content": query}], temperature=0.0)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if not match:
                return _fallback_route(query)
            data = json.loads(match.group(0))

        items = data.get("agents", []) if isinstance(data, dict) else []
        roles: list[AgentRole] = []
        for item in items:
            try:
                roles.append(AgentRole(str(item)))
            except ValueError:
                continue

        return roles or _fallback_route(query)

    except Exception:
        return _fallback_route(query)


@dataclass
class OrchestratorAgent:
    specialists: dict[AgentRole, SpecialistAgent] = field(
        default_factory=lambda: {
            AgentRole.FLIGHT: create_flight_agent(),
            AgentRole.HOTEL: create_hotel_agent(),
            AgentRole.ITINERARY: create_itinerary_agent(),
        }
    )
    history: list[dict[str, str]] = field(default_factory=list)

    def _synthesize(self, query: str, specialist_outputs: dict[AgentRole, str]) -> str:
        synthesis_prompt = (
            "Eres un coordinador senior de TravelOps. "
            "Integra las respuestas de especialistas en una sola recomendación clara, "
            "accionable y en español."
        )
        snippets = "\n\n".join(
            f"[{role.value}]\n{text}" for role, text in specialist_outputs.items()
        )
        user_payload = (
            f"Consulta original:\n{query}\n\n"
            f"Respuestas de especialistas:\n{snippets}\n\n"
            "Entrega una respuesta final consolidada."
        )
        return invoke_with_history(
            synthesis_prompt,
            [{"role": "user", "content": user_payload}],
            temperature=0.2,
        )

    def chat(self, user_message: str) -> str:
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        self.history.append({"role": "user", "content": user_message})

        roles = route_query(user_message)
        outputs: dict[AgentRole, str] = {}

        for role in roles:
            specialist = self.specialists.get(role)
            if not specialist:
                continue
            try:
                outputs[role] = specialist.respond(user_message)
            except Exception as exc:
                outputs[role] = f"No se pudo obtener respuesta del especialista {role.value}: {exc}"

        if not outputs:
            response = "No pude procesar tu solicitud en este momento. ¿Puedes reformularla?"
        elif len(outputs) == 1:
            response = next(iter(outputs.values()))
        else:
            response = self._synthesize(user_message, outputs)

        self.history.append({"role": "assistant", "content": response})
        return response

    def reset(self) -> None:
        self.history = []
        for specialist in self.specialists.values():
            specialist.reset()

    def run_interactive(self) -> None:
        config = get_llm_config()
        print("=" * 62)
        print("TRAVELOPS LANGCHAIN — Ejercicio 03")
        print("=" * 62)
        print(f"Modelo : {config['model']}")
        print(f"Servidor: {config['base_url']}")
        print("Escribe 'salir' para terminar.\n")

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
                print(f"\nTravelOps Orchestrator> {answer}\n")
            except RuntimeError as exc:
                print(f"\nError> {exc}\n")


def main() -> int:
    agent = OrchestratorAgent()
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
