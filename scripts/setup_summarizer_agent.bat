@echo off
title Setup Summarizer Agent Environment
echo =======================================================
echo Setting up virtual environment for Summarizer Agent...
echo =======================================================

cd /d "%~dp0..\agents\summarizer_agent"

if not exist .venv (
    echo Creating virtual environment in agents/summarizer_agent/.venv...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo agents/summarizer_agent/.venv already exists. Skipping creation.
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Summarizer Agent dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install Summarizer Agent dependencies.
    exit /b 1
)

echo Summarizer Agent environment setup completed successfully.
exit /b 0
