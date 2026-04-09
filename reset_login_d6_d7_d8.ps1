#!/usr/bin/env powershell
# Reset admin login on D6, D7, D8

Import-Module Posh-SSH -ErrorAction Stop

$devices = @(
    @{ D='6'; H='mecamdev6.local'; P='Kidcudi123456' }
    @{ D='7'; H='mecamdev7.local'; P='Kiducdi1234567' }
    @{ D='8'; H='mecamdev8.local'; P='Kidcudi12345678' }
)

foreach ($dc in $devices) {
    Write-Host "`n=== Resetting Admin Login for D$($dc.D) ===" -ForegroundColor Cyan
    
    try {
        $cred = [pscredential]::new('pi', (ConvertTo-SecureString $dc.P -AsPlainText -Force))
        $s = New-SSHSession -ComputerName $dc.H -Credential $cred -AcceptKey -ConnectionTimeout 10
        $sid = $s.SessionId
        
        Write-Host "Connected to D$($dc.D)" -ForegroundColor Yellow
        
        # Reset admin password
        $reset_cmd = @"
cd ~/ME_CAM-DEV && python3 << 'EOF'
import sqlite3
import os
from werkzeug.security import generate_password_hash

db_path = 'instance/users.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM user')
    users = cursor.fetchall()
    print(f'Existing users: {[u[0] for u in users]}')
    new_hash = generate_password_hash('admin')
    cursor.execute('UPDATE user SET password = ? WHERE username = ?', (new_hash, 'admin'))
    if cursor.rowcount == 0:
        cursor.execute('INSERT INTO user (username, password) VALUES (?, ?)', ('admin', new_hash))
        print('✓ Created admin user')
    else:
        print('✓ Updated admin password')
    conn.commit()
    conn.close()
    print('✓ Admin ready: username=admin, password=admin')
else:
    print('✗ Database not found')
EOF
"@
        
        $output = Invoke-SSHCommand -SessionId $sid -Command $reset_cmd -TimeOut 30
        Write-Host $output.Output -ForegroundColor White
        
        Remove-SSHSession -SessionId $sid | Out-Null
        Write-Host "✓ D$($dc.D) password reset complete" -ForegroundColor Green
        
    } catch {
        Write-Host "✗ D$($dc.D) failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== Web Login Credentials ===" -ForegroundColor Cyan
Write-Host "Username: admin" -ForegroundColor Yellow
Write-Host "Password: admin" -ForegroundColor Yellow
Write-Host "`nBrowsers are open at:" -ForegroundColor Cyan
Write-Host "  http://mecamdev6.local:8080" -ForegroundColor Yellow
Write-Host "  http://mecamdev7.local:8080" -ForegroundColor Yellow
Write-Host "  http://mecamdev8.local:8080" -ForegroundColor Yellow
