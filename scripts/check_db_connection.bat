@echo off
title Check Backend Database Connection
echo =======================================================
echo Checking DB connection status via Backend Gateway...
echo =======================================================
echo.
curl -s http://127.0.0.1:8000/api/v1/system/db-health
echo.
echo.
pause
