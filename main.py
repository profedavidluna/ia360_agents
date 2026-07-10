"""Agente RAG para consultar información de PDFs usando Pinecone y LLM.

Usa Pinecone como base de datos vectorial para almacenar embeddings de documentos.
El agente responde preguntas basadas en la información contenida en los PDFs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.request import urlopen
import urllib.request as urllib_request
import time

# Cargar variables de entorno desde .env
def _load_env():
	"""Carga variables de entorno desde .env si existe."""
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

try:
	from pinecone import Pinecone, ServerlessSpec
except ImportError:
	Pinecone = None
	ServerlessSpec = None

try:
	from PyPDF2 import PdfReader
except ImportError:
	PdfReader = None

try:
	from sentence_transformers import SentenceTransformer
except ImportError:
	SentenceTransformer = None


@dataclass
class RAGConfig:
	"""Configuración del sistema RAG con Pinecone."""
	pdf_folder: str = "company_docs"
	pinecone_api_key: str = ""
	pinecone_index_name: str = "company-documents"
	pinecone_environment: str = "us-east-1"
	chunk_size: int = 1000
	chunk_overlap: int = 200
	top_k: int = 5
	embedding_model: str = "all-MiniLM-L6-v2"
	
	def __post_init__(self):
		"""Carga configuración desde variables de entorno."""
		self.chunk_size = int(os.getenv("RAG_CHUNK_SIZE", self.chunk_size))
		self.chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", self.chunk_overlap))
		self.top_k = int(os.getenv("RAG_TOP_K", self.top_k))
		self.embedding_model = os.getenv("RAG_EMBEDDING_MODEL", self.embedding_model)
		self.pdf_folder = os.getenv("RAG_PDF_FOLDER", self.pdf_folder)
		self.pinecone_api_key = os.getenv("PINECONE_API_KEY", self.pinecone_api_key)
		self.pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", self.pinecone_index_name)
		self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", self.pinecone_environment)


@dataclass
class AgentReply:
	text: str
	should_exit: bool = False


def get_llm_config() -> dict[str, str]:
	"""Obtiene configuración del LLM."""
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
	"""Verifica si el LLM está configurado."""
	config = get_llm_config()
	return bool(config["base_url"])


def post_json(url: str, body: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
	"""POST request con manejo de SSE streaming."""
	data = json.dumps(body).encode("utf-8")
	request_headers = {"Content-Type": "application/json"}
	if headers:
		request_headers.update(headers)
	request = urllib_request.Request(url, data=data, headers=request_headers, method="POST")
	
	with urlopen(request, timeout=60) as response:
		response_text = response.read().decode("utf-8")
		
		if not response_text or not response_text.strip():
			raise ValueError(f"Servidor devolvió respuesta vacía. Status: {response.status}")
		
		# Detectar Server-Sent Events (SSE)
		if response_text.strip().startswith("event:"):
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
			
			if events:
				return {"__sse_events": events}
			else:
				raise ValueError("No se pudieron parsear eventos SSE")
		
		# JSON normal
		try:
			return json.loads(response_text)
		except json.JSONDecodeError as e:
			preview = response_text[:200] if len(response_text) > 200 else response_text
			raise ValueError(f"Servidor devolvió respuesta no-JSON: {preview}")


def call_llm(messages: list[dict[str, str]], temperature: float = 0.2) -> str:
	"""Llama al LLM y retorna la respuesta."""
	config = get_llm_config()
	api_type = config.get("api_type", "anthropic").lower()
	
	# Extraer mensaje del sistema
	system_message = ""
	user_messages = []
	
	for msg in messages:
		if msg["role"] == "system":
			system_message = msg["content"]
		else:
			user_messages.append({"role": msg["role"], "content": msg["content"]})
	
	# Preparar body
	body = {
		"model": config["model"],
		"max_tokens": 2048,
		"messages": user_messages,
		"temperature": temperature,
	}
	if system_message:
		body["system"] = system_message
	
	headers = {"x-api-key": config["api_key"]}
	
	try:
		response = post_json(config["base_url"], body, headers=headers)
	except Exception as e:
		raise ValueError(f"Error al conectar con LLM: {e}")
	
	# Manejar SSE
	if "__sse_events" in response:
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
			raise ValueError("No se encontró contenido en los eventos SSE")
	
	# JSON normal (Anthropic)
	content = response.get("content") or []
	if content and isinstance(content, list) and len(content) > 0:
		return str(content[0].get("text", ""))
	
	raise ValueError("No se pudo extraer respuesta del LLM")


class PineconeVectorStore:
	"""Almacén vectorial usando Pinecone."""
	
	def __init__(self, config: RAGConfig):
		if Pinecone is None:
			raise ImportError("pinecone no está instalado. Instala con: pip install pinecone-client")
		
		if SentenceTransformer is None:
			raise ImportError("sentence-transformers no está instalado. Instala con: pip install sentence-transformers")
		
		if not config.pinecone_api_key:
			raise ValueError("PINECONE_API_KEY no está configurada")
		
		self.config = config
		self.pc = Pinecone(api_key=config.pinecone_api_key)
		
		# Cargar modelo de embeddings
		print("\n🤖 Cargando modelo de embeddings...", end=" ")
		self.embedding_model = SentenceTransformer(config.embedding_model)
		embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
		print(f"✓ ({embedding_dim} dimensiones)")
		
		# Verificar o crear índice
		self._ensure_index(embedding_dim)
		
		self.index = self.pc.Index(config.pinecone_index_name)
	
	def _ensure_index(self, dimension: int):
		"""Verifica que el índice existe, sino lo crea."""
		index_name = self.config.pinecone_index_name
		
		try:
			# Verificar si existe
			self.pc.describe_index(index_name)
			print(f"✓ Índice '{index_name}' ya existe")
		except Exception:
			# Crear si no existe
			print(f"\n📦 Creando índice '{index_name}'...", end=" ")
			self.pc.create_index(
				name=index_name,
				dimension=dimension,
				metric="cosine",
				spec=ServerlessSpec(
					cloud="aws",
					region=self.config.pinecone_environment
				)
			)
			# Esperar a que se cree
			time.sleep(30)
			print("✓")
	
	def add_documents(self, documents: list[dict[str, str]]) -> int:
		"""Agrega documentos al almacén vectorial."""
		if not documents:
			return 0
		
		print(f"\n📤 Generando embeddings para {len(documents)} chunks...", end=" ")
		
		# Generar embeddings
		texts = [doc["text"] for doc in documents]
		embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
		
		print(f"✓")
		print(f"   Enviando a Pinecone...", end=" ")
		
		# Preparar vectores para Pinecone
		vectors_to_upsert = []
		for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
			vectors_to_upsert.append({
				"id": doc["id"],
				"values": embedding.tolist(),
				"metadata": {
					"text": doc["text"],
					"source": doc.get("source", "unknown")
				}
			})
		
		# Upsert por lotes (Pinecone tiene límites)
		batch_size = 100
		for i in range(0, len(vectors_to_upsert), batch_size):
			batch = vectors_to_upsert[i:i + batch_size]
			self.index.upsert(vectors=batch)
		
		print(f"✓\n   Indexados: {len(documents)} chunks")
		return len(documents)
	
	def search(self, query: str) -> list[dict[str, str]]:
		"""Busca documentos similares."""
		# Generar embedding de la consulta
		query_embedding = self.embedding_model.encode(query, show_progress_bar=False)
		
		# Buscar en Pinecone
		results = self.index.query(
			vector=query_embedding.tolist(),
			top_k=self.config.top_k,
			include_metadata=True
		)
		
		documents = []
		for match in results.get("matches", []):
			metadata = match.get("metadata", {})
			documents.append({
				"text": metadata.get("text", ""),
				"source": metadata.get("source", "unknown"),
				"distance": 1 - match.get("score", 0)  # Convertir score a distance
			})
		
		return documents
	
	def clear(self):
		"""Limpia el índice."""
		print("🗑️  Limpiando índice...", end=" ")
		self.index.delete(delete_all=True)
		print("✓")


class PDFProcessor:
	"""Procesa PDFs y extrae texto."""
	
	def __init__(self, config: RAGConfig):
		if PdfReader is None:
			raise ImportError("PyPDF2 no está instalado. Instala con: pip install PyPDF2")
		
		self.config = config
		self.pdf_folder = Path(config.pdf_folder)
	
	def process_all_pdfs(self) -> list[dict[str, str]]:
		"""Procesa todos los PDFs en la carpeta y retorna chunks de texto."""
		documents = []
		
		if not self.pdf_folder.exists():
			print(f"⚠ Carpeta {self.config.pdf_folder} no existe")
			return documents
		
		pdf_files = list(self.pdf_folder.glob("*.pdf"))
		if not pdf_files:
			print(f"⚠ No se encontraron PDFs en {self.config.pdf_folder}")
			return documents
		
		print(f"\n📄 Procesando {len(pdf_files)} PDF(s)...\n")
		
		for pdf_path in pdf_files:
			print(f"  • {pdf_path.name}...", end=" ")
			try:
				chunks = self._extract_chunks_from_pdf(pdf_path)
				documents.extend(chunks)
				print(f"✓ ({len(chunks)} chunks)")
			except Exception as e:
				print(f"✗ Error: {e}")
		
		return documents
	
	def _extract_chunks_from_pdf(self, pdf_path: Path) -> list[dict[str, str]]:
		"""Extrae chunks de un PDF."""
		reader = PdfReader(pdf_path)
		text = ""
		
		for page in reader.pages:
			text += page.extract_text()
		
		# Crear chunks
		chunks = []
		chunk_size = self.config.chunk_size
		overlap = self.config.chunk_overlap
		
		for i in range(0, len(text), chunk_size - overlap):
			chunk = text[i:i + chunk_size]
			if chunk.strip():
				chunk_id = f"{pdf_path.name}_chunk_{i}"
				chunks.append({
					"id": chunk_id,
					"text": chunk,
					"source": pdf_path.name
				})
		
		return chunks


class RAGAgent:
	"""Agente RAG para responder preguntas sobre documentos."""
	
	def __init__(self):
		self.config = RAGConfig()
		self.vector_store = PineconeVectorStore(self.config)
		self.pdf_processor = PDFProcessor(self.config)
	
	def initialize(self) -> int:
		"""Inicializa el agente indexando todos los PDFs."""
		print("\n" + "="*70)
		print("AGENTE RAG - INFORMACIÓN DE LA EMPRESA (Pinecone)")
		print("="*70)
		
		if not llm_is_configured():
			print("\n⚠ LLM no está configurado")
			print("Define: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL")
			return 1
		
		print("\n✓ LLM configurado correctamente")
		print(f"✓ Pinecone Index: {self.config.pinecone_index_name}")
		
		# Procesar PDFs
		documents = self.pdf_processor.process_all_pdfs()
		if not documents:
			print("\n⚠ No hay documentos para procesar")
			return 1
		
		# Indexar en Pinecone
		print(f"\n🗂️  Indexando en Pinecone...")
		self.vector_store.add_documents(documents)
		
		return 0
	
	def answer_question(self, question: str) -> AgentReply:
		"""Responde una pregunta basada en los documentos."""
		question = question.strip()
		
		if not question:
			return AgentReply("Por favor, escribe una pregunta sobre la empresa.")
		
		if question.lower() in {"salir", "exit", "quit", "q"}:
			return AgentReply("Hasta luego.", should_exit=True)
		
		# Buscar documentos relevantes
		print("\n🔍 Buscando documentos relevantes...", end=" ")
		relevant_docs = self.vector_store.search(question)
		print("✓")
		
		if not relevant_docs:
			return AgentReply("No encontré información relevante en los documentos.")
		
		# Construir contexto
		context = "Documentos relevantes:\n\n"
		for i, doc in enumerate(relevant_docs, 1):
			context += f"[{doc['source']}]:\n{doc['text']}\n\n"
		
		# Llamar al LLM
		print("🤖 Consultando LLM...", end=" ")
		messages = [
			{
				"role": "system",
				"content": """Eres un asistente experto en información empresarial. 
