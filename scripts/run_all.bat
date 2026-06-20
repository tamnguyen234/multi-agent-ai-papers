@echo off
title AI Paper Multi-Agent - Run All Services
echo ==============================================================================
echo Starting the full system: Backend Gateway, Frontend, and all AI Agents
echo ==============================================================================
echo Ports and services configured:
echo  - Backend Gateway on Port 8000
echo  - Summarizer Agent on Port 8101
echo  - Trend Agent on Port 8102
echo  - QA Agent on Port 8103
echo  - TTS Agent on Port 8104
echo  - Frontend (React + Vite) on Port 5173
echo ==============================================================================
echo.
echo [INFO] If a port is already in use, run first:
echo        scripts\kill_project_ports.bat
echo.

cd /d "%~dp0"

start "Backend Gateway" cmd /k run_backend.bat
start "Summarizer Agent" cmd /k run_summarizer_agent.bat
start "Trend Agent" cmd /k run_trend_agent.bat
start "QA Agent" cmd /k run_qa_agent.bat
start "TTS Agent" cmd /k run_tts_agent.bat
start "Frontend Vite" cmd /k run_frontend.bat

echo Full system processes launched in separate terminal windows.
pause
