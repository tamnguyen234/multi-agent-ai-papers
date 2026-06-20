@echo off
title TTS Agent Manager
cd /d "%~dp0..\agents\tts_agent"
echo Starting TTS Agent on port 8104 using reference venv...
echo Host: 127.0.0.1  Port: 8104
echo.
"..\tts_agent\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8104
pause
