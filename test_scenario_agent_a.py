"""Test Scenario Generator Agent - OPCIÓN A (Quick & Simple)

Generador básico de escenarios de prueba usando LLM.
- ~300 líneas
- Ideal para aprendizaje
- Genera escenarios y tests simples
- Sin validación compleja
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.request import urlopen
import urllib.request as urllib_request


@dataclass
class TestScenario:
	"""Escenario de prueba generado."""
	name: str
	description: str
	inputs: dict[str, Any]
	expected_output: Any
	test_type: str  # 'happy_path', 'edge_case', 'error'


def get_llm_config() -> dict[str, str]:
	"""Obtiene configuración del LLM."""
	return {
		"base_url": os.getenv("LLM_BASE_URL", "http://localhost:8082/v1/messages"),
		"api_key": os.getenv("LLM_API_KEY", "freecc"),
		"model": os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022"),
	}


def call_llm(messages: list[dict[str, str]]) -> str:
	"""Llama al LLM y retorna la respuesta."""
	config = get_llm_config()
	
	system_message = ""
	user_messages = []
	
	for msg in messages:
		if msg["role"] == "system":
			system_message = msg["content"]
		else:
			user_messages.append({"role": msg["role"], "content": msg["content"]})
	
	body = {
		"model": config["model"],
		"max_tokens": 4096,
		"messages": user_messages,
		"temperature": 0.3,
	}
	if system_message:
		body["system"] = system_message
	
	headers = {"x-api-key": config["api_key"]}
	
	data = json.dumps(body).encode("utf-8")
	request_headers = {"Content-Type": "application/json"}
	request_headers.update(headers)
	request = urllib_request.Request(
		config["base_url"],
		data=data,
		headers=request_headers,
		method="POST"
	)
	
	with urlopen(request, timeout=60) as response:
		response_text = response.read().decode("utf-8")
	
	# Manejar SSE o JSON normal
	if response_text.strip().startswith("event:"):
		text_content = ""
		for line in response_text.strip().split("\n"):
			if line.startswith("data:"):
				try:
					data_json = json.loads(line[5:].strip())
					if "delta" in data_json and "text" in data_json["delta"]:
						text_content += data_json["delta"]["text"]
				except:
					pass
		return text_content
	else:
		result = json.loads(response_text)
		content = result.get("content", [])
		if content and isinstance(content, list):
			return str(content[0].get("text", ""))
	
	return ""


class TestScenarioGenerator:
	"""Generador básico de escenarios de prueba."""
	
	def __init__(self):
		"""Inicializa el generador."""
		self.scenarios: list[TestScenario] = []
	
	def analyze_function(self, function_spec: str) -> list[TestScenario]:
		"""Analiza una especificación de función y genera escenarios.
		
		Args:
			function_spec: Descripción de la función (nombre, parámetros, comportamiento)
		
		Returns:
			Lista de escenarios de prueba
		"""
		print("\n🔍 Analizando función...", end=" ")
		
		prompt = f"""Analiza esta especificación de función y genera 5 escenarios de prueba:

ESPECIFICACIÓN:
{function_spec}

Genera escenarios en JSON con esta estructura:
{{
	"scenarios": [
		{{
			"name": "nombre_del_escenario",
			"description": "descripción breve",
			"test_type": "happy_path|edge_case|error",
			"inputs": {{"param1": valor, "param2": valor}},
			"expected_output": resultado_esperado
		}}
	]
}}

