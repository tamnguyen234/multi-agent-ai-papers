@echo off
title AI Paper Multi-Agent - Full Pipeline Test
echo ==============================================================================
echo  Task 19: Full Pipeline End-to-End Test
echo ==============================================================================
echo.
echo  Script se kiem tra toan bo pipeline qua Backend Gateway (port 8000)
echo  Bao gom: Health, Auth, Daily Digest, Trend, Chat Q^&A, TTS
echo.
echo  Bien moi truong tuy chon (dat truoc khi chay):
echo    set TEST_USERNAME=demo_user_pipeline
echo    set TEST_PASSWORD=DemoPassword123!
echo    set TEST_EMAIL=aipapereveryday@gmail.com
echo    set BACKEND_URL=http://127.0.0.1:8000
echo.
echo ==============================================================================
echo.

cd /d "%~dp0.."

REM Chay script Python tu thu muc goc cua project
python scripts\test_full_pipeline.py

echo.
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] All tests PASSED or WARN only.
) else (
    echo [WARNING] Some tests FAILED. Check output above.
)
echo.
pause
