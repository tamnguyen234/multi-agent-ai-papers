@echo off
title Setup Backend Environment
echo =======================================================
echo Setting up virtual environment for Backend...
echo =======================================================

cd /d "%~dp0..\backend"

if not exist .venv (
    echo Creating virtual environment in backend/.venv...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo backend/.venv already exists. Skipping creation.
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Backend dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install Backend dependencies.
    exit /b 1
)

echo Backend gateway environment setup completed successfully.
exit /b 0
