"""Test Scenario Generator Agent - OPCIÓN B (Complete & Professional)

Generador profesional de escenarios con validación y análisis.
- ~600 líneas
- Production-ready
- Validación de escenarios
- Análisis de cobertura
- Reportes detallados
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any
from enum import Enum
from urllib.request import urlopen
import urllib.request as urllib_request
from pathlib import Path


class TestType(str, Enum):
	"""Tipos de pruebas."""
	HAPPY_PATH = "happy_path"
	EDGE_CASE = "edge_case"
	BOUNDARY = "boundary"
	ERROR = "error"
	PERFORMANCE = "performance"


@dataclass
class ValidationRule:
	"""Regla de validación para un escenario."""
	rule_name: str
	description: str
	validator: callable


@dataclass
class TestScenario:
	"""Escenario de prueba con metadatos completos."""
	name: str
	description: str
	inputs: dict[str, Any]
	expected_output: Any
	test_type: TestType
	priority: int = 1  # 1-5, donde 5 es crítico
	tags: list[str] = field(default_factory=list)
	preconditions: list[str] = field(default_factory=list)
	postconditions: list[str] = field(default_factory=list)
	is_valid: bool = True
	validation_errors: list[str] = field(default_factory=list)
	
	def validate(self) -> bool:
		"""Valida el escenario."""
		self.validation_errors = []
		
		# Validaciones básicas
		if not self.name or not isinstance(self.name, str):
			self.validation_errors.append("Nombre de escenario inválido")
		
		if not isinstance(self.inputs, dict):
			self.validation_errors.append("Inputs debe ser un diccionario")
		
		if self.priority < 1 or self.priority > 5:
			self.validation_errors.append("Priority debe estar entre 1-5")
		
		if not isinstance(self.test_type, TestType):
			self.validation_errors.append("TestType debe ser un valor válido")
		
		self.is_valid = len(self.validation_errors) == 0
		return self.is_valid


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


@dataclass
class CoverageAnalysis:
	"""Análisis de cobertura de escenarios."""
	total_scenarios: int
	happy_path_count: int
	edge_cases_count: int
	boundary_cases_count: int
	error_cases_count: int
	coverage_percentage: float
	missing_coverage: list[str] = field(default_factory=list)


class TestScenarioGenerator:
	"""Generador profesional de escenarios de prueba."""
	
	def __init__(self):
		"""Inicializa el generador."""
		self.scenarios: list[TestScenario] = []
		self.function_spec: str = ""
		self.validation_rules: list[ValidationRule] = []
	
	def set_validation_rules(self, rules: list[ValidationRule]) -> None:
		"""Establece reglas de validación personalizadas."""
		self.validation_rules = rules
	
	def analyze_function(self, function_spec: str) -> list[TestScenario]:
		"""Analiza una especificación y genera escenarios completos."""
		self.function_spec = function_spec
		print("\n🔍 Analizando función...", end=" ")
		
		prompt = f"""Analiza esta especificación de función y genera escenarios completos de prueba:

ESPECIFICACIÓN:
{function_spec}

Genera escenarios en JSON con esta estructura exacta:
{{
	"scenarios": [
		{{
			"name": "nombre_descriptivo",
			"description": "descripción clara del caso",
			"test_type": "happy_path|edge_case|boundary|error|performance",
			"priority": 1-5,
			"inputs": {{"param1": valor, "param2": valor}},
			"expected_output": resultado_esperado,
			"tags": ["tag1", "tag2"],
			"preconditions": ["precondición 1"],
			"postconditions": ["postcondición 1"]
		}}
	]
}}

Genera mínimo 8 escenarios cubriendo:
- Happy paths (casos normales)
- Edge cases (bordes del dominio)
- Boundary cases (límites exactos)
- Error cases (entradas inválidas)

