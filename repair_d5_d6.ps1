Import-Module Posh-SSH -ErrorAction Stop

function Fix-Device {
    param($Name, $IP, $Pass)
    
    Write-Host ""
    Write-Host "=== Fixing Device $Name [$IP] ==="
    $cred = [pscredential]::new('pi', (ConvertTo-SecureString $Pass -AsPlainText -Force))
    try {
        $ss = New-SSHSession -ComputerName $IP -Credential $cred -AcceptKey -ConnectionTimeout 15 -ErrorAction Stop
    } catch {
        Write-Host "  UNREACHABLE: $($_.Exception.Message.Split('.')[0])"
        return
    }
    
    # Step 1: Fix dpkg corruption
    Write-Host "  [1/5] Fixing dpkg..."
    $fix1 = "echo '$Pass' | sudo -S dpkg --configure -a 2>&1 | tail -5"
    $o1 = Invoke-SSHCommand -SessionId $ss.SessionId -Command $fix1 -TimeOut 60
    $o1.Output | ForEach-Object { Write-Host "    dpkg: $_" }
    
    # Step 2: Clean apt cache
    Write-Host "  [2/5] Cleaning apt cache..."
    $fix2 = "echo '$Pass' | sudo -S apt-get clean 2>&1; echo '$Pass' | sudo -S rm -f /var/lib/apt/lists/*.Packages /var/lib/apt/lists/*.InRelease /var/lib/apt/lists/*.Release 2>/dev/null; echo CLEAN_DONE"
    $o2 = Invoke-SSHCommand -SessionId $ss.SessionId -Command $fix2 -TimeOut 30
    $o2.Output | ForEach-Object { Write-Host "    clean: $_" }
    
    # Step 3: apt-get update
    Write-Host "  [3/5] apt update (may take ~60s)..."
    $fix3 = "echo '$Pass' | sudo -S apt-get update -qq 2>&1 | grep -E 'error|Error|Reading|Done|Err' | tail -5; echo APT_UPDATE_DONE"
    $o3 = Invoke-SSHCommand -SessionId $ss.SessionId -Command $fix3 -TimeOut 180
    $o3.Output | ForEach-Object { Write-Host "    update: $_" }
    
    # Step 4: Install ffmpeg and espeak
    Write-Host "  [4/5] Installing ffmpeg + espeak (may take ~3 min)..."
    $fix4 = "echo '$Pass' | sudo -S apt-get install -y --no-install-recommends ffmpeg espeak espeak-ng alsa-utils 2>&1 | tail -10; echo INSTALL_DONE"
    $o4 = Invoke-SSHCommand -SessionId $ss.SessionId -Command $fix4 -TimeOut 360
    $o4.Output | ForEach-Object { Write-Host "    install: $_" }
    
    # Step 5: Verify + restart service
    Write-Host "  [5/5] Verifying + restarting service..."
    $fix5 = "which ffmpeg 2>/dev/null || echo NO_FFMPEG; which espeak-ng 2>/dev/null || which espeak 2>/dev/null || echo NO_ESPEAK; echo '$Pass' | sudo -S systemctl restart mecamera 2>/dev/null; sleep 4; systemctl is-active mecamera"
    $o5 = Invoke-SSHCommand -SessionId $ss.SessionId -Command $fix5 -TimeOut 30
    $o5.Output | ForEach-Object { Write-Host "    check: $_" }
    
    Remove-SSHSession -SessionId $ss.SessionId | Out-Null
}

Fix-Device -Name "5" -IP "10.2.1.6"  -Pass "Kidcudi12345"
Fix-Device -Name "6" -IP "10.2.1.20" -Pass "Kidcudi123456"

Write-Host ""
Write-Host "=== REPAIR COMPLETE ==="
