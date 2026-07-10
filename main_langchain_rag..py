"""Agente RAG para consultar PDFs usando LangChain y Pinecone.

Demuestra la integración de:
- LangChain: Orquestación de componentes
- Pinecone: Base de datos vectorial
- Sentence Transformers: Embeddings
- Anthropic/LLM: Generación de respuestas
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

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
	from langchain_text_splitters import RecursiveCharacterTextSplitter
	from langchain_community.document_loaders import PyPDFLoader
	from langchain_community.vectorstores import Pinecone as LangChainPinecone
	from langchain_community.embeddings import HuggingFaceEmbeddings
	from langchain.chains import RetrievalQA
	from langchain.prompts import PromptTemplate
	from langchain_anthropic import ChatAnthropic
	from pinecone import Pinecone
except ImportError as e:
	# Intenta importación alternativa para versiones antiguas
	try:
		from langchain.text_splitter import RecursiveCharacterTextSplitter
		from langchain_community.document_loaders import PyPDFLoader
		from langchain_community.vectorstores import Pinecone as LangChainPinecone
		from langchain_community.embeddings import HuggingFaceEmbeddings
		from langchain.chains import RetrievalQA
		from langchain.prompts import PromptTemplate
		from langchain_anthropic import ChatAnthropic
		from pinecone import Pinecone
	except ImportError as e2:
		print(f"Error de importación: {e2}")
		print("Instala: pip install langchain langchain-community langchain-anthropic langchain-text-splitters")
		sys.exit(1)


class RAGAgentLangChain:
	"""Agente RAG usando LangChain y Pinecone."""
	
	def __init__(self):
		"""Inicializa el agente con configuración."""
		self.pdf_folder = Path(os.getenv("RAG_PDF_FOLDER", "company_docs"))
		self.chunk_size = int(os.getenv("RAG_CHUNK_SIZE", 1000))
		self.chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", 200))
		self.top_k = int(os.getenv("RAG_TOP_K", 5))
		self.embedding_model = os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
		
		# Configuración de Pinecone
		self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
		self.pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "company-documents")
		
		# Configuración del LLM
		self.llm_base_url = os.getenv("LLM_BASE_URL", "http://localhost:8082/v1/messages")
		self.llm_api_key = os.getenv("LLM_API_KEY", "freecc")
		self.llm_model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
		
		# Inicializar componentes
		self._init_embeddings()
		self._init_llm()
		self._init_vector_store()
		self.qa_chain = None
	
	def _init_embeddings(self):
		"""Inicializa el modelo de embeddings."""
		print("\n🤖 Inicializando embeddings...", end=" ")
		self.embeddings = HuggingFaceEmbeddings(
			model_name=self.embedding_model,
			show_progress=False
		)
		print("✓")
	
	def _init_llm(self):
		"""Inicializa el LLM."""
		print("🧠 Inicializando LLM...", end=" ")
		try:
			self.llm = ChatAnthropic(
				model=self.llm_model,
				api_key=self.llm_api_key,
				temperature=0.2,
				max_tokens=2048
			)
			print("✓")
		except Exception as e:
			# Fallback si Anthropic no está disponible
			print(f"\n⚠ Advertencia: {e}")
			print("  Usando endpoint personalizado...")
			from langchain_openai import ChatOpenAI
			self.llm = ChatOpenAI(
				base_url=self.llm_base_url,
				api_key=self.llm_api_key,
				model=self.llm_model,
				temperature=0.2,
				max_tokens=2048
			)
	
	def _init_vector_store(self):
		"""Inicializa el almacén vectorial con Pinecone."""
		print("📦 Inicializando almacén vectorial Pinecone...", end=" ")
		
		if not self.pinecone_api_key:
			raise ValueError("PINECONE_API_KEY no está configurada")
		
		# Conectar a Pinecone
		pc = Pinecone(api_key=self.pinecone_api_key)
		
		# Verificar que el índice existe
		try:
			pc.describe_index(self.pinecone_index_name)
		except Exception:
			raise ValueError(f"Índice '{self.pinecone_index_name}' no existe en Pinecone")
		
		# Crear vector store de LangChain
		self.vector_store = LangChainPinecone(
			index_name=self.pinecone_index_name,
			embedding=self.embeddings
		)
		print("✓")
	
	def _create_prompt_template(self) -> PromptTemplate:
		"""Crea el template de prompt personalizado."""
		template = """Eres un asistente experto en información empresarial.
Responde preguntas sobre la empresa basándote SOLO en los documentos proporcionados.

Si la información no está en los documentos, dilo explícitamente.
Sé conciso, claro y profesional.

Contexto de los documentos:
{context}

