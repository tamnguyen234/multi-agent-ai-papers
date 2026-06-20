@echo off
title AI Paper Multi-Agent - Run All Agents
echo =======================================================
echo Starting all AI Agent services...
echo Ports: 8101 8102 8103 8104
echo =======================================================
echo.
echo [INFO] If a port is already in use, run first:
echo        scripts\kill_project_ports.bat
echo.

cd /d "%~dp0"

start "Summarizer Agent" cmd /k run_summarizer_agent.bat
start "Trend Agent" cmd /k run_trend_agent.bat
start "QA Agent" cmd /k run_qa_agent.bat
start "TTS Agent" cmd /k run_tts_agent.bat

echo All agents are opening in separate terminals.
pause
