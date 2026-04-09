#!/usr/bin/env powershell
# Reset admin login on D6, D7, D8 - SIMPLE VERSION

Import-Module Posh-SSH

$devices = @(
    @{ D='6'; H='mecamdev6.local'; P='Kidcudi123456' }
    @{ D='7'; H='mecamdev7.local'; P='Kiducdi1234567' }
    @{ D='8'; H='mecamdev8.local'; P='Kidcudi12345678' }
)

foreach ($dc in $devices) {
    Write-Host "`n=== D$($dc.D) Password Reset ===" -ForegroundColor Cyan
    
    try {
        $cred = [pscredential]::new('pi', (ConvertTo-SecureString $dc.P -AsPlainText -Force))
        $session = New-SSHSession -ComputerName $dc.H -Credential $cred -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop
        $sid = $session.SessionId
        
        Write-Host "Connected - Resetting password..." -ForegroundColor Yellow
        
        $cmd = 'cd ~/ME_CAM-DEV && python3 -c "import sqlite3, os;from werkzeug.security import generate_password_hash;db=sqlite3.connect(''instance/users.db'');db.execute(''UPDATE user SET password=? WHERE username=?'',(generate_password_hash(''admin''),''admin''));db.commit();print(''Admin password reset to: admin'')"'
        
        $out = Invoke-SSHCommand -SessionId $sid -Command $cmd -TimeOut 30 -ErrorAction Stop
        Write-Host $out.Output -ForegroundColor Green
        
        Remove-SSHSession -SessionId $sid | Out-Null
        Write-Host "✓ D$($dc.D) ready" -ForegroundColor Green
        
    } catch {
        Write-Host "Error on D$($dc.D): $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  WEB LOGIN CREDENTIALS FOR ALL DEVICES  ║" -ForegroundColor Green
Write-Host "╠════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  Username: admin                        ║" -ForegroundColor Yellow
Write-Host "║  Password: admin                        ║" -ForegroundColor Yellow
Write-Host "╠════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  Open in browser:                       ║" -ForegroundColor Green
Write-Host "║  - http://mecamdev6.local:8080          ║" -ForegroundColor Yellow
Write-Host "║  - http://mecamdev7.local:8080          ║" -ForegroundColor Yellow
Write-Host "║  - http://mecamdev8.local:8080          ║" -ForegroundColor Yellow
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green
