from __future__ import annotations

import sys
from dataclasses import dataclass, field

try:
    from .common import get_llm_config, invoke_with_history
except ImportError:
    from common import get_llm_config, invoke_with_history


def build_system_prompt() -> str:
    return (
        "Eres TravelBot LangChain, un asistente experto en viajes. "
        "Recomienda destinos, arma itinerarios y da consejos prácticos. "
        "Responde siempre en español, de forma clara y breve. "
        "Si falta información, pídela explícitamente."
    )


@dataclass
class TravelAgent:
    system_prompt: str = field(default_factory=build_system_prompt)
    history: list[dict[str, str]] = field(default_factory=list)

    def chat(self, user_message: str) -> str:
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        self.history.append({"role": "user", "content": user_message})
        response = invoke_with_history(self.system_prompt, self.history, temperature=0.3)
        self.history.append({"role": "assistant", "content": response})
        return response

    def reset(self) -> None:
        self.history = []

    def run_interactive(self) -> None:
        config = get_llm_config()
        print("=" * 60)
        print("TRAVELOPS LANGCHAIN — Ejercicio 01")
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
                print(f"\nTravelBot> {answer}\n")
            except RuntimeError as exc:
                print(f"\nError> {exc}\n")


def main() -> int:
    agent = TravelAgent()
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:]).strip()
        try:
            print(agent.chat(question))
            return 0
        except (RuntimeError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    agent.run_interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main())
