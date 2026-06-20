@echo off
title QA Agent Manager
cd /d "%~dp0..\agents\qa_agent"
echo Starting QA Agent on port 8103 using reference venv...
echo Host: 127.0.0.1  Port: 8103
echo.
"..\qa_agent\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8103
pause
