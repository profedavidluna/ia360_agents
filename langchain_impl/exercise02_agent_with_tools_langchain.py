from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from typing import Any

from langchain_core.tools import StructuredTool

try:
    from .common import get_langchain_model, get_llm_config, invoke_with_history, dict_history_to_messages
except ImportError:
    from common import get_langchain_model, get_llm_config, invoke_with_history, dict_history_to_messages

# ---------------------------------------------------------------------------
# Importaciones opcionales de langchain.agents
# Se usan cuando el paquete langchain está instalado (langchain>=0.3).
# Si no están disponibles el agente cae al ciclo manual original.
# ---------------------------------------------------------------------------

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    _LANGCHAIN_AGENTS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _LANGCHAIN_AGENTS_AVAILABLE = False


def search_flights(origin: str, destination: str, date: str) -> str:
    return (
        f"Vuelos simulados de {origin} a {destination} para {date}: "
        "✈ Opción A $320 (1 escala), ✈ Opción B $410 (directo), ✈ Opción C $290 (2 escalas)."
    )


def search_hotels(city: str, check_in: str, check_out: str, budget: str = "medio") -> str:
    return (
        f"Hoteles simulados en {city} ({check_in} a {check_out}, presupuesto {budget}): "
        "🏨 Central Inn $85/noche, 🏨 City Stay $110/noche, 🏨 Premium View $160/noche."
    )


def get_weather(city: str, month: str) -> str:
    return (
        f"Clima estimado en {city} durante {month}: "
        "temperatura 18-25°C, probabilidad de lluvia moderada, recomendable llevar capas ligeras."
    )


def calculate_budget(items: str) -> str:
    try:
        parsed = json.loads(items)
        if not isinstance(parsed, list):
            return "Error: items debe ser un arreglo JSON."

        total = 0.0
        details: list[str] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "item"))
            cost = float(item.get("cost", 0))
            total += cost
            details.append(f"- {name}: ${cost:.2f}")

        lines = ["Presupuesto calculado:", *details, f"Total estimado: ${total:.2f}"]
        return "\n".join(lines)
    except Exception as exc:
        return f"Error al calcular presupuesto: {exc}"


TOOLS: dict[str, StructuredTool] = {
    "search_flights": StructuredTool.from_function(search_flights),
    "search_hotels": StructuredTool.from_function(search_hotels),
    "get_weather": StructuredTool.from_function(get_weather),
    "calculate_budget": StructuredTool.from_function(calculate_budget),
}



def build_system_prompt_with_tools() -> str:
    return (
        "Eres TravelOps Tools Agent con LangChain. "
        "Responde en español y usa las herramientas disponibles cuando sea necesario. "
        "Cuando tengas toda la información necesaria, responde directamente al usuario "
        "de forma clara y útil."
    )


# ---------------------------------------------------------------------------
# Prompt para el AgentExecutor de LangChain
# (requiere {input}, {chat_history} y {agent_scratchpad})
# ---------------------------------------------------------------------------

