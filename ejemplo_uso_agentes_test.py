"""Ejemplos de Uso para los 3 Test Scenario Generators

Demuestra cómo usar cada opción (A, B, C) con ejemplos prácticos.
"""

from pathlib import Path
import sys

# Importar los agentes
try:
	from test_scenario_agent_a import TestScenarioGenerator as GeneratorA
	from test_scenario_agent_b import TestScenarioGenerator as GeneratorB
	from test_scenario_agent_c import TestScenarioGeneratorWithRAG as GeneratorC
except ImportError as e:
	print(f"Error importando módulos: {e}")
	sys.exit(1)


# Especificaciones de ejemplo
FUNCTION_SPEC_SIMPLE = """
Función: validate_email
Parámetros:
- email (str): Dirección de correo electrónico
Comportamiento:
- Retorna True si el email es válido
- Retorna False si el email es inválido
- Debe contener @ y dominio válido
- No acepta espacios
"""

FUNCTION_SPEC_COMPLETE = """
Función: process_payment
Parámetros:
- amount (float): Cantidad a procesar (debe ser > 0)
- currency (str): Moneda ('USD', 'EUR', 'COP')
- card_number (str): Número de tarjeta (16 dígitos)
- card_cvv (str): CVV (3 dígitos)

Comportamiento:
- Si amount <= 0: Lanza ValueError("Amount must be positive")
- Si currency no está en lista: Lanza ValueError("Invalid currency")
- Si card_number no es 16 dígitos: Lanza ValueError("Invalid card")
- Si card_cvv no es 3 dígitos: Lanza ValueError("Invalid CVV")
- Si todo es válido: Retorna dict con status='success' y transaction_id
- Debe validar formato de tarjeta (Visa/Mastercard)

Restricciones:
- Máximo $10,000 por transacción
- Mínimo $0.01
- Requiere validación de seguridad
"""

FUNCTION_SPEC_CALCULATOR = """
Función: fibonacci
Parámetros:
- n (int): Posición en la serie Fibonacci (n >= 0)

Comportamiento:
- Si n < 0: Lanza ValueError("n must be non-negative")
- Si n == 0: Retorna 0
- Si n == 1: Retorna 1
- Si n > 1: Retorna fibonacci(n-1) + fibonacci(n-2)
- Debe retornar enteros
- Debe ser eficiente para n hasta 100

Casos especiales:
- n = 0 → 0
- n = 1 → 1
- n = 10 → 55
- n = 20 → 6765
"""


def ejemplo_opcion_a():
	"""Ejemplo: Opción A - Quick & Simple"""
	print("\n" + "="*70)
	print("EJEMPLO: OPCIÓN A (Quick & Simple)")
	print("="*70)
	print("✓ Generador básico")
	print("✓ ~300 líneas")
	print("✓ Ideal para aprendizaje")
	print("✓ Rápido y directo\n")
	
	generator = GeneratorA()
	
	print("📌 Caso de uso: validate_email")
	print("-" * 70)
	
	scenarios = generator.analyze_function(FUNCTION_SPEC_SIMPLE)
	generator.display_scenarios()
	
	test_code = generator.generate_test_code("validate_email", "validators_module")
	
	print("\n📄 Código generado (primeras líneas):")
	print(test_code[:500] + "\n...")
	
	# Guardar
	output_file = "example_a_tests.py"
	with open(output_file, "w") as f:
		f.write(test_code)
	print(f"✅ Guardado en: {output_file}\n")


def ejemplo_opcion_b():
	"""Ejemplo: Opción B - Complete & Professional"""
	print("\n" + "="*70)
	print("EJEMPLO: OPCIÓN B (Complete & Professional)")
	print("="*70)
	print("✓ Generador profesional")
	print("✓ ~600 líneas")
	print("✓ Validación completa")
	print("✓ Reportes detallados\n")
	
	generator = GeneratorB()
	
	print("📌 Caso de uso: process_payment")
	print("-" * 70)
	
	scenarios = generator.analyze_function(FUNCTION_SPEC_COMPLETE)
	generator.display_scenarios()
	
	# Analizar cobertura
	print(generator.generate_report())
	
	test_code = generator.generate_test_code("process_payment", "payment_module")
	
	# Guardar
	output_file = "example_b_tests.py"
	with open(output_file, "w") as f:
		f.write(test_code)
	
	output_json = "example_b_scenarios.json"
	generator.save_to_file(output_json)
	
	print(f"✅ Archivos guardados:")
	print(f"   • {output_file}")
	print(f"   • {output_json}\n")


