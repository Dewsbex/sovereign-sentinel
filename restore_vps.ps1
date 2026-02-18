# Sovereign Sentinel - One-Click Disaster Recovery (restore_vps.ps1)
# Restores the Oracle VPS from a local backup artifact.

param (
    [Parameter(Mandatory=$false)]
    [string]$BackupFile = ""
)

$VPS_IP = "145.241.226.107"
$VPS_USER = "ubuntu"
$REMOTE_DIR = "~/Sovereign-Sentinel"

Write-Host "🚑 SOVEREIGN SENTINEL - DISASTER RECOVERY PROTOCOL" -ForegroundColor Red
Write-Host "===================================================" -ForegroundColor Red
Write-Host ""

# 1. Select Backup File
if ([string]::IsNullOrEmpty($BackupFile)) {
    # Try to find the latest in ORACLE_BACKUP_LIVE
    $latest = Get-ChildItem "ORACLE_BACKUP_LIVE" -Filter "*.tar.gz" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    if ($latest) {
        $BackupFile = $latest.FullName
        Write-Host "ℹ️  Auto-detected latest backup: $($latest.Name)" -ForegroundColor Yellow
    } else {
        Write-Host "❌ No backup file found in ORACLE_BACKUP_LIVE or provided." -ForegroundColor Red
        exit 1
    }
}

if (-not (Test-Path $BackupFile)) {
    Write-Host "❌ Backup file not found: $BackupFile" -ForegroundColor Red
    exit 1
}

$BackupName = Split-Path $BackupFile -Leaf

# 2. Confirmation
Write-Host "⚠️  WARNING: This will OVERWRITE data on the VPS ($VPS_IP)." -ForegroundColor Red
Write-Host "   Target: $REMOTE_DIR" -ForegroundColor White
Write-Host "   Source: $BackupName" -ForegroundColor White
Write-Host ""
$confirm = Read-Host "Type 'RESTORE' to proceed"
if ($confirm -ne 'RESTORE') {
    Write-Host "🚫 Aborted."
    exit 0
}

# 3. Stop Service
Write-Host "`nStep 1/4: Stopping Sovereign Service..." -ForegroundColor Yellow
ssh ${VPS_USER}@${VPS_IP} "sudo systemctl stop sovereign-web"

# 4. Upload Backup
Write-Host "Step 2/4: Uploading Backup Artifact..." -ForegroundColor Yellow
scp $BackupFile ${VPS_USER}@${VPS_IP}:~/restore_temp.tar.gz

# 5. Extract and Restore
Write-Host "Step 3/4: Extracting and Restoring..." -ForegroundColor Yellow
# Strategy: Extract to temp, then rsync over to preserve permissions and ensure clean overwrite
ssh ${VPS_USER}@${VPS_IP} "
    mkdir -p ~/restore_stage
    tar -xzf ~/restore_temp.tar.gz -C ~/restore_stage
    
    # Check if backup has a top-level folder or is flat. Adjust as needed.
    # Assuming flat backup of 'Sovereign-Sentinel' contents for now based on standard backup scripts.
    
    echo '   -> Overwriting Application Files...'
    rsync -av --exclude='.git' ~/restore_stage/ $REMOTE_DIR/
    
    echo '   -> Cleaning up...'
    rm ~/restore_temp.tar.gz
    rm -rf ~/restore_stage
"

# 6. Restart Service
Write-Host "Step 4/4: Restarting Sovereign Service..." -ForegroundColor Yellow
ssh ${VPS_USER}@${VPS_IP} "sudo systemctl start sovereign-web"

# 7. Validation
Write-Host "`nVerifying Pulse..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
ssh ${VPS_USER}@${VPS_IP} "curl -s http://localhost:5000/api/live_data | head -c 100"

Write-Host "`n✅ RESTORE COMPLETE. THE ORACLE IS LIVE." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Red
