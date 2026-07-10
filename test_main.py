#!/usr/bin/env python
"""Script de prueba simple para main.py"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

try:
    # Intentar cargar las dependencias
    print("Verificando dependencias...")
    
    from pinecone import Pinecone
    print("✓ Pinecone")
    
    from PyPDF2 import PdfReader
    print("✓ PyPDF2")
    
    from sentence_transformers import SentenceTransformer
    print("✓ SentenceTransformer")
    
    print("\n✓ Todas las dependencias están instaladas correctamente")
    print("\nAhora puedes ejecutar:")
    print("  python main.py --chat")
    print("  python main.py 'Tu pregunta aquí'")
    
except ImportError as e:
    print(f"✗ Error de importación: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
