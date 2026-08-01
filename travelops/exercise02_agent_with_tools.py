"""
Ejercicio 02: Agente con Herramientas (Tool Use / ReAct)
=========================================================

Enunciado
---------
Mejora el agente de viajes del Ejercicio 01 para que pueda **usar herramientas**.
El agente debe ser capaz de:

1. Recibir un mensaje del usuario y decidir si necesita llamar a una o más
   herramientas antes de responder (patrón ReAct: Reason → Act → Observe → Respond).

2. Disponer de las siguientes herramientas de viaje:
   - ``search_flights(origin, destination, date)``    → busca vuelos disponibles
   - ``search_hotels(city, check_in, check_out, budget)`` → busca hoteles disponibles
   - ``get_weather(city, month)``                     → consulta el clima de un destino
   - ``calculate_budget(items)``                      → calcula el presupuesto total del viaje

3. El LLM decide qué herramienta llamar usando un formato JSON estructurado dentro
   de su respuesta.  El agente detecta ese JSON, ejecuta la herramienta real,
   inyecta el resultado como un nuevo mensaje de rol ``tool`` en el historial
   y vuelve a llamar al LLM para que formule la respuesta final.

4. Si el LLM no necesita ninguna herramienta, responde directamente (igual que
   en el Ejercicio 01).

5. Limitar el ciclo a un máximo de ``max_tool_rounds`` iteraciones para evitar
   bucles infinitos.

Tareas implementadas
--------------------
- [x] Definición de herramientas con ``ToolDefinition``
- [x] ``search_flights()``       — herramienta: buscar vuelos
- [x] ``search_hotels()``        — herramienta: buscar hoteles
- [x] ``get_weather()``          — herramienta: consultar clima
- [x] ``calculate_budget()``     — herramienta: calcular presupuesto
- [x] ``TOOL_REGISTRY``          — diccionario de todas las herramientas disponibles
- [x] ``parse_tool_call()``      — extrae el JSON de llamada a herramienta de la respuesta del LLM
- [x] ``execute_tool()``         — ejecuta la herramienta con los argumentos indicados
- [x] ``TravelAgentWithTools.chat()`` — bucle ReAct completo
- [x] ``TravelAgentWithTools.run_interactive()`` — modo terminal

Conceptos que aprenderás
-------------------------
- Patrón ReAct (Reason → Act → Observe → Respond)
- Diseño de herramientas como funciones Python puras
- Prompt engineering para invocar herramientas en formato JSON
- Parsing de respuestas semiestructuradas del LLM
- Control de ciclos con límite de iteraciones (guardrail)

Cómo ejecutar
-------------
    python travelops/exercise02_agent_with_tools.py
    python travelops/exercise02_agent_with_tools.py "Busca vuelos de Lima a Madrid para el 15 de marzo"

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
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ---------------------------------------------------------------------------
# Configuración del LLM  (idéntica al ejercicio 01)
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
# Definición de herramientas
# ---------------------------------------------------------------------------

@dataclass
class ToolDefinition:
    """Describe una herramienta disponible para el agente.

    Attributes:
        name:        Nombre de la herramienta (identificador único).
        description: Descripción para el LLM de cuándo y cómo usar la herramienta.
        parameters:  Diccionario con nombre → descripción de cada parámetro.
        fn:          Función Python que implementa la herramienta.
    """

    name: str
    description: str
    parameters: dict[str, str]
    fn: Callable[..., str]


# ---------------------------------------------------------------------------
# Implementaciones de las herramientas
# ---------------------------------------------------------------------------

def search_flights(origin: str, destination: str, date: str) -> str:
    """Simula la búsqueda de vuelos disponibles.

    En un sistema real esta función llamaría a una API como Amadeus o Skyscanner.

    Args:
        origin:      Ciudad o código IATA de origen (p. ej. "Lima" o "LIM").
        destination: Ciudad o código IATA de destino (p. ej. "Madrid" o "MAD").
        date:        Fecha del vuelo en formato libre (p. ej. "15 de marzo de 2025").

    Returns:
        Cadena de texto con las opciones de vuelo encontradas.
    """
    return (
        f"Vuelos de {origin} a {destination} para {date}:\n"
        f"  ✈ Vuelo AA123 | Salida 08:00 | Llegada 20:30 | $450 USD\n"
        f"  ✈ Vuelo IB456 | Salida 14:15 | Llegada 05:45+1 | $380 USD\n"
        f"  ✈ Vuelo LA789 | Salida 22:00 | Llegada 14:20+1 | $320 USD"
    )


def search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    budget: str = "cualquier",
) -> str:
    """Simula la búsqueda de hoteles disponibles.

    Args:
        city:      Ciudad donde se busca alojamiento.
        check_in:  Fecha de entrada en formato libre.
        check_out: Fecha de salida en formato libre.
        budget:    Rango de precio deseado (p. ej. "bajo", "medio", "alto").

    Returns:
        Cadena de texto con los hoteles encontrados.
    """
    return (
        f"Hoteles en {city} del {check_in} al {check_out} (presupuesto: {budget}):\n"
        f"  🏨 Hotel Sol y Luna    | ⭐⭐⭐   | $60/noche  | Incluye desayuno\n"
        f"  🏨 Grand Plaza Hotel   | ⭐⭐⭐⭐  | $120/noche | Centro de la ciudad\n"
        f"  🏨 Boutique Viajero    | ⭐⭐⭐⭐⭐ | $200/noche | Vista al mar"
    )


def get_weather(city: str, month: str) -> str:
    """Consulta el clima típico de una ciudad en un mes determinado.

    Args:
        city:  Ciudad consultada (p. ej. "Tokio").
        month: Mes en español (p. ej. "enero", "julio").

    Returns:
        Cadena de texto con el resumen climático.
    """
    return (
        f"Clima en {city} durante {month}:\n"
        f"  🌡 Temperatura: 18–25 °C\n"
        f"  🌧 Precipitaciones: bajas (3–5 días de lluvia)\n"
        f"  ☀ Horas de sol: ~7 horas/día\n"
        f"  👕 Ropa recomendada: ropa ligera con una chaqueta para las noches"
    )


def calculate_budget(items: str) -> str:
    """Calcula el presupuesto total de un viaje.

    Args:
        items: Cadena JSON con una lista de objetos ``{"name": str, "cost": float}``.
               Ejemplo: ``'[{"name": "vuelo", "cost": 450}, {"name": "hotel", "cost": 360}]'``

    Returns:
        Cadena de texto con el desglose y el total del presupuesto.
    """
    try:
        expense_list: list[dict[str, Any]] = json.loads(items)
    except (json.JSONDecodeError, TypeError):
        return "Error: el parámetro 'items' debe ser un JSON válido con la forma [{\"name\": ..., \"cost\": ...}]."

    if not isinstance(expense_list, list):
        return "Error: 'items' debe ser una lista JSON."

    lines: list[str] = ["Desglose del presupuesto:"]
    total: float = 0.0

    for item in expense_list:
        name = item.get("name", "ítem desconocido")
        try:
            cost = float(item.get("cost", 0))
        except (ValueError, TypeError):
            cost = 0.0
        lines.append(f"  • {name}: ${cost:,.2f} USD")
        total += cost

    lines.append(f"\n  💰 TOTAL: ${total:,.2f} USD")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registro de herramientas
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "search_flights": ToolDefinition(
        name="search_flights",
        description="Busca vuelos disponibles entre dos ciudades en una fecha dada.",
        parameters={
            "origin": "Ciudad o código IATA de origen (p. ej. 'Lima').",
            "destination": "Ciudad o código IATA de destino (p. ej. 'Madrid').",
            "date": "Fecha del vuelo en formato libre (p. ej. '15 de marzo de 2025').",
        },
        fn=search_flights,
    ),
    "search_hotels": ToolDefinition(
        name="search_hotels",
        description="Busca hoteles disponibles en una ciudad para un período de estadía.",
        parameters={
            "city": "Ciudad donde buscar alojamiento.",
            "check_in": "Fecha de entrada en formato libre.",
            "check_out": "Fecha de salida en formato libre.",
            "budget": "Nivel de presupuesto: 'bajo', 'medio' o 'alto'. Opcional.",
        },
        fn=search_hotels,
    ),
    "get_weather": ToolDefinition(
        name="get_weather",
        description="Obtiene el clima típico de una ciudad en un mes específico.",
        parameters={
            "city": "Nombre de la ciudad.",
            "month": "Mes del año en español (p. ej. 'enero', 'julio').",
        },
        fn=get_weather,
    ),
    "calculate_budget": ToolDefinition(
        name="calculate_budget",
        description=(
            "Calcula el presupuesto total de un viaje sumando una lista de gastos. "
            "Los gastos deben pasarse como un JSON de objetos con 'name' y 'cost'."
        ),
        parameters={
            "items": (
                'Lista JSON de gastos. Formato: \'[{"name": "vuelo", "cost": 450}, ...]\''
            ),
        },
        fn=calculate_budget,
    ),
}


# ---------------------------------------------------------------------------
# Prompt del sistema con descripción de herramientas
# ---------------------------------------------------------------------------

def build_system_prompt_with_tools() -> str:
    """Construye el prompt del sistema incluyendo la descripción de las herramientas.

    Le indica al LLM cómo invocar herramientas usando un bloque JSON con el
    formato ``{"tool": "<nombre>", "args": {<argumentos>}}``.

    Returns:
        Prompt del sistema completo con instrucciones de uso de herramientas.
    """
    tool_descriptions: list[str] = []
    for tool in TOOL_REGISTRY.values():
        params = "\n".join(
            f"      - {name}: {desc}"
            for name, desc in tool.parameters.items()
        )
        tool_descriptions.append(
            f"  • {tool.name}: {tool.description}\n    Parámetros:\n{params}"
        )

    tools_text = "\n".join(tool_descriptions)

    return (
        "Eres TravelBot, un asistente experto en viajes y turismo.\n\n"
        "Tienes acceso a las siguientes herramientas:\n"
        f"{tools_text}\n\n"
        "Cuándo usar herramientas:\n"
        "  - Si necesitas información concreta (vuelos, hoteles, clima, presupuesto),\n"
        "    DEBES llamar a la herramienta correspondiente ANTES de responder.\n"
        "  - Para preguntas generales (consejos, recomendaciones de destino, etc.)\n"
        "    responde directamente sin usar herramientas.\n\n"
        "Cómo llamar a una herramienta:\n"
        "  Incluye EXACTAMENTE este bloque JSON en tu respuesta y nada más:\n"
        '  {"tool": "<nombre_herramienta>", "args": {"param1": "valor1", ...}}\n\n'
        "  Una vez que obtengas el resultado de la herramienta, úsalo para formular\n"
        "  una respuesta completa y útil para el usuario.\n\n"
        "Responde siempre en español, de forma amigable y concisa."
    )


# ---------------------------------------------------------------------------
# Parsing y ejecución de herramientas
# ---------------------------------------------------------------------------

def parse_tool_call(llm_response: str) -> dict[str, Any] | None:
    """Extrae la llamada a herramienta del texto de respuesta del LLM.

    Busca el primer bloque JSON válido con las claves ``"tool"`` y ``"args"``.

    Args:
        llm_response: Texto completo devuelto por el LLM.

    Returns:
        Diccionario con ``"tool"`` (str) y ``"args"`` (dict) si se encontró
        una llamada válida, o ``None`` si la respuesta no contiene herramienta.
    """
    # Buscar primer '{' y último '}' en la respuesta
    start = llm_response.find("{")
    end = llm_response.rfind("}") + 1

    if start < 0 or end <= start:
        return None

    try:
        data = json.loads(llm_response[start:end])
    except json.JSONDecodeError:
        return None

    if "tool" in data and "args" in data:
        return data

    return None


def execute_tool(tool_name: str, args: dict[str, Any]) -> str:
    """Ejecuta una herramienta del registro con los argumentos proporcionados.

    Args:
        tool_name: Nombre de la herramienta a ejecutar.
        args:      Argumentos de la herramienta como diccionario.

    Returns:
        Resultado de la herramienta como cadena de texto.

    Raises:
        KeyError: Si ``tool_name`` no existe en ``TOOL_REGISTRY``.
        TypeError: Si los argumentos no coinciden con la firma de la función.
    """
    if tool_name not in TOOL_REGISTRY:
        raise KeyError(
            f"Herramienta '{tool_name}' no encontrada. "
            f"Disponibles: {list(TOOL_REGISTRY.keys())}"
        )

    tool = TOOL_REGISTRY[tool_name]
    return tool.fn(**args)


# ---------------------------------------------------------------------------
# Clase TravelAgentWithTools
# ---------------------------------------------------------------------------

@dataclass
class TravelAgentWithTools:
    """Agente de viajes con soporte para herramientas (patrón ReAct).

    En cada turno el agente puede invocar una herramienta, recibir su resultado
    y luego formular la respuesta final, o responder directamente si no necesita
    herramientas.

    Attributes:
        system_prompt:   Prompt del sistema con la descripción de herramientas.
        history:         Historial de la conversación (mensajes user/assistant/tool).
        max_tool_rounds: Número máximo de invocaciones de herramientas por turno.

    Example::

        agent = TravelAgentWithTools()
        response = agent.chat("Busca vuelos de Bogotá a París para el 10 de junio")
        print(response)
    """

    system_prompt: str = field(default_factory=build_system_prompt_with_tools)
    history: list[dict[str, str]] = field(default_factory=list)
    max_tool_rounds: int = 5

    def chat(self, user_message: str) -> str:
        """Procesa un mensaje usando el ciclo ReAct: razonar → actuar → observar.

        Flujo:
        1. Agrega el mensaje del usuario al historial.
        2. Llama al LLM.
        3. Si la respuesta contiene una llamada a herramienta → ejecuta la
           herramienta, agrega el resultado al historial y vuelve al paso 2.
        4. Si la respuesta es texto normal → la guarda en el historial y la retorna.
        5. Si se supera ``max_tool_rounds`` → retorna la última respuesta del LLM.

        Args:
            user_message: Texto escrito por el usuario.

        Returns:
            Respuesta final del agente.

        Raises:
            ValueError: Si ``user_message`` está vacío.
            RuntimeError: Si el LLM devuelve un error.
        """
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        self.history.append({"role": "user", "content": user_message})

        for _ in range(self.max_tool_rounds):
            llm_response = call_llm(
                messages=list(self.history),
                system_prompt=self.system_prompt,
            )

            tool_call = parse_tool_call(llm_response)

            if tool_call is None:
                # Respuesta final: no hay herramienta que ejecutar
                self.history.append({"role": "assistant", "content": llm_response})
                return llm_response

            # Registrar la decisión del LLM de llamar a la herramienta
            self.history.append({"role": "assistant", "content": llm_response})

            # Ejecutar la herramienta
            tool_name = tool_call["tool"]
            tool_args = tool_call.get("args", {})

            try:
                tool_result = execute_tool(tool_name, tool_args)
            except (KeyError, TypeError) as exc:
                tool_result = f"Error al ejecutar '{tool_name}': {exc}"

            # Inyectar resultado como mensaje de herramienta en el historial
            self.history.append({
                "role": "user",
                "content": f"[Resultado de herramienta '{tool_name}']:\n{tool_result}",
            })

        # Guardrail: máximo de rondas alcanzado, pedir respuesta final
        final_response = call_llm(
            messages=list(self.history),
            system_prompt=self.system_prompt,
        )
        self.history.append({"role": "assistant", "content": final_response})
        return final_response

    def reset(self) -> None:
        """Limpia el historial de conversación conservando el prompt del sistema."""
        self.history = []

    def run_interactive(self) -> None:
        """Inicia un bucle de conversación interactiva en la terminal."""
        config = get_llm_config()

        print("=" * 60)
        print("TRAVELBOT CON HERRAMIENTAS — Asistente de Viajes")
        print("=" * 60)
        print(f"Modelo : {config['model']}")
        print(f"Servidor: {config['base_url']}")
        print("Herramientas disponibles:", ", ".join(TOOL_REGISTRY.keys()))
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
                print("¡Hasta pronto! Que tengas un excelente viaje. ✈️")
                return

            try:
                answer = self.chat(user_input)
                print(f"\nTravelBot> {answer}\n")
            except RuntimeError as exc:
                print(f"\nError> {exc}\n")


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def main() -> int:
    """Función principal."""
    agent = TravelAgentWithTools()

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
