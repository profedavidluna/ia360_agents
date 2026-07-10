#!/usr/bin/env python3
"""Script para probar diferentes configuraciones de chunks y embeddings."""

import os
import sys
import time
from main import RAGAgent


def test_configuration(name: str, chunk_size: int, chunk_overlap: int, top_k: int, embedding_model: str = "all-MiniLM-L6-v2"):
	"""Prueba una configuración específica."""
	
	print("\n" + "="*70)
	print(f"PRUEBA: {name}")
	print("="*70)
	print(f"chunk_size: {chunk_size}")
	print(f"chunk_overlap: {chunk_overlap}")
	print(f"top_k: {top_k}")
	print(f"embedding_model: {embedding_model}\n")
	
	# Configurar variables de entorno
	os.environ["RAG_CHUNK_SIZE"] = str(chunk_size)
	os.environ["RAG_CHUNK_OVERLAP"] = str(chunk_overlap)
	os.environ["RAG_TOP_K"] = str(top_k)
	os.environ["RAG_EMBEDDING_MODEL"] = embedding_model
	
	try:
		# Crear agente
		agent = RAGAgent()
		
		# Medir tiempo de indexación
		print("📄 Indexando...", end=" ")
		start = time.time()
		if agent.initialize() != 0:
			print("✗ Error")
			return None
		index_time = time.time() - start
		print(f"✓ ({index_time:.2f}s)")
		
		# Prueba de consultas
		test_questions = [
			"¿Qué es microservicios?",
			"¿Cuál es la arquitectura?",
			"¿Cómo se implementa?",
		]
		
		query_times = []
		print("\n📋 Pruebas de consulta:")
		
		for question in test_questions:
			print(f"  Q: {question[:40]}...", end=" ")
			start = time.time()
			reply = agent.answer_question(question)
			query_time = time.time() - start
			query_times.append(query_time)
			print(f"✓ ({query_time:.2f}s)")
		
		avg_query_time = sum(query_times) / len(query_times)
		
		# Resumen
		print(f"\n📊 Resultados:")
		print(f"  Indexación: {index_time:.2f}s")
		print(f"  Consulta promedio: {avg_query_time:.2f}s")
		print(f"  Tiempo total: {index_time + sum(query_times):.2f}s")
		
		return {
			"name": name,
			"index_time": index_time,
			"avg_query_time": avg_query_time,
			"total_time": index_time + sum(query_times)
		}
		
	except Exception as e:
		print(f"✗ Error: {e}")
		return None


def main():
	"""Ejecuta pruebas de configuración."""
	
	print("\n" + "="*70)
	print("PRUEBA DE CONFIGURACIONES RAG")
	print("="*70)
	print("\nEsto probará diferentes configuraciones de chunks y embeddings.")
	print("Los PDFs se re-indexarán para cada prueba.\n")
	
	results = []
	
	# Diferentes configuraciones a probar
	configs = [
		("Pequeños chunks (500)", 500, 100, 5),
		("Chunks medianos (1000, default)", 1000, 200, 5),
		("Chunks grandes (1500)", 1500, 300, 5),
		("Chunks muy grandes (2000)", 2000, 400, 5),
		("Más resultados (top_k=10)", 1000, 200, 10),
		("Menos resultados (top_k=3)", 1000, 200, 3),
	]
	
	for name, chunk_size, chunk_overlap, top_k in configs:
		result = test_configuration(name, chunk_size, chunk_overlap, top_k)
		if result:
			results.append(result)
		
		# Re-indexar para próxima prueba
		print("\n🔄 Preparando siguiente prueba...")
		from main import RAGConfig
		config = RAGConfig()
		agent = RAGAgent()
		agent.vector_store.clear()
		time.sleep(1)
	
	# Resumen comparativo
	print("\n" + "="*70)
	print("COMPARATIVA")
	print("="*70)
	print(f"\n{'Config':<35} {'Index':<10} {'Query':<10} {'Total':<10}")
	print("-" * 70)
	
	for r in results:
		print(f"{r['name']:<35} {r['index_time']:<10.2f} {r['avg_query_time']:<10.2f} {r['total_time']:<10.2f}")
	
	# Recomendación
	if results:
		fastest = min(results, key=lambda x: x["total_time"])
		print(f"\n✓ La configuración más rápida es: {fastest['name']}")
		print(f"  Tiempo total: {fastest['total_time']:.2f}s")


if __name__ == "__main__":
	main()
