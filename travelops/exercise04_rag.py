"""
Ejercicio 04: Agente RAG de TravelOps
=====================================

Enunciado
---------
Construye un agente de viajes con recuperación de contexto (RAG) que cumpla
con los siguientes requisitos:

1. Mantenga una pequeña base de conocimiento de destinos, políticas y consejos
   de viaje.
2. Divida los documentos en fragmentos reutilizables para poder recuperarlos
   por similitud léxica.
3. Reciba una consulta del usuario, recupere los fragmentos más relevantes y
   se los entregue al LLM como contexto.
4. Devuelva una respuesta útil en español citando las fuentes recuperadas.
5. Ofrezca un modo interactivo de terminal y un método para reiniciar la
   conversación.

Tareas implementadas
--------------------
- [x] ``get_llm_config()`` — lee la configuración del LLM desde el entorno
- [x] ``split_text()`` — divide documentos largos en fragmentos solapados
- [x] ``TravelKnowledgeBase`` — indexa y recupera fragmentos relevantes
- [x] ``build_rag_system_prompt()`` — prompt del sistema orientado a RAG
- [x] ``TravelRAGAgent.chat()`` — recupera contexto y consulta al LLM
- [x] ``TravelRAGAgent.reset()`` — limpia historial
- [x] ``TravelRAGAgent.run_interactive()`` — bucle de terminal

Conceptos que aprenderás
------------------------
- Fundamentos de Retrieval-Augmented Generation
- Indexación simple basada en chunks y términos
- Construcción de contexto para consultas al LLM
- Separación entre recuperación, prompting y conversación

Cómo ejecutar
-------------
    python travelops/exercise04_rag.py
    python travelops/exercise04_rag.py "¿Cuál es la mejor época para visitar Kioto?"

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
import unicodedata
from dataclasses import dataclass, field
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


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", _normalize(text))


def split_text(
    text: str,
    chunk_size: int = 80,
    overlap: int = 15,
) -> list[str]:
    """Divide texto en fragmentos por palabras con solapamiento."""
    words = text.split()
    if not words:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size debe ser mayor que cero.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap debe ser >= 0 y menor que chunk_size.")

    chunks: list[str] = []
    step = chunk_size - overlap

    for start in range(0, len(words), step):
        chunk_words = words[start:start + chunk_size]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break

    return chunks


@dataclass(frozen=True)
class KnowledgeChunk:
    source_id: str
    source_title: str
    chunk_id: int
    content: str
    tokens: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalResult:
    chunk: KnowledgeChunk
    score: float
    matched_terms: tuple[str, ...]


def build_default_documents() -> list[dict[str, str]]:
    """Retorna un corpus inicial con conocimientos de TravelOps."""
    return [
        {
            "id": "paris_guide",
            "title": "Guía rápida de París",
            "content": (
                "París es ideal en primavera y principios de otoño, cuando el clima "
                "es templado y hay menos filas que en pleno verano. Para una primera "
                "visita conviene alojarse cerca del metro en zonas como Saint-Germain, "
                "Le Marais o alrededor de la Ópera. Conviene reservar con antelación "
                "museos populares como el Louvre y considerar un pase de transporte "
                "semanal si la estancia supera tres días."
            ),
        },
        {
            "id": "tokyo_guide",
            "title": "Consejos para Tokio y Kioto",
            "content": (
                "Tokio funciona muy bien con una tarjeta IC para metro y trenes. "
                "Kioto se disfruta mejor con un itinerario temprano para visitar "
                "templos antes de que lleguen las multitudes. La mejor época para "
                "visitar ambas ciudades suele ser marzo-abril por los cerezos o "
                "octubre-noviembre por el follaje. En verano hace calor y humedad, "
                "por lo que conviene priorizar ropa ligera y descansos frecuentes."
            ),
        },
        {
            "id": "travel_policy",
            "title": "Política interna de TravelOps",
            "content": (
                "Para viajes corporativos, TravelOps recomienda reservar vuelos con "
                "al menos 21 días de anticipación. Los hoteles deben incluir desayuno "
                "y cancelación flexible cuando el viaje dure más de dos noches. "
                "Si el presupuesto total supera 1500 USD por persona, se requiere "
                "aprobación adicional del supervisor. Toda recomendación debe dejar "
                "claros los supuestos de precio y disponibilidad."
            ),
        },
    ]


@dataclass
class TravelKnowledgeBase:
    """Base de conocimiento simple con recuperación léxica."""

    chunk_size: int = 80
    overlap: int = 15
    chunks: list[KnowledgeChunk] = field(default_factory=list)

    def add_document(self, source_id: str, title: str, content: str) -> None:
        """Agrega un documento y lo divide en fragmentos indexables."""
        parts = split_text(content, chunk_size=self.chunk_size, overlap=self.overlap)
        for index, part in enumerate(parts):
            self.chunks.append(
                KnowledgeChunk(
                    source_id=source_id,
                    source_title=title,
                    chunk_id=index,
                    content=part,
                    tokens=tuple(_tokenize(part)),
                )
            )

    def add_documents(self, documents: list[dict[str, str]]) -> None:
        """Agrega múltiples documentos a la base de conocimiento."""
        for document in documents:
            self.add_document(
                source_id=document["id"],
                title=document["title"],
                content=document["content"],
            )

    def search(self, query: str, top_k: int = 3) -> list[RetrievalResult]:
        """Recupera los fragmentos más relevantes para una consulta."""
        query_terms = set(_tokenize(query))
        if not query_terms:
            return []

        results: list[RetrievalResult] = []
        for chunk in self.chunks:
            chunk_terms = set(chunk.tokens)
            matched_terms = tuple(sorted(query_terms & chunk_terms))
            if not matched_terms:
                continue

            overlap_score = len(matched_terms)
            density_bonus = overlap_score / max(1, len(chunk_terms))
            score = overlap_score + density_bonus
            results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=score,
                    matched_terms=matched_terms,
                )
            )

        results.sort(
            key=lambda item: (
                item.score,
                len(item.matched_terms),
                -item.chunk.chunk_id,
            ),
            reverse=True,
        )
        return results[:top_k]

    @staticmethod
    def format_context(results: list[RetrievalResult]) -> str:
        """Convierte resultados recuperados en un bloque de contexto legible."""
        if not results:
            return "No se recuperó contexto relevante."

        lines: list[str] = []
        for result in results:
            lines.append(
                f"[Fuente: {result.chunk.source_title} | chunk {result.chunk.chunk_id}]\n"
                f"{result.chunk.content}"
            )
        return "\n\n".join(lines)


def build_rag_system_prompt() -> str:
    """Construye el prompt del sistema del agente RAG."""
    return (
        "Eres TravelBot RAG, un asistente de viajes que responde usando el contexto "
        "recuperado de una base de conocimiento. Usa el contexto como fuente primaria, "
        "indica cuando algo proviene de las políticas o guías recuperadas y no inventes "
        "datos específicos si no aparecen en el contexto. Responde siempre en español "
        "de forma clara, útil y concisa."
    )


@dataclass
class TravelRAGAgent:
    """Agente de viajes con recuperación de contexto."""

    knowledge_base: TravelKnowledgeBase = field(default_factory=TravelKnowledgeBase)
    system_prompt: str = field(default_factory=build_rag_system_prompt)
    history: list[dict[str, str]] = field(default_factory=list)
    top_k: int = 3

    def __post_init__(self) -> None:
        if not self.knowledge_base.chunks:
            self.knowledge_base.add_documents(build_default_documents())

    def _build_contextual_messages(
        self,
        user_message: str,
        context_text: str,
    ) -> list[dict[str, str]]:
        previous_messages = list(self.history[:-1])
        contextual_user_message = {
            "role": "user",
            "content": (
                f"Consulta del usuario:\n{user_message}\n\n"
                f"Contexto recuperado:\n{context_text}\n\n"
                "Responde usando el contexto y aclara si algún detalle es una "
                "recomendación general."
            ),
        }
        return previous_messages + [contextual_user_message]

    def chat(self, user_message: str) -> str:
        """Recupera contexto y genera una respuesta del LLM."""
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        self.history.append({"role": "user", "content": user_message})

        results = self.knowledge_base.search(user_message, top_k=self.top_k)
        if not results:
            response = (
                "No encontré contexto suficiente en la base de conocimiento para "
                "responder con seguridad. ¿Puedes dar más detalles del destino o del tipo "
                "de recomendación que necesitas?"
            )
            self.history.append({"role": "assistant", "content": response})
            return response

        context_text = self.knowledge_base.format_context(results)
        messages = self._build_contextual_messages(user_message, context_text)
        response = call_llm(
            messages=messages,
            system_prompt=self.system_prompt,
        )
        self.history.append({"role": "assistant", "content": response})
        return response

    def reset(self) -> None:
        """Limpia el historial de conversación."""
        self.history = []

    def run_interactive(self) -> None:
        """Inicia un bucle de conversación interactiva en la terminal."""
        config = get_llm_config()

        print("=" * 62)
        print("TRAVELOPS RAG — Asistente de Viajes con Contexto")
        print("=" * 62)
        print(f"Modelo : {config['model']}")
        print(f"Servidor: {config['base_url']}")
        print(f"Fragmentos indexados: {len(self.knowledge_base.chunks)}")
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
                print("¡Hasta pronto! Que tengas un excelente viaje. 📚✈️")
                return

            try:
                answer = self.chat(user_input)
                print(f"\nTravelOps RAG> {answer}\n")
            except RuntimeError as exc:
                print(f"\nError> {exc}\n")


def main() -> int:
    """Función principal."""
    agent = TravelRAGAgent()

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
