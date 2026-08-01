"""
Ejercicio 03: Sistema Multi-Agente de TravelOps
================================================

Enunciado
---------
Diseña un sistema de múltiples agentes especializados coordinados por un
orquestador central.  El sistema debe:

1. Tener tres agentes **especialistas**, cada uno con su propio prompt de
   sistema y área de conocimiento:
   - ``FlightAgent``    → especialista en vuelos y aerolíneas
   - ``HotelAgent``     → especialista en alojamiento y hospedaje
   - ``ItineraryAgent`` → especialista en planificar itinerarios día a día

2. Tener un agente **orquestador** (``OrchestratorAgent``) que:
   - Analiza el mensaje del usuario y decide a qué especialista(s) enviarlo.
   - Puede enrutar a un solo especialista o a varios en paralelo (simulado
     de forma secuencial para simplificar).
   - Combina las respuestas de los especialistas en una respuesta final
     coherente y unificada.

3. El orquestador usa el LLM para:
   a. Clasificar la consulta (``route_query``): determinar qué agentes necesita.
   b. Sintetizar las respuestas (``synthesize``): combinar las respuestas
      de los especialistas en un único texto para el usuario.

4. Cada especialista tiene su propio historial de conversación independiente.

Tareas implementadas
--------------------
- [x] ``AgentRole``                — enum de los roles disponibles
- [x] ``SpecialistAgent``          — agente base reutilizable para los especialistas
- [x] ``FlightAgent``              — agente especializado en vuelos
- [x] ``HotelAgent``               — agente especializado en hoteles
- [x] ``ItineraryAgent``           — agente especializado en itinerarios
- [x] ``OrchestratorAgent.route_query()``  — clasifica y enruta la consulta
- [x] ``OrchestratorAgent.chat()``         — ciclo completo de orquestación
- [x] ``OrchestratorAgent.reset()``        — reinicia todos los agentes
- [x] ``OrchestratorAgent.run_interactive()`` — modo terminal

Conceptos que aprenderás
-------------------------
- Arquitectura multi-agente con especialistas y orquestador
- Principio de responsabilidad única aplicado a agentes de IA
- Enrutamiento de consultas basado en el LLM (classifier pattern)
- Síntesis de respuestas de múltiples fuentes
- Reutilización de código mediante herencia y composición

Cómo ejecutar
-------------
    python travelops/exercise03_multi_agent.py
    python travelops/exercise03_multi_agent.py "Planifica un viaje de 5 días a Roma"

Variables de entorno (opcionales)
----------------------------------
    LLM_BASE_URL  — URL del servidor LLM  (default: http://localhost:8082/v1/messages)
    LLM_API_KEY   — clave de API           (default: freecc)
    LLM_MODEL     — modelo a usar          (default: claude-3-5-sonnet-20241022)
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ---------------------------------------------------------------------------
# Configuración del LLM  (idéntica a los ejercicios anteriores)
# ---------------------------------------------------------------------------

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
    temperature: float = 0.3,
) -> str:
    """Envía mensajes al LLM y retorna el texto de la respuesta (SSE o JSON)."""
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


# ---------------------------------------------------------------------------
# Roles de agentes
# ---------------------------------------------------------------------------

class AgentRole(str, Enum):
    """Roles disponibles en el sistema multi-agente.

    Cada valor es también una cadena de texto para facilitar la serialización.
    """

    FLIGHT = "flight"
    HOTEL = "hotel"
    ITINERARY = "itinerary"
    ORCHESTRATOR = "orchestrator"


# ---------------------------------------------------------------------------
# Agente especialista base
# ---------------------------------------------------------------------------

@dataclass
class SpecialistAgent:
    """Agente especializado en un área específica del dominio de viajes.

    Cada especialista tiene su propio prompt de sistema e historial
    independiente.  Se puede reutilizar para todos los especialistas
    cambiando únicamente el ``role`` y el ``system_prompt``.

    Attributes:
        role:          Rol del especialista (valor de ``AgentRole``).
        system_prompt: Descripción del área de especialización del agente.
        history:       Historial de mensajes de este especialista.

    Example::

        agent = SpecialistAgent(
            role=AgentRole.FLIGHT,
            system_prompt="Eres un experto en vuelos...",
        )
        response = agent.respond("¿Hay vuelos baratos a Roma en agosto?")
    """

    role: AgentRole
    system_prompt: str
    history: list[dict[str, str]] = field(default_factory=list)

    def respond(self, query: str) -> str:
        """Procesa una consulta y retorna la respuesta del especialista.

        La consulta y la respuesta se agregan al historial del especialista,
        permitiendo continuidad en conversaciones de múltiples turnos.

        Args:
            query: Pregunta o tarea enviada al especialista.

        Returns:
            Respuesta del especialista.

        Raises:
            ValueError: Si ``query`` está vacía.
            RuntimeError: Si el LLM devuelve un error.
        """
        query = query.strip()
        if not query:
            raise ValueError("La consulta al especialista no puede estar vacía.")

        self.history.append({"role": "user", "content": query})

        response = call_llm(
            messages=list(self.history),
            system_prompt=self.system_prompt,
        )

        self.history.append({"role": "assistant", "content": response})
        return response

    def reset(self) -> None:
        """Limpia el historial del especialista."""
        self.history = []


# ---------------------------------------------------------------------------
# Especialistas concretos
# ---------------------------------------------------------------------------

def create_flight_agent() -> SpecialistAgent:
    """Crea el agente especialista en vuelos.

    Returns:
        Instancia de ``SpecialistAgent`` configurada para vuelos.
    """
    return SpecialistAgent(
        role=AgentRole.FLIGHT,
        system_prompt=(
            "Eres FlightBot, un experto en vuelos, aerolíneas y transporte aéreo. "
            "Tu área de conocimiento cubre:\n"
            "- Búsqueda y comparación de vuelos (directos, con escala, low-cost).\n"
            "- Consejos para encontrar los mejores precios y épocas para comprar boletos.\n"
            "- Información sobre aerolíneas, clases de servicio y equipaje.\n"
            "- Conexiones aéreas, tiempo mínimo de tránsito y aeropuertos principales.\n"
            "- Documentación requerida para vuelos internacionales.\n\n"
            "Responde en español, de forma precisa y útil. "
            "Si no tienes datos exactos de precios o disponibilidad, ofrece rangos "
            "típicos y recomendaciones basadas en tu conocimiento general."
        ),
    )


def create_hotel_agent() -> SpecialistAgent:
    """Crea el agente especialista en hoteles y alojamiento.

    Returns:
        Instancia de ``SpecialistAgent`` configurada para hoteles.
    """
    return SpecialistAgent(
        role=AgentRole.HOTEL,
        system_prompt=(
            "Eres HotelBot, un experto en alojamiento y hospedaje para viajeros. "
            "Tu área de conocimiento cubre:\n"
            "- Tipos de alojamiento: hoteles, hostales, Airbnb, apart-hoteles, resorts.\n"
            "- Recomendaciones por presupuesto (económico, medio, lujo).\n"
            "- Mejores zonas y barrios donde hospedarse en cada ciudad.\n"
            "- Amenidades, servicios y características a tener en cuenta.\n"
            "- Políticas de cancelación y consejos para reservar.\n\n"
            "Responde en español, de forma amigable y práctica. "
            "Ofrece alternativas para diferentes presupuestos cuando sea posible."
        ),
    )


def create_itinerary_agent() -> SpecialistAgent:
    """Crea el agente especialista en itinerarios de viaje.

    Returns:
        Instancia de ``SpecialistAgent`` configurada para itinerarios.
    """
    return SpecialistAgent(
        role=AgentRole.ITINERARY,
        system_prompt=(
            "Eres ItineraryBot, un experto en planificación de itinerarios de viaje. "
            "Tu área de conocimiento cubre:\n"
            "- Diseño de itinerarios día a día adaptados al tiempo disponible.\n"
            "- Ordenamiento lógico de visitas para minimizar desplazamientos.\n"
            "- Actividades culturales, gastronómicas y de aventura.\n"
            "- Estimación de tiempos y recomendaciones de horarios.\n"
            "- Equilibrio entre lugares turísticos populares y rincones locales.\n\n"
            "Responde en español con itinerarios concretos, estructurados y detallados. "
            "Usa listas o días numerados para que sea fácil de seguir."
        ),
    )


# ---------------------------------------------------------------------------
# Clasificación de consultas
# ---------------------------------------------------------------------------

_ROUTING_SYSTEM_PROMPT = (
    "Eres un clasificador de consultas de viaje. "
    "Debes analizar la consulta del usuario y determinar qué agentes especialistas "
    "deben responderla.\n\n"
    "Agentes disponibles:\n"
    "  - flight:    preguntas sobre vuelos, aerolíneas, transporte aéreo\n"
    "  - hotel:     preguntas sobre alojamiento, hoteles, hospedaje\n"
    "  - itinerary: preguntas sobre planificación de actividades, qué hacer, rutas\n\n"
    "Responde ÚNICAMENTE con un JSON válido en este formato exacto:\n"
    '{"agents": ["agent1", "agent2"]}\n\n'
    "Puedes incluir uno, dos o los tres agentes según lo que requiera la consulta. "
    "No incluyas ningún texto fuera del JSON."
)


def route_query(query: str) -> list[AgentRole]:
    """Usa el LLM para clasificar una consulta y determinar qué especialistas necesita.

    Args:
        query: Consulta del usuario.

    Returns:
        Lista de ``AgentRole`` de los especialistas que deben responder.
        Si la clasificación falla, retorna los tres agentes (fallback seguro).
    """
    try:
        response = call_llm(
            messages=[{"role": "user", "content": query}],
            system_prompt=_ROUTING_SYSTEM_PROMPT,
            temperature=0.0,
        )

        start = response.find("{")
        end = response.rfind("}") + 1
        if start < 0 or end <= start:
            return list(AgentRole)[:3]  # fallback: todos los especialistas

        data = json.loads(response[start:end])
        agent_names: list[str] = data.get("agents", [])

        roles: list[AgentRole] = []
        for name in agent_names:
            try:
                roles.append(AgentRole(name))
            except ValueError:
                pass  # ignorar roles desconocidos

        return roles if roles else list(AgentRole)[:3]

    except (RuntimeError, json.JSONDecodeError, KeyError):
        return list(AgentRole)[:3]


# ---------------------------------------------------------------------------
# Agente orquestador
# ---------------------------------------------------------------------------

@dataclass
class OrchestratorAgent:
    """Agente orquestador que coordina a los especialistas de TravelOps.

    El orquestador actúa como punto de entrada único: clasifica la consulta
    del usuario, la delega a los especialistas pertinentes y sintetiza sus
    respuestas en una única respuesta cohesiva.

    Attributes:
        specialists: Diccionario de agentes especialistas indexados por rol.
        history:     Historial de conversación a nivel de orquestador
                     (pares user → síntesis).

    Example::

        agent = OrchestratorAgent()
        response = agent.chat("Planifica un viaje de 5 días a Roma con vuelos y hotel")
        print(response)
    """

    specialists: dict[AgentRole, SpecialistAgent] = field(
        default_factory=lambda: {
            AgentRole.FLIGHT: create_flight_agent(),
            AgentRole.HOTEL: create_hotel_agent(),
            AgentRole.ITINERARY: create_itinerary_agent(),
        }
    )
    history: list[dict[str, str]] = field(default_factory=list)

    def _synthesize(self, query: str, specialist_responses: dict[AgentRole, str]) -> str:
        """Combina las respuestas de los especialistas en una respuesta unificada.

        Args:
            query:                Consulta original del usuario.
            specialist_responses: Respuestas de cada especialista indexadas por rol.

        Returns:
            Respuesta final sintetizada para el usuario.
        """
        if not specialist_responses:
            return "No se pudo obtener respuesta de los especialistas."

        if len(specialist_responses) == 1:
            # Con un solo especialista, su respuesta es directamente la final
            return next(iter(specialist_responses.values()))

        # Construir contexto para la síntesis
        responses_text = "\n\n".join(
            f"[{role.value.upper()}]:\n{response}"
            for role, response in specialist_responses.items()
        )

        synthesis_prompt = (
            "Eres un asistente de viajes que combina información de múltiples expertos "
            "en una respuesta unificada, clara y completa para el usuario. "
            "Integra la información sin repetir datos. Mantén un tono amigable. "
            "Responde en español."
        )

        synthesis_messages = [
            {
                "role": "user",
                "content": (
                    f"El usuario preguntó: {query}\n\n"
                    f"Respuestas de los especialistas:\n\n{responses_text}\n\n"
                    "Por favor, sintetiza estas respuestas en una única respuesta "
                    "coherente y útil para el usuario."
                ),
            }
        ]

        return call_llm(
            messages=synthesis_messages,
            system_prompt=synthesis_prompt,
        )

    def chat(self, user_message: str) -> str:
        """Procesa un mensaje del usuario a través del sistema multi-agente.

        Flujo:
        1. Clasifica la consulta para determinar qué especialistas necesita.
        2. Envía la consulta a cada especialista seleccionado.
        3. Sintetiza las respuestas en una única respuesta final.
        4. Guarda la síntesis en el historial del orquestador.

        Args:
            user_message: Texto del usuario.

        Returns:
            Respuesta final sintetizada.

        Raises:
            ValueError: Si ``user_message`` está vacío.
            RuntimeError: Si el LLM devuelve un error irrecuperable.
        """
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        self.history.append({"role": "user", "content": user_message})

        # 1. Clasificar la consulta
        target_roles = route_query(user_message)

        # 2. Consultar a cada especialista seleccionado
        specialist_responses: dict[AgentRole, str] = {}
        for role in target_roles:
            specialist = self.specialists.get(role)
            if specialist is None:
                continue
            try:
                specialist_responses[role] = specialist.respond(user_message)
            except RuntimeError as exc:
                specialist_responses[role] = f"[Error del especialista {role.value}: {exc}]"

        # 3. Sintetizar y guardar
        final_response = self._synthesize(user_message, specialist_responses)
        self.history.append({"role": "assistant", "content": final_response})

        return final_response

    def reset(self) -> None:
        """Reinicia el historial del orquestador y de todos los especialistas."""
        self.history = []
        for specialist in self.specialists.values():
            specialist.reset()

    def run_interactive(self) -> None:
        """Inicia un bucle de conversación interactiva en la terminal."""
        config = get_llm_config()

        print("=" * 65)
        print("TRAVELOPS MULTI-AGENTE — Sistema de Viajes Especializado")
        print("=" * 65)
        print(f"Modelo : {config['model']}")
        print(f"Servidor: {config['base_url']}")
        print("Especialistas: vuelos, hoteles, itinerarios")
        print("Escribe 'salir' para terminar.\n")

        while True:
            try:
                user_input = input("Tú> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nHasta pronto. ¡Buen viaje!")
                return

            if not user_input:
                continue

            if user_input.lower() in {"salir", "exit", "quit", "q"}:
                print("¡Hasta pronto! Que tengas un excelente viaje. ✈️🏨🗺️")
                return

            try:
                answer = self.chat(user_input)
                print(f"\nTravelOps> {answer}\n")
            except RuntimeError as exc:
                print(f"\nError> {exc}\n")


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def main() -> int:
    """Función principal."""
    orchestrator = OrchestratorAgent()

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:]).strip()
        try:
            answer = orchestrator.chat(question)
            print(answer)
            return 0
        except (RuntimeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    orchestrator.run_interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main())
