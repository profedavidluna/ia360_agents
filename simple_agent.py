"""Agente básico conectado a Free Claude Code."""

from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get_llm_config() -> dict[str, str]:
    """
    Conserva exactamente la configuración del agente original.
    """

    return  {
        "base_url": os.getenv(
            "LLM_BASE_URL",
            "http://localhost:8082/v1/messages"
        ),
        "api_key": os.getenv(
            "LLM_API_KEY",
            "freecc"
        ),
        "model": os.getenv(
            "LLM_MODEL",
            "claude-3-5-sonnet-20241022"
        ),
        "api_type": os.getenv(
            "LLM_API_TYPE",
            "anthropic"
        ),
    }


def call_llm(
    question: str,
    system_prompt: str = (
        "Eres un asistente útil. "
        "Responde siempre en español de forma clara."
    ),
    temperature: float = 0.2,
) -> str:
    """
    Envía una pregunta a Free Claude Code y consume su respuesta SSE.
    """

    config = get_llm_config()

    body = {
        "model": config["model"],
        "max_tokens": 2048,
        "messages": [
            {
                "role": "user",
                "content": question,
            }
        ],
        "temperature": temperature,
        "system": system_prompt,
    }

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
                line = raw_line.decode(
                    "utf-8",
                    errors="replace",
                ).strip()

                if not line:
                    continue

                # Las líneas "event:" solamente identifican el evento.
                if line.startswith("event:"):
                    continue

                # El contenido JSON viene en las líneas "data:".
                if not line.startswith("data:"):
                    continue

                data_text = line[5:].strip()

                if not data_text or data_text == "[DONE]":
                    continue

                try:
                    event_data: dict[str, Any] = json.loads(
                        data_text
                    )
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

                    if isinstance(error, dict):
                        message = error.get(
                            "message",
                            "Error desconocido del LLM.",
                        )
                    else:
                        message = str(error)

                    raise RuntimeError(message)

                elif event_type == "message_stop":
                    break

    except HTTPError as error:
        response_body = error.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Error HTTP {error.code}: {response_body}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"No fue posible conectarse con "
            f"{config['base_url']}: {error.reason}"
        ) from error

    answer = "".join(fragments).strip()

    if not answer:
        raise RuntimeError(
            "El LLM finalizó la respuesta sin devolver texto."
        )

    return answer


def run_chat() -> None:
    config = get_llm_config()

    print("=" * 60)
    print("AGENTE CON FREE CLAUDE CODE")
    print("=" * 60)
    print(f"Servidor: {config['base_url']}")
    print(f"Modelo: {config['model']}")
    print("Escribe 'salir' para terminar.")
    print("=" * 60)

    while True:
        try:
            question = input("\nTú> ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\nAgente finalizado.")
            return

        if not question:
            continue

        if question.lower() in {
            "salir",
            "exit",
            "quit",
            "q",
        }:
            print("Agente finalizado.")
            return

        try:
            answer = call_llm(question)
            print(f"\nAgente> {answer}")

        except RuntimeError as error:
            print(f"\nError> {error}")


def main() -> int:
    # Permite hacer una sola pregunta desde la terminal:
    #
    # python agente_llm.py "¿Qué es un agente de IA?"

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:]).strip()

        try:
            answer = call_llm(question)
            print(answer)
            return 0

        except RuntimeError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1

    run_chat()
    return 0


if __name__ == "__main__":
    sys.exit(main())