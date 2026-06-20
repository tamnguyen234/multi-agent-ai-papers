@echo off
setlocal enabledelayedexpansion

:: Determine project root
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"
for %%I in ("!SCRIPT_DIR!") do set "PROJECT_ROOT=%%~dpI"
if "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT:~0,-1!"

set "OLLAMA_EXE=!PROJECT_ROOT!\Ollama\ollama.exe"

echo Checking Ollama executable...
if exist "!OLLAMA_EXE!" (
    echo Portable Ollama exists at: !OLLAMA_EXE!
    "!OLLAMA_EXE!" --version
    echo.
    echo Running 'ollama list' to check models...
    "!OLLAMA_EXE!" list
) else (
    echo [WARNING] Portable Ollama not found at !OLLAMA_EXE!
)

echo.
echo Checking Ollama server health...
curl -s -f http://127.0.0.1:11434/api/tags >nul
if errorlevel 1 (
    echo [ERROR] Ollama server is NOT running.
    echo To start the server, please run:
    echo   scripts\run_ollama.bat
) else (
    echo [OK] Ollama server is running.
    echo.
    echo Checking for model qwen2.5:3b...
    curl -s http://127.0.0.1:11434/api/tags | findstr "qwen2.5:3b" >nul
    if errorlevel 1 (
        echo [WARNING] Model qwen2.5:3b is NOT loaded in Ollama.
        echo To pull this model, please run:
        echo   "!OLLAMA_EXE!" pull qwen2.5:3b
    ) else (
        echo [OK] Model qwen2.5:3b is loaded and ready.
    )
)
