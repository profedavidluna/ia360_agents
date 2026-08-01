from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass, field

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from .common import get_llm_config, invoke_with_history
except ImportError:
    from common import get_llm_config, invoke_with_history


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", _normalize(text))


def build_default_documents() -> list[dict[str, str]]:
    return [
        {
            "id": "paris_guide",
            "title": "Guía rápida de París",
            "content": (
                "París es ideal en primavera y otoño. Conviene reservar museos con antelación, "
                "usar transporte público y alojarse en zonas conectadas como Le Marais o Saint-Germain."
            ),
        },
        {
            "id": "tokyo_guide",
            "title": "Consejos para Tokio y Kioto",
            "content": (
                "Tokio y Kioto son ideales en marzo-abril y octubre-noviembre. "
                "En verano hay calor y humedad, por lo que conviene ropa ligera e hidratación constante."
            ),
        },
        {
            "id": "travel_policy",
            "title": "Política interna de TravelOps",
            "content": (
                "Para viajes corporativos se recomienda reservar vuelos con 21 días de anticipación. "
                "Si el presupuesto supera 1500 USD por persona se requiere aprobación del supervisor."
            ),
        },
    ]


@dataclass
class RetrievalResult:
    doc: Document
    score: float
    matched_terms: tuple[str, ...]


@dataclass
class TravelKnowledgeBase:
    chunk_size: int = 300
    chunk_overlap: int = 40
    chunks: list[Document] = field(default_factory=list)

    def add_document(self, source_id: str, title: str, content: str) -> None:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        docs = splitter.create_documents(
            texts=[content],
            metadatas=[{"source_id": source_id, "source_title": title}],
        )
        self.chunks.extend(docs)

    def add_documents(self, documents: list[dict[str, str]]) -> None:
        for item in documents:
            self.add_document(item["id"], item["title"], item["content"])

    def search(self, query: str, top_k: int = 3) -> list[RetrievalResult]:
        query_terms = set(_tokenize(query))
        if not query_terms:
            return []

        results: list[RetrievalResult] = []
        for doc in self.chunks:
            doc_terms = set(_tokenize(doc.page_content))
            matched = tuple(sorted(query_terms & doc_terms))
            if not matched:
                continue

            overlap = len(matched)
            density = overlap / max(1, len(doc_terms))
            score = overlap + density
            results.append(RetrievalResult(doc=doc, score=score, matched_terms=matched))

        results.sort(key=lambda x: (x.score, len(x.matched_terms)), reverse=True)
        return results[:top_k]

    @staticmethod
    def format_context(results: list[RetrievalResult]) -> str:
        if not results:
            return "No se recuperó contexto relevante."

        lines: list[str] = []
        for index, result in enumerate(results, start=1):
            source = result.doc.metadata.get("source_title", "fuente")
            lines.append(f"[Fuente {index}: {source}]\n{result.doc.page_content}")
        return "\n\n".join(lines)


def build_rag_system_prompt() -> str:
    return (
        "Eres TravelBot RAG con LangChain. Usa el contexto recuperado como fuente principal, "
        "responde en español y evita inventar datos que no estén en el contexto."
    )


@dataclass
class TravelRAGAgent:
    knowledge_base: TravelKnowledgeBase = field(default_factory=TravelKnowledgeBase)
    system_prompt: str = field(default_factory=build_rag_system_prompt)
    history: list[dict[str, str]] = field(default_factory=list)
    top_k: int = 3

    def __post_init__(self) -> None:
        if not self.knowledge_base.chunks:
            self.knowledge_base.add_documents(build_default_documents())

    def chat(self, user_message: str) -> str:
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        self.history.append({"role": "user", "content": user_message})
        results = self.knowledge_base.search(user_message, top_k=self.top_k)

        if not results:
            response = (
                "No encontré contexto suficiente en la base de conocimiento para responder "
                "con seguridad. ¿Puedes agregar más detalles?"
            )
            self.history.append({"role": "assistant", "content": response})
            return response

        context = self.knowledge_base.format_context(results)
        rag_input = (
            f"Consulta del usuario:\n{user_message}\n\n"
            f"Contexto recuperado:\n{context}\n\n"
            "Responde usando el contexto y cita brevemente qué fuente respalda tu respuesta."
        )

        llm_history = list(self.history[:-1]) + [{"role": "user", "content": rag_input}]
        response = invoke_with_history(self.system_prompt, llm_history, temperature=0.2)
        self.history.append({"role": "assistant", "content": response})
        return response

    def reset(self) -> None:
        self.history = []

    def run_interactive(self) -> None:
        config = get_llm_config()
        print("=" * 62)
        print("TRAVELOPS LANGCHAIN — Ejercicio 04 (RAG)")
        print("=" * 62)
        print(f"Modelo : {config['model']}")
        print(f"Servidor: {config['base_url']}")
        print(f"Chunks indexados: {len(self.knowledge_base.chunks)}")
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
                print(f"\nTravelOps RAG> {answer}\n")
            except RuntimeError as exc:
                print(f"\nError> {exc}\n")


def main() -> int:
    agent = TravelRAGAgent()
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
