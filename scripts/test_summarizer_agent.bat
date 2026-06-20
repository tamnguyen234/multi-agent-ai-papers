@echo off
title "Summarizer Agent Test Utility"
echo ==============================================================================
echo Testing Summarizer Agent API on Port 8101
echo ==============================================================================

echo.
echo ====================================================
echo [1] GET /health (Health Check)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" http://127.0.0.1:8101/health
echo.

echo.
echo ====================================================
echo [2] POST /summarize/daily-top5 (Mode: mock)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8101/summarize/daily-top5 ^
  -H "Content-Type: application/json" ^
  -d "{\"mode\":\"mock\"}"
echo.

echo.
echo ====================================================
echo [3] POST /summarize/daily-top5 (Mode: mock_fallback)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8101/summarize/daily-top5 ^
  -H "Content-Type: application/json" ^
  -d "{\"mode\":\"mock_fallback\"}"
echo.

echo.
echo ====================================================
echo [4] POST /summarize/daily-top5 (Mode: real)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8101/summarize/daily-top5 ^
  -H "Content-Type: application/json" ^
  -d "{\"mode\":\"real\"}"
echo.

echo.
echo ====================================================
echo [5] POST /summarize/daily-top5 (Error: Invalid Mode)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8101/summarize/daily-top5 ^
  -H "Content-Type: application/json" ^
  -d "{\"mode\":\"invalid_mode_name\"}"
echo.

echo ==============================================================================
echo Summarizer Agent test queries completed.
echo ==============================================================================
pause
