"""Test Scenario Generator Agent - OPCIÓN C (With RAG Learning)

Generador avanzado que aprende de tests existentes usando RAG.
- ~800 líneas
- Análisis semántico de tests históricos
- Mejora iterativa de escenarios
- Recomendaciones basadas en patrones
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any
from enum import Enum
from pathlib import Path
from urllib.request import urlopen
import urllib.request as urllib_request

try:
	import chromadb
except ImportError:
	chromadb = None

try:
	from PyPDF2 import PdfReader
except ImportError:
	PdfReader = None


class TestType(str, Enum):
	"""Tipos de pruebas."""
	HAPPY_PATH = "happy_path"
	EDGE_CASE = "edge_case"
	BOUNDARY = "boundary"
	ERROR = "error"
	PERFORMANCE = "performance"
	SECURITY = "security"


@dataclass
class TestExample:
	"""Ejemplo de test existente extraído para aprendizaje."""
	name: str
	code: str
	test_type: TestType
	description: str
	source_file: str


@dataclass
class TestScenario:
	"""Escenario de prueba mejorado por RAG."""
	name: str
	description: str
	inputs: dict[str, Any]
	expected_output: Any
	test_type: TestType
	priority: int = 1
	tags: list[str] = field(default_factory=list)
	preconditions: list[str] = field(default_factory=list)
	postconditions: list[str] = field(default_factory=list)
	learned_from: list[str] = field(default_factory=list)  # Referencia a tests de los que aprendió
	confidence_score: float = 1.0
	is_valid: bool = True
	validation_errors: list[str] = field(default_factory=list)
	
	def validate(self) -> bool:
		"""Valida el escenario."""
		self.validation_errors = []
		
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


class TestLibrary:
	"""Almacén vectorial de tests históricos usando Chroma."""
	
	def __init__(self, db_path: str = ".test_chroma"):
		"""Inicializa el almacén de tests."""
		if chromadb is None:
			raise ImportError("chromadb no está instalado")
		
		self.db_path = db_path
		self.client = chromadb.PersistentClient(path=db_path)
		self.collection = self.client.get_or_create_collection(
			name="test_examples",
			metadata={"hnsw:space": "cosine"}
		)
		self.examples: list[TestExample] = []
	
	def index_test_files(self, folder: str) -> int:
		"""Indexa archivos de tests desde una carpeta."""
		print(f"\n📚 Indexando tests desde {folder}...", end=" ")
		
		test_folder = Path(folder)
		if not test_folder.exists():
			print(f"✗ Carpeta no existe")
			return 0
		
		test_files = list(test_folder.glob("test_*.py")) + list(test_folder.glob("*_test.py"))
		if not test_files:
			print("✗ No se encontraron archivos test")
			return 0
		
		count = 0
		for test_file in test_files:
			try:
				with open(test_file, "r") as f:
					content = f.read()
				
				# Extraer funciones de test
				import re
				test_functions = re.findall(r'def (test_\w+)\([^)]*\):.*?(?=\n    def |\nclass |\Z)', content, re.DOTALL)
				
				for func_name in test_functions[:5]:  # Máximo 5 por archivo
					doc_id = f"{test_file.name}_{func_name}"
					
					self.collection.upsert(
						ids=[doc_id],
						documents=[content[:500]],  # Primeros 500 chars
						metadatas={
							"source": str(test_file.name),
							"function": func_name
						}
					)
					count += 1
			except Exception as e:
				pass
		
		print(f"✓ ({count} tests indexados)")
		return count
	
	def search_similar_tests(self, query: str, top_k: int = 3) -> list[dict[str, str]]:
		"""Busca tests similares en la biblioteca."""
		results = self.collection.query(
			query_texts=[query],
			n_results=top_k
		)
		
		documents = []
		if results["documents"] and len(results["documents"]) > 0:
			for i, doc in enumerate(results["documents"][0]):
				metadata = results["metadatas"][0][i] if results["metadatas"] else {}
				documents.append({
					"content": doc,
					"source": metadata.get("source", "unknown"),
					"function": metadata.get("function", "unknown"),
				})
		
		return documents


class TestScenarioGeneratorWithRAG:
	"""Generador de escenarios que aprende de tests históricos."""
	
	def __init__(self, test_folder: str = "tests"):
		"""Inicializa el generador con RAG."""
		self.scenarios: list[TestScenario] = []
		self.function_spec: str = ""
		self.test_library = TestLibrary()
		
		# Indexar tests existentes
		self.test_library.index_test_files(test_folder)
	
	def _extract_patterns_from_similar_tests(self, function_spec: str) -> str:
		"""Extrae patrones de tests similares."""
		print("🔍 Buscando patrones en tests históricos...", end=" ")
		
		similar_tests = self.test_library.search_similar_tests(function_spec, top_k=5)
		
		if not similar_tests:
			print("(ninguno)")
			return ""
		
		patterns = "Tests similares encontrados:\n"
		for test in similar_tests:
			patterns += f"\n- {test['source']}::{test['function']}\n"
			patterns += f"  {test['content'][:200]}...\n"
		
		print(f"✓ ({len(similar_tests)} encontrados)")
		return patterns
	
	def analyze_function(self, function_spec: str) -> list[TestScenario]:
		"""Analiza función y genera escenarios mejorados por RAG."""
		self.function_spec = function_spec
		print("\n🔍 Analizando función con contexto de tests históricos...", end=" ")
		
		# Obtener patrones similares
		similar_patterns = self._extract_patterns_from_similar_tests(function_spec)
		
		context = f"Contexto de tests históricos similar:\n{similar_patterns}\n" if similar_patterns else ""
		
		prompt = f"""Analiza esta especificación y APRENDE de los tests históricos similares para generar escenarios mejorados:

