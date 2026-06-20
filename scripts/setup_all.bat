@echo off
title Setup All Service Environments
echo =======================================================
echo Setting up all service environments for Multi-Agent System...
echo =======================================================

cd /d "%~dp0"

echo.
echo === [1/5] Setting up Backend Environment ===
call setup_backend.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Backend setup failed!
    goto error
)

echo.
echo === [2/5] Setting up Summarizer Agent Environment ===
call setup_summarizer_agent.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Summarizer Agent setup failed!
    goto error
)

echo.
echo === [3/5] Setting up Trend Agent Environment ===
call setup_trend_agent.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Trend Agent setup failed!
    goto error
)

echo.
echo === [4/5] Setting up QA Agent Environment ===
call setup_qa_agent.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: QA Agent setup failed!
    goto error
)

echo.
echo === [5/5] Setting up TTS Agent Environment ===
call setup_tts_agent.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: TTS Agent setup failed!
    goto error
)

echo.
echo =======================================================
echo SUCCESS: All service environments set up successfully!
echo =======================================================
pause
exit /b 0

:error
echo =======================================================
echo ERROR: Environment setup failed. Please check the logs.
echo =======================================================
pause
exit /b 1
