@echo off
title AI Paper Multi-Agent - Environment Setup
echo =======================================================
echo Starting environment setup for AI Paper Multi-Agent System...
echo =======================================================

:: Determine project root
cd /d "%~dp0.."

:: Set target requirements file based on arguments
set "REQ_FILE=requirements-health.txt"
set "MODE_NAME=Health-check (Skeleton) mode"
if "%1"=="--full" (
    set "REQ_FILE=requirements.txt"
    set "MODE_NAME=Full dependencies mode"
)
if "%1"=="full" (
    set "REQ_FILE=requirements.txt"
    set "MODE_NAME=Full dependencies mode"
)

echo Setup Mode: %MODE_NAME%
echo.

:: 1. Copy .env files from .env.example if they do not exist
echo [1/3] Copying environment configurations...

if not exist .env (
    echo Creating root .env from .env.example...
    copy .env.example .env > nul
) else (
    echo Root .env already exists. Skipping.
)

if not exist backend\.env (
    echo Creating backend/.env from backend/.env.example...
    copy backend\.env.example backend\.env > nul
) else (
    echo backend/.env already exists. Skipping.
)

if not exist agents\summarizer_agent\.env (
    echo Creating agents/summarizer_agent/.env from example...
    copy agents\summarizer_agent\.env.example agents\summarizer_agent\.env > nul
) else (
    echo agents/summarizer_agent/.env already exists. Skipping.
)

if not exist agents\trend_agent\.env (
    echo Creating agents/trend_agent/.env from example...
    copy agents\trend_agent\.env.example agents\trend_agent\.env > nul
) else (
    echo agents/trend_agent/.env already exists. Skipping.
)

if not exist agents\qa_agent\.env (
    echo Creating agents/qa_agent/.env from example...
    copy agents\qa_agent\.env.example agents\qa_agent\.env > nul
) else (
    echo agents/qa_agent/.env already exists. Skipping.
)

if not exist agents\tts_agent\.env (
    echo Creating agents/tts_agent/.env from example...
    copy agents\tts_agent\.env.example agents\tts_agent\.env > nul
) else (
    echo agents/tts_agent/.env already exists. Skipping.
)

if not exist frontend\.env (
    echo Creating frontend/.env from example...
    copy frontend\.env.example frontend\.env > nul
) else (
    echo frontend/.env already exists. Skipping.
)

:: 2. Create Backend virtual environment and install packages
echo.
echo [2/3] Setting up Backend virtual environment...
if not exist backend\.venv (
    echo Creating virtual environment in backend/.venv...
    python -m venv backend\.venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment for Backend.
        goto error
    )
) else (
    echo backend/.venv already exists. Skipping creation.
)

echo Upgrading pip and installing Backend requirements...
backend\.venv\Scripts\python.exe -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to upgrade pip for Backend.
    goto error
)
backend\.venv\Scripts\pip.exe install -r backend\requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install Backend dependencies.
    goto error
)

:: 3. Create Agent virtual environments and install requirements
echo.
echo [3/3] Setting up virtual environments for AI Agents (%MODE_NAME%)...

:: Loop helper to setup each agent
for %%A in (summarizer_agent trend_agent qa_agent tts_agent) do (
    echo.
    echo ---------------------------------------------------
    echo Configuring agents/%%A...
    echo ---------------------------------------------------
    
    if not exist agents\%%A\.venv (
        echo Creating virtual environment in agents/%%A/.venv...
        python -m venv agents\%%A\.venv
        if %ERRORLEVEL% neq 0 (
            echo ERROR: Failed to create virtual environment for agents/%%A.
            goto error
        )
    ) else (
        echo agents/%%A/.venv already exists. Skipping creation.
    )

    echo Upgrading pip for agents/%%A...
    agents\%%A\.venv\Scripts\python.exe -m pip install --upgrade pip
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to upgrade pip for agents/%%A.
        goto error
    )

    echo Installing dependencies (%REQ_FILE%) for agents/%%A...
    agents\%%A\.venv\Scripts\pip.exe install -r agents\%%A\%REQ_FILE%
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to install dependencies for agents/%%A.
        goto error
    )
)

echo.
echo =======================================================
echo SUCCESS: Environment setup completed successfully!
echo =======================================================
echo To start the services, run:
echo    scripts\run_all.bat
echo =======================================================
goto end

:error
echo.
echo =======================================================
echo ERROR: Environment setup failed. Please check the logs above.
echo =======================================================
exit /b 1

:end
pause
