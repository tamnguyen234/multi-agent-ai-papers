@echo off
title Summarizer Agent Manager
cd /d "%~dp0..\agents\summarizer_agent"
echo Starting Summarizer Agent on port 8101 using reference venv...
echo Host: 127.0.0.1  Port: 8101
echo.
"..\summarizer_agent\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8101
pause
