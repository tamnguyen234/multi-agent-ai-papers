@echo off
title TTS Agent Test Utility
echo ==============================================================================
echo Testing TTS Agent API on Port 8104
echo ==============================================================================

echo.
echo ====================================================
echo [1] GET /health (Health Check)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" http://127.0.0.1:8104/health
echo.

echo.
echo ====================================================
echo [2] POST /tts/synthesize (Mode: mock)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8104/tts/synthesize ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Xin chào, đây là kiểm tra chế độ mock.\",\"mode\":\"mock\",\"language\":\"vi\",\"voice\":\"default\",\"speed\":1.0}"
echo.

echo.
echo ====================================================
echo [3] POST /tts/synthesize (Mode: mock_fallback)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8104/tts/synthesize ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Xin chào, đây là kiểm tra chế độ mock fallback.\",\"mode\":\"mock_fallback\",\"language\":\"vi\",\"voice\":\"default\",\"speed\":1.0}"
echo.

echo.
echo ====================================================
echo [4] POST /tts/synthesize (Mode: real)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8104/tts/synthesize ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Xin chào, đây là kiểm tra chế độ real.\",\"mode\":\"real\",\"language\":\"vi\",\"voice\":\"default\",\"speed\":1.0}"
echo.

echo.
echo ====================================================
echo [5] POST /tts/synthesize (Error: Empty text)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8104/tts/synthesize ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"\",\"mode\":\"mock\",\"language\":\"vi\",\"voice\":\"default\",\"speed\":1.0}"
echo.

echo.
echo ====================================================
echo [6] POST /tts/synthesize (Error: Unsupported Language in real mode)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8104/tts/synthesize ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Hello standard english text.\",\"mode\":\"real\",\"language\":\"en\",\"voice\":\"default\",\"speed\":1.0}"
echo.

echo.
echo ====================================================
echo [7] POST /tts/synthesize (Error: Invalid Mode)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8104/tts/synthesize ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Test text.\",\"mode\":\"invalid_mode_name\",\"language\":\"vi\",\"voice\":\"default\",\"speed\":1.0}"
echo.

echo ==============================================================================
echo TTS Agent test queries completed.
echo ==============================================================================
pause
