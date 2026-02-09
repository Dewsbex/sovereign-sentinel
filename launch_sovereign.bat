@echo off
REM Sovereign Sentinel v1.9.4 - One-Click Launch Bridge
REM Wraps PowerShell pre-flight checks and initiates SSH tunnel

powershell -ExecutionPolicy Bypass -NoProfile -Command ^
    "$MasterPath = 'data/master_universe.json'; " ^
    "$GlobalPath = 'data/instruments.json'; " ^
    "$KillFlag = 'data/kill_flag.lock'; " ^
    "Write-Host '--- SOVEREIGN SENTINEL: PRE-FLIGHT BRIDGE V1.9.4 ---' -ForegroundColor Cyan; " ^
    "if (Test-Path $KillFlag) { " ^
    "    Write-Host '⚠️  EMERGENCY LOCK DETECTED: data/kill_flag.lock is ACTIVE.' -ForegroundColor Red; " ^
    "    Write-Host '   System will remain in safe-mode until file is deleted.' -ForegroundColor Gray; " ^
    "} else { " ^
    "    Write-Host '✅ Emergency System: CLEAR' -ForegroundColor Green; " ^
    "}; " ^
    "if (Test-Path $MasterPath) { " ^
    "    $MasterData = Get-Content $MasterPath | ConvertFrom-Json; " ^
    "    $Count = $MasterData.instruments.Count; " ^
    "    Write-Host \"[OK] Master Universe: $Count vetted tickers (Job C Ready)\" -ForegroundColor Green; " ^
    "} else { " ^
    "    Write-Host '[FAIL] master_universe.json missing. Run python build_universe.py' -ForegroundColor Red; " ^
    "}; " ^
    "if (Test-Path $GlobalPath) { " ^
    "    $GlobalData = Get-Content $GlobalPath | ConvertFrom-Json; " ^
    "    $Count = $GlobalData.instruments.Count; " ^
    "    Write-Host \"[OK] Global Map: $Count instruments (Manual Hub Ready)\" -ForegroundColor Green; " ^
    "} else { " ^
    "    Write-Host '[FAIL] instruments.json missing. T212 sync required.' -ForegroundColor Red; " ^
    "}; " ^
    "Write-Host \"`n--- INITIATING VPS TUNNEL (LONDON ORACLE) ---\" -ForegroundColor Yellow; " ^
    "Write-Host 'Action Required: Once logged in, verify crontab -l matches vps_crontab.txt' -ForegroundColor Gray; " ^
    "ssh -i \"Stores/ssh-key-2026-02-08.key\" ubuntu@145.241.226.107"