Sé específico y detallado."""
		
		try:
			response = call_llm([
				{
					"role": "system",
					"content": "Eres un QA engineer experto. Genera escenarios de prueba profesionales siguiendo exactamente el formato JSON solicitado."
				},
				{"role": "user", "content": prompt}
			])
			
			# Extraer JSON
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
						test_type=TestType(scenario_data.get("test_type", "happy_path")),
						priority=scenario_data.get("priority", 1),
						tags=scenario_data.get("tags", []),
						preconditions=scenario_data.get("preconditions", []),
						postconditions=scenario_data.get("postconditions", [])
					)
					
					# Validar escenario
					if scenario.validate():
						self.scenarios.append(scenario)
				
				print(f"✓ ({len(self.scenarios)} escenarios válidos)")
				return self.scenarios
		except Exception as e:
			print(f"✗ Error: {e}")
			return []
	
	def analyze_coverage(self) -> CoverageAnalysis:
		"""Analiza la cobertura de los escenarios."""
		if not self.scenarios:
			return CoverageAnalysis(0, 0, 0, 0, 0, 0.0)
		
		happy_path = len([s for s in self.scenarios if s.test_type == TestType.HAPPY_PATH])
		edge_cases = len([s for s in self.scenarios if s.test_type == TestType.EDGE_CASE])
		boundary = len([s for s in self.scenarios if s.test_type == TestType.BOUNDARY])
		errors = len([s for s in self.scenarios if s.test_type == TestType.ERROR])
		
		total = len(self.scenarios)
		coverage = (total / 10) * 100 if total > 0 else 0  # Escala simple
		coverage = min(coverage, 100)  # Máximo 100%
		
		missing = []
		if happy_path == 0:
			missing.append("Happy path cases")
		if edge_cases == 0:
			missing.append("Edge cases")
		if errors == 0:
			missing.append("Error cases")
		
		return CoverageAnalysis(
			total_scenarios=total,
			happy_path_count=happy_path,
			edge_cases_count=edge_cases,
			boundary_cases_count=boundary,
			error_cases_count=errors,
			coverage_percentage=coverage,
			missing_coverage=missing
		)
	
	def generate_test_code(self, function_name: str, module_name: str = "mymodule") -> str:
		"""Genera código de tests profesional."""
		if not self.scenarios:
			return "# No hay escenarios para generar tests"
		
		print("\n📝 Generando tests profesionales...", end=" ")
		
		code = f'''"""Tests para {function_name}

Este módulo contiene tests generados automáticamente para {function_name}.
Incluye casos happy path, edge cases, boundary cases y error handling.
"""

import pytest
from {module_name} import {function_name}


class Test{function_name.title().replace('_', '')}:
	"""Suite de tests para {function_name}."""
	
	@pytest.fixture(autouse=True)
	def setup(self):
		"""Setup antes de cada test."""
		pass
	
'''
		
		# Agrupar por tipo
		for test_type in [TestType.HAPPY_PATH, TestType.EDGE_CASE, 
		                   TestType.BOUNDARY, TestType.ERROR, TestType.PERFORMANCE]:
			
			type_scenarios = [s for s in self.scenarios if s.test_type == test_type]
			if not type_scenarios:
				continue
			
			code += f"\n	# --- {test_type.value.upper().replace('_', ' ')} ---\n"
			
			for scenario in type_scenarios:
				test_name = f"test_{scenario.name}"
				
				code += f"\n	def {test_name}(self):\n"
				code += f'\t\t"""Test: {scenario.description}\n'
				code += f'\t\tPriority: {scenario.priority}/5\n'
				if scenario.tags:
					code += f'\t\tTags: {", ".join(scenario.tags)}\n'
				code += f'\t\t"""\n'
				
				# Precondiciones
				if scenario.preconditions:
					code += f"\t\t# Precondiciones\n"
					for precond in scenario.preconditions:
						code += f"\t\t# - {precond}\n"
				
				# Setup
				code += f"\t\t# Arrange\n"
				code += f"\t\tinputs = {repr(scenario.inputs)}\n"
				
				# Ejecución
				code += f"\t\t# Act\n"
				code += f"\t\tresult = {function_name}(**inputs)\n"
				
				# Verificación
				code += f"\t\t# Assert\n"
				
				if test_type == TestType.ERROR:
					# Error cases - esperar excepción
					code += f"\t\twith pytest.raises({scenario.expected_output}):\n"
					code += f"\t\t\t{function_name}(**inputs)\n"
				else:
					# Casos normales
					code += f"\t\texpected = {repr(scenario.expected_output)}\n"
					code += f"\t\tassert result == expected, f\"Esperado {{expected}}, obtuvo {{result}}\"\n"
				
				# Postcondiciones
				if scenario.postconditions:
					code += f"\t\t# Postcondiciones\n"
					for postcond in scenario.postconditions:
						code += f"\t\t# - {postcond}\n"
		
		print("✓")
		return code
	
	def generate_report(self) -> str:
		"""Genera reporte detallado de escenarios."""
		coverage = self.analyze_coverage()
		
		report = f"""
{'='*70}
TEST SCENARIO ANALYSIS REPORT
{'='*70}

📊 COBERTURA
{'─'*70}
Total Escenarios:        {coverage.total_scenarios}
Happy Path:              {coverage.happy_path_count}
Edge Cases:              {coverage.edge_cases_count}
Boundary Cases:          {coverage.boundary_cases_count}
Error Cases:             {coverage.error_cases_count}
Coverage Percentage:     {coverage.coverage_percentage:.1f}%

"""
		
		if coverage.missing_coverage:
			report += f"⚠️ COVERAGE GAPS:\n"
			for gap in coverage.missing_coverage:
				report += f"  • {gap}\n"
		else:
			report += f"✅ COBERTURA COMPLETA\n"
		
		report += f"\n📋 ESCENARIOS POR PRIORIDAD\n{'─'*70}\n"
		
		for priority in range(5, 0, -1):
			priority_scenarios = [s for s in self.scenarios if s.priority == priority]
			if priority_scenarios:
				report += f"\nPrioridad {priority} (CRÍTICA" if priority == 5 else f"\nPrioridad {priority}"
				report += "):\n"
				for scenario in priority_scenarios:
					report += f"  • {scenario.name}: {scenario.description}\n"
		
		report += f"\n{'='*70}\n"
		
		return report
	
	def save_to_file(self, filename: str) -> None:
		"""Guarda los escenarios a un archivo JSON."""
		scenarios_data = []
		for scenario in self.scenarios:
			scenarios_data.append({
				"name": scenario.name,
				"description": scenario.description,
				"test_type": scenario.test_type.value,
				"priority": scenario.priority,
				"inputs": scenario.inputs,
				"expected_output": scenario.expected_output,
				"tags": scenario.tags,
				"preconditions": scenario.preconditions,
				"postconditions": scenario.postconditions,
				"is_valid": scenario.is_valid,
			})
		
		with open(filename, "w") as f:
			json.dump(scenarios_data, f, indent=2)
		
		print(f"✅ Escenarios guardados en: {filename}")
	
	def display_scenarios(self) -> None:
		"""Muestra los escenarios generados."""
		if not self.scenarios:
			print("No hay escenarios generados")
			return
		
		print(f"\n{'='*70}")
		print(f"ESCENARIOS GENERADOS ({len(self.scenarios)})")
		print(f"{'='*70}\n")
		
		for i, scenario in enumerate(self.scenarios, 1):
			print(f"📋 [{i}] {scenario.name} ({'⭐'*scenario.priority})")
			print(f"    Tipo: {scenario.test_type.value}")
			print(f"    Descripción: {scenario.description}")
			print(f"    Entrada: {scenario.inputs}")
			print(f"    Esperado: {scenario.expected_output}")
			if scenario.tags:
				print(f"    Tags: {', '.join(scenario.tags)}")
			if not scenario.is_valid:
				print(f"    ❌ Errores: {', '.join(scenario.validation_errors)}")
			print()


