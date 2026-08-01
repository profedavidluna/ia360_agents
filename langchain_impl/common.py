from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

try:
    from langchain_anthropic import ChatAnthropic
except Exception:  # pragma: no cover - import opcional
    ChatAnthropic = None

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - import opcional
    ChatOpenAI = None


def get_llm_config() -> dict[str, str]:
    """Lee configuración del LLM desde variables de entorno."""
    return {
        "base_url": os.getenv("LLM_BASE_URL", "http://localhost:8082/v1/messages"),
        "api_key": os.getenv("LLM_API_KEY", "freecc"),
        "model": os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022"),
        "api_type": os.getenv("LLM_API_TYPE", "anthropic").lower(),
    }


def dict_history_to_messages(history: list[dict[str, str]]) -> list[BaseMessage]:
    """Convierte historial role/content al formato de mensajes LangChain."""
    messages: list[BaseMessage] = []
    for item in history:
        role = item.get("role", "").strip().lower()
        content = str(item.get("content", ""))
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
    return messages


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for piece in content:
            if isinstance(piece, str):
                parts.append(piece)
            elif isinstance(piece, dict):
                text = piece.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(p for p in parts if p).strip()
    return str(content)


def _build_langchain_model(temperature: float):
    config = get_llm_config()

    if config["api_type"] == "openai" and ChatOpenAI:
        return ChatOpenAI(
            model=config["model"],
            api_key=config["api_key"],
            base_url=config["base_url"],
            temperature=temperature,
            max_tokens=2048,
        )

    if ChatAnthropic:
        try:
            return ChatAnthropic(
                model=config["model"],
                api_key=config["api_key"],
                base_url=config["base_url"],
                temperature=temperature,
                max_tokens=2048,
            )
        except TypeError:
            # Compatibilidad con versiones que usan anthropic_api_url
            return ChatAnthropic(
                model=config["model"],
                api_key=config["api_key"],
                anthropic_api_url=config["base_url"],
                temperature=temperature,
                max_tokens=2048,
            )

    if ChatOpenAI:
        return ChatOpenAI(
            model=config["model"],
            api_key=config["api_key"],
            base_url=config["base_url"],
            temperature=temperature,
            max_tokens=2048,
        )

    raise RuntimeError(
        "No se encontró backend LangChain para chat. "
        "Instala: langchain-openai o langchain-anthropic."
    )


def _http_fallback(messages: list[BaseMessage], temperature: float) -> str:
    """Fallback directo HTTP compatible con endpoint Anthropic style."""
    config = get_llm_config()

    system_parts: list[str] = []
    payload_messages: list[dict[str, str]] = []

    for msg in messages:
        if isinstance(msg, SystemMessage):
            system_parts.append(_extract_text(msg.content))
        elif isinstance(msg, HumanMessage):
            payload_messages.append({"role": "user", "content": _extract_text(msg.content)})
        elif isinstance(msg, AIMessage):
            payload_messages.append({"role": "assistant", "content": _extract_text(msg.content)})

    body: dict[str, Any] = {
        "model": config["model"],
        "max_tokens": 2048,
        "temperature": temperature,
        "messages": payload_messages,
    }
    if system_parts:
        body["system"] = "\n\n".join(system_parts)

    request = Request(
        url=config["base_url"],
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": config["api_key"],
        },
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
        raise RuntimeError("El LLM finalizó sin devolver texto.")
    return answer


def invoke_messages(messages: list[BaseMessage], temperature: float = 0.3) -> str:
    """Invoca al LLM con mensajes LangChain y retorna texto."""
    try:
        model = _build_langchain_model(temperature=temperature)
        response = model.invoke(messages)
        text = _extract_text(response.content)
        if text.strip():
            return text.strip()
    except Exception:
        pass

    return _http_fallback(messages=messages, temperature=temperature)


def invoke_with_history(
    system_prompt: str,
    history: list[dict[str, str]],
    temperature: float = 0.3,
) -> str:
    """Invoca al LLM usando prompt del sistema + historial role/content."""
    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
    messages.extend(dict_history_to_messages(history))
    return invoke_messages(messages, temperature=temperature)
