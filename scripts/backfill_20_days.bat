@echo off
title Historical Data Backfill Simulation
cd /d "%~dp0.."
echo Running arXiv Daily Digests Backfill simulation with args: %*
"backend\.venv\Scripts\python.exe" backend\scripts\backfill_arxiv_daily_digests.py %*
