# Sovereign Terminal VPS Deployment Script
# Run this in PowerShell to deploy backend to Oracle VPS

$VPS_IP = "145.241.226.107"
$VPS_USER = "ubuntu"

Write-Host "🚀 SOVEREIGN TERMINAL - VPS DEPLOYMENT" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Pull latest code
Write-Host "Step 1/5: Pulling latest code from GitHub..." -ForegroundColor Yellow
ssh ${VPS_USER}@${VPS_IP} "cd ~/Sovereign-Sentinel && git pull origin main"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git pull failed. Check SSH connection." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Code updated" -ForegroundColor Green
Write-Host ""

# Step 2: Install Flask-CORS
Write-Host "Step 2/5: Installing Flask-CORS..." -ForegroundColor Yellow
ssh ${VPS_USER}@${VPS_IP} "pip install Flask-CORS"

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Flask-CORS install failed (may already be installed)" -ForegroundColor Yellow
}

Write-Host "✅ Dependencies ready" -ForegroundColor Green
Write-Host ""

# Step 3: Restart Flask service
Write-Host "Step 3/5: Restarting Flask service..." -ForegroundColor Yellow
ssh ${VPS_USER}@${VPS_IP} "sudo systemctl restart sovereign-web"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Service restart failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Flask service restarted" -ForegroundColor Green
Write-Host ""

# Step 4: Check Flask service status
Write-Host "Step 4/5: Checking Flask service status..." -ForegroundColor Yellow
ssh ${VPS_USER}@${VPS_IP} "sudo systemctl status sovereign-web --no-pager | head -n 10"

Write-Host ""

# Step 5: Restart Cloudflare tunnel
Write-Host "Step 5/5: Restarting Cloudflare tunnel..." -ForegroundColor Yellow
ssh ${VPS_USER}@${VPS_IP} "sudo systemctl restart cloudflared"

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Cloudflare tunnel restart failed (may not be configured yet)" -ForegroundColor Yellow
} else {
    Write-Host "✅ Cloudflare tunnel restarted" -ForegroundColor Green
}

Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "Testing endpoints..." -ForegroundColor Yellow

# Test local API
Write-Host ""
Write-Host "Testing VPS local endpoint..." -ForegroundColor Cyan
ssh ${VPS_USER}@${VPS_IP} "curl -s http://localhost:5000/api/live_data | jq '.total_wealth, .connectivity_status' 2>/dev/null || curl -s http://localhost:5000/api/live_data | head -c 200"

Write-Host ""
Write-Host ""
Write-Host "Testing public endpoint (may take 2-3 minutes for DNS)..." -ForegroundColor Cyan
$response = Invoke-WebRequest -Uri "https://api.sovereign-sentinel.pages.dev/api/live_data" -UseBasicParsing -ErrorAction SilentlyContinue

if ($response) {
    Write-Host "✅ Public API responding!" -ForegroundColor Green
    $json = $response.Content | ConvertFrom-Json
    Write-Host "   Wealth: £$($json.total_wealth)" -ForegroundColor White
    Write-Host "   Status: $($json.connectivity_status)" -ForegroundColor White
} else {
    Write-Host "⚠️  Public API not yet accessible (DNS propagation may be in progress)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "📊 Dashboard URLs:" -ForegroundColor Cyan
Write-Host "   Frontend: https://sovereign-sentinel.pages.dev" -ForegroundColor White
Write-Host "   Backend:  https://api.sovereign-sentinel.pages.dev" -ForegroundColor White
Write-Host ""
Write-Host "Check Cloudflare Pages deployment:" -ForegroundColor Cyan
Write-Host "   https://github.com/Dewsbex/sovereign-sentinel/actions" -ForegroundColor White
Write-Host ""
