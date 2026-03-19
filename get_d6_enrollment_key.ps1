#!/usr/bin/env powershell
# Extract enrollment key from D6

Import-Module Posh-SSH

$device_info = @{
    D = '6'
    H = 'mecamdev6.local'
    P = 'Kidcudi123456'
}

try {
    $cred = [pscredential]::new('pi', (ConvertTo-SecureString $device_info.P -AsPlainText -Force))
    $session = New-SSHSession -ComputerName $device_info.H -Credential $cred -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop
    $sid = $session.SessionId
    
    # Extract enrollment key from config
    $cmd = 'cat ~/ME_CAM-DEV/config/config.json | python3 -c "import json, sys; d=json.load(sys.stdin); print(d.get(\"security\",{}).get(\"enrollment_key\",\"NOT_FOUND\"))"'
    $out = Invoke-SSHCommand -SessionId $sid -Command $cmd -TimeOut 15 -ErrorAction Stop
    $enrollment_key = ($out.Output | Select-Object -First 1).Trim()
    
    Remove-SSHSession -SessionId $sid | Out-Null
    
    # Display results
    Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  D6 CUSTOMER SECURITY KEY (Enrollment Key)                ║" -ForegroundColor Green
    Write-Host "╠═══════════════════════════════════════════════════════════╣" -ForegroundColor Green
    Write-Host "║ IP Address: 10.2.1.20                                     ║" -ForegroundColor Cyan
    Write-Host "║ Hostname:   mecamdev6.local                               ║" -ForegroundColor Cyan
    Write-Host "║                                                           ║" -ForegroundColor White
    
    if ($enrollment_key -eq "NOT_FOUND" -or [string]::IsNullOrEmpty($enrollment_key)) {
        Write-Host "║ Key: [Not set - needs recovery]                           ║" -ForegroundColor Red
    } else {
        Write-Host "║ Key: $enrollment_key                               ║" -ForegroundColor Yellow
    }
    
    Write-Host "║                                                           ║" -ForegroundColor White
    Write-Host "╠═══════════════════════════════════════════════════════════╣" -ForegroundColor Green
    Write-Host "║ REGISTRATION INSTRUCTIONS:                                ║" -ForegroundColor Green
    Write-Host "╠═══════════════════════════════════════════════════════════╣" -ForegroundColor Green
    Write-Host "║                                                           ║" -ForegroundColor White
    Write-Host "║ 1. Open: http://mecamdev6.local:8080                      ║" -ForegroundColor Cyan
    Write-Host "║ 2. Click 'Already have an account? Login'                 ║" -ForegroundColor Cyan
    Write-Host "║ 3. Enter:                                                 ║" -ForegroundColor Cyan
    Write-Host "║    Username: admin                                        ║" -ForegroundColor Yellow
    Write-Host "║    Password: admin123                                     ║" -ForegroundColor Yellow
    Write-Host "║                                                           ║" -ForegroundColor White
    Write-Host "║ If login fails or you need registration:                  ║" -ForegroundColor White
    Write-Host "║ 1. Fill in username & password on registration form       ║" -ForegroundColor Cyan
    Write-Host "║ 2. Paste enrollment key in Customer Security Key field    ║" -ForegroundColor Cyan
    Write-Host "║                                                           ║" -ForegroundColor White
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
