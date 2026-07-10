#!/usr/bin/env python3
"""Script para explorar la base de datos vectorial de Chroma como una BD normal."""

import os
import sys
import json
from pathlib import Path
from tabulate import tabulate

try:
	import chromadb
except ImportError:
	print("✗ chromadb no está instalado. Instala con: pip install chromadb")
	sys.exit(1)

from main import RAGConfig


class RAGExplorer:
	"""Explorador de la base de datos vectorial."""
	
	def __init__(self):
		self.config = RAGConfig()
		self.client = chromadb.PersistentClient(path=self.config.chroma_db_path)
	
	def get_collection(self):
		"""Obtiene la colección de documentos."""
		try:
			return self.client.get_collection(name=self.config.collection_name)
		except Exception as e:
			print(f"✗ Error: No se encontró la colección. ¿Has indexado documentos?")
			print(f"  Ejecuta primero: python main.py --chat")
			return None
	
	def show_statistics(self):
		"""Muestra estadísticas de la BD."""
		collection = self.get_collection()
		if not collection:
			return
		
		print("\n" + "="*70)
		print("📊 ESTADÍSTICAS DE LA BASE DE DATOS")
		print("="*70)
		
		# Obtener todos los documentos
		all_docs = collection.get()
		
		total_documents = len(all_docs["ids"]) if all_docs["ids"] else 0
		
		# Contar por fuente
		sources = {}
		if all_docs["metadatas"]:
			for metadata in all_docs["metadatas"]:
				source = metadata.get("source", "unknown")
				sources[source] = sources.get(source, 0) + 1
		
		print(f"\n📁 Información General:")
		print(f"  Total de chunks: {total_documents}")
		print(f"  Archivos fuente: {len(sources)}")
		print(f"  Tamaño de embeddings: 384 dimensiones (all-MiniLM-L6-v2)")
		print(f"  Ubicación: {self.config.chroma_db_path}")
		
		print(f"\n📄 Distribución por archivo:")
		for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
			print(f"  • {source}: {count} chunks")
	
	def show_documents(self, limit: int = 10, source: str = None):
		"""Muestra documentos con formato de tabla."""
		collection = self.get_collection()
		if not collection:
			return
		
		print("\n" + "="*70)
		print("📋 DOCUMENTOS EN LA BASE DE DATOS")
		print("="*70)
		
		all_docs = collection.get()
		
		if not all_docs["ids"]:
			print("\n✗ No hay documentos indexados.")
			return
		
		# Filtrar por fuente si se especifica
		filtered_ids = []
		filtered_texts = []
		filtered_sources = []
		
		for i, doc_id in enumerate(all_docs["ids"]):
			metadata = all_docs["metadatas"][i] if all_docs["metadatas"] else {}
			source_name = metadata.get("source", "unknown")
			
			if source is None or source_name == source:
				filtered_ids.append(doc_id)
				filtered_texts.append(all_docs["documents"][i] if all_docs["documents"] else "")
				filtered_sources.append(source_name)
		
		# Limitar resultados
		filtered_ids = filtered_ids[:limit]
		filtered_texts = filtered_texts[:limit]
		filtered_sources = filtered_sources[:limit]
		
		# Crear tabla
		table_data = []
		for i, (doc_id, text, source_name) in enumerate(zip(filtered_ids, filtered_texts, filtered_sources), 1):
			# Truncar texto para la tabla
			text_preview = text[:60].replace("\n", " ") + ("..." if len(text) > 60 else "")
			table_data.append([i, doc_id[:40] + "..." if len(doc_id) > 40 else doc_id, text_preview, source_name])
		
		headers = ["#", "ID", "Texto (preview)", "Fuente"]
		print(f"\nMostrando {len(filtered_ids)} de {len(all_docs['ids'])} documentos:")
		print(tabulate(table_data, headers=headers, tablefmt="grid"))
	
	def show_document_detail(self, doc_id: str):
		"""Muestra detalles completos de un documento."""
		collection = self.get_collection()
		if not collection:
			return
		
		try:
			result = collection.get(ids=[doc_id], include=["documents", "metadatas", "embeddings"])
			
			if not result["ids"]:
				print(f"\n✗ Documento no encontrado: {doc_id}")
				return
			
			doc_text = result["documents"][0] if result["documents"] else ""
			metadata = result["metadatas"][0] if result["metadatas"] else {}
			embedding = result["embeddings"][0] if result["embeddings"] else None
			
			print("\n" + "="*70)
			print("📄 DETALLES DEL DOCUMENTO")
			print("="*70)
			print(f"\nID: {doc_id}")
			print(f"Fuente: {metadata.get('source', 'unknown')}")
			print(f"\n📝 Texto:")
			print("-" * 70)
			print(doc_text[:500])
			if len(doc_text) > 500:
				print(f"\n... ({len(doc_text) - 500} caracteres más)")
			print("-" * 70)
			
			if embedding:
				print(f"\n🔢 Embedding:")
				print(f"  Dimensiones: {len(embedding)}")
				print(f"  Primeros 10 valores: {embedding[:10]}")
				print(f"  Últimos 10 valores: {embedding[-10:]}")
		
		except Exception as e:
			print(f"✗ Error: {e}")
	
	def search_and_show(self, query: str, limit: int = 5):
		"""Busca y muestra resultados con scores."""
		collection = self.get_collection()
		if not collection:
			return
		
		print("\n" + "="*70)
		print("🔍 RESULTADOS DE BÚSQUEDA")
		print("="*70)
		print(f"\nBúsqueda: {query}\n")
		
		results = collection.query(
			query_texts=[query],
			n_results=limit,
			include=["documents", "metadatas", "distances"]
		)
		
		if not results["ids"][0]:
			print("✗ No se encontraron resultados.")
			return
		
		table_data = []
		for i, (doc_id, text, metadata, distance) in enumerate(zip(
			results["ids"][0],
			results["documents"][0],
			results["metadatas"][0],
			results["distances"][0]
		), 1):
			# Calcular similaridad (1 - distance para cosine)
			similarity = 1 - distance
			text_preview = text[:50].replace("\n", " ") + ("..." if len(text) > 50 else "")
			source = metadata.get("source", "unknown")
			
			table_data.append([
				i,
				f"{similarity:.3f}",
				text_preview,
				source
			])
		
		headers = ["#", "Similaridad", "Texto (preview)", "Fuente"]
		print(tabulate(table_data, headers=headers, tablefmt="grid"))
	
	def export_to_json(self, filename: str = "rag_export.json"):
		"""Exporta toda la base de datos a JSON."""
		collection = self.get_collection()
		if not collection:
			return
		
		print(f"\n📤 Exportando a {filename}...", end=" ")
		
		all_docs = collection.get(include=["documents", "metadatas"])
		
		export_data = {
			"config": {
				"collection": self.config.collection_name,
				"chunk_size": self.config.chunk_size,
				"chunk_overlap": self.config.chunk_overlap,
				"embedding_model": self.config.embedding_model
			},
			"documents": []
		}
		
		for doc_id, text, metadata in zip(
			all_docs["ids"],
			all_docs["documents"] if all_docs["documents"] else [],
			all_docs["metadatas"] if all_docs["metadatas"] else []
		):
			export_data["documents"].append({
				"id": doc_id,
				"text": text,
				"source": metadata.get("source", "unknown")
			})
		
		with open(filename, "w", encoding="utf-8") as f:
			json.dump(export_data, f, indent=2, ensure_ascii=False)
		
		print(f"✓\n  Archivo: {filename}\n  Documentos: {len(export_data['documents'])}")
	
	def interactive_mode(self):
		"""Modo interactivo para explorar la BD."""
		while True:
			print("\n" + "="*70)
			print("🗂️  EXPLORADOR DE RAG - MENÚ PRINCIPAL")
			print("="*70)
			print("\n1. Ver estadísticas")
			print("2. Listar documentos")
			print("3. Ver detalles de un documento")
			print("4. Buscar documentos")
			print("5. Exportar a JSON")
			print("6. Salir")
			
			choice = input("\nOpción (1-6): ").strip()
			
			if choice == "1":
				self.show_statistics()
			
			elif choice == "2":
				limit_str = input("¿Cuántos documentos mostrar? (default: 10): ").strip()
				limit = int(limit_str) if limit_str else 10
				self.show_documents(limit=limit)
			
			elif choice == "3":
				doc_id = input("ID del documento: ").strip()
				if doc_id:
					self.show_document_detail(doc_id)
				else:
					print("✗ ID requerido")
			
			elif choice == "4":
				query = input("¿Qué quieres buscar?: ").strip()
				if query:
					limit_str = input("¿Cuántos resultados? (default: 5): ").strip()
					limit = int(limit_str) if limit_str else 5
					self.search_and_show(query, limit=limit)
				else:
					print("✗ Búsqueda vacía")
			
			elif choice == "5":
				filename = input("Nombre del archivo (default: rag_export.json): ").strip()
				filename = filename if filename else "rag_export.json"
				self.export_to_json(filename)
			
			elif choice == "6":
				print("\nHasta luego.")
				break
			
			else:
				print("✗ Opción inválida")


def main():
	"""Función principal."""
	import argparse
	
	parser = argparse.ArgumentParser(description="Explorador de base de datos RAG")
	parser.add_argument("--stats", action="store_true", help="Muestra estadísticas")
	parser.add_argument("--list", type=int, metavar="N", help="Lista N documentos")
	parser.add_argument("--detail", metavar="ID", help="Detalles de un documento")
	parser.add_argument("--search", metavar="QUERY", help="Busca documentos")
	parser.add_argument("--export", metavar="FILE", help="Exporta a JSON")
	parser.add_argument("--interactive", action="store_true", help="Modo interactivo")
	
	args = parser.parse_args()
	
	explorer = RAGExplorer()
	
	if args.stats:
		explorer.show_statistics()
	
	elif args.list:
		explorer.show_documents(limit=args.list)
	
	elif args.detail:
		explorer.show_document_detail(args.detail)
	
	elif args.search:
		explorer.search_and_show(args.search)
	
	elif args.export:
		explorer.export_to_json(args.export)
	
	elif args.interactive or not any([args.stats, args.list, args.detail, args.search, args.export]):
		explorer.interactive_mode()


if __name__ == "__main__":
	main()
