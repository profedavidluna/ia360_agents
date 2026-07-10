#!/usr/bin/env python3
"""Carga variables de entorno desde .env"""

import os
from pathlib import Path


def load_env():
    """Carga las variables de entorno del archivo .env"""
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print(f"⚠ Archivo .env no encontrado en {env_file}")
        return False
    
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            # Ignorar líneas vacías y comentarios
            if not line or line.startswith("#"):
                continue
            
            # Parsear KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                # Configurar en os.environ
                os.environ[key] = value
    
    print("✓ Variables de entorno cargadas desde .env")
    return True


if __name__ == "__main__":
    load_env()