ESPECIFICACIÓN:
{function_spec}

{context}

Basándote en los tests históricos similares, genera escenarios en JSON:
{{
	"scenarios": [
		{{
			"name": "nombre_descriptivo",
			"description": "descripción clara",
			"test_type": "happy_path|edge_case|boundary|error|performance|security",
			"priority": 1-5,
			"inputs": {{"param1": valor}},
			"expected_output": resultado,
			"tags": ["tag1", "tag2"],
			"preconditions": ["precondición"],
			"postconditions": ["postcondición"],
			"learned_from": ["referencia a test similar"],
			"confidence_score": 0.0-1.0
		}}
	]
}}

Genera al menos 10 escenarios, incluyendo tipos que viste en tests históricos.
Usa confidence_score alto para escenarios que coinciden con patrones históricos.
Incluye security tests si los tests históricos tienen validación."""
		
		try:
			response = call_llm([
				{
					"role": "system",
					"content": "Eres un QA engineer experto que aprende de tests históricos. Genera escenarios mejorados basado en patrones similares."
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
						postconditions=scenario_data.get("postconditions", []),
						learned_from=scenario_data.get("learned_from", []),
						confidence_score=scenario_data.get("confidence_score", 1.0)
					)
					
					if scenario.validate():
						self.scenarios.append(scenario)
				
				print(f"✓ ({len(self.scenarios)} escenarios)")
				return self.scenarios
		except Exception as e:
			print(f"✗ Error: {e}")
			return []
	
	def generate_test_code(self, function_name: str, module_name: str = "mymodule") -> str:
		"""Genera tests con comentarios sobre aprendizaje."""
		if not self.scenarios:
			return "# No hay escenarios para generar tests"
		
		print("\n📝 Generando tests (mejorados con RAG)...", end=" ")
		
		code = f'''"""Tests para {function_name}

