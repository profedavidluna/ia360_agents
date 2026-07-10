"""Agente de clima en Python puro.

Consulta una ciudad usando Open-Meteo, obtiene el clima actual y genera una
recomendación simple sobre si conviene viajar en ese momento.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from math import isnan
from typing import Any
from urllib.parse import quote_plus
from urllib.request import urlopen
import urllib.request as urllib_request


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=es&format=json"
WEATHER_URL = (
	"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
	"&current=temperature_2m,apparent_temperature,precipitation,rain,showers,weather_code,wind_speed_10m"
	"&hourly=temperature_2m,precipitation_probability,weather_code,wind_speed_10m"
	"&forecast_days=1&timezone=auto"
)


@dataclass
class WeatherResult:
	city: str
	country: str
	latitude: float
	longitude: float
	temperature: float
	apparent_temperature: float
	precipitation: float
	wind_speed: float
	weather_code: int
	travel_score: int
	recommendation: str
	reasons: list[str]


@dataclass
class AgentState:
	last_city: str | None = None
	last_result: WeatherResult | None = None
	awaiting_city: bool = False
	awaiting_followup: str | None = None


@dataclass
class AgentReply:
	text: str
	should_exit: bool = False
	kind: str = "message"
	payload: dict[str, Any] | None = None


def fetch_json(url: str) -> dict[str, Any]:
	with urlopen(url, timeout=15) as response:
		return json.loads(response.read().decode("utf-8"))


def post_json(url: str, body: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
	data = json.dumps(body).encode("utf-8")
	request_headers = {"Content-Type": "application/json"}
	if headers:
		request_headers.update(headers)
	request = urllib_request.Request(url, data=data, headers=request_headers, method="POST")
	with urlopen(request, timeout=60) as response:
		response_text = response.read().decode("utf-8")
		
		# Si la respuesta está vacía
		if not response_text or not response_text.strip():
			raise ValueError(f"Servidor devolvió respuesta vacía. Status: {response.status}")
		
		# Detectar si es Server-Sent Events (SSE) streaming
		if response_text.strip().startswith("event:"):
			# Parsear SSE: cada línea es "event: TYPE" o "data: JSON"
			events = []
			current_event = None
			
			for line in response_text.strip().split("\n"):
				line = line.strip()
				if not line:
					continue
				
				if line.startswith("event:"):
					current_event = line[6:].strip()
				elif line.startswith("data:"):
					data_str = line[5:].strip()
					try:
						data_json = json.loads(data_str)
						events.append({"type": current_event, "data": data_json})
					except json.JSONDecodeError:
						pass
			
			# Retornar eventos como respuesta SSE
			if events:
				return {"__sse_events": events}
			else:
				raise ValueError("No se pudieron parsear eventos SSE")
		
		# Si no es SSE, intenta parsear como JSON normal
		try:
			return json.loads(response_text)
		except json.JSONDecodeError as e:
			# Si no es JSON válido, muestra qué recibió
			preview = response_text[:200] if len(response_text) > 200 else response_text
			raise ValueError(f"Servidor devolvió respuesta no-JSON: {preview}")


def safe_json_loads(text: str) -> dict[str, Any] | None:
	try:
		value = json.loads(text)
		return value if isinstance(value, dict) else None
	except json.JSONDecodeError:
		return None


def find_city(city_name: str) -> dict[str, Any]:
	data = fetch_json(GEOCODING_URL.format(city=quote_plus(city_name)))
	results = data.get("results") or []
	if not results:
		raise ValueError(f"No encontré la ciudad '{city_name}'. Prueba con otro nombre o agrega el país.")
	return results[0]


def normalize_text(text: str) -> str:
	return " ".join(text.strip().split())


def extract_city(text: str) -> str | None:
	patterns = [
		r"\ben\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s\-']{2,})$",
		r"\bpara\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s\-']{2,})$",
		r"\bde\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s\-']{2,})$",
	]
	for pattern in patterns:
		match = re.search(pattern, text, flags=re.IGNORECASE)
		if match:
			return normalize_text(match.group(1))

	if len(text.split()) <= 4 and not any(keyword in text.lower() for keyword in ("clima", "tiempo", "viajar", "viaje")):
		return normalize_text(text)

	return None


def is_exit_text(text: str) -> bool:
	return text.lower() in {"salir", "exit", "quit", "q", "adios", "adiós"}


def wants_weather(text: str) -> bool:
	keywords = ("clima", "tiempo", "llueve", "lluvia", "viajar", "viaje", "temperatura", "pronostico", "pronóstico")
	return any(keyword in text.lower() for keyword in keywords)


def weather_description(code: int) -> str:
	descriptions = {
		0: "cielo despejado",
		1: "principalmente despejado",
		2: "parcialmente nublado",
		3: "nublado",
		45: "niebla",
		48: "niebla con escarcha",
		51: "llovizna ligera",
		53: "llovizna moderada",
		55: "llovizna intensa",
		61: "lluvia ligera",
		63: "lluvia moderada",
		65: "lluvia intensa",
		71: "nieve ligera",
		73: "nieve moderada",
		75: "nieve intensa",
		80: "chubascos ligeros",
		81: "chubascos moderados",
		82: "chubascos intensos",
		95: "tormenta",
		96: "tormenta con granizo",
		99: "tormenta fuerte con granizo",
	}
	return descriptions.get(code, f"condición meteorológica {code}")


def format_weather_summary(result: WeatherResult) -> str:
	lines = [
		f"Clima actual para {result.city}, {result.country}",
		f"Estado: {weather_description(result.weather_code)}",
		f"Temperatura: {result.temperature:.1f} °C",
		f"Sensación térmica: {result.apparent_temperature:.1f} °C",
		f"Precipitación: {result.precipitation:.1f} mm",
		f"Viento: {result.wind_speed:.0f} km/h",
		f"Puntaje de viaje: {result.travel_score}/100",
		f"Recomendación: {result.recommendation}",
	]
	if result.reasons:
		lines.append("Motivos:")
		lines.extend(f"- {reason}" for reason in result.reasons)
	return "\n".join(lines)


def format_weather_for_llm_analysis(result: WeatherResult) -> str:
	return (
		f"Datos meteorológicos para {result.city}, {result.country}:\n"
		f"- Temperatura: {result.temperature:.1f} °C\n"
		f"- Sensación térmica: {result.apparent_temperature:.1f} °C\n"
		f"- Precipitación: {result.precipitation:.1f} mm\n"
		f"- Viento: {result.wind_speed:.0f} km/h\n"
		f"- Condición: {weather_description(result.weather_code)}\n"
		f"Analiza estos datos y decide si es buen momento para viajar. "
		f"Responde con una recomendación breve y clara."
	)


def score_travel(current: dict[str, Any], hourly: dict[str, Any]) -> tuple[int, str, list[str]]:
	"""Calcula un puntaje de viaje basándose en condiciones meteorológicas.
	
	Retorna: (puntaje 0-100, recomendación, lista de razones)
	"""
	score = 100
	reasons = []
	
	# Penalizar por lluvia
	precipitation = float(current.get("precipitation", 0.0))
	if precipitation > 0:
		score -= int(precipitation * 5)
		reasons.append(f"Hay precipitación ({precipitation:.1f} mm)")
	
	# Penalizar por viento fuerte
	wind_speed = float(current.get("wind_speed_10m", 0.0))
	if wind_speed > 30:
		score -= 20
		reasons.append(f"Viento fuerte ({wind_speed:.0f} km/h)")
	elif wind_speed > 20:
		score -= 10
		reasons.append(f"Viento moderado ({wind_speed:.0f} km/h)")
	
	# Penalizar por temperaturas extremas
	temp = float(current.get("temperature_2m", 0.0))
	if temp < -5 or temp > 35:
		score -= 15
		reasons.append(f"Temperatura extrema ({temp:.1f} °C)")
	elif temp < 5 or temp > 30:
		score -= 5
		reasons.append(f"Temperatura poco confortable ({temp:.1f} °C)")
	
	# Penalizar por código de clima desfavorable
	weather_code = int(current.get("weather_code", 0))
	unfavorable_codes = {45, 48, 61, 63, 65, 71, 73, 75, 80, 81, 82, 95, 96, 99}
	if weather_code in unfavorable_codes:
		score -= 25
		reasons.append(f"Condición meteorológica desfavorable: {weather_description(weather_code)}")
	
	# Asegurar que el score esté en el rango 0-100
	score = max(0, min(100, score))
	
	# Generar recomendación
	if score >= 80:
		recommendation = "Excelente momento para viajar"
	elif score >= 60:
		recommendation = "Buen momento para viajar"
	elif score >= 40:
		recommendation = "Es posible viajar, pero toma precauciones"
	else:
		recommendation = "No es recomendable viajar en estas condiciones"
	
	return score, recommendation, reasons


def get_weather(city_name: str) -> WeatherResult:
	location = find_city(city_name)
	lat = float(location["latitude"])
	lon = float(location["longitude"])
	city = str(location.get("name", city_name))
	country = str(location.get("country", ""))

	data = fetch_json(WEATHER_URL.format(lat=lat, lon=lon))
	current = data.get("current") or {}
	hourly = data.get("hourly") or {}

	travel_score, recommendation, reasons = score_travel(current, hourly)

	return WeatherResult(
		city=city,
		country=country,
		latitude=lat,
		longitude=lon,
		temperature=float(current.get("temperature_2m", float("nan"))),
		apparent_temperature=float(current.get("apparent_temperature", float("nan"))),
		precipitation=float(current.get("precipitation", 0.0)),
		wind_speed=float(current.get("wind_speed_10m", 0.0)),
		weather_code=int(current.get("weather_code", 0)),
		travel_score=travel_score,
		recommendation=recommendation,
		reasons=reasons,
	)


def print_report(result: WeatherResult) -> None:
	print("\n" + format_weather_summary(result))


def get_llm_config_openai() -> dict[str, str]:
	return {
		"base_url": os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
		"api_key": os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
		"model": os.getenv("LLM_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
	}


def get_llm_config() -> dict[str, str]:
    return {
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
def llm_is_configured() -> bool:
	config = get_llm_config()
	# Considera configurado si hay una URL de base_url (local o remota)
	has_url = bool(config["base_url"])
	return has_url


def call_llm(messages: list[dict[str, str]], temperature: float = 0.2) -> str:
	config = get_llm_config()
	api_type = config.get("api_type", "anthropic").lower()
	
	# Extraer mensaje del sistema si existe
	system_message = ""
	user_messages = []
	
	for msg in messages:
		if msg["role"] == "system":
			system_message = msg["content"]
		else:
			user_messages.append({"role": msg["role"], "content": msg["content"]})
	
	# Preparar body según tipo de API
	if api_type == "anthropic":
		# Formato Anthropic Messages API
		body = {
			"model": config["model"],
			"max_tokens": 2048,
			"messages": user_messages,
			"temperature": temperature,
		}
		if system_message:
			body["system"] = system_message
		
		headers = {"x-api-key": config["api_key"]}
	else:
		# Formato OpenAI Chat Completions
		body = {
			"model": config["model"],
			"messages": messages,
			"temperature": temperature,
		}
		headers = {}
		if config["api_key"]:
			headers["Authorization"] = f"Bearer {config['api_key']}"
	
	headers["Content-Type"] = "application/json"
	
	try:
		response = post_json(config["base_url"], body, headers=headers)
	except Exception as e:
		error_str = str(e)
		raise ValueError(f"Error al conectar con LLM en {config['base_url']}: {error_str}")
	
	# Mostrar respuesta para debugging
	if not response or len(str(response)) < 10:
		raise ValueError(f"Respuesta vacía del servidor: {response}")
	
	# Manejar Server-Sent Events (SSE)
	if "__sse_events" in response:
		# Extraer el último evento "message_delta" que contiene el contenido
		events = response["__sse_events"]
		text_content = ""
		
		for event in events:
			if event["type"] == "content_block_delta":
				delta = event["data"].get("delta", {})
				if "text" in delta:
					text_content += delta["text"]
		
		if text_content:
			return text_content
		else:
			raise ValueError("No se encontró contenido de texto en los eventos SSE")
	
	# Extraer respuesta según tipo de API (non-SSE)
	if api_type == "anthropic":
		# Respuesta Anthropic puede ser en diferentes formatos
		if isinstance(response, dict):
			# Formato dict: {"content": [...]}
			content = response.get("content") or []
			if content and isinstance(content, list) and len(content) > 0:
				return str(content[0].get("text", ""))
			# Formato alternativo: {"text": "..."}
			elif "text" in response:
				return str(response["text"])
			# Si es un dict pero no tiene lo esperado
			else:
				raise ValueError(f"Formato inesperado de Anthropic: {str(response)[:200]}")
		# Si respuesta es string (error en el servidor)
		else:
			raise ValueError(f"El servidor retornó respuesta no-JSON: {str(response)[:200]}")
	else:
		# OpenAI format
		choices = response.get("choices") or []
		if not choices:
			raise ValueError(f"El servidor no devolvió choices. Respuesta: {str(response)[:200]}")
		message = (choices[0].get("message") or {}).get("content")
		if not message:
			raise ValueError(f"El servidor no devolvió contenido. Respuesta: {str(response)[:200]}")
		return str(message)


def agent_system_prompt() -> str:
	return (
		"Eres un agente de clima y viajes amable y útil. "
		"Tu tarea es ayudar a los usuarios a decidir si es buen momento para viajar a una ciudad. "
		"Responde SIEMPRE en JSON válido con una de estas estructuras:\n\n"
		"{\"action\":\"weather\",\"city\":\"Nombre de la ciudad\"}\n"
		"{\"action\":\"clarify\",\"question\":\"Tu pregunta al usuario\"}\n"
		"{\"action\":\"answer\",\"answer\":\"Tu respuesta final\"}\n"
		"{\"action\":\"exit\"}\n\n"
		"Reglas importantes:\n"
		"- Usa 'weather' cuando necesites consultar el clima de una ciudad específica\n"
		"- Usa 'clarify' si la ciudad no está clara o necesitas más información\n"
		"- Usa 'answer' para respuestas finales o conversación general\n"
		"- Usa 'exit' solo si el usuario pide salir explícitamente (salir, exit, quit, etc.)\n"
		"- Siempre responde EN ESPAÑOL\n"
		"- Responde SOLO JSON, sin texto adicional"
	)


def parse_agent_decision(raw_text: str) -> dict[str, Any] | None:
	clean_text = raw_text.strip()
	parsed = safe_json_loads(clean_text)
	if parsed is not None:
		return parsed
	match = re.search(r"\{.*\}", clean_text, flags=re.DOTALL)
	if match:
		return safe_json_loads(match.group(0))
	return None


def route_llm_turn(user_text: str, state: AgentState) -> AgentReply:
	if not llm_is_configured():
		return AgentReply(
			"No veo un LLM configurado. Define LLM_BASE_URL y LLM_API_KEY, o usa un servidor local compatible con Chat Completions."
		)

	messages = [
		{"role": "system", "content": agent_system_prompt()},
	]
	
	# Agregar contexto de ciudad anterior si existe
	if state.last_result is not None:
		messages.append(
			{
				"role": "system",
				"content": (
					"Contexto previo: la última ciudad consultada fue "
					f"{state.last_city}. Última observación:\n{format_weather_summary(state.last_result)}"
				),
			}
		)
	
	messages.append({"role": "user", "content": user_text})

	raw_decision = call_llm(messages)
	decision = parse_agent_decision(raw_decision)
	
	if not decision:
		return AgentReply(
			"El LLM no devolvió JSON válido. Respuesta recibida: " + raw_decision[:100]
		)

	action = str(decision.get("action", "answer")).lower()
	
	if action == "exit":
		return AgentReply("Cerrando el agente de clima.", should_exit=True)
	
	if action == "clarify":
		question = str(decision.get("question", "¿Qué ciudad quieres consultar?"))
		return AgentReply(question, kind="clarify")
	
	if action == "weather":
		city = normalize_text(str(decision.get("city", "")))
		if not city:
			return AgentReply("¿Qué ciudad quieres consultar?", kind="clarify")
		
		try:
			result = get_weather(city)
			state.last_city = city
			state.last_result = result
			
			# Pedir análisis al LLM basado en datos reales
			weather_data = format_weather_for_llm_analysis(result)
			analysis_messages = [
				{"role": "system", "content": "Eres un experto meteorológico. Analiza los datos meteorológicos y decide si es buen momento para viajar. Sé conciso y claro."},
				{"role": "user", "content": weather_data},
			]
			travel_decision = call_llm(analysis_messages)
			return AgentReply(f"Clima en {result.city}, {result.country}:\n\n{travel_decision}", kind="answer")
		except ValueError as e:
			return AgentReply(f"No pude encontrar la ciudad '{city}': {e}")
	
	if action == "answer":
		answer = str(decision.get("answer", ""))
		if answer:
			return AgentReply(answer, kind="answer")

	return AgentReply("No entendí la acción del modelo. Intenta reformular la consulta.")


def build_agent_reply(user_text: str, state: AgentState) -> AgentReply:
	text = normalize_text(user_text)

	if not text:
		return AgentReply("Escribe una ciudad o una consulta, por ejemplo: '¿conviene viajar a Lima?' ")

	if is_exit_text(text):
		return AgentReply("Cerrando el agente de clima.", should_exit=True)

	# Intenta usar LLM si está configurado
	if llm_is_configured():
		try:
			return route_llm_turn(text, state)
		except Exception as e:
			error_msg = str(e)
			print(f"\n⚠ Error de LLM: {error_msg}")
			print("  Usando modo local como fallback...\n")
	
	# Fallback: modo local sin LLM
	if state.awaiting_city:
		city = extract_city(text)
		if city:
			state.awaiting_city = False
			state.awaiting_followup = None
			result = get_weather(city)
			state.last_city = city
			state.last_result = result
			return AgentReply(format_weather_answer(result, city))
		return AgentReply("Necesito una ciudad concreta. Puedes decirme, por ejemplo: 'Madrid' o 'clima en Bogotá'.")

	if wants_weather(text) or extract_city(text):
		city = extract_city(text)
		if not city:
			state.awaiting_city = True
			state.awaiting_followup = "city"
			return AgentReply("¿Sobre qué ciudad quieres que consulte el clima?")
		result = get_weather(city)
		state.last_city = city
		state.last_result = result
		return AgentReply(format_weather_answer(result, city))

	if state.last_result is not None:
		return AgentReply(
			f"Ya consulté {state.last_city}. Si quieres otra ciudad, dime: 'clima en París' o 'viajar a Roma'."
		)

	return AgentReply(
		"Puedo consultar clima y darte una recomendación de viaje. Prueba con: '¿conviene viajar a Medellín?'"
	)


def format_weather_answer(result: WeatherResult, city_query: str) -> str:
	lines = [
		f"Entendido: voy a revisar el clima para {city_query}.",
		f"Clima actual para {result.city}, {result.country}",
		f"Estado: {weather_description(result.weather_code)}",
		f"Temperatura: {result.temperature:.1f} °C",
		f"Sensación térmica: {result.apparent_temperature:.1f} °C",
		f"Precipitación: {result.precipitation:.1f} mm",
		f"Viento: {result.wind_speed:.0f} km/h",
		f"Puntaje de viaje: {result.travel_score}/100",
		f"Recomendación: {result.recommendation}",
	]
	if result.reasons:
		lines.append("Motivos:")
		lines.extend(f"- {reason}" for reason in result.reasons)
	return "\n".join(lines)


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Agente de clima con LLM en Python puro")
	parser.add_argument("city", nargs="*", help="Nombre de la ciudad a consultar")
	parser.add_argument("--chat", action="store_true", help="Inicia el modo conversacional del agente")
	parser.add_argument("--llm", action="store_true", help="Fuerza el uso del LLM si está configurado")
	return parser.parse_args()


def run_chat(initial_text: str | None = None) -> int:
	state = AgentState()
	config = get_llm_config()
	api_type = config.get("api_type", "anthropic").upper()
	
	print("\n" + "="*60)
	print("AGENTE DE CLIMA Y VIAJES")
	print("="*60)
	
	if llm_is_configured():
		print(f"✓ Modo LLM ACTIVO ({api_type})")
		print(f"  Servidor: {config['base_url']}")
		print(f"  Modelo: {config['model']}")
		print("  Respuestas más naturales y contextuales")
	else:
		print("⚠ Modo LOCAL - LLM no configurado")
		print("  Usando análisis simplificado")
	
	print("\nEscribe una consulta natural o 'salir' para terminar.")
	print("Ejemplos: '¿Qué tal el clima en París?', 'Viajar a Medellín', 'Salir'")
	print("="*60 + "\n")

	if initial_text:
		print(f"Tú> {initial_text}")
		reply = build_agent_reply(initial_text, state)
		print(f"\nAgente> {reply.text}\n")
		if reply.should_exit:
			return 0

	while True:
		try:
			user_text = input("Tú> ").strip()
		except KeyboardInterrupt:
			print("\n\nCerrando el agente de clima. ¡Hasta luego!")
			return 0
		except EOFError:
			print("\n\nCerrando el agente de clima. ¡Hasta luego!")
			return 0

		if not user_text:
			continue

		reply = build_agent_reply(user_text, state)
		print(f"\nAgente> {reply.text}\n")
		if reply.should_exit:
			return 0


def main() -> int:
	args = parse_args()
	city_name = " ".join(args.city).strip()

	# Si hay --llm, fuerza modo LLM (ahora es el comportamiento por defecto)
	if args.llm:
		return run_chat(city_name or None)
	
	# Si hay --chat, usa modo chat
	if args.chat:
		return run_chat(city_name or None)
	
	# Si hay una ciudad específica, consulta una vez y luego chat
	if city_name:
		print(f"Consultando clima para: {city_name}\n")
		reply = build_agent_reply(f"¿Cómo está el clima en {city_name}?", AgentState())
		print(reply.text)
		return 0
	
	# Por defecto: entra en modo chat/LLM
	return run_chat()


if __name__ == "__main__":
	sys.exit(main())