"""
Ejercicio 06: Agente con Memoria Persistente
=============================================

Enunciado
---------
Extiende el agente de viajes para que disponga de **memoria a largo plazo**
que persiste entre sesiones.  El agente debe ser capaz de:

1. Guardar hechos relevantes sobre el usuario (nombre, destinos visitados,
   preferencias de viaje, alergias, idiomas) en un almacén de memoria
   persistente (archivo JSON).
2. Cargar la memoria almacenada al iniciar, de modo que el agente recuerde
   información de sesiones anteriores.
3. Detectar automáticamente hechos relevantes en el mensaje del usuario y
   almacenarlos en memoria usando el LLM.
4. Recuperar recuerdos relevantes para enriquecer el contexto antes de
   responder al usuario.
5. Permitir que el usuario consulte, actualice y borre su memoria
   explícitamente.

Tareas implementadas
--------------------
- [x] ``MemoryEntry``                — entrada individual de la memoria
- [x] ``MemoryStore``                — almacén JSON con carga/guardado y búsqueda
- [x] ``MemoryStore.save()``         — persiste la memoria en disco
- [x] ``MemoryStore.load()``         — carga la memoria desde disco
- [x] ``MemoryStore.add()``          — agrega o actualiza una entrada
- [x] ``MemoryStore.search()``       — busca entradas por categoría o texto
- [x] ``MemoryStore.forget()``       — elimina una entrada por clave
- [x] ``extract_memories()``         — usa el LLM para detectar hechos memorizables
- [x] ``PersistentTravelAgent.chat()``          — ciclo completo con memoria
- [x] ``PersistentTravelAgent.reset()``         — limpia historial (conserva memoria)
- [x] ``PersistentTravelAgent.clear_memory()``  — borra toda la memoria persistente
- [x] ``PersistentTravelAgent.run_interactive()`` — modo terminal

Conceptos que aprenderás
------------------------
- Memoria a largo plazo vs. memoria a corto plazo (historial de conversación)
- Almacenamiento y recuperación de hechos estructurados
- Enriquecimiento de contexto antes de llamar al LLM
- Extracción automática de hechos con el LLM

Cómo ejecutar
-------------
    python travelops/exercise06_persistent_memory.py
    python travelops/exercise06_persistent_memory.py "Soy Ana y me gustan los viajes de aventura"

Variables de entorno (opcionales)
---------------------------------
    LLM_BASE_URL      — URL del servidor LLM  (default: http://localhost:8082/v1/messages)
    LLM_API_KEY       — clave de API           (default: freecc)
    LLM_MODEL         — modelo a usar          (default: claude-3-5-sonnet-20241022)
    MEMORY_FILE_PATH  — ruta del archivo JSON de memoria (default: .travelops_memory.json)
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ---------------------------------------------------------------------------
# Configuración del LLM
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


# ---------------------------------------------------------------------------
# Llamada al LLM
# ---------------------------------------------------------------------------

def call_llm(
    messages: list[dict[str, str]],
    system_prompt: str = "",
    temperature: float = 0.3,
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


# ---------------------------------------------------------------------------
# Modelo de memoria
# ---------------------------------------------------------------------------

VALID_CATEGORIES = frozenset(
    {
        "nombre",
        "preferencia",
        "destino_visitado",
        "destino_deseado",
        "restriccion",
        "presupuesto",
        "idioma",
        "otro",
    }
)


@dataclass
class MemoryEntry:
    """Representa un hecho individual almacenado sobre el usuario.

    Attributes:
        key:       Identificador único del recuerdo (p. ej. ``"nombre_usuario"``).
        value:     Valor del recuerdo (p. ej. ``"Ana"``).
        category:  Categoría semántica del recuerdo.
        updated_at: Marca de tiempo ISO 8601 de la última actualización.
    """

    key: str
    value: str
    category: str = "otro"
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if self.category not in VALID_CATEGORIES:
            self.category = "otro"


# ---------------------------------------------------------------------------
# Almacén de memoria
# ---------------------------------------------------------------------------

class MemoryStore:
    """Almacén de memoria persistente basado en un archivo JSON.

    Cada entrada es un :class:`MemoryEntry` indexada por su ``key``.  El
    almacén se carga automáticamente al crearse y se guarda en disco después
    de cada modificación.

    Args:
        file_path: Ruta del archivo JSON donde se persiste la memoria.
                   Si no existe se crea al primer guardado.
    """

    def __init__(self, file_path: str) -> None:
        self._file_path = file_path
        self._entries: dict[str, MemoryEntry] = {}
        self.load()

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persiste la memoria en disco."""
        data = {key: asdict(entry) for key, entry in self._entries.items()}
        try:
            with open(self._file_path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def load(self) -> None:
        """Carga la memoria desde disco si el archivo existe."""
        if not os.path.isfile(self._file_path):
            return
        try:
            with open(self._file_path, encoding="utf-8") as fh:
                raw: dict[str, Any] = json.load(fh)
            for key, values in raw.items():
                if isinstance(values, dict):
                    entry = MemoryEntry(
                        key=values.get("key", key),
                        value=values.get("value", ""),
                        category=values.get("category", "otro"),
                        updated_at=values.get("updated_at", ""),
                    )
                    self._entries[key] = entry
        except (OSError, json.JSONDecodeError, KeyError):
            self._entries = {}

    # ------------------------------------------------------------------
    # Operaciones CRUD
    # ------------------------------------------------------------------

    def add(self, key: str, value: str, category: str = "otro") -> MemoryEntry:
        """Agrega o actualiza una entrada de memoria.

        Args:
            key:      Identificador único del recuerdo.
            value:    Valor a almacenar.
            category: Categoría semántica.

        Returns:
            La :class:`MemoryEntry` creada o actualizada.
        """
        entry = MemoryEntry(key=key, value=value, category=category)
        self._entries[key] = entry
        self.save()
        return entry

    def forget(self, key: str) -> bool:
        """Elimina una entrada de memoria por su clave.

        Args:
            key: Identificador del recuerdo a eliminar.

        Returns:
            ``True`` si la entrada existía y fue eliminada, ``False`` en caso
            contrario.
        """
        if key in self._entries:
            del self._entries[key]
            self.save()
            return True
        return False

    def clear(self) -> None:
        """Borra toda la memoria almacenada."""
        self._entries = {}
        self.save()

    def all(self) -> list[MemoryEntry]:
        """Retorna todas las entradas de memoria."""
        return list(self._entries.values())

    def search(self, query: str = "", category: str = "") -> list[MemoryEntry]:
        """Busca entradas que coincidan con el texto o la categoría.

        Args:
            query:    Texto parcial a buscar en la clave o el valor.
            category: Filtra por categoría si se especifica.

        Returns:
            Lista de :class:`MemoryEntry` que cumplen los criterios.
        """
        results = list(self._entries.values())

        if category:
            results = [e for e in results if e.category == category]

        if query:
            query_lower = query.lower()
            results = [
                e
                for e in results
                if query_lower in e.key.lower() or query_lower in e.value.lower()
            ]

        return results

    def to_context_string(self) -> str:
        """Serializa la memoria en un bloque de texto para el contexto del LLM."""
        if not self._entries:
            return "(sin memoria almacenada)"
        lines = []
        for entry in self._entries.values():
            lines.append(f"- [{entry.category}] {entry.key}: {entry.value}")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._entries)