Generado con aprendizaje de tests históricos (RAG).
Los tests incluyen patrones encontrados en bases de datos similares.
"""

import pytest
from {module_name} import {function_name}


class Test{function_name.title().replace('_', '')}:
	"""Suite de tests mejorada con patrones históricos."""
	
'''
		
		# Agrupar por tipo
		for test_type in [TestType.HAPPY_PATH, TestType.EDGE_CASE, 
		                   TestType.BOUNDARY, TestType.ERROR, TestType.SECURITY, TestType.PERFORMANCE]:
			
			type_scenarios = [s for s in self.scenarios if s.test_type == test_type]
			if not type_scenarios:
				continue
			
			code += f"\n	# --- {test_type.value.upper().replace('_', ' ')} ---\n"
			
			for scenario in type_scenarios:
				test_name = f"test_{scenario.name}"
				
				code += f"\n	def {test_name}(self):\n"
				code += f'\t\t"""Test: {scenario.description}\n'
				code += f'\t\tPriority: {scenario.priority}/5\n'
				code += f'\t\tConfidence (from historical patterns): {scenario.confidence_score:.2f}\n'
				
				if scenario.learned_from:
					code += f'\t\tLearned from: {", ".join(scenario.learned_from[:2])}\n'
				
				code += f'\t\t"""\n'
				
				# Precondiciones
				if scenario.preconditions:
					code += f"\t\t# Precondiciones\n"
					for precond in scenario.preconditions:
						code += f"\t\t# {precond}\n"
				
				code += f"\t\t# Arrange\n"
				code += f"\t\tinputs = {repr(scenario.inputs)}\n"
				
				code += f"\t\t# Act\n"
				code += f"\t\tresult = {function_name}(**inputs)\n"
				
				code += f"\t\t# Assert\n"
				
				if test_type == TestType.ERROR or test_type == TestType.SECURITY:
					code += f"\t\twith pytest.raises({scenario.expected_output}):\n"
					code += f"\t\t\t{function_name}(**inputs)\n"
				else:
					code += f"\t\texpected = {repr(scenario.expected_output)}\n"
					code += f"\t\tassert result == expected\n"
				
				if scenario.postconditions:
					code += f"\t\t# Postcondiciones\n"
					for postcond in scenario.postconditions:
						code += f"\t\t# {postcond}\n"
		
		print("✓")
		return code
	
	def generate_learning_report(self) -> str:
		"""Genera reporte de lo que aprendió del historial."""
		high_confidence = len([s for s in self.scenarios if s.confidence_score >= 0.8])
		medium_confidence = len([s for s in self.scenarios if 0.5 <= s.confidence_score < 0.8])
		low_confidence = len([s for s in self.scenarios if s.confidence_score < 0.5])
		
		learned_sources = set()
		for scenario in self.scenarios:
			learned_sources.update(scenario.learned_from)
		
		report = f"""
{'='*70}
RAG LEARNING REPORT
{'='*70}

📚 APRENDIZAJE DE TESTS HISTÓRICOS
{'─'*70}
Escenarios con confianza ALTA (>0.8):     {high_confidence}
Escenarios con confianza MEDIA (0.5-0.8): {medium_confidence}
Escenarios con confianza BAJA (<0.5):     {low_confidence}

Fuentes aprendidas: {len(learned_sources)}
"""
		
		if learned_sources:
			report += "\nPatrones encontrados en:\n"
			for source in sorted(learned_sources):
				report += f"  • {source}\n"
		
		report += f"\n{'='*70}\n"
		
		return report
	
	def display_scenarios(self) -> None:
		"""Muestra escenarios con información de aprendizaje."""
		if not self.scenarios:
			print("No hay escenarios")
			return
		
		print(f"\n{'='*70}")
		print(f"ESCENARIOS CON APRENDIZAJE RAG ({len(self.scenarios)})")
		print(f"{'='*70}\n")
		
		for scenario in self.scenarios:
			confidence_bar = "█" * int(scenario.confidence_score * 10) + "░" * (10 - int(scenario.confidence_score * 10))
			
			print(f"📋 {scenario.name}")
			print(f"   Tipo: {scenario.test_type.value}")
			print(f"   Confianza: [{confidence_bar}] {scenario.confidence_score:.2f}")
			print(f"   Descripción: {scenario.description}")
			print(f"   Entrada: {scenario.inputs}")
			print(f"   Esperado: {scenario.expected_output}")
			
			if scenario.learned_from:
				print(f"   Aprendido de: {', '.join(scenario.learned_from)}")
			
			print()


def main():
	"""Ejemplo de uso con RAG."""
	function_spec = """
	Función: calculate_discount
	Parámetros:
	- price (float): Precio del producto
	- customer_type (str): Tipo de cliente ('regular', 'vip', 'corporate')
	Comportamiento:
	- Si price < 0: Lanza ValueError
	- Si customer_type inválido: Lanza ValueError
	- Aplica descuentos: regular 0%, vip 10%, corporate 15%
	- Retorna precio final redondeado a 2 decimales
	"""
	
	try:
		# Crear generador con RAG
		generator = TestScenarioGeneratorWithRAG("tests")
		
		# Analizar función
		scenarios = generator.analyze_function(function_spec)
		
		# Mostrar escenarios
		generator.display_scenarios()
		
		# Generar reportes
		print(generator.generate_learning_report())
		
		# Generar tests
		test_code = generator.generate_test_code("calculate_discount", "commerce")
		
		print("CÓDIGO GENERADO")
		print("="*70 + "\n")
		print(test_code)
		
		# Guardar
		with open("test_calculate_discount_rag.py", "w") as f:
			f.write(test_code)
		
		print("\n✅ Tests generados con RAG: test_calculate_discount_rag.py")
		
	except ImportError as e:
		print(f"✗ Error: {e}")
		print("Instala chromadb: pip install chromadb")


if __name__ == "__main__":
	main()
