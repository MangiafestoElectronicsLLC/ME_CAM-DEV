#!/usr/bin/env powershell
# Setup/Recovery for D5, D6, D7, D8

Import-Module Posh-SSH

$devices = @(
    @{ D='5'; H='mecamdev5.local'; P='Kidcudi12345'; Status='Fresh Flash' }
    @{ D='6'; H='mecamdev6.local'; P='Kidcudi123456'; Status='Reset Credentials' }
    @{ D='7'; H='mecamdev7.local'; P='Kiducdi1234567'; Status='New Deployment' }
    @{ D='8'; H='mecamdev8.local'; P='Kidcudi12345678'; Status='New Deployment' }
)

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  D5/D6/D7/D8 - SETUP & CREDENTIAL RESET                      ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

foreach ($dev in $devices) {
    Write-Host "┌─ Device D$($dev.D) ($($dev.Status))─────────────────────────────────" -ForegroundColor Yellow
    
    try {
        $cred = [pscredential]::new('pi', (ConvertTo-SecureString $dev.P -AsPlainText -Force))
        $session = New-SSHSession -ComputerName $dev.H -Credential $cred -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop
        $sid = $session.SessionId
        
        Write-Host "✓ SSH Connected" -ForegroundColor Green
        
        # Common setup for all devices
        Write-Host "  Setting up directories and configs..." -ForegroundColor White
        
        $setup_cmd = @'
cd ~/ME_CAM-DEV
echo "=== Git Status ===" && git status --short | head -3
echo "=== Config ===" && test -f config/config.json && echo "✓ config exists" || echo "⚠ config missing"
echo "=== Database ===" && test -f instance/users.db && echo "✓ database exists" || echo "⚠ database missing"
'@
        
        $out = Invoke-SSHCommand -SessionId $sid -Command $setup_cmd -TimeOut 20 -ErrorAction Stop
        $out.Output | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        
        # Reset/create admin account
        Write-Host "  Resetting admin credentials..." -ForegroundColor White
        
        $reset_admin = @'
cd ~/ME_CAM-DEV && python3 - <<'PY'
import sqlite3, os
from werkzeug.security import generate_password_hash

db_path = 'instance/users.db'
try:
    os.makedirs('instance', exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table if needed
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            pin TEXT,
            role TEXT
        )
    """)
    
    # Delete existing admin if any
    cursor.execute("DELETE FROM user WHERE username='admin'")
    
    # Create new admin
    admin_hash = generate_password_hash('admin123')
    cursor.execute("INSERT INTO user VALUES (NULL, 'admin', ?, '1234', 'admin')", (admin_hash,))
    
    conn.commit()
    conn.close()
    print('✓ Admin account reset: username=admin, password=admin123')
except Exception as e:
    print(f'✗ Error: {e}')
PY
'@
        
        $reset_out = Invoke-SSHCommand -SessionId $sid -Command $reset_admin -TimeOut 30 -ErrorAction Stop
        $reset_out.Output | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }
        
        Remove-SSHSession -SessionId $sid | Out-Null
        Write-Host "└─ ✓ D$($dev.D) READY`n" -ForegroundColor Green
        
    } catch {
        Write-Host "└─ ✗ D$($dev.D) Error: $($_.Exception.Message)`n" -ForegroundColor Red
    }
}

Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  LOGIN CREDENTIALS FOR ALL DEVICES (D5-D8)                   ║" -ForegroundColor Green
Write-Host "╠═══════════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  Username: admin                                             ║" -ForegroundColor Cyan
Write-Host "║  Password: admin123                                          ║" -ForegroundColor Cyan
Write-Host "╠═══════════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  Web Dashboards:                                             ║" -ForegroundColor Green
Write-Host "║  - D5: http://mecamdev5.local:8080                           ║" -ForegroundColor Yellow
Write-Host "║  - D6: http://mecamdev6.local:8080                           ║" -ForegroundColor Yellow
Write-Host "║  - D7: http://mecamdev7.local:8080                           ║" -ForegroundColor Yellow
Write-Host "║  - D8: http://mecamdev8.local:8080                           ║" -ForegroundColor Yellow
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
