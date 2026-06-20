@echo off
title Trend Agent Manager
cd /d "%~dp0..\agents\trend_agent"
echo Starting Trend Agent on port 8102 using reference venv...
echo Host: 127.0.0.1  Port: 8102
echo.
"..\trend_agent\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8102
pause
