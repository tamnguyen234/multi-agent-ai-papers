@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo Killing project ports if they are in use...
echo Ports: 8000 8101 8102 8103 8104 5173
echo ==========================================

for %%p in (8000 8101 8102 8103 8104 5173) do (
    echo.
    echo Checking port %%p...
    set "FOUND=0"

    rem Get PID of process LISTENING on this port
    for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr /C:":%%p " ^| findstr /C:"LISTENING"') do (
        set "FOUND=1"
        echo   [OCCUPIED] Port %%p is LISTENING by PID %%a. Killing...
        taskkill /PID %%a /F >nul 2>&1
        if not errorlevel 1 (
            echo   [OK] PID %%a killed successfully.
        ) else (
            echo   [WARN] Could not kill PID %%a - may require admin rights.
        )
    )

    if "!FOUND!"=="0" (
        echo   [FREE] Port %%p is free.
    )
)

echo.
echo ==========================================
echo Done. Wait 2 seconds before restarting services.
echo ==========================================
timeout /t 2 /nobreak >nul
pause
