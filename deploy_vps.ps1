# Sovereign Terminal VPS Deployment Script
# Run this in PowerShell to deploy backend to Oracle VPS

$VPS_IP = "145.241.226.107"
$VPS_USER = "ubuntu"
$SSH_KEY = "Stores\ssh-key-2026-02-08.key"
$TARGET = "$VPS_USER@$VPS_IP"

Write-Host "SOVEREIGN TERMINAL - VPS DEPLOYMENT" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Check if key exists
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "SSH Key file not found: $SSH_KEY" -ForegroundColor Red
    exit 1
}

# Step 1: Pull latest code
Write-Host "Step 1/5: Pulling latest code from GitHub..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET "cd ~/Sovereign-Sentinel && git pull origin main"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Git pull failed. Check SSH connection." -ForegroundColor Red
    exit 1
}

Write-Host "Code updated" -ForegroundColor Green
Write-Host ""

# Step 1.1: Direct File Sync (Krypto Healthcheck Integration)
Write-Host "Step 1.1: Syncing Krypto Healthcheck files..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no requirements.txt "$TARGET`:~/Sovereign-Sentinel/"
scp -i $SSH_KEY -o StrictHostKeyChecking=no vps_crontab.txt "$TARGET`:~/Sovereign-Sentinel/"
scp -i $SSH_KEY -o StrictHostKeyChecking=no telegram_bot.py "$TARGET`:~/Sovereign-Sentinel/"
scp -i $SSH_KEY -o StrictHostKeyChecking=no trading212_client.py "$TARGET`:~/Sovereign-Sentinel/"
scp -i $SSH_KEY -o StrictHostKeyChecking=no krypto_healthcheck.py "$TARGET`:~/Sovereign-Sentinel/"
scp -i $SSH_KEY -o StrictHostKeyChecking=no krypto_system_test.py "$TARGET`:~/Sovereign-Sentinel/"
scp -i $SSH_KEY -o StrictHostKeyChecking=no kraken_client.py "$TARGET`:~/Sovereign-Sentinel/"
Write-Host "   Copying Krypto workspace..." -ForegroundColor Gray
scp -i $SSH_KEY -r -o StrictHostKeyChecking=no Krypto "$TARGET`:~/Sovereign-Sentinel/"
Write-Host "Files synced" -ForegroundColor Green
Write-Host ""

# Step 2: Install Flask-CORS
Write-Host "Step 2/5: Installing Flask-CORS..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET "pip install Flask-CORS"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Flask-CORS install failed or already installed" -ForegroundColor Yellow
}

Write-Host "Dependencies ready" -ForegroundColor Green
Write-Host ""

# Step 3: Restart Flask service
Write-Host "Step 3/5: Restarting Flask service..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET "sudo systemctl restart sovereign-web"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Service restart failed" -ForegroundColor Red
    exit 1
}

Write-Host "Flask service restarted" -ForegroundColor Green
Write-Host ""

# Step 4: Check Flask service status
Write-Host "Step 4/5: Checking Flask service status..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET "sudo systemctl status sovereign-web --no-pager | head -n 10"

Write-Host ""

# Step 5: Restart Cloudflare tunnel
Write-Host "Step 5/5: Restarting Cloudflare tunnel..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET "sudo systemctl restart cloudflared"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Cloudflare tunnel restart failed (may not be configured yet)" -ForegroundColor Yellow
} else {
    Write-Host "Cloudflare tunnel restarted" -ForegroundColor Green
}

Write-Host ""

# Step 6: Update Crontab
Write-Host "Step 6/6: Updating Crontab..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET "crontab ~/Sovereign-Sentinel/vps_crontab.txt"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Crontab update failed" -ForegroundColor Yellow
} else {
    Write-Host "Crontab updated" -ForegroundColor Green
}

Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "Testing endpoints..." -ForegroundColor Yellow

# Test local API
Write-Host ""
Write-Host "Testing VPS local endpoint..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET "curl -s http://localhost:5000/api/live_data | jq '.total_wealth, .connectivity_status' 2>/dev/null || curl -s http://localhost:5000/api/live_data | head -c 200"

Write-Host ""
Write-Host ""
Write-Host "Testing public endpoint (may take 2-3 minutes for DNS)..." -ForegroundColor Cyan
$response = Invoke-WebRequest -Uri "https://api.sovereign-sentinel.pages.dev/api/live_data" -UseBasicParsing -ErrorAction SilentlyContinue

if ($response) {
    Write-Host "Public API responding!" -ForegroundColor Green
    $json = $response.Content | ConvertFrom-Json
    Write-Host "   Wealth: ($($json.total_wealth))" -ForegroundColor White
    Write-Host "   Status: $($json.connectivity_status)" -ForegroundColor White
} else {
    Write-Host "Public API not yet accessible (DNS propagation may be in progress)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "Dashboard URLs:" -ForegroundColor Cyan
Write-Host "   Frontend: https://sovereign-sentinel.pages.dev" -ForegroundColor White
Write-Host "   Backend:  https://api.sovereign-sentinel.pages.dev" -ForegroundColor White
Write-Host ""
Write-Host "Check Cloudflare Pages deployment:" -ForegroundColor Cyan
Write-Host "   https://github.com/Dewsbex/sovereign-sentinel/actions" -ForegroundColor White
Write-Host ""
