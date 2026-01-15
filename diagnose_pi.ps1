#!/usr/bin/env pwsh
# ============================================================
# ME Camera LITE MODE - Quick Diagnostics & Recovery
# ============================================================

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   ME CAMERA LITE MODE - Diagnostics & Recovery" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Pi connection details
$piHost = "10.2.1.47"
$piUser = "pi"

Write-Host "Checking Pi at: $piHost" -ForegroundColor Yellow
Write-Host ""

# Step 1: Check if Pi is reachable
Write-Host "[1/6] Testing network connection..." -NoNewline
$pingResult = Test-Connection -ComputerName $piHost -Count 1 -Quiet -ErrorAction SilentlyContinue
if (-not $pingResult) {
    Write-Host " ❌ FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Pi is not responding to ping." -ForegroundColor Red
    Write-Host "Possible causes:" -ForegroundColor Yellow
    Write-Host "  • Pi is powered off or rebooting" -ForegroundColor Gray
    Write-Host "  • Network cable/WiFi disconnected" -ForegroundColor Gray
    Write-Host "  • IP address changed" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Try:" -ForegroundColor Yellow
    Write-Host "  1. Power cycle the Pi (unplug/replug power)" -ForegroundColor Gray
    Write-Host "  2. Wait 60 seconds for boot" -ForegroundColor Gray
    Write-Host "  3. Run this script again" -ForegroundColor Gray
    exit 1
}
Write-Host " ✅ OK" -ForegroundColor Green

# Step 2: Check SSH connection
Write-Host "[2/6] Testing SSH connection..." -NoNewline
$sshTest = ssh -o ConnectTimeout=5 -o BatchMode=yes "${piUser}@${piHost}" "echo OK" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host " ⚠️  SSH requires password" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "SSH connection available (will prompt for password)" -ForegroundColor Gray
} else {
    Write-Host " ✅ OK" -ForegroundColor Green
}

# Step 3: Check LITE MODE service
Write-Host "[3/6] Checking LITE MODE service..." -NoNewline
$serviceStatus = ssh "${piUser}@${piHost}" "systemctl is-active mecamera-lite 2>/dev/null || echo 'inactive'" 2>$null
if ($serviceStatus -match "active") {
    Write-Host " ✅ RUNNING" -ForegroundColor Green
} elseif ($serviceStatus -match "inactive") {
    Write-Host " ❌ STOPPED" -ForegroundColor Red
    
    # Try to start it
    Write-Host ""
    Write-Host "Attempting to start LITE MODE service..." -ForegroundColor Yellow
    ssh "${piUser}@${piHost}" "sudo systemctl start mecamera-lite"
    Start-Sleep -Seconds 3
    
    $serviceStatus = ssh "${piUser}@${piHost}" "systemctl is-active mecamera-lite 2>/dev/null"
    if ($serviceStatus -match "active") {
        Write-Host "✅ Service started successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to start service" -ForegroundColor Red
    }
} else {
    Write-Host " ⚠️  NOT INSTALLED" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "LITE MODE service not found. Checking standard service..." -ForegroundColor Yellow
    
    $stdService = ssh "${piUser}@${piHost}" "systemctl is-active mecamera 2>/dev/null || echo 'inactive'" 2>$null
    if ($stdService -match "active") {
        Write-Host "✅ Standard ME Camera service is running" -ForegroundColor Green
        Write-Host ""
        Write-Host "Note: Standard mode may not work well on Pi Zero 2W (512MB RAM)" -ForegroundColor Yellow
        Write-Host "Consider installing LITE MODE: .\deploy_lite_mode.ps1" -ForegroundColor Cyan
    } else {
        Write-Host "❌ No ME Camera service running" -ForegroundColor Red
    }
}

# Step 4: Check port 8080
Write-Host "[4/6] Checking web server (port 8080)..." -NoNewline
$portCheck = ssh "${piUser}@${piHost}" "sudo netstat -tlnp 2>/dev/null | grep ':8080' || echo 'not listening'" 2>$null
if ($portCheck -match "LISTEN") {
    Write-Host " ✅ LISTENING" -ForegroundColor Green
} else {
    Write-Host " ❌ NOT LISTENING" -ForegroundColor Red
}

