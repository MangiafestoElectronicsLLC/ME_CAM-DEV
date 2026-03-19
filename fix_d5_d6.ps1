Import-Module Posh-SSH -ErrorAction Stop

Write-Host "=== Fixing Device 5 (10.2.1.6) ==="
$cred5 = [pscredential]::new('pi', (ConvertTo-SecureString 'Kidcudi12345' -AsPlainText -Force))
try {
    $ss = New-SSHSession -ComputerName '10.2.1.6' -Credential $cred5 -AcceptKey -ConnectionTimeout 15 -ErrorAction Stop
    
    # Fix apt repos and install packages
    Write-Host "  Installing packages on D5..."
    $cmd1 = "echo 'Kidcudi12345' | sudo -S apt-get update --allow-releaseinfo-change -q 2>&1 | tail -5"
    $o1 = Invoke-SSHCommand -SessionId $ss.SessionId -Command $cmd1 -TimeOut 120
    $o1.Output | ForEach-Object { Write-Host "  apt-update: $_" }
    
    $cmd2 = "echo 'Kidcudi12345' | sudo -S apt-get install -y ffmpeg espeak-ng alsa-utils 2>&1 | tail -10"
    $o2 = Invoke-SSHCommand -SessionId $ss.SessionId -Command $cmd2 -TimeOut 300
    $o2.Output | ForEach-Object { Write-Host "  apt-install: $_" }
    
    # Check for config.json
    Write-Host "  Checking config..."
    $cmd3 = "ls /home/pi/ME_CAM-DEV/config.json 2>/dev/null && echo CONFIG_OK || echo NO_CONFIG"
    $o3 = Invoke-SSHCommand -SessionId $ss.SessionId -Command $cmd3 -TimeOut 10
    $configStatus = $o3.Output -join ""
    Write-Host "  Config: $configStatus"
    
    # If no config, create default from template
    if ($configStatus -match "NO_CONFIG") {
        Write-Host "  Creating default config..."
        $cmd4 = "ls /home/pi/ME_CAM-DEV/config_default.json 2>/dev/null | head -1"
        $o4 = Invoke-SSHCommand -SessionId $ss.SessionId -Command $cmd4 -TimeOut 10
        if ($o4.Output -join "" -match "config_default") {
            $cmd4b = "cp /home/pi/ME_CAM-DEV/config_default.json /home/pi/ME_CAM-DEV/config.json"
            Invoke-SSHCommand -SessionId $ss.SessionId -Command "echo 'Kidcudi12345' | sudo -S sh -c '$cmd4b'" -TimeOut 15 | Out-Null
        } else {
            # Create minimal config
            $minConfig = '{"device_name":"Device 5","stream_port":5000,"audio_record_on_motion":true}'
            $cmd4c = "echo '$minConfig' > /home/pi/ME_CAM-DEV/config.json"
            Invoke-SSHCommand -SessionId $ss.SessionId -Command $cmd4c -TimeOut 10 | Out-Null
        }
        Write-Host "  Config created"
    }
    
    # Restart service
    Write-Host "  Restarting service..."
    $cmd5 = "echo 'Kidcudi12345' | sudo -S systemctl restart mecamera; sleep 4; systemctl is-active mecamera"
    $o5 = Invoke-SSHCommand -SessionId $ss.SessionId -Command $cmd5 -TimeOut 30
    Write-Host "  Service: $($o5.Output -join ' ')"
    
    # Verify tools
    $cmd6 = "which ffmpeg 2>/dev/null || echo NO_FFMPEG; which espeak-ng 2>/dev/null || echo NO_ESPEAK"
    $o6 = Invoke-SSHCommand -SessionId $ss.SessionId -Command $cmd6 -TimeOut 10
    Write-Host "  Tools: $($o6.Output -join ' | ')"
    
    Remove-SSHSession -SessionId $ss.SessionId | Out-Null
} catch {
    Write-Host "  D5 ERROR: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "=== Probing Device 6 ==="
$cred6 = [pscredential]::new('pi', (ConvertTo-SecureString 'Kidcudi123456' -AsPlainText -Force))
$d6hosts = @('10.2.1.20','mecamdev6.local','mecam6.local','pi6.local')
$found6 = ''
foreach ($h in $d6hosts) {
    try {
        $s = New-SSHSession -ComputerName $h -Credential $cred6 -AcceptKey -ConnectionTimeout 6 -ErrorAction Stop
        $found6 = $h
        Remove-SSHSession -SessionId $s.SessionId | Out-Null
        break
    } catch {}
}
if ($found6) {
    Write-Host "  D6 found at: $found6"
    $ss6 = New-SSHSession -ComputerName $found6 -Credential $cred6 -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop
    $o = Invoke-SSHCommand -SessionId $ss6.SessionId -Command "hostname -I; systemctl is-active mecamera" -TimeOut 10
    $o.Output | ForEach-Object { Write-Host "  $_" }
    Remove-SSHSession -SessionId $ss6.SessionId | Out-Null
} else {
    Write-Host "  D6 UNREACHABLE on all known addresses."
    Write-Host "  => Device 6 needs physical power cycle or network check."
}

Write-Host ""
Write-Host "DONE"
