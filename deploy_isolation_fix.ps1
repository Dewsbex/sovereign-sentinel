# Portfolio Isolation Fix - VPS Deployment Script
# Deploys v2.4 safeguards to Oracle VPS

$VPS_IP = "145.241.226.107"
$VPS_USER = "ubuntu"
$SSH_KEY = "Stores\ssh-key-2026-02-08.key"
$TARGET = "$VPS_USER@$VPS_IP"

Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "PORTFOLIO ISOLATION FIX v2.4 - VPS DEPLOYMENT" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""

# Check if key exists
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "SSH Key file not found: $SSH_KEY" -ForegroundColor Red
    exit 1
}

Write-Host "Files to deploy:" -ForegroundColor Yellow
Write-Host "   - strategy_engine.py" -ForegroundColor White
Write-Host "   - main_bot.py" -ForegroundColor White
Write-Host "   - data/strategic_holdings.json" -ForegroundColor White
Write-Host ""

# Step 1: Upload modified files
Write-Host "Step 1/4: Uploading modified files..." -ForegroundColor Yellow

$remote_dir = "~/Sovereign-Sentinel"

scp -i $SSH_KEY -o StrictHostKeyChecking=no strategy_engine.py "${TARGET}:$remote_dir/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to upload strategy_engine.py" -ForegroundColor Red
    exit 1
}

scp -i $SSH_KEY -o StrictHostKeyChecking=no main_bot.py "${TARGET}:$remote_dir/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to upload main_bot.py" -ForegroundColor Red
    exit 1
}

scp -i $SSH_KEY -o StrictHostKeyChecking=no data/strategic_holdings.json "${TARGET}:$remote_dir/data/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to upload strategic_holdings.json" -ForegroundColor Red
    exit 1
}

Write-Host "Files uploaded successfully" -ForegroundColor Green
Write-Host ""

# Step 2: Verify strategic holdings file
Write-Host "Step 2/4: Verifying strategic holdings..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET "cat ~/Sovereign-Sentinel/data/strategic_holdings.json | head -n 20"
Write-Host ""

# Step 3: Restart sovereign-bot service
Write-Host "Step 3/4: Restarting sovereign-bot.service..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET "sudo systemctl restart sovereign-bot.service"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Service restart failed" -ForegroundColor Red
    exit 1
}

Write-Host "Service restarted" -ForegroundColor Green
Write-Host ""

# Step 4: Check service status
Write-Host "Step 4/4: Checking service status..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET "sudo systemctl status sovereign-bot.service --no-pager | head -n 15"

Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""