def ejemplo_opcion_c():
	"""Ejemplo: Opción C - With RAG Learning"""
	print("\n" + "="*70)
	print("EJEMPLO: OPCIÓN C (With RAG Learning)")
	print("="*70)
	print("✓ Generador con RAG")
	print("✓ ~800 líneas")
	print("✓ Aprende de tests históricos")
	print("✓ Mejora iterativa\n")
	
	try:
		generator = GeneratorC("tests")
		
		print("📌 Caso de uso: fibonacci")
		print("-" * 70)
		
		scenarios = generator.analyze_function(FUNCTION_SPEC_CALCULATOR)
		generator.display_scenarios()
		
		# Generar reporte de aprendizaje
		print(generator.generate_learning_report())
		
		test_code = generator.generate_test_code("fibonacci", "math_module")
		
		# Guardar
		output_file = "example_c_tests.py"
		with open(output_file, "w") as f:
			f.write(test_code)
		
		print(f"✅ Archivos guardados:")
		print(f"   • {output_file}\n")
		
	except ImportError as e:
		print(f"⚠ RAG requiere chromadb: {e}")
		print("   Instala: pip install chromadb")
		print("   Luego intenta de nuevo\n")


def comparativa_opciones():
	"""Muestra comparativa de las 3 opciones"""
	print("\n" + "="*70)
	print("COMPARATIVA DE LAS 3 OPCIONES")
	print("="*70)
	
	comparacion = """
┌─────────────────────┬──────────┬────────────┬───────────────┐
│ Característica      │ Opción A │ Opción B   │ Opción C      │
├─────────────────────┼──────────┼────────────┼───────────────┤
│ Líneas de código    │ ~300     │ ~600       │ ~800          │
│ Dificultad          │ Fácil    │ Media      │ Difícil       │
│ Validación          │ Básica   │ Completa   │ Completa + RAG│
│ Cobertura           │ Simple   │ Análisis   │ Análisis + ML │
│ Reportes            │ No       │ Sí         │ Sí (avanzado) │
│ JSON export         │ No       │ Sí         │ Sí            │
│ Aprendizaje         │ No       │ No         │ Sí (histórico)│
│ Confianza scores    │ No       │ No         │ Sí            │
│ Tiempo ejecución    │ Rápido   │ Normal     │ Lento (RAG)   │
│ Caso de uso ideal   │ Inicio   │ Producción │ Empresa grade │
└─────────────────────┴──────────┴────────────┴───────────────┘
"""
	print(comparacion)
	
	recomendaciones = """
RECOMENDACIONES:

✅ Usa OPCIÓN A si:
   • Estás aprendiendo testing
   • Necesitas generar tests rápido
   • Funciones simples
   • No necesitas análisis profundo

✅ Usa OPCIÓN B si:
   • Necesitas tests production-ready
   • Quieres análisis de cobertura
   • Requieres validación completa
   • Prefieres exportar a JSON

✅ Usa OPCIÓN C si:
   • Tu empresa tiene tests históricos
   • Quieres mejorar con IA
   • Necesitas confidence scores
   • Buscas machine learning en tests
"""
	print(recomendaciones)


def main():
	"""Ejecuta los ejemplos"""
	import argparse
	
	parser = argparse.ArgumentParser(description="Test Scenario Generator - Ejemplos")
	parser.add_argument("--opcion", choices=["a", "b", "c", "todas", "comparar"],
	                    default="todas",
	                    help="Qué ejemplo ejecutar")
	
	args = parser.parse_args()
	
	print("\n" + "="*70)
	print("TEST SCENARIO GENERATOR - EJEMPLOS DE USO")
	print("="*70)
	
	try:
		if args.opcion in ["a", "todas"]:
			ejemplo_opcion_a()
		
		if args.opcion in ["b", "todas"]:
			ejemplo_opcion_b()
		
		if args.opcion in ["c", "todas"]:
			ejemplo_opcion_c()
		
		if args.opcion == "comparar" or args.opcion == "todas":
			comparativa_opciones()
		
		print("\n" + "="*70)
		print("✅ Ejemplos completados")
		print("="*70)
		
	except Exception as e:
		print(f"\n❌ Error: {e}")
		import traceback
		traceback.print_exc()


if __name__ == "__main__":
	main()
