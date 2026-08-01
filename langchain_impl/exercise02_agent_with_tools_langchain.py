from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from typing import Any

from langchain_core.tools import StructuredTool

try:
    from .common import get_llm_config, invoke_with_history
except ImportError:
    from common import get_llm_config, invoke_with_history


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


@dataclass
class TravelAgentWithTools:
    system_prompt: str = field(default_factory=build_system_prompt_with_tools)
    history: list[dict[str, str]] = field(default_factory=list)
    max_tool_rounds: int = 3

    def chat(self, user_message: str) -> str:
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        self.history.append({"role": "user", "content": user_message})

        for _ in range(self.max_tool_rounds):
            llm_text = invoke_with_history(self.system_prompt, self.history, temperature=0.2)
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
        final_response = invoke_with_history(self.system_prompt, self.history, temperature=0.2)
        self.history.append({"role": "assistant", "content": final_response})
        return final_response

    def reset(self) -> None:
        self.history = []

    def run_interactive(self) -> None:
        config = get_llm_config()
        print("=" * 60)
        print("TRAVELOPS LANGCHAIN — Ejercicio 02")
        print("=" * 60)
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