Sé concreto y específico en los valores."""
		
		try:
			response = call_llm([
				{
					"role": "system",
					"content": "Eres un experto en testing. Genera escenarios de prueba siguiendo exactamente el formato JSON solicitado."
				},
				{"role": "user", "content": prompt}
			])
			
			# Extraer JSON de la respuesta
			json_start = response.find("{")
			json_end = response.rfind("}") + 1
			
			if json_start >= 0 and json_end > json_start:
				json_str = response[json_start:json_end]
				data = json.loads(json_str)
				
				self.scenarios = []
				for scenario_data in data.get("scenarios", []):
					scenario = TestScenario(
						name=scenario_data.get("name", "test"),
						description=scenario_data.get("description", ""),
						inputs=scenario_data.get("inputs", {}),
						expected_output=scenario_data.get("expected_output", None),
						test_type=scenario_data.get("test_type", "happy_path")
					)
					self.scenarios.append(scenario)
				
				print(f"✓ ({len(self.scenarios)} escenarios)")
				return self.scenarios
		except Exception as e:
			print(f"✗ Error: {e}")
			return []
	
	def generate_test_code(self, function_name: str, module_name: str = "mymodule") -> str:
		"""Genera código de tests basado en los escenarios.
		
		Args:
			function_name: Nombre de la función a testear
			module_name: Nombre del módulo (default: mymodule)
		
		Returns:
			Código Python de tests
		"""
		if not self.scenarios:
			return "# No hay escenarios para generar tests"
		
		print("\n📝 Generando tests...", end=" ")
		
		code = f'''"""Tests para {function_name}"""

import pytest
from {module_name} import {function_name}


'''
		
		for scenario in self.scenarios:
			test_name = f"test_{scenario.name}"
			
			# Happy path
			if scenario.test_type == "happy_path":
				code += f'''def {test_name}():
	"""Test: {scenario.description}"""
	# Entrada
	inputs = {repr(scenario.inputs)}
	
	# Ejecutar
	result = {function_name}(**inputs)
	
	# Verificar
	assert result == {repr(scenario.expected_output)}, f"Esperado {repr(scenario.expected_output)}, obtuvo {{result}}"

'''
			
			# Edge cases
			elif scenario.test_type == "edge_case":
				code += f'''def {test_name}():
	"""Test: {scenario.description}"""
	# Entrada (caso límite)
	inputs = {repr(scenario.inputs)}
	
	# Ejecutar
	result = {function_name}(**inputs)
	
	# Verificar comportamiento en caso límite
	assert result == {repr(scenario.expected_output)}

'''
			
			# Error cases
			elif scenario.test_type == "error":
				code += f'''def {test_name}():
	"""Test: {scenario.description}"""
	# Verificar que lanza excepción
	with pytest.raises({scenario.expected_output}):
		inputs = {repr(scenario.inputs)}
		{function_name}(**inputs)

'''
		
		print("✓")
		return code
	
	def display_scenarios(self) -> None:
		"""Muestra los escenarios generados."""
		if not self.scenarios:
			print("No hay escenarios generados")
			return
		
		print(f"\n{'='*70}")
		print(f"ESCENARIOS GENERADOS ({len(self.scenarios)})")
		print(f"{'='*70}\n")
		
		for i, scenario in enumerate(self.scenarios, 1):
			print(f"📋 Escenario {i}: {scenario.name}")
			print(f"   Tipo: {scenario.test_type}")
			print(f"   Descripción: {scenario.description}")
			print(f"   Entrada: {scenario.inputs}")
			print(f"   Esperado: {scenario.expected_output}")
			print()


def main():
	"""Ejemplo de uso."""
	# Especificación de función
	function_spec = """
	Función: calculate_discount
	Parámetros:
	- price (float): Precio del producto
	- customer_type (str): Tipo de cliente ('regular', 'vip', 'corporate')
	
	Comportamiento:
	- Si price < 0: Lanza ValueError
	- Si customer_type es 'regular': sin descuento (0%)
	- Si customer_type es 'vip': 10% descuento
	- Si customer_type es 'corporate': 15% descuento
	- Retorna el precio final (price con descuento aplicado)
	"""
	
	# Crear generador
	generator = TestScenarioGenerator()
	
	# Analizar y generar escenarios
	scenarios = generator.analyze_function(function_spec)
	
	# Mostrar escenarios
	generator.display_scenarios()
	
	# Generar tests
	test_code = generator.generate_test_code("calculate_discount", "commerce_module")
	
	print("\n" + "="*70)
	print("CÓDIGO DE TESTS GENERADO")
	print("="*70 + "\n")
	print(test_code)
	
	# Guardar a archivo
	with open("test_calculate_discount.py", "w") as f:
		f.write(test_code)
	
	print("✅ Tests guardados en: test_calculate_discount.py")


if __name__ == "__main__":
	main()
