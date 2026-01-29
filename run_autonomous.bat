@echo off
taskkill /F /IM python.exe /T 2>nul
echo Starting Sovereign-Sentinel...
python sentinel_daemon.py
pause