Tu tarea es responder preguntas sobre la empresa basándote en los documentos proporcionados.
Sé conciso, claro y profesional. Si la información no está en los documentos, dilo explícitamente."""
			},
			{
				"role": "user",
				"content": f"{context}\n\nPregunta: {question}"
			}
		]
		
		try:
			response = call_llm(messages)
			print("✓\n")
			return AgentReply(response)
		except Exception as e:
			return AgentReply(f"Error al procesar la pregunta: {e}")
	
	def run_interactive(self):
		"""Inicia el modo interactivo."""
		print("\nModo interactivo. Escribe 'salir' para terminar.\n")
		
		while True:
			try:
				question = input("Tu pregunta> ").strip()
			except KeyboardInterrupt:
				print("\n\nHasta luego.")
				break
			except EOFError:
				print("\n\nHasta luego.")
				break
			
			if not question:
				continue
			
			reply = self.answer_question(question)
			print(f"\nAgente> {reply.text}\n")
			
			if reply.should_exit:
				break


def parse_args() -> argparse.Namespace:
	"""Parsea argumentos de línea de comandos."""
	parser = argparse.ArgumentParser(description="Agente RAG con Pinecone para consultar documentos de la empresa")
	parser.add_argument("question", nargs="*", help="Pregunta a responder")
	parser.add_argument("--chat", action="store_true", help="Modo interactivo")
	parser.add_argument("--reset", action="store_true", help="Limpia el índice de Pinecone")
	return parser.parse_args()


def main() -> int:
	"""Función principal."""
	args = parse_args()
	
	try:
		agent = RAGAgent()
		
		# Resetear si se solicita
		if args.reset:
			agent.vector_store.clear()
		
		# Inicializar
		if agent.initialize() != 0:
			return 1
		
		# Procesar pregunta o entrar en modo interactivo
		question = " ".join(args.question).strip()
		
		if args.chat or not question:
			agent.run_interactive()
		else:
			reply = agent.answer_question(question)
			print(f"\nAgente> {reply.text}\n")
		
		return 0
		
	except Exception as e:
		print(f"\n✗ Error: {e}")
		import traceback
		traceback.print_exc()
		return 1


if __name__ == "__main__":
	sys.exit(main())