# ---------------------------------------------------------------------------
# Extracción de recuerdos con el LLM
# ---------------------------------------------------------------------------

_EXTRACT_SYSTEM_PROMPT = (
    "Eres un extractor de hechos memorizables sobre el usuario en el contexto de "
    "viajes y turismo. Analiza el mensaje y extrae SOLO los hechos relevantes a "
    "largo plazo (nombre, preferencias, destinos visitados o deseados, restricciones "
    "alimenticias, idiomas, presupuesto habitual). "
    "Devuelve exclusivamente un array JSON con objetos que tengan los campos "
    "\"key\" (snake_case), \"value\" (string) y \"category\" "
    "(una de: nombre, preferencia, destino_visitado, destino_deseado, "
    "restriccion, presupuesto, idioma, otro). "
    "Si no hay hechos relevantes devuelve []. "
    "No incluyas texto adicional fuera del JSON."
)


def extract_memories(message: str) -> list[dict[str, str]]:
    """Usa el LLM para extraer hechos memorizables de un mensaje.

    Args:
        message: Texto del usuario.

    Returns:
        Lista de diccionarios con claves ``key``, ``value`` y ``category``.
        Puede ser una lista vacía si no hay hechos relevantes o si el LLM
        no responde correctamente.
    """
    try:
        raw = call_llm(
            messages=[{"role": "user", "content": message}],
            system_prompt=_EXTRACT_SYSTEM_PROMPT,
            temperature=0.0,
        )
    except RuntimeError:
        return []

    raw = raw.strip()

    # Intentar extraer el bloque JSON aunque el LLM agregue texto extra
    import re

    match = re.search(r"\[.*\]", raw, flags=re.DOTALL)
    if not match:
        return []

    try:
        items = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []

    if not isinstance(items, list):
        return []

    result: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key", "")).strip()
        value = str(item.get("value", "")).strip()
        category = str(item.get("category", "otro")).strip()
        if key and value:
            result.append({"key": key, "value": value, "category": category})

    return result


