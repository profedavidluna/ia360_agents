@echo off
REM Script para instalar dependencias del Agente RAG

echo.
echo ============================================================
echo Instalando dependencias para Agente RAG
echo ============================================================
echo.

REM Instalar chromadb
echo Instalando chromadb...
Scripts\pip.exe install chromadb -q
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo instalar chromadb
    goto error
)

REM Instalar PyPDF2
echo Instalando PyPDF2...
Scripts\pip.exe install PyPDF2 -q
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo instalar PyPDF2
    goto error
)

echo.
echo ============================================================
echo ✓ Dependencias instaladas exitosamente
echo ============================================================
echo.
echo Proximos pasos:
echo 1. Coloca tus PDFs en la carpeta company_docs/
echo 2. Inicia el servidor LLM: python -m free_claude_code
echo 3. Ejecuta el agente: Scripts\python.exe main.py --chat
echo.
pause
exit /b 0

:error
echo.
echo ============================================================
echo ✗ Error durante la instalacion
echo ============================================================
pause
exit /b 1
