@echo off
title Setup TTS Agent Environment
echo =======================================================
echo Setting up virtual environment for TTS Agent...
echo =======================================================

cd /d "%~dp0..\agents\tts_agent"

if not exist .venv (
    echo Creating virtual environment in agents/tts_agent/.venv...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo agents/tts_agent/.venv already exists. Skipping creation.
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing TTS Agent dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install TTS Agent dependencies.
    exit /b 1
)

echo TTS Agent environment setup completed successfully.
exit /b 0