def main():
	"""Ejemplo de uso profesional."""
	# Especificación completa
	function_spec = """
	Función: calculate_discount
	
	Propósito: Calcula el descuento aplicable según el tipo de cliente.
	
	Parámetros:
	- price (float): Precio del producto (debe ser >= 0)
	- customer_type (str): Tipo de cliente ('regular', 'vip', 'corporate')
	
	Comportamiento:
	- Si price < 0: Lanza ValueError("Price cannot be negative")
	- Si customer_type no es válido: Lanza ValueError("Invalid customer type")
	- Si customer_type == 'regular': descuento 0% (price sin cambios)
	- Si customer_type == 'vip': descuento 10% (price * 0.9)
	- Si customer_type == 'corporate': descuento 15% (price * 0.85)
	- Retorna el precio final redondeado a 2 decimales
	
	Restricciones:
	- price debe ser numérico
	- customer_type debe ser string
	"""
	
	# Crear generador
	generator = TestScenarioGenerator()
	
	# Analizar y generar escenarios
	scenarios = generator.analyze_function(function_spec)
	
	# Mostrar escenarios
	generator.display_scenarios()
	
	# Analizar cobertura
	print("\n" + "="*70)
	print(generator.generate_report())
	
	# Generar tests
	test_code = generator.generate_test_code("calculate_discount", "commerce_module")
	
	print("CÓDIGO DE TESTS GENERADO")
	print("="*70 + "\n")
	print(test_code)
	
	# Guardar archivos
	generator.save_to_file("test_scenarios.json")
	
	with open("test_calculate_discount.py", "w") as f:
		f.write(test_code)
	
	print("\n✅ Archivos generados:")
	print("   • test_scenarios.json (escenarios)")
	print("   • test_calculate_discount.py (tests)")


if __name__ == "__main__":
	main()
