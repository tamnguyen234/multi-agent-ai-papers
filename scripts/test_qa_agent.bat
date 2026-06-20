@echo off
title QA Agent Test Utility
echo ==============================================================================
echo Testing QA Agent API on Port 8103
echo ==============================================================================

echo.
echo ====================================================
echo [1] GET /health (Health Check)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" http://127.0.0.1:8103/health
echo.

echo.
echo ====================================================
echo [2] POST /qa/ask (Mode: mock)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8103/qa/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"paper_id\":8,\"question\":\"What is the main contribution?\",\"title\":\"Attention Is All You Need\",\"abstract\":\"We present a new network architecture...\",\"summary\":\"Introduce Transformer model.\",\"mode\":\"mock\"}"
echo.

echo.
echo ====================================================
echo [3] POST /qa/ask (Mode: mock_fallback with missing PDF)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8103/qa/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"paper_id\":8,\"question\":\"What is the main contribution?\",\"pdf_path\":\"missing_file.pdf\",\"title\":\"Attention Is All You Need\",\"abstract\":\"We present a new network architecture...\",\"summary\":\"Introduce Transformer model.\",\"mode\":\"mock_fallback\"}"
echo.

echo.
echo ====================================================
echo [4] POST /qa/ask (Mode: real with missing PDF - should fail with HTTP 500 or 400)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8103/qa/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"paper_id\":8,\"question\":\"What is the main contribution?\",\"pdf_path\":\"missing_file.pdf\",\"title\":\"Attention Is All You Need\",\"abstract\":\"We present a new network architecture...\",\"summary\":\"Introduce Transformer model.\",\"mode\":\"real\"}"
echo.

echo.
echo ====================================================
echo [5] POST /qa/ask (Error: Empty question)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8103/qa/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"paper_id\":8,\"question\":\"\",\"title\":\"Test Paper\",\"mode\":\"mock\"}"
echo.

echo.
echo ====================================================
echo [6] POST /qa/ask (Error: Invalid Mode)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8103/qa/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"paper_id\":8,\"question\":\"What is this?\",\"title\":\"Test Paper\",\"mode\":\"invalid_mode_name\"}"
echo.

echo ==============================================================================
echo QA Agent test queries completed.
echo ==============================================================================
pause
