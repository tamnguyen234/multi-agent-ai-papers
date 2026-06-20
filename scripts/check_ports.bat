@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo Checking project port status (READ-ONLY)
echo Ports: 8000 8101 8102 8103 8104 5173
echo ==========================================

for %%p in (8000 8101 8102 8103 8104 5173) do (
    echo.
    echo Port %%p:
    set "FOUND=0"

    for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr /C:":%%p " ^| findstr /C:"LISTENING"') do (
        set "FOUND=1"
        echo   [IN USE] State=LISTENING   PID=%%a
        echo   Process: 
        tasklist /fi "PID eq %%a" /fo list /nh 2>nul | findstr "Image Name:"
    )

    if "!FOUND!"=="0" (
        echo   [FREE] No process is listening on port %%p.
    )
)

echo.
echo ==========================================
echo Port check complete (nothing was killed).
echo To free ports, run: scripts\kill_project_ports.bat
echo ==========================================
pause
