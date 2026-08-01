"""
Ejercicio 07: Agente con Crítica y Auto-Mejora (Evaluator Pattern)
==================================================================

Enunciado
---------
Construye un sistema de dos agentes cooperativos que implemente el patrón
**Planificador–Crítico** para producir planes de viaje de alta calidad:

1. Un **agente planificador** genera un plan de viaje inicial dado el destino,
   la duración y las preferencias del usuario.

2. Un **agente crítico** evalúa el plan según criterios objetivos:
   adecuación del presupuesto, diversidad de actividades, logística y
   seguridad.  Produce una puntuación (0–10) y sugerencias concretas.

3. Un **agente evaluador** (orquestador) repite el ciclo planificador →
   crítico → revisión hasta que la puntuación supere un umbral mínimo o se
   alcance el número máximo de iteraciones.

4. Cada iteración del ciclo queda registrada en un historial de revisiones
   para que el usuario pueda ver cómo mejoró el plan.

5. El sistema expone un método ``chat()`` que acepta la consulta del usuario,
   ejecuta el ciclo completo y devuelve el plan final con su puntuación.

Tareas implementadas
--------------------
- [x] ``EvaluationResult``               — resultado estructurado de la crítica
- [x] ``TravelPlannerAgent.plan()``       — genera o revisa el plan de viaje
- [x] ``TravelCriticAgent.evaluate()``   — puntúa y critica el plan
- [x] ``parse_evaluation()``             — extrae puntuación y sugerencias del texto
- [x] ``EvaluatorAgent.run_cycle()``     — ciclo completo planificador–crítico
- [x] ``EvaluatorAgent.chat()``          — interfaz de alto nivel para el usuario
- [x] ``EvaluatorAgent.reset()``         — reinicia el historial de revisiones
- [x] ``EvaluatorAgent.run_interactive()`` — modo terminal con resumen del ciclo

Conceptos que aprenderás
------------------------
- Patrón Planificador–Crítico (Planner–Critic)
- Ciclos de auto-mejora con control de iteraciones
- Extracción de puntuaciones estructuradas desde texto libre
- Orquestación de múltiples agentes LLM con objetivos distintos
- Trazabilidad del proceso de mejora

Cómo ejecutar
-------------
    python travelops/exercise07_critic_evaluator.py
    python travelops/exercise07_critic_evaluator.py "Planifica 5 días en Tokio, presupuesto 1500 USD"

Variables de entorno (opcionales)
---------------------------------
    LLM_BASE_URL      — URL del servidor LLM    (default: http://localhost:8082/v1/messages)
    LLM_API_KEY       — clave de API             (default: freecc)
    LLM_MODEL         — modelo a usar            (default: claude-3-5-sonnet-20241022)
    MIN_SCORE         — puntuación mínima aceptable (default: 7)
    MAX_ITERATIONS    — máximo de ciclos          (default: 3)
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
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
# Modelos de datos
# ---------------------------------------------------------------------------

@dataclass
class EvaluationResult:
    """Resultado estructurado producido por el agente crítico.

    Attributes:
        score:       Puntuación del plan de 0 a 10.
        critique:    Texto completo de la crítica.
        suggestions: Lista de sugerencias concretas de mejora.
        passed:      ``True`` si la puntuación supera el umbral mínimo.
    """

    score: float
    critique: str
    suggestions: list[str] = field(default_factory=list)
    passed: bool = False

    def __post_init__(self) -> None:
        self.score = max(0.0, min(10.0, float(self.score)))


@dataclass
class RevisionRecord:
    """Registro de una iteración del ciclo planificador–crítico.

    Attributes:
        iteration:  Número de iteración (empieza en 1).
        plan:       Texto del plan generado en esta iteración.
        evaluation: Resultado de la evaluación del crítico.
    """

    iteration: int
    plan: str
    evaluation: EvaluationResult


# ---------------------------------------------------------------------------
# Extracción de la evaluación
# ---------------------------------------------------------------------------

def parse_evaluation(text: str, min_score: float = 7.0) -> EvaluationResult:
    """Extrae la puntuación y las sugerencias desde el texto del crítico.

    Busca patrones como ``Puntuación: 8/10`` o ``Score: 7`` en el texto.
    Si no encuentra ningún número, asigna 5.0 como valor neutro.

    Args:
        text:      Texto completo de la respuesta del crítico.
        min_score: Umbral mínimo para considerar el plan aprobado.

    Returns:
        :class:`EvaluationResult` con la puntuación y las sugerencias extraídas.
    """
    # Buscar puntuación en distintos formatos
    score_match = re.search(
        r"\b(?:puntuaci[oó]n|score|nota|calificaci[oó]n)\s*:?\s*(\d+(?:\.\d+)?)\s*(?:/\s*10)?\b",
        text,
        flags=re.IGNORECASE,
    )
    if not score_match:
        # Intento secundario: «X/10» en cualquier posición
        score_match = re.search(r"\b(\d+(?:\.\d+)?)\s*/\s*10\b", text)

    score = float(score_match.group(1)) if score_match else 5.0

    # Extraer sugerencias marcadas con viñetas comunes
    suggestion_pattern = re.compile(
        r"^\s*(?:[-•*▸]|\d+[.):])\s+(.+)$", re.MULTILINE
    )
    suggestions = [m.group(1).strip() for m in suggestion_pattern.finditer(text)]

    return EvaluationResult(
        score=score,
        critique=text,
        suggestions=suggestions,
        passed=score >= min_score,
    )


# ---------------------------------------------------------------------------
# Agente planificador
# ---------------------------------------------------------------------------

def _planner_system_prompt() -> str:
    return (
        "Eres TravelPlanner, un experto en diseño de itinerarios de viaje. "
        "Tu tarea es generar planes de viaje detallados, prácticos y atractivos.\n\n"
        "Incluye siempre:\n"
        "- Itinerario día a día con actividades concretas y horarios sugeridos.\n"
        "- Estimación de costos para vuelos, alojamiento y actividades.\n"
        "- Recomendaciones de transporte local.\n"
        "- Consejos prácticos de seguridad y cultura local.\n\n"
        "Cuando recibas retroalimentación de un crítico, revisa el plan "
        "incorporando específicamente cada sugerencia de mejora.\n"
        "Responde siempre en español."
    )


@dataclass
class TravelPlannerAgent:
    """Agente que genera y revisa planes de viaje.

    Attributes:
        system_prompt: Prompt del sistema del planificador.
    """

    system_prompt: str = field(default_factory=_planner_system_prompt)

    def plan(
        self,
        request: str,
        feedback: str = "",
        previous_plan: str = "",
    ) -> str:
        """Genera un plan de viaje o lo revisa según retroalimentación.

        En la primera iteración recibe solo la solicitud del usuario.  En
        las iteraciones siguientes recibe también el plan anterior y la
        crítica para que pueda mejorar el resultado.

        Args:
            request:       Solicitud original del usuario.
            feedback:      Crítica del agente evaluador (vacía en la 1.ª iter.).
            previous_plan: Plan de la iteración anterior (vacío en la 1.ª iter.).

        Returns:
            Texto del plan de viaje (nuevo o revisado).

        Raises:
            RuntimeError: Si el LLM no responde.
        """
        if previous_plan and feedback:
            content = (
                f"Solicitud original del usuario:\n{request}\n\n"
                f"Plan anterior:\n{previous_plan}\n\n"
                f"Crítica recibida:\n{feedback}\n\n"
                "Por favor revisa el plan incorporando cada sugerencia de mejora."
            )
        else:
            content = f"Genera un plan de viaje detallado para:\n{request}"

        return call_llm(
            messages=[{"role": "user", "content": content}],
            system_prompt=self.system_prompt,
            temperature=0.4,
        )


# ---------------------------------------------------------------------------
# Agente crítico
# ---------------------------------------------------------------------------

def _critic_system_prompt() -> str:
    return (
        "Eres TravelCritic, un evaluador experto en calidad de itinerarios de viaje. "
        "Tu tarea es revisar planes de viaje de forma objetiva y constructiva.\n\n"
        "Criterios de evaluación:\n"
        "1. Adecuación al presupuesto (los costos son realistas y detallados)\n"
        "2. Diversidad de actividades (cultura, gastronomía, naturaleza, descanso)\n"
        "3. Logística y viabilidad (tiempos de traslado, disponibilidad horaria)\n"
        "4. Seguridad y consejos prácticos\n"
        "5. Personalización (el plan se adapta al perfil del viajero)\n\n"
        "Tu respuesta debe incluir:\n"
        "- Puntuación: X/10 (en la primera línea o párrafo)\n"
        "- Fortalezas del plan\n"
        "- Lista de sugerencias de mejora con viñetas (-)\n\n"
        "Sé honesto pero constructivo. Responde en español."
    )


@dataclass
class TravelCriticAgent:
    """Agente que evalúa la calidad de un plan de viaje.

    Attributes:
        system_prompt: Prompt del sistema del crítico.
        min_score:     Puntuación mínima para considerar el plan aprobado.
    """

    system_prompt: str = field(default_factory=_critic_system_prompt)
    min_score: float = 7.0

    def evaluate(self, plan: str, request: str) -> EvaluationResult:
        """Evalúa un plan de viaje y retorna una crítica estructurada.

        Args:
            plan:    Texto del plan a evaluar.
            request: Solicitud original del usuario (contexto).

        Returns:
            :class:`EvaluationResult` con puntuación y sugerencias.

        Raises:
            RuntimeError: Si el LLM no responde.
        """
        content = (
            f"Solicitud original del viajero:\n{request}\n\n"
            f"Plan de viaje a evaluar:\n{plan}"
        )

        raw_critique = call_llm(
            messages=[{"role": "user", "content": content}],
            system_prompt=self.system_prompt,
            temperature=0.2,
        )

        return parse_evaluation(raw_critique, min_score=self.min_score)


# ---------------------------------------------------------------------------
# Orquestador evaluador
# ---------------------------------------------------------------------------

@dataclass
class EvaluatorAgent:
    """Orquestador del ciclo Planificador–Crítico.

    Coordina a :class:`TravelPlannerAgent` y :class:`TravelCriticAgent`
    en ciclos iterativos hasta alcanzar la calidad deseada.

    Attributes:
        planner:        Agente planificador.
        critic:         Agente crítico.
        min_score:      Puntuación mínima aceptable (0–10).
        max_iterations: Número máximo de ciclos de revisión.
        revisions:      Historial de iteraciones con plan y evaluación.

    Example::

        agent = EvaluatorAgent()
        result = agent.chat("5 días en París, presupuesto 1200 USD, pareja")
        print(result)
    """

    planner: TravelPlannerAgent = field(default_factory=TravelPlannerAgent)
    critic: TravelCriticAgent = field(
        default_factory=lambda: TravelCriticAgent(
            min_score=float(os.getenv("MIN_SCORE", "7"))
        )
    )
    min_score: float = field(
        default_factory=lambda: float(os.getenv("MIN_SCORE", "7"))
    )
    max_iterations: int = field(
        default_factory=lambda: int(os.getenv("MAX_ITERATIONS", "3"))
    )
    revisions: list[RevisionRecord] = field(default_factory=list)

    def run_cycle(self, request: str) -> str:
        """Ejecuta el ciclo planificador–crítico y devuelve el plan final.

        El ciclo se detiene cuando:
        - La evaluación supera ``min_score``, o
        - Se alcanza ``max_iterations``.

        Args:
            request: Solicitud de viaje en lenguaje natural.

        Returns:
            Texto del plan de viaje más reciente y de mayor calidad.

        Raises:
            RuntimeError: Si el LLM falla en cualquier paso.
        """
        self.revisions = []
        current_plan = ""
        last_feedback = ""

        for iteration in range(1, self.max_iterations + 1):
            # --- Generar / revisar plan ---
            current_plan = self.planner.plan(
                request=request,
                feedback=last_feedback,
                previous_plan=current_plan,
            )

            # --- Evaluar plan ---
            evaluation = self.critic.evaluate(
                plan=current_plan,
                request=request,
            )

            self.revisions.append(
                RevisionRecord(
                    iteration=iteration,
                    plan=current_plan,
                    evaluation=evaluation,
                )
            )

            last_feedback = evaluation.critique

            if evaluation.passed:
                break

        return current_plan

    def chat(self, user_message: str) -> str:
        """Procesa la solicitud del usuario y devuelve el plan mejorado.

        Ejecuta el ciclo completo planificador–crítico y añade un resumen
        del proceso al final de la respuesta.

        Args:
            user_message: Solicitud de viaje en lenguaje natural.

        Returns:
            Plan de viaje final con un resumen del ciclo de mejora.

        Raises:
            ValueError: Si ``user_message`` es una cadena vacía.
            RuntimeError: Si el LLM no está disponible.
        """
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        final_plan = self.run_cycle(user_message)

        # Resumen del ciclo de mejora
        last = self.revisions[-1]
        iterations_done = len(self.revisions)
        summary = (
            f"\n\n---\n"
            f"📊 Proceso de mejora: {iterations_done} iteración(es) | "
            f"Puntuación final: {last.evaluation.score:.1f}/10"
        )

        return final_plan + summary

    def reset(self) -> None:
        """Limpia el historial de revisiones."""
        self.revisions = []

    def run_interactive(self) -> None:
        """Inicia un bucle de conversación interactiva en la terminal."""
        config = get_llm_config()

        print("=" * 66)
        print("TRAVELBOT — Agente con Crítica y Auto-Mejora")
        print("=" * 66)
        print(f"Modelo         : {config['model']}")
        print(f"Servidor       : {config['base_url']}")
        print(f"Puntuación mín : {self.min_score}/10")
        print(f"Máx. iteraciones: {self.max_iterations}")
        print("Escribe 'historial' para ver las iteraciones o 'salir' para terminar.\n")

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

            if user_input.lower() == "historial":
                if not self.revisions:
                    print("\n(Sin iteraciones previas)\n")
                else:
                    for rev in self.revisions:
                        print(
                            f"\n[Iteración {rev.iteration}] "
                            f"Puntuación: {rev.evaluation.score:.1f}/10"
                        )
                        if rev.evaluation.suggestions:
                            print("  Sugerencias:")
                            for s in rev.evaluation.suggestions[:3]:
                                print(f"    - {s}")
                print()
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
    agent = EvaluatorAgent()

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
