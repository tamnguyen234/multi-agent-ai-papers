@echo off
title Frontend Manager
cd /d "%~dp0..\frontend"
echo Starting Frontend (React + Vite) on port 5173 (strict)...
echo Note: Please ensure 'npm install' has been executed first in the frontend/ folder.
echo If port 5173 is already in use, this will fail immediately. Run:
echo   scripts\kill_project_ports.bat
echo.
npx vite --host 127.0.0.1 --port 5173 --strictPort
pause
