@echo off
title "Trend Agent Test Utility"
echo ==============================================================================
echo Testing Trend Agent API on Port 8102
echo ==============================================================================

echo.
echo ====================================================
echo [1] GET /health (Health Check)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" http://127.0.0.1:8102/health
echo.

echo.
echo ====================================================
echo [2] POST /trend/analyze (Mode: rule_based)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8102/trend/analyze ^
  -H "Content-Type: application/json" ^
  -d "{\"papers\":[{\"id\":1,\"title\":\"Retrieval-Augmented Generation for Scientific QA\",\"abstract\":\"RAG methods combine retriever and generator models for QA.\",\"summary\":\"GraphRAG evaluation.\"}],\"mode\":\"rule_based\"}"
echo.

echo.
echo ====================================================
echo [3] POST /trend/analyze (Mode: rule_based_fallback - Dataset too small -> Fallback to rule_based)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8102/trend/analyze ^
  -H "Content-Type: application/json" ^
  -d "{\"papers\":[{\"id\":1,\"title\":\"Retrieval-Augmented Generation for Scientific QA\",\"abstract\":\"RAG methods combine retriever and generator models for QA.\",\"summary\":\"GraphRAG evaluation.\"}],\"mode\":\"rule_based_fallback\"}"
echo.

echo.
echo ====================================================
echo [4] POST /trend/analyze (Mode: real - Dataset too small -> Should fail with 400)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8102/trend/analyze ^
  -H "Content-Type: application/json" ^
  -d "{\"papers\":[{\"id\":1,\"title\":\"Retrieval-Augmented Generation for Scientific QA\",\"abstract\":\"RAG methods combine retriever and generator models for QA.\",\"summary\":\"GraphRAG evaluation.\"}],\"mode\":\"real\"}"
echo.

echo.
echo ====================================================
echo [5] POST /trend/analyze (Error: Invalid Mode)
echo ----------------------------------------------------
curl -s -w "\nHTTP Status: %%{http_code}\n" -X POST http://127.0.0.1:8102/trend/analyze ^
  -H "Content-Type: application/json" ^
  -d "{\"papers\":[{\"id\":1,\"title\":\"Retrieval-Augmented Generation for Scientific QA\",\"abstract\":\"RAG methods combine retriever and generator models for QA.\",\"summary\":\"GraphRAG evaluation.\"}],\"mode\":\"invalid_mode_name\"}"
echo.

echo ==============================================================================
echo Trend Agent test queries completed.
echo ==============================================================================
pause
