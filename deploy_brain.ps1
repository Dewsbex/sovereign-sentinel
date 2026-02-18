# Deploy Brain Script
# Deploys ALL intelligence components (Bot, Macro-Clock, Janitor, Alt-Data)

$VPS_IP = "145.241.226.107"
$VPS_USER = "ubuntu"
$SSH_KEY = "Stores\ssh-key-2026-02-08.key"
$TARGET = "$VPS_USER@$VPS_IP"

Write-Host "DEPLOYING SOVEREIGN BRAIN..." -ForegroundColor Cyan

# 1. Upload Core Scripts
$files = @(
    "main_bot.py",
    "macro_clock.py",
    "strategy_engine.py",
    "strategic_moat.py",
    "session_manager.py",
    "trading212_client.py",
    "telegram_bot.py",
    "audit_log.py",
    "auditor.py",
    "requirements.txt"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Uploading $file..." -ForegroundColor Yellow
        scp -i $SSH_KEY -o StrictHostKeyChecking=no $file "$TARGET`:~/Sovereign-Sentinel/"
    }
    else {
        Write-Host "WARNING: $file not found!" -ForegroundColor Red
    }
}

# 2. Install ALL dependencies
Write-Host "Installing dependencies on VPS..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET @"
cd ~/Sovereign-Sentinel
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium
else
    echo "ERROR: .venv not found!"
    exit 1
fi
"@

# 3. Restart Services
Write-Host "Restarting Sovereign Bot..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET @"
sudo systemctl restart sovereign-bot
sleep 2
sudo systemctl status sovereign-bot --no-pager | head -20
"@

Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
