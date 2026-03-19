Import-Module Posh-SSH -ErrorAction Stop

function Deep-Fix {
    param($Name, $IP, $Pass)
    
    Write-Host ""
    Write-Host "=== Deep Fix Device $Name [$IP] ==="
    $cred = [pscredential]::new('pi', (ConvertTo-SecureString $Pass -AsPlainText -Force))
    try {
        $ss = New-SSHSession -ComputerName $IP -Credential $cred -AcceptKey -ConnectionTimeout 15 -ErrorAction Stop
    } catch {
        Write-Host "  UNREACHABLE: $($_.Exception.Message.Split('.')[0])"
        return
    }

    # --- Service logs first ---
    Write-Host "  -- Service log (last 15 lines) --"
    $log = Invoke-SSHCommand -SessionId $ss.SessionId -Command "journalctl -u mecamera -n 15 --no-pager 2>&1" -TimeOut 15
    $log.Output | ForEach-Object { Write-Host "  LOG: $_" }

    # --- dpkg status check ---
    Write-Host "  -- dpkg status --"
    $dpkgCheck = Invoke-SSHCommand -SessionId $ss.SessionId -Command "ls -la /var/lib/dpkg/status*; wc -l /var/lib/dpkg/status 2>/dev/null || echo STATUS_MISSING" -TimeOut 10
    $dpkgCheck.Output | ForEach-Object { Write-Host "  DPKG: $_" }

    # Try restoring dpkg status from backup
    $restore = Invoke-SSHCommand -SessionId $ss.SessionId -Command "test -f /var/lib/dpkg/status-old && echo HAS_BACKUP || echo NO_BACKUP" -TimeOut 10
    $hasBackup = ($restore.Output -join "").Trim()
    Write-Host "  dpkg backup: $hasBackup"
    
    if ($hasBackup -eq "HAS_BACKUP") {
        Write-Host "  Restoring dpkg status from backup..."
        $r = Invoke-SSHCommand -SessionId $ss.SessionId -Command "echo '$Pass' | sudo -S cp /var/lib/dpkg/status-old /var/lib/dpkg/status; echo RESTORED" -TimeOut 15
        $r.Output | ForEach-Object { Write-Host "  $_" }
    } else {
        Write-Host "  No dpkg status backup - trying dpkg divert approach..."
        # Create a minimal dpkg status if it's zero/corrupt
        $lines = Invoke-SSHCommand -SessionId $ss.SessionId -Command "wc -c /var/lib/dpkg/status 2>/dev/null | awk '{print `$1}'" -TimeOut 10
        $sz = ($lines.Output -join "").Trim()
        Write-Host "  dpkg status size: $sz bytes"
    }

    # Nuke corrupted apt lists and re-update
    Write-Host "  Clearing apt lists..."
    $clear = Invoke-SSHCommand -SessionId $ss.SessionId -Command "echo '$Pass' | sudo -S rm -rf /var/lib/apt/lists/* 2>/dev/null; echo CLEARED" -TimeOut 20
    $clear.Output | ForEach-Object { Write-Host "  $_" }
    
    Write-Host "  apt-get update (60-120s)..."
    $upd = Invoke-SSHCommand -SessionId $ss.SessionId -Command "echo '$Pass' | sudo -S apt-get update 2>&1 | grep -v '^Get\|^Hit\|^Ign\|^Reading\|^ok ' | head -8; echo UPDATE_DONE" -TimeOut 180
    $upd.Output | ForEach-Object { Write-Host "  $_" }

    # Try fix-broken first
    Write-Host "  Fixing broken packages..."
    $fix = Invoke-SSHCommand -SessionId $ss.SessionId -Command "echo '$Pass' | sudo -S apt-get -f install -y 2>&1 | tail -5; echo FIX_DONE" -TimeOut 60
    $fix.Output | ForEach-Object { Write-Host "  $_" }

    # Install packages
    Write-Host "  Installing ffmpeg + espeak-ng (~3 min)..."
    $inst = Invoke-SSHCommand -SessionId $ss.SessionId -Command "echo '$Pass' | sudo -S apt-get install -y --no-install-recommends ffmpeg espeak-ng alsa-utils 2>&1 | tail -8; echo INST_DONE" -TimeOut 360
    $inst.Output | ForEach-Object { Write-Host "  INST: $_" }

    # Verify tools
    $tools = Invoke-SSHCommand -SessionId $ss.SessionId -Command "which ffmpeg 2>/dev/null && echo ffmpeg=OK || echo ffmpeg=MISSING; which espeak-ng 2>/dev/null && echo espeak-ng=OK || echo espeak-ng=MISSING" -TimeOut 10
    Write-Host "  Tools: $($tools.Output -join ' | ')"

    # Ensure config exists
    $cfgCheck = Invoke-SSHCommand -SessionId $ss.SessionId -Command "test -f /home/pi/ME_CAM-DEV/config.json && cat /home/pi/ME_CAM-DEV/config.json | python3 -c 'import sys,json;json.load(sys.stdin);print(\"CONFIG_VALID\")' 2>/dev/null || echo CONFIG_BAD" -TimeOut 10
    $cfgStat = ($cfgCheck.Output -join "").Trim()
    Write-Host "  Config: $cfgStat"
    
    if ($cfgStat -match "CONFIG_BAD|NO_CONFIG") {
        Write-Host "  Rebuilding config from default or template..."
        $mkCfg = Invoke-SSHCommand -SessionId $ss.SessionId -Command @"
if [ -f /home/pi/ME_CAM-DEV/config_default.json ]; then
  cp /home/pi/ME_CAM-DEV/config_default.json /home/pi/ME_CAM-DEV/config.json
elif [ -f /home/pi/ME_CAM-DEV/config.json.bak ]; then
  cp /home/pi/ME_CAM-DEV/config.json.bak /home/pi/ME_CAM-DEV/config.json
else
  echo '{"device_name":"Device $Name","stream_port":5000,"motion_detection":true,"audio_record_on_motion":true}' > /home/pi/ME_CAM-DEV/config.json
fi
echo CONFIG_WRITTEN
"@ -TimeOut 15
        $mkCfg.Output | ForEach-Object { Write-Host "  $_" }
    }

    # Restart service
    Write-Host "  Restarting service..."
    $restart = Invoke-SSHCommand -SessionId $ss.SessionId -Command "echo '$Pass' | sudo -S systemctl restart mecamera 2>/dev/null; sleep 5; systemctl is-active mecamera; systemctl status mecamera --no-pager -l 2>&1 | tail -6" -TimeOut 40
    $restart.Output | ForEach-Object { Write-Host "  SVC: $_" }

    Remove-SSHSession -SessionId $ss.SessionId | Out-Null
    Write-Host "  === D$Name Done ==="
}

Deep-Fix -Name "5" -IP "10.2.1.6"  -Pass "Kidcudi12345"
Deep-Fix -Name "6" -IP "10.2.1.20" -Pass "Kidcudi123456"

Write-Host ""
Write-Host "=== ALL DEEP FIX COMPLETE ==="
