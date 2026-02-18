$ErrorActionPreference = "Stop"

# Get current ISO timestamp
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
Write-Host "ðŸš€ Starting Sovereign Terminal Deployment..." -ForegroundColor Cyan
Write-Host "ðŸ“… Build Timestamp: $timestamp" -ForegroundColor Gray

# 1. Update timestamp in dist/index.html
$distPath = "dist\index.html"
if (Test-Path $distPath) {
    $content = Get-Content $distPath -Raw
    # Regex replacement for timestamp in footer
    $newContent = $content -replace "// \d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z", "// $timestamp"
    # Regex replacement for BUILD header comment
    $newContent = $newContent -replace "<!-- BUILD: .* -->", "<!-- BUILD: $timestamp | CACHE-BUST: $(Get-Random) -->"
    
    Set-Content -Path $distPath -Value $newContent
    Write-Host "âœ… Updated timestamp in $distPath" -ForegroundColor Green
} else {
    Write-Error "âŒ dist/index.html not found!"
}

# 2. Sync to root index.html (Golden Path)
Copy-Item -Path $distPath -Destination "index.html" -Force
Write-Host "âœ… Synced dist/index.html -> index.html (Root Override for Cloudflare)" -ForegroundColor Green

# 3. Git Commit & Push
Write-Host "ðŸ“¦ Committing changes..." -ForegroundColor Yellow
git add dist/index.html index.html
git commit -m "deploy: Sovereign Terminal v1.1 Build $timestamp"

Write-Host "ðŸš€ Pushing to GitHub (Triggers Cloudflare Build)..." -ForegroundColor Yellow
git push origin main

Write-Host "âœ… Deployment initiated! Wait ~2 mins for Cloudflare Pages." -ForegroundColor Green
Write-Host "ðŸ”— Monitor: https://dash.cloudflare.com/" -ForegroundColor Gray

