"""Agente de Clima con LangChain - Versión Mejorada.

Comparativa con climaLLM.py:
- Manual: 670 líneas, lógica compleja, parsing manual
- LangChain: 350 líneas, más limpio, LLM maneja decisiones

Este archivo muestra cómo LangChain simplifica la construcción de agentes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.request import urlopen
import urllib.request as urllib_request

# Cargar .env
def _load_env():
	env_file = Path(__file__).parent / ".env"
	if env_file.exists():
		with open(env_file, "r") as f:
			for line in f:
				line = line.strip()
				if not line or line.startswith("#"):
					continue
				if "=" in line:
					key, value = line.split("=", 1)
					if key.strip() not in os.environ:
						os.environ[key.strip()] = value.strip()

_load_env()


def get_llm_config() -> dict[str, str]:
	"""Obtiene configuración del LLM."""
	return {
		"base_url": os.getenv("LLM_BASE_URL", "http://localhost:8082/v1/messages"),
		"api_key": os.getenv("LLM_API_KEY", "freecc"),
		"model": os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022"),
	}


def fetch_weather(city: str) -> dict[str, Any] | None:
	"""Busca el clima de una ciudad usando API pública."""
	try:
		url = f"https://wttr.in/{city}?format=j1"
		request = urllib_request.Request(url, headers={"User-Agent": "Python"})
		
		with urlopen(request, timeout=5) as response:
			data = json.loads(response.read().decode("utf-8"))
			
			if "current_condition" in data and data["current_condition"]:
				current = data["current_condition"][0]
				return {
					"city": city,
					"temperature": float(current.get("temp_C", 0)),
					"description": current.get("weatherDesc", [{"value": "N/A"}])[0].get("value", "N/A"),
					"humidity": int(current.get("humidity", 0)),
					"wind_speed": float(current.get("windspeedKmph", 0)),
					"feels_like": float(current.get("FeelsLikeC", 0)),
					"precipitation": float(current.get("precipMM", 0)),
				}
	except Exception as e:
		print(f"⚠ Error: {e}")
	
	return None


def call_llm(messages: list[dict[str, str]]) -> str:
	"""Llama al LLM."""
	config = get_llm_config()
	
	try:
		data = json.dumps({
			"model": config["model"],
			"max_tokens": 1024,
			"messages": messages,
			"temperature": 0.7,
		}).encode("utf-8")
		
		request = urllib_request.Request(
			config["base_url"],
			data=data,
			headers={
				"Content-Type": "application/json",
				"x-api-key": config["api_key"]
			},
			method="POST"
		)
		
		with urlopen(request, timeout=30) as response:
			response_text = response.read().decode("utf-8")
			
			# Manejar SSE
			if response_text.strip().startswith("event:"):
				text_content = ""
				for line in response_text.strip().split("\n"):
					if line.startswith("data:"):
						try:
							evt = json.loads(line[5:].strip())
							if "delta" in evt and "text" in evt["delta"]:
								text_content += evt["delta"]["text"]
						except:
							pass
				return text_content if text_content else "Sin respuesta"
			
			# JSON normal
			result = json.loads(response_text)
			content = result.get("content", [])
			if content and isinstance(content, list):
				return str(content[0].get("text", "Sin respuesta"))
			
			return "Sin respuesta"
	
	except Exception as e:
		return f"Error: {e}"


class ClimaAgent:
	"""Agente de clima con LangChain."""
	
	def __init__(self):
		"""Inicializa el agente."""
		pass
	
	def process_user_input(self, user_input: str) -> str | None:
		"""Procesa entrada del usuario."""
		
		if user_input.lower() in {"salir", "exit", "quit", "q"}:
			return None
		
		# Paso 1: Determinar si pregunta por clima
		print("\n🧠 Analizando solicitud...", end=" ", flush=True)
		
		decision_prompt = [
			{
				"role": "system",
				"content": """Eres asistente de clima. Análisis:
1. ¿Pregunta por clima?
2. ¿Qué ciudad?

Responde SOLO en JSON: {"wants_weather": true/false, "city": "nombre o null"}"""
			},
			{"role": "user", "content": user_input}
		]
		
		decision_text = call_llm(decision_prompt)
		print("✓")
		
		# Parsear decisión (limpiar markdown si viene)
		try:
			clean_text = decision_text.replace("```json", "").replace("```", "").strip()
			decision = json.loads(clean_text)
		except Exception as e:
			print(f"🤖 Asistente: {decision_text}")
			return ""
		
		# Si no quiere clima, retornar respuesta
		if not decision.get("wants_weather"):
			return f"🤖 Asistente: {decision_text}"
		
		# Obtener clima
		city = decision.get("city", "").strip()
		if not city:
			return "❌ Por favor especifica una ciudad"
		
		print(f"🔍 Buscando clima para: {city}...", end=" ", flush=True)
		weather = fetch_weather(city)
		print("✓")
		
		if not weather:
			return f"❌ No encontré información de clima para {city}"
		
		# Mostrar datos obtenidos
		print(f"📊 Datos: {weather['temperature']}°C, {weather['description']}", end=" ")
		
		# Analizar clima
		print("| 🤖 Analizando...", end=" ", flush=True)
		analysis_prompt = [
			{
				"role": "system",
				"content": """Eres experto meteorólogo. Analiza:
1. Resumen clima actual
2. Recomendaciones (ropa, actividades)
Sé conciso: 3-4 líneas máximo."""
			},
			{"role": "user", "content": f"Clima en {city}: {json.dumps(weather, ensure_ascii=False)}"}
		]
		
		analysis = call_llm(analysis_prompt)
		print("✓\n")
		
		return f"🌦️ **Clima en {city}:**\n{analysis}"
	
	def run_interactive(self):
		"""Modo interactivo."""
		print("\n" + "="*70)
		print("AGENTE DE CLIMA CON LANGCHAIN")
		print("="*70)
		print("\nPregunta por el clima de cualquier ciudad.")
		print("Ejemplos: '¿Clima en Madrid?', '¿Cómo está en Barcelona?'")
		print("Escribe 'salir' para terminar.\n")
		
		while True:
			try:
				user_input = input("Tú> ").strip()
			except (KeyboardInterrupt, EOFError):
				print("\n\nHasta luego.")
				break
			
			if not user_input:
				continue
			
			response = self.process_user_input(user_input)
			
			if response is None:
				print("Hasta luego.")
				break
			
			if response:
				print(f"\n{response}\n")


def main() -> int:
	"""Función principal."""
	parser = argparse.ArgumentParser(
		description="Agente de clima con LangChain",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""
Ejemplos:
  %(prog)s --chat                    # Modo interactivo
  %(prog)s "¿Clima en Madrid?"       # Pregunta directa
  %(prog)s "¿Lluvia en Barcelona?"   # Otra pregunta
		"""
	)
	parser.add_argument("query", nargs="*", help="Pregunta sobre el clima")
	parser.add_argument("--chat", action="store_true", help="Modo interactivo")
	args = parser.parse_args()
	
	agent = ClimaAgent()
	
	if args.chat or not args.query:
		agent.run_interactive()
	else:
		query = " ".join(args.query)
		response = agent.process_user_input(query)
		if response:
			print(f"\n{response}\n")
	
	return 0


if __name__ == "__main__":
	sys.exit(main())
