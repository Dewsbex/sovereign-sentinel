@echo off
title Sovereign Sentinel Autonomous Node
color 0A
echo.
echo ========================================================
echo   SOVEREIGN SENTINEL - AUTONOMOUS NODE LAUNCHER
echo ========================================================
echo.
echo   [1] Initializing Environment...
echo   [2] Starting Sentinel Daemon...
echo.
echo   Keep this window open to maintain autonomous updates.
echo   (Updates Dashboard 09:00-21:00 GMT, Syncs Ledger @ 21:00)
echo.

python sentinel_daemon.py
pause
