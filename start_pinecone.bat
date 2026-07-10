@echo off
REM Script para iniciar el agente RAG con Pinecone

echo.
echo ============================================================
echo AGENTE RAG CON PINECONE
echo ============================================================
echo.

REM Verificar que el LLM está corriendo
echo Verificando LLM...
timeout /t 1 /nobreak >nul

REM Instalar dependencias si no están
echo.
echo Instalando dependencias...
Scripts\pip.exe install -q pinecone-client sentence-transformers PyPDF2

REM Ejecutar agente
echo.
echo ✓ Iniciando agente...
echo.
Scripts\python.exe main.py --chat

pause