# ---------------------------------------------------------------------------
# Prompt del sistema para el agente
# ---------------------------------------------------------------------------

def build_system_prompt() -> str:
    """Construye el prompt del sistema para el agente con memoria."""
    return (
        "Eres TravelBot, un asistente experto en viajes y turismo con memoria "
        "personalizada. Recuerdas las preferencias, destinos favoritos y detalles "
        "importantes de cada viajero a lo largo del tiempo.\n\n"
        "Usa la información en el bloque [MEMORIA DEL VIAJERO] para personalizar "
        "tus respuestas. Si la memoria está vacía, responde normalmente y aprovecha "
        "la conversación para conocer mejor al viajero.\n\n"
        "Responde siempre en español, de forma amigable y concisa."
    )


# ---------------------------------------------------------------------------
# Agente con memoria persistente
# ---------------------------------------------------------------------------

@dataclass
class PersistentTravelAgent:
    """Agente de viajes con memoria persistente entre sesiones.

    Combina un historial de conversación a corto plazo con un almacén de
    memoria a largo plazo guardado en disco.  En cada turno:

    1. Extrae posibles hechos memorizables del mensaje del usuario.
    2. Construye un contexto enriquecido con la memoria actual.
    3. Llama al LLM con el historial y el contexto de memoria.
    4. Guarda la nueva información en el almacén persistente.

    Attributes:
        memory:        Almacén de memoria persistente.
        system_prompt: Prompt base del sistema.
        history:       Historial de conversación de la sesión actual.

    Example::

        agent = PersistentTravelAgent()
        agent.chat("Me llamo Ana y adoro el senderismo")
        agent.chat("¿Qué destino me recomiendas?")
        # En la siguiente sesión la memoria de Ana sigue disponible.
    """

    memory: MemoryStore = field(
        default_factory=lambda: MemoryStore(
            os.getenv("MEMORY_FILE_PATH", ".travelops_memory.json")
        )
    )
    system_prompt: str = field(default_factory=build_system_prompt)
    history: list[dict[str, str]] = field(default_factory=list)

    def _build_system_with_memory(self) -> str:
        """Construye el prompt del sistema incluyendo el bloque de memoria."""
        memory_block = self.memory.to_context_string()
        return (
            f"{self.system_prompt}\n\n"
            f"[MEMORIA DEL VIAJERO]\n{memory_block}"
        )

    def _update_memory_from_message(self, message: str) -> None:
        """Extrae y almacena hechos memorizables del mensaje."""
        facts = extract_memories(message)
        for fact in facts:
            self.memory.add(
                key=fact["key"],
                value=fact["value"],
                category=fact.get("category", "otro"),
            )

    def chat(self, user_message: str) -> str:
        """Procesa un turno de la conversación.

        Extrae hechos memorizables, enriquece el contexto con la memoria
        existente y delega en el LLM para generar la respuesta.

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

        # Extraer y guardar hechos memorizables antes de responder
        self._update_memory_from_message(user_message)

        # Agregar el mensaje al historial
        self.history.append({"role": "user", "content": user_message})

        # Llamar al LLM con el contexto enriquecido
        response = call_llm(
            messages=list(self.history),
            system_prompt=self._build_system_with_memory(),
        )

        self.history.append({"role": "assistant", "content": response})
        return response

    def reset(self) -> None:
        """Limpia el historial de conversación de la sesión actual.

        La memoria persistente **no** se borra; use :meth:`clear_memory`
        para eso.
        """
        self.history = []

    def clear_memory(self) -> None:
        """Borra toda la memoria persistente del usuario."""
        self.memory.clear()

    def run_interactive(self) -> None:
        """Inicia un bucle de conversación interactiva en la terminal."""
        config = get_llm_config()

        print("=" * 66)
        print("TRAVELBOT — Agente con Memoria Persistente")
        print("=" * 66)
        print(f"Modelo  : {config['model']}")
        print(f"Servidor: {config['base_url']}")
        print(f"Memoria : {self.memory._file_path}  ({len(self.memory)} entradas)")
        print(
            "Comandos: 'ver memoria', 'borrar memoria', 'salir'\n"
        )

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

            if user_input.lower() == "ver memoria":
                print("\n[Memoria almacenada]")
                print(self.memory.to_context_string())
                print()
                continue

            if user_input.lower() == "borrar memoria":
                self.clear_memory()
                print("\nMemoria borrada.\n")
                continue

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
    agent = PersistentTravelAgent()

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
