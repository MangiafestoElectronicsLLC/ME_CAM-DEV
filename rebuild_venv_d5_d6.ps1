Import-Module Posh-SSH -ErrorAction Stop

function Rebuild-Venv {
    param($Name, $IP, $Pass)
    
    Write-Host ""
    Write-Host "=== Rebuilding venv on Device $Name [$IP] ==="
    $cred = [pscredential]::new('pi', (ConvertTo-SecureString $Pass -AsPlainText -Force))
    try {
        $ss = New-SSHSession -ComputerName $IP -Credential $cred -AcceptKey -ConnectionTimeout 15 -ErrorAction Stop
    } catch {
        Write-Host "  UNREACHABLE: $($_.Exception.Message.Split('.')[0])"
        return
    }

    # Check python3 availability
    $pyver = Invoke-SSHCommand -SessionId $ss.SessionId -Command "python3 --version 2>&1" -TimeOut 10
    Write-Host "  Python: $($pyver.Output -join ' ')"

    # Check if venv already exists
    $venvCheck = Invoke-SSHCommand -SessionId $ss.SessionId -Command "test -f /home/pi/ME_CAM-DEV/venv/bin/python3 && echo VENV_OK || echo VENV_MISSING" -TimeOut 10
    $venvStat = ($venvCheck.Output -join "").Trim()
    Write-Host "  Current venv: $venvStat"

    if ($venvStat -ne "VENV_OK") {
        # Create venv with system-site-packages (same as D1)
        Write-Host "  Creating venv (may take 30s)..."
        $mk = Invoke-SSHCommand -SessionId $ss.SessionId -Command "python3 -m venv --system-site-packages /home/pi/ME_CAM-DEV/venv 2>&1; echo VENV_CREATED" -TimeOut 60
        $mk.Output | ForEach-Object { Write-Host "  venv: $_" }
    }

    # Install essential pip packages
    Write-Host "  Installing pip packages (60-120s)..."
    $pip = Invoke-SSHCommand -SessionId $ss.SessionId -Command "/home/pi/ME_CAM-DEV/venv/bin/pip install --quiet Flask Werkzeug psutil cryptography qrcode loguru flask-cors 2>&1 | tail -8; echo PIP_DONE" -TimeOut 300
    $pip.Output | ForEach-Object { Write-Host "  pip: $_" }

    # Verify Flask installed
    $flaskCheck = Invoke-SSHCommand -SessionId $ss.SessionId -Command "/home/pi/ME_CAM-DEV/venv/bin/python3 -c 'import flask; print(flask.__version__)' 2>&1" -TimeOut 15
    Write-Host "  Flask: $($flaskCheck.Output -join ' ')"

    # Check config
    $cfg = Invoke-SSHCommand -SessionId $ss.SessionId -Command "test -s /home/pi/ME_CAM-DEV/config.json && echo CONFIG_OK || echo CONFIG_MISSING" -TimeOut 10
    $cfgStat = ($cfg.Output -join "").Trim()
    Write-Host "  Config: $cfgStat"

    if ($cfgStat -eq "CONFIG_MISSING") {
        Write-Host "  Creating config.json..."
        $minJson = '{"device_name":"Device' + $Name + '","stream_port":5000,"motion_detection":true,"audio_record_on_motion":true}'
        $cfgCmd = "[ -f /home/pi/ME_CAM-DEV/config_default.json ] && cp /home/pi/ME_CAM-DEV/config_default.json /home/pi/ME_CAM-DEV/config.json && echo COPIED_DEFAULT || echo '" + $minJson + "' > /home/pi/ME_CAM-DEV/config.json && echo CREATED_MINIMAL"
        $cfgResult = Invoke-SSHCommand -SessionId $ss.SessionId -Command $cfgCmd -TimeOut 15
        $cfgResult.Output | ForEach-Object { Write-Host "  config: $_" }
    }

    # Restart service and check
    Write-Host "  Restarting service..."
    $restart = Invoke-SSHCommand -SessionId $ss.SessionId -Command "echo '$Pass' | sudo -S systemctl restart mecamera 2>/dev/null; sleep 6; systemctl is-active mecamera" -TimeOut 30
    $svcState = ($restart.Output -join " ").Trim()
    Write-Host "  Service state: $svcState"

    if ($svcState -notmatch "^active") {
        # Check why it failed
        $why = Invoke-SSHCommand -SessionId $ss.SessionId -Command "journalctl -u mecamera -n 10 --no-pager 2>&1 | tail -8" -TimeOut 15
        $why.Output | ForEach-Object { Write-Host "  LOG: $_" }
    }

    Remove-SSHSession -SessionId $ss.SessionId | Out-Null
    Write-Host "  === D$Name Done ==="
}

Rebuild-Venv -Name "5" -IP "10.2.1.6"  -Pass "Kidcudi12345"
Rebuild-Venv -Name "6" -IP "10.2.1.20" -Pass "Kidcudi123456"

Write-Host ""
Write-Host "=== VENV REBUILD COMPLETE ==="
