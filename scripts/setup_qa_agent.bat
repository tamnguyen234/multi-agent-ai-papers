@echo off
title Setup QA Agent Environment
echo =======================================================
echo Setting up virtual environment for QA Agent...
echo =======================================================

cd /d "%~dp0..\agents\qa_agent"

if not exist .venv (
    echo Creating virtual environment in agents/qa_agent/.venv...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo agents/qa_agent/.venv already exists. Skipping creation.
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing QA Agent dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install QA Agent dependencies.
    exit /b 1
)

echo QA Agent environment setup completed successfully.
exit /b 0
