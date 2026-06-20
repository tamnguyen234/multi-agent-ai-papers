@echo off
title AI Paper Multi-Agent - Health Check
echo ==============================================================================
echo  AI Paper Multi-Agent System - Health Check
echo  Services: Backend (8000), Agents (8101-8104), Frontend (5173)
echo ==============================================================================

echo.
echo ====================================================
echo [1/6] Backend DB Health (Port 8000)
echo Endpoint: GET http://127.0.0.1:8000/api/v1/system/db-health
echo ----------------------------------------------------
curl -s --max-time 5 http://127.0.0.1:8000/api/v1/system/db-health
if %ERRORLEVEL% neq 0 (
    echo.
    echo [WARNING] curl failed - trying PowerShell fallback...
    powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/system/db-health' -TimeoutSec 5; ConvertTo-Json $r } catch { Write-Host '[FAIL] Backend not responding:' $_.Exception.Message -ForegroundColor Red }"
)
echo.

echo.
echo ====================================================
echo [2/6] Summarizer Agent Health (Port 8101)
echo Endpoint: GET http://127.0.0.1:8101/health
echo ----------------------------------------------------
curl -s --max-time 5 http://127.0.0.1:8101/health
if %ERRORLEVEL% neq 0 (
    echo.
    echo [WARNING] curl failed - trying PowerShell fallback...
    powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8101/health' -TimeoutSec 5; ConvertTo-Json $r } catch { Write-Host '[FAIL] Summarizer Agent not responding:' $_.Exception.Message -ForegroundColor Red }"
)
echo.

echo.
echo ====================================================
echo [3/6] Trend Agent Health (Port 8102)
echo Endpoint: GET http://127.0.0.1:8102/health
echo ----------------------------------------------------
curl -s --max-time 5 http://127.0.0.1:8102/health
if %ERRORLEVEL% neq 0 (
    echo.
    echo [WARNING] curl failed - trying PowerShell fallback...
    powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8102/health' -TimeoutSec 5; ConvertTo-Json $r } catch { Write-Host '[FAIL] Trend Agent not responding:' $_.Exception.Message -ForegroundColor Red }"
)
echo.

echo.
echo ====================================================
echo [4/6] QA Agent Health (Port 8103)
echo Endpoint: GET http://127.0.0.1:8103/health
echo ----------------------------------------------------
curl -s --max-time 5 http://127.0.0.1:8103/health
if %ERRORLEVEL% neq 0 (
    echo.
    echo [WARNING] curl failed - trying PowerShell fallback...
    powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8103/health' -TimeoutSec 5; ConvertTo-Json $r } catch { Write-Host '[FAIL] QA Agent not responding:' $_.Exception.Message -ForegroundColor Red }"
)
echo.

echo.
echo ====================================================
echo [5/6] TTS Agent Health (Port 8104)
echo Endpoint: GET http://127.0.0.1:8104/health
echo ----------------------------------------------------
curl -s --max-time 5 http://127.0.0.1:8104/health
if %ERRORLEVEL% neq 0 (
    echo.
    echo [WARNING] curl failed - trying PowerShell fallback...
    powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8104/health' -TimeoutSec 5; ConvertTo-Json $r } catch { Write-Host '[FAIL] TTS Agent not responding:' $_.Exception.Message -ForegroundColor Red }"
)
echo.

echo.
echo ====================================================
echo [6/6] Frontend (Port 5173)
echo URL: http://127.0.0.1:5173
echo Note: Expects HTML response (not JSON)
echo ----------------------------------------------------
curl -s --max-time 5 -o nul -w "HTTP Status: %%{http_code}" http://127.0.0.1:5173
if %ERRORLEVEL% neq 0 (
    echo.
    echo [WARNING] Frontend not responding on port 5173.
    echo   - Check if it is running: scripts\run_frontend.bat
    echo   - Or open browser manually: http://localhost:5173
) else (
    echo.
    echo [OK] Frontend is serving HTML on port 5173.
    echo   -> Open http://localhost:5173 in browser to verify UI.
)
echo.

echo ==============================================================================
echo Health check complete. Review results above.
echo If any service shows FAIL, check ports first:
echo   scripts\check_ports.bat
echo Then free ports if needed:
echo   scripts\kill_project_ports.bat
echo Then restart with corresponding run_*.bat script.
echo ==============================================================================
pause
