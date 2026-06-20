@echo off
title Historical Data Audio Abstracts Batch Generator
cd /d "%~dp0.."
echo Running Audio Abstracts Batch Generator with args: %*
"backend\.venv\Scripts\python.exe" backend\scripts\generate_missing_audio_abstracts.py %*
