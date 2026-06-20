@echo off
title Backend Gateway Manager
cd /d "%~dp0..\backend"
echo Starting Backend Gateway on port 8000 using reference venv...
echo Host: 127.0.0.1  Port: 8000
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
