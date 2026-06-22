@echo off
title AI Paper Multi-Agent - Service Manager
setlocal enabledelayedexpansion

:: Determine project root
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"
for %%I in ("!SCRIPT_DIR!") do set "PROJECT_ROOT=%%~dpI"
if "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT:~0,-1!"

cd /d "!PROJECT_ROOT!"

:: Help display
if "%1"=="--help" (
    goto help
)
if "%1"=="-h" (
    goto help
)

echo ==============================================================================
echo  AI Paper Multi-Agent Service Manager
echo  Project Root: !PROJECT_ROOT!
echo ==============================================================================

:: Default flags
set "START_OLLAMA=0"
set "START_BACKEND=0"
set "START_AGENTS=0"
set "START_FRONTEND=0"

:: Parse arguments
if "%1"=="" (
    :: Run all
    set "START_OLLAMA=1"
    set "START_BACKEND=1"
    set "START_AGENTS=1"
    set "START_FRONTEND=1"
) else (
    :parse_args
    if "%1"=="" goto run_services
    if "%1"=="--ollama" (
        set "START_OLLAMA=1"
    ) else if "%1"=="--backend" (
        set "START_BACKEND=1"
    ) else if "%1"=="--agents" (
        set "START_AGENTS=1"
    ) else if "%1"=="--frontend" (
        set "START_FRONTEND=1"
    ) else (
        echo [ERROR] Unknown option: %1
        echo Run with --help to see available options.
        exit /b 1
    )
    shift
    goto parse_args
)

:run_services
echo.
echo [INFO] If a port is already in use, run first:
echo        scripts\kill_project_ports.bat
echo.

:: 1. Ollama Server
if "!START_OLLAMA!"=="1" (
    echo Starting Ollama...
    set "OLLAMA_EXE=!PROJECT_ROOT!\Ollama\ollama.exe"
    if exist "!OLLAMA_EXE!" (
        echo Using portable Ollama: !OLLAMA_EXE!
        start "Ollama Server" cmd /k "set PATH=!PROJECT_ROOT!\Ollama;%%PATH%% && cd /d !PROJECT_ROOT!\Ollama && ollama.exe serve"
    ) else (
        echo Portable Ollama not found, launching system ollama.exe
        start "Ollama Server" cmd /k "ollama serve"
    )
)

:: 2. Backend Gateway
if "!START_BACKEND!"=="1" (
    echo Starting Backend Gateway on port 8000...
    start "Backend Gateway" cmd /k "set PYTHONPATH=!PROJECT_ROOT!&& cd /d !PROJECT_ROOT!\backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
)

:: 3. AI Agents
if "!START_AGENTS!"=="1" (
    echo Starting AI Agents [Ports 8005, 8103, 8104, 8105]...
    start "Trend Agent" cmd /k "set PYTHONPATH=!PROJECT_ROOT!;!PROJECT_ROOT!\backend&& cd /d !PROJECT_ROOT!\agents\trend_agent && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8005"
    start "QA Agent" cmd /k "set PYTHONPATH=!PROJECT_ROOT!;!PROJECT_ROOT!\backend&& cd /d !PROJECT_ROOT!\agents\qa_agent && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8103"
    start "TTS Agent" cmd /k "set PYTHONPATH=!PROJECT_ROOT!;!PROJECT_ROOT!\backend&& cd /d !PROJECT_ROOT!\agents\tts_agent && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8104"
    start "Daily Paper Agent" cmd /k "set PYTHONPATH=!PROJECT_ROOT!;!PROJECT_ROOT!\backend&& cd /d !PROJECT_ROOT!\agents\daily_paper_agent && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8105"
)

:: 4. Frontend
if "!START_FRONTEND!"=="1" (
    echo Starting Frontend Vite server on port 5173...
    start "Frontend Vite" cmd /k "cd /d !PROJECT_ROOT!\frontend && npm run dev -- --strictPort"
)

echo Services launched in separate terminal windows.
pause
exit /b 0

:help
echo Usage: run_all.bat [options]
echo.
echo Options:
echo   (No options)   Start everything (Ollama, Backend, Agents, Frontend)
echo   --ollama       Start only Ollama Server
echo   --backend      Start only Backend Gateway (Port 8000)
echo   --agents       Start only 3 AI Agents (Ports 8005, 8103, 8104)
echo   --frontend     Start only Frontend Vite (Port 5173)
echo   --help         Display this help message
echo.
pause
exit /b 0