def build_agent_prompt():
    """Construye el ChatPromptTemplate requerido por create_tool_calling_agent."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", build_system_prompt_with_tools()),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )


# ---------------------------------------------------------------------------
# Funciones auxiliares para el fallback (ciclo manual)
# Se conservan para compatibilidad cuando langchain.agents no está disponible.
# ---------------------------------------------------------------------------

def build_system_prompt_manual_fallback() -> str:
    return (
        "Eres TravelOps Tools Agent con LangChain. "
        "Responde en español y usa herramientas cuando sea necesario. "
        "Si necesitas una herramienta, responde SOLO con JSON estricto: "
        '{"tool": "nombre", "args": {"param": "valor"}}. '
        "Herramientas disponibles:\n"
        "- search_flights(origin, destination, date)\n"
        "- search_hotels(city, check_in, check_out, budget='medio')\n"
        "- get_weather(city, month)\n"
        "- calculate_budget(items: json string)\n"
        "Si ya tienes suficiente información, responde normalmente sin JSON."
    )


def parse_tool_call(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None

    try:
        data = json.loads(text)
        if isinstance(data, dict) and "tool" in data:
            return {"tool": str(data["tool"]), "args": data.get("args", {}) or {}}
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict) or "tool" not in data:
        return None

    return {"tool": str(data["tool"]), "args": data.get("args", {}) or {}}


def execute_tool(tool_name: str, args: dict[str, Any]) -> str:
    if tool_name not in TOOLS:
        raise KeyError(f"Herramienta '{tool_name}' no encontrada")
    return str(TOOLS[tool_name].invoke(args))


# ---------------------------------------------------------------------------
# Clase TravelAgentWithTools
# ---------------------------------------------------------------------------

@dataclass
class TravelAgentWithTools:
    """Agente de viajes con herramientas usando LangChain.

    Cuando el paquete ``langchain`` está instalado (>=0.3) el agente usa
    ``create_tool_calling_agent`` + ``AgentExecutor``, que es la forma
    oficial de crear agentes con uso de herramientas en LangChain.

    Cuando ``langchain.agents`` no está disponible se usa un ciclo manual
    de parseo JSON como fallback, conservando la misma interfaz pública.

    Attributes:
        system_prompt:    Prompt del sistema.
        history:          Historial de conversación (role/content).
        max_tool_rounds:  Máximo de iteraciones de herramientas.
    """

    system_prompt: str = field(default_factory=build_system_prompt_with_tools)
    history: list[dict[str, str]] = field(default_factory=list)
    max_tool_rounds: int = 3
    _executor: Any = field(default=None, init=False, repr=False)

    def _get_executor(self) -> Any:
        """Construye o retorna el AgentExecutor cacheado."""
        if self._executor is not None:
            return self._executor

        prompt = build_agent_prompt()
        llm = get_langchain_model(temperature=0.2)
        tools = list(TOOLS.values())
        agent = create_tool_calling_agent(llm, tools, prompt)
        self._executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            max_iterations=self.max_tool_rounds,
        )
        return self._executor

    def _chat_with_agent_executor(self, user_message: str) -> str:
        """Ciclo de agente usando create_tool_calling_agent + AgentExecutor."""
        executor = self._get_executor()

        # Historial previo convertido a mensajes LangChain
        chat_history = dict_history_to_messages(self.history)

        result = executor.invoke(
            {"input": user_message, "chat_history": chat_history}
        )

        response = str(result.get("output", "")).strip()
        if not response:
            raise RuntimeError("AgentExecutor devolvió respuesta vacía.")

        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": response})
        return response

    def _chat_with_manual_loop(self, user_message: str) -> str:
        """Ciclo manual de herramientas (fallback cuando langchain.agents no está disponible)."""
        fallback_prompt = build_system_prompt_manual_fallback()
        self.history.append({"role": "user", "content": user_message})

        for _ in range(self.max_tool_rounds):
            llm_text = invoke_with_history(fallback_prompt, self.history, temperature=0.2)
            tool_call = parse_tool_call(llm_text)

            if not tool_call:
                self.history.append({"role": "assistant", "content": llm_text})
                return llm_text

            self.history.append({"role": "assistant", "content": llm_text})

            tool_name = tool_call["tool"]
            args = tool_call.get("args", {})
            try:
                tool_result = execute_tool(tool_name, args if isinstance(args, dict) else {})
            except Exception as exc:
                tool_result = f"Error ejecutando herramienta {tool_name}: {exc}"

            self.history.append(
                {
                    "role": "user",
                    "content": f"Resultado de herramienta ({tool_name}):\n{tool_result}",
                }
            )

        guardrail_message = (
            "Ya agotaste el máximo de uso de herramientas. "
            "Responde con la mejor recomendación posible usando los resultados disponibles."
        )
        self.history.append({"role": "user", "content": guardrail_message})
        final_response = invoke_with_history(fallback_prompt, self.history, temperature=0.2)
        self.history.append({"role": "assistant", "content": final_response})
        return final_response

    def chat(self, user_message: str) -> str:
        """Procesa un mensaje usando el agente LangChain o el fallback manual.

        Si ``langchain.agents`` está disponible, invoca al agente con
        ``create_tool_calling_agent`` + ``AgentExecutor``; de lo contrario
        usa el ciclo manual de parseo JSON.

        Args:
            user_message: Texto del usuario.

        Returns:
            Respuesta del agente de viajes.

        Raises:
            ValueError: Si ``user_message`` es una cadena vacía.
            RuntimeError: Si el LLM no está disponible.
        """
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        if _LANGCHAIN_AGENTS_AVAILABLE:
            return self._chat_with_agent_executor(user_message)

        return self._chat_with_manual_loop(user_message)

    def reset(self) -> None:
        self.history = []
        self._executor = None

    def run_interactive(self) -> None:
        config = get_llm_config()
        mode = "AgentExecutor (create_tool_calling_agent)" if _LANGCHAIN_AGENTS_AVAILABLE else "ciclo manual (fallback)"
        print("=" * 60)
        print("TRAVELOPS LANGCHAIN — Ejercicio 02")
        print("=" * 60)
        print(f"Modelo : {config['model']}")
        print(f"Servidor: {config['base_url']}")
        print(f"Modo   : {mode}")
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
                print(f"\nTravelOps Tools> {answer}\n")
            except RuntimeError as exc:
                print(f"\nError> {exc}\n")


def main() -> int:
    agent = TravelAgentWithTools()
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
