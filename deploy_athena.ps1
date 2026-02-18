# Project Athena Deployment Script
# Deploys Athena Janitor and Alternative Data Engine to Oracle VPS

$VPS_IP = "145.241.226.107"
$VPS_USER = "ubuntu"
$SSH_KEY = "Stores\ssh-key-2026-02-08.key"
$TARGET = "$VPS_USER@$VPS_IP"

Write-Host "PROJECT ATHENA - VPS DEPLOYMENT" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Check if key exists
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "SSH Key file not found: $SSH_KEY" -ForegroundColor Red
    exit 1
}

# Check if credentials.json exists
if (-not (Test-Path "credentials.json")) {
    Write-Host "credentials.json not found!" -ForegroundColor Red
    Write-Host "Make sure credentials.json is in the current directory" -ForegroundColor Yellow
    exit 1
}

# Step 1: Upload credentials.json
Write-Host "Step 1/6: Uploading Google Service Account credentials..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no credentials.json "$TARGET`:~/Sovereign-Sentinel/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Credentials upload failed" -ForegroundColor Red
    exit 1
}

Write-Host "   credentials.json uploaded" -ForegroundColor Green
Write-Host ""

# Step 2: Upload .env file with Athena config
Write-Host "Step 2/6: Uploading updated .env file..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no .env "$TARGET`:~/Sovereign-Sentinel/"

if ($LASTEXITCODE -ne 0) {
    Write-Host ".env upload failed" -ForegroundColor Red
    exit 1
}

Write-Host "   .env uploaded" -ForegroundColor Green
Write-Host ""

# Step 3: Upload Python scripts
Write-Host "Step 3/6: Uploading Athena scripts..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no athena_janitor.py "$TARGET`:~/Sovereign-Sentinel/"
scp -i $SSH_KEY -o StrictHostKeyChecking=no alt_data_engine.py "$TARGET`:~/Sovereign-Sentinel/"

Write-Host "   Python scripts uploaded" -ForegroundColor Green
Write-Host ""

# Step 4: Upload systemd service files
Write-Host "Step 4/6: Uploading systemd service files..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no athena_janitor.service "$TARGET`:~/Sovereign-Sentinel/"
scp -i $SSH_KEY -o StrictHostKeyChecking=no alt_data_engine.service "$TARGET`:~/Sovereign-Sentinel/"

Write-Host "   Service files uploaded" -ForegroundColor Green
Write-Host ""

# Step 5: Install dependencies on VPS
Write-Host "Step 5/6: Installing Python dependencies on VPS..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET @"
cd ~/Sovereign-Sentinel
# Ensure .venv is used
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
    pip install pytrends newsapi-python requests beautifulsoup4 lxml playwright finnhub-python
    playwright install chromium
else
    echo "ERROR: .venv not found!"
    exit 1
fi
"@


if ($LASTEXITCODE -ne 0) {
    Write-Host "Dependency installation failed (check output above)" -ForegroundColor Yellow
    Write-Host "Continuing anyway..." -ForegroundColor Gray
}

Write-Host "   Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 6: Configure and start systemd services
Write-Host "Step 6/6: Configuring systemd services..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $TARGET @"
cd ~/Sovereign-Sentinel

# Install Athena Janitor service
sudo cp athena_janitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable athena_janitor
sudo systemctl restart athena_janitor

# Install Alternative Data Engine service
sudo cp alt_data_engine.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable alt_data_engine
sudo systemctl restart alt_data_engine

echo ""
echo "=== SERVICE STATUS ==="
echo ""
echo "Athena Janitor:"
sudo systemctl status athena_janitor --no-pager | head -n 8
echo ""
echo "Alternative Data Engine:"
sudo systemctl status alt_data_engine --no-pager | head -n 8
"@

Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Verify services are running (shown above)" -ForegroundColor White
Write-Host "2. Check logs: ssh to VPS and run:" -ForegroundColor White
Write-Host "   tail -f ~/Sovereign-Sentinel/athena_janitor.log" -ForegroundColor Gray
Write-Host "   tail -f ~/Sovereign-Sentinel/alt_data_engine.log" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test by dropping a Google Doc in your Inbox folder" -ForegroundColor White
Write-Host "   Folder: https://drive.google.com/drive/folders/16Ig5NMEpOQs_jzNXI4zLsu2CxYXQVVjf" -ForegroundColor Gray
Write-Host ""
