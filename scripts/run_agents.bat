@echo off
cd /d "%~dp0"

echo Starting all AI Agents...

start "Summarizer Agent" cmd /k run_summarizer_agent.bat
start "Trend Agent" cmd /k run_trend_agent.bat
start "QA Agent" cmd /k run_qa_agent.bat
start "TTS Agent" cmd /k run_tts_agent.bat

echo All agent terminals have been opened.
pause
