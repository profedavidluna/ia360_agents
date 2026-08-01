"""
Ejercicio 01: Agente Único de TravelOps
========================================

Enunciado
---------
Construye un agente asistente de viajes que cumpla con los siguientes requisitos:

1. Tenga un prompt del sistema que lo defina como experto en viajes,
   capaz de recomendar destinos, armar itinerarios y dar consejos de viaje.

2. Reciba mensajes del usuario y mantenga el historial completo de la
   conversación para que el agente recuerde lo que ya se habló.

3. Llame al LLM enviando el historial acumulado en cada turno.

4. Devuelva la respuesta del agente como una cadena de texto.

5. Ofrezca un modo interactivo de terminal que termine cuando el usuario
   escriba "salir", "exit" o "q".

Tareas implementadas
--------------------
- [x] get_llm_config()       — lee la configuración del LLM desde el entorno
- [x] build_system_prompt()  — construye el prompt del sistema para el agente
- [x] call_llm(messages)     — envía mensajes al LLM y retorna la respuesta
- [x] TravelAgent.chat()     — procesa un mensaje y actualiza el historial
- [x] TravelAgent.reset()    — limpia el historial de conversación
- [x] TravelAgent.run_interactive() — bucle de conversación en terminal

Conceptos que aprenderás
-------------------------
- Estructura básica de un agente de IA (entrada → LLM → salida)
- Diseño de prompts de sistema orientados a un dominio específico
- Manejo de historial de conversación (lista de mensajes role/content)
- Llamadas streaming SSE a la API de Anthropic
- Separación de responsabilidades en clases

Cómo ejecutar
-------------
    python travelops/exercise01_single_agent.py
    python travelops/exercise01_single_agent.py "¿Qué llevar a Japón en invierno?"

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
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ---------------------------------------------------------------------------
# Configuración del LLM
# ---------------------------------------------------------------------------

def get_llm_config() -> dict[str, str]:
    """Retorna la configuración del LLM leyendo variables de entorno.

    Returns:
        Diccionario con claves ``base_url``, ``api_key`` y ``model``.
    """
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


# ---------------------------------------------------------------------------
# Prompt del sistema
# ---------------------------------------------------------------------------

def build_system_prompt() -> str:
    """Construye el prompt del sistema para el agente de viajes.

    El prompt define la personalidad, especialidad y restricciones del agente.

    Returns:
        Cadena de texto con el prompt del sistema.
    """
    return (
        "Eres TravelBot, un asistente experto en viajes y turismo. "
        "Tu misión es ayudar a los viajeros a planificar sus aventuras de forma "
        "clara, práctica y entusiasta.\n\n"
        "Puedes:\n"
        "- Recomendar destinos según los intereses y presupuesto del viajero.\n"
        "- Armar itinerarios detallados día a día.\n"
        "- Dar consejos sobre qué llevar en la maleta según el clima y la actividad.\n"
        "- Informar sobre requisitos de visado y documentación.\n"
        "- Sugerir las mejores épocas para visitar cada destino.\n"
        "- Recomendar restaurantes, hoteles y actividades locales.\n\n"
        "Responde siempre en español, de forma amigable y concisa. "
        "Si no tienes información suficiente para responder con seguridad, "
        "indícalo claramente en lugar de inventar datos."
    )


# ---------------------------------------------------------------------------
# Llamada al LLM
# ---------------------------------------------------------------------------

def call_llm(
    messages: list[dict[str, str]],
    system_prompt: str = "",
    temperature: float = 0.3,
) -> str:
    """Envía una lista de mensajes al LLM y retorna la respuesta de texto.

    Soporta tanto respuestas JSON normales como streaming SSE (Server-Sent
    Events), que es el formato devuelto por Free Claude Code.

    Args:
        messages:      Lista de mensajes en formato ``[{"role": ..., "content": ...}]``.
                       No debe incluir mensajes con ``role == "system"``; esos se
                       pasan en el parámetro ``system_prompt``.
        system_prompt: Texto del prompt del sistema (puede estar vacío).
        temperature:   Temperatura de generación (0.0 – 1.0).

    Returns:
        Texto de la respuesta del LLM.

    Raises:
        RuntimeError: Si no se pudo conectar al LLM o la respuesta está vacía.
    """
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
        raise RuntimeError(
            f"Error HTTP {exc.code}: {body_text}"
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            f"No se pudo conectar con {config['base_url']}: {exc.reason}"
        ) from exc

    answer = "".join(fragments).strip()

    if not answer:
        raise RuntimeError(
            "El LLM finalizó la respuesta sin devolver texto."
        )

    return answer


# ---------------------------------------------------------------------------
# Clase TravelAgent
# ---------------------------------------------------------------------------

@dataclass
class TravelAgent:
    """Agente único de asistencia para viajes.

    Mantiene el historial de conversación y llama al LLM en cada turno.

    Attributes:
        system_prompt: Prompt del sistema que define el comportamiento del agente.
        history:       Lista de mensajes intercambiados (excluye el system prompt).

    Example::

        agent = TravelAgent()
        response = agent.chat("¿Cuál es el mejor destino en Asia para familias?")
        print(response)
    """

    system_prompt: str = field(default_factory=build_system_prompt)
    history: list[dict[str, str]] = field(default_factory=list)

    def chat(self, user_message: str) -> str:
        """Procesa un mensaje del usuario y retorna la respuesta del agente.

        El mensaje se agrega al historial antes de llamar al LLM, y la
        respuesta también se guarda en el historial para el siguiente turno.

        Args:
            user_message: Texto escrito por el usuario.

        Returns:
            Respuesta del agente de viajes.

        Raises:
            ValueError: Si ``user_message`` es una cadena vacía.
            RuntimeError: Si el LLM devuelve un error o no está disponible.
        """
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        # Agregar mensaje del usuario al historial
        self.history.append({"role": "user", "content": user_message})

        # Llamar al LLM con una copia del historial en su estado actual
        response = call_llm(
            messages=list(self.history),
            system_prompt=self.system_prompt,
        )

        # Guardar la respuesta en el historial
        self.history.append({"role": "assistant", "content": response})

        return response

    def reset(self) -> None:
        """Limpia el historial de conversación.

        Útil para iniciar una nueva conversación sin crear un nuevo agente.
        El ``system_prompt`` se conserva.
        """
        self.history = []

    def run_interactive(self) -> None:
        """Inicia un bucle de conversación interactiva en la terminal.

        El bucle termina cuando el usuario escribe ``salir``, ``exit`` o ``q``.
        """
        config = get_llm_config()

        print("=" * 60)
        print("TRAVELBOT — Asistente de Viajes")
        print("=" * 60)
        print(f"Modelo : {config['model']}")
        print(f"Servidor: {config['base_url']}")
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
    """Función principal.

    Permite enviar una pregunta directa desde la terminal::

        python travelops/exercise01_single_agent.py "¿Cuándo visitar Tailandia?"

    Sin argumentos inicia el modo interactivo.
    """
    agent = TravelAgent()

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