Pregunta: {question}

Respuesta:"""
		
		return PromptTemplate(
			template=template,
			input_variables=["context", "question"]
		)
	
	def initialize(self) -> bool:
		"""Inicializa el agente y carga los documentos."""
		print("\n" + "="*70)
		print("AGENTE RAG CON LANGCHAIN - INFORMACIÓN DE LA EMPRESA")
		print("="*70)
		
		print("\n✓ Configuración:")
		print(f"  • Embeddings: {self.embedding_model}")
		print(f"  • Índice Pinecone: {self.pinecone_index_name}")
		print(f"  • Chunk size: {self.chunk_size}")
		print(f"  • Top K: {self.top_k}")
		print(f"  • LLM Model: {self.llm_model}")
		
		# Crear cadena QA
		self.qa_chain = RetrievalQA.from_chain_type(
			llm=self.llm,
			chain_type="stuff",  # Otras opciones: "map_reduce", "refine", "map_rerank"
			retriever=self.vector_store.as_retriever(
				search_type="similarity",
				search_kwargs={"k": self.top_k}
			),
			chain_type_kwargs={
				"prompt": self._create_prompt_template(),
				"verbose": False
			},
			return_source_documents=True
		)
		
		print("\n✓ Agente RAG inicializado correctamente")
		return True
	
	def answer_question(self, question: str) -> dict[str, Any]:
		"""Responde una pregunta usando la cadena QA."""
		if not self.qa_chain:
			return {
				"answer": "Error: Agente no inicializado",
				"source_documents": [],
				"error": True
			}
		
		question = question.strip()
		if not question:
			return {
				"answer": "Por favor, escribe una pregunta.",
				"source_documents": [],
				"error": False
			}
		
		try:
			print("\n🔍 Procesando pregunta...", end=" ")
			result = self.qa_chain.invoke({"query": question})
			print("✓")
			
			return {
				"answer": result.get("result", "No se pudo obtener respuesta"),
				"source_documents": result.get("source_documents", []),
				"error": False
			}
		except Exception as e:
			return {
				"answer": f"Error al procesar: {e}",
				"source_documents": [],
				"error": True
			}
	
	def run_interactive(self):
		"""Inicia el modo interactivo de chat."""
		print("\n" + "-"*70)
		print("Modo interactivo. Escribe 'salir' para terminar.")
		print("-"*70 + "\n")
		
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
			
			if question.lower() in {"salir", "exit", "quit", "q"}:
				print("Hasta luego.")
				break
			
			result = self.answer_question(question)
			
			print(f"\n🤖 Respuesta:\n{result['answer']}")
			
			# Mostrar fuentes
			if result["source_documents"]:
				print("\n📚 Fuentes consultadas:")
				for i, doc in enumerate(result["source_documents"], 1):
					source = doc.metadata.get("source", "Desconocida")
					print(f"  {i}. {source}")
			
			print()


def parse_args() -> argparse.Namespace:
	"""Parsea argumentos de línea de comandos."""
	parser = argparse.ArgumentParser(
		description="Agente RAG con LangChain y Pinecone para consultar PDFs",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""
Ejemplos:
  %(prog)s --chat                          # Modo interactivo
  %(prog)s "¿Cuál es el objetivo?"         # Pregunta específica
  %(prog)s "info" --chat                   # Iniciar con pregunta inicial
		"""
	)
	parser.add_argument("question", nargs="*", help="Pregunta a responder")
	parser.add_argument("--chat", action="store_true", help="Modo interactivo")
	parser.add_argument("--debug", action="store_true", help="Modo debug con información adicional")
	
	return parser.parse_args()


def main() -> int:
	"""Función principal."""
	args = parse_args()
	
	try:
		# Inicializar agente
		agent = RAGAgentLangChain()
		
		# Inicializar componentes
		if not agent.initialize():
			return 1
		
		# Procesar pregunta o entrar en modo interactivo
		question = " ".join(args.question).strip()
		
		if args.chat or not question:
			agent.run_interactive()
		else:
			result = agent.answer_question(question)
			print(f"\n🤖 Respuesta:\n{result['answer']}")
			
			if result["source_documents"]:
				print("\n📚 Fuentes:")
				for i, doc in enumerate(result["source_documents"], 1):
					source = doc.metadata.get("source", "Desconocida")
					print(f"  {i}. {source}")
		
		return 0
		
	except KeyboardInterrupt:
		print("\n\nInterrumpido por el usuario.")
		return 0
	except Exception as e:
		print(f"\n✗ Error: {e}")
		if args.debug:
			import traceback
			traceback.print_exc()
		return 1


if __name__ == "__main__":
	sys.exit(main())
