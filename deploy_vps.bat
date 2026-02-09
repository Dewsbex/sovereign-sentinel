@echo off
REM Sovereign Terminal VPS Deployment Script
REM Run this to deploy backend to Oracle VPS (145.241.226.107)

echo ========================================
echo SOVEREIGN TERMINAL - VPS DEPLOYMENT
echo ========================================
echo.

set SSH_KEY=Stores\ssh-key-2026-02-08.key
set VPS_IP=145.241.226.107
set VPS_USER=ubuntu
set WORK_DIR=sovereign_repair

echo SSH Key: %SSH_KEY%
echo VPS: %VPS_USER%@%VPS_IP%
echo Working Directory: ~/%WORK_DIR%
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo [1/6] Pulling latest code from GitHub...
ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_IP% "cd ~/%WORK_DIR% && git pull origin main"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Git pull failed
    pause
    exit /b 1
)

echo.
echo [2/6] Installing Flask-CORS...
ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_IP% "pip install Flask-CORS"

echo.
echo [3/6] Finding Flask service name...
ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_IP% "systemctl list-units --type=service --all | grep -i flask"

echo.
echo [4/6] Restarting Flask service (trying sovereign-web)...
ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_IP% "sudo systemctl restart sovereign-web"
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: sovereign-web restart failed, trying alternative names...
    ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_IP% "sudo systemctl restart flask"
)

echo.
echo [5/6] Checking service status...
ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_IP% "sudo systemctl status sovereign-web --no-pager | head -n 15"

echo.
echo [6/6] Testing local API endpoint...
ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_IP% "curl -s http://localhost:5000/api/live_data | head -c 500"

echo.
echo ========================================
echo DEPLOYMENT COMPLETE
echo ========================================
echo.
echo Frontend: https://sovereign-sentinel.pages.dev
echo Backend:  https://api.sovereign-sentinel.pages.dev
echo.
echo Check GitHub Actions: https://github.com/Dewsbex/sovereign-sentinel/actions
echo.
pause
