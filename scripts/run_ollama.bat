@echo off
setlocal enabledelayedexpansion

:: Determine project root
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"
for %%I in ("!SCRIPT_DIR!") do set "PROJECT_ROOT=%%~dpI"
if "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT:~0,-1!"

echo Project Root: !PROJECT_ROOT!

set "OLLAMA_EXE=!PROJECT_ROOT!\Ollama\ollama.exe"

if exist "!OLLAMA_EXE!" (
    echo Using portable Ollama: !OLLAMA_EXE!
) else (
    echo Portable Ollama not found at !OLLAMA_EXE!, trying system ollama.exe
    set "OLLAMA_EXE=ollama.exe"
)

:: Set temporary PATH
set "PATH=!PROJECT_ROOT!\Ollama;%PATH%"

echo Starting Ollama serve...
"!OLLAMA_EXE!" serve