# Step 5: Check recent logs
Write-Host "[5/6] Checking logs for errors..." -ForegroundColor Yellow
Write-Host ""
$logs = ssh "${piUser}@${piHost}" "sudo journalctl -u mecamera-lite -n 20 --no-pager 2>/dev/null || sudo journalctl -u mecamera -n 20 --no-pager 2>/dev/null" 2>$null
if ($logs) {
    Write-Host "Recent logs:" -ForegroundColor Gray
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    Write-Host $logs -ForegroundColor Gray
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
} else {
    Write-Host "⚠️  No logs available" -ForegroundColor Yellow
}

# Step 6: Memory check
Write-Host ""
Write-Host "[6/6] Checking available memory..." -NoNewline
$memInfo = ssh "${piUser}@${piHost}" "free -m | grep Mem | awk '{print \`$4}'" 2>$null
if ($memInfo) {
    $freeMem = [int]$memInfo
    if ($freeMem -lt 50) {
        Write-Host " ⚠️  LOW ($freeMem MB free)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Pi Zero 2W is running low on memory!" -ForegroundColor Yellow
        Write-Host "This is why standard mode doesn't work well." -ForegroundColor Gray
    } else {
        Write-Host " ✅ OK ($freeMem MB free)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   DIAGNOSIS COMPLETE" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Provide recommendations
Write-Host "📋 RECOMMENDED ACTIONS:" -ForegroundColor Yellow
Write-Host ""

if ($pingResult -and $portCheck -match "LISTEN") {
    Write-Host "✅ Pi is online and web server is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Try accessing:" -ForegroundColor White
    Write-Host "  • http://${piHost}:8080" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "If browser still can't connect:" -ForegroundColor Yellow
    Write-Host "  1. Check Windows Firewall" -ForegroundColor Gray
    Write-Host "  2. Try different browser" -ForegroundColor Gray
    Write-Host "  3. Try incognito/private mode" -ForegroundColor Gray
} elseif ($pingResult -and $serviceStatus -notmatch "active") {
    Write-Host "⚠️  Pi is online but service not running" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To fix:" -ForegroundColor White
    Write-Host "  Option 1: Restart service" -ForegroundColor Cyan
    ssh "${piUser}@${piHost}" "sudo systemctl restart mecamera-lite || sudo systemctl restart mecamera"
    Write-Host ""
    Write-Host "  Option 2: Check what went wrong" -ForegroundColor Cyan
    Write-Host "    ssh ${piUser}@${piHost}" -ForegroundColor Gray
    Write-Host "    sudo journalctl -u mecamera-lite -n 50" -ForegroundColor Gray
} else {
    Write-Host "❌ Pi appears to be offline or unreachable" -ForegroundColor Red
    Write-Host ""
    Write-Host "To fix:" -ForegroundColor White
    Write-Host "  1. Power cycle Pi (unplug, wait 10 sec, replug)" -ForegroundColor Gray
    Write-Host "  2. Wait 60 seconds for boot" -ForegroundColor Gray
    Write-Host "  3. Run this script again" -ForegroundColor Gray
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan

# Offer quick fixes
Write-Host ""
$choice = Read-Host "Would you like to try quick fixes? (Y/N)"
if ($choice -eq "Y" -or $choice -eq "y") {
    Write-Host ""
    Write-Host "Applying quick fixes..." -ForegroundColor Yellow
    Write-Host ""
    
    # Stop both services
    Write-Host "1. Stopping any running services..." -NoNewline
    ssh "${piUser}@${piHost}" "sudo systemctl stop mecamera mecamera-lite 2>/dev/null"
    Write-Host " ✅" -ForegroundColor Green
    
    # Start LITE MODE
    Write-Host "2. Starting LITE MODE..." -NoNewline
    ssh "${piUser}@${piHost}" "sudo systemctl start mecamera-lite 2>/dev/null"
    Start-Sleep -Seconds 5
    Write-Host " ✅" -ForegroundColor Green
    
    # Check status
    Write-Host "3. Checking status..." -NoNewline
    $finalStatus = ssh "${piUser}@${piHost}" "systemctl is-active mecamera-lite 2>/dev/null"
    if ($finalStatus -match "active") {
        Write-Host " ✅ RUNNING" -ForegroundColor Green
        Write-Host ""
        Write-Host "✅ LITE MODE is now running!" -ForegroundColor Green
        Write-Host "   Access at: http://${piHost}:8080" -ForegroundColor Cyan
    } else {
        Write-Host " ❌ FAILED" -ForegroundColor Red
        Write-Host ""
        Write-Host "Service failed to start. Checking logs..." -ForegroundColor Yellow
        ssh "${piUser}@${piHost}" "sudo journalctl -u mecamera-lite -n 30 --no-pager"
    }
}
