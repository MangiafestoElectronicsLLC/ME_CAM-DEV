#!/usr/bin/env powershell
# Get enrollment key and device info for D6, D7, D8

Import-Module Posh-SSH

$devices = @(
    @{ D='6'; H='mecamdev6.local'; P='Kidcudi123456' }
    @{ D='7'; H='mecamdev7.local'; P='Kiducdi1234567' }
    @{ D='8'; H='mecamdev8.local'; P='Kidcudi12345678' }
)

Write-Host "`n╔═════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║ CUSTOMER SECURITY KEY & REGISTRATION INFO for D6-D8    ║" -ForegroundColor Green
Write-Host "╚═════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

foreach ($dc in $devices) {
    Write-Host "Device D$($dc.D):" -ForegroundColor Yellow
    Write-Host "  URL: http://$($dc.H):8080" -ForegroundColor Cyan
    
    try {
        $cred = [pscredential]::new('pi', (ConvertTo-SecureString $dc.P -AsPlainText -Force))
        $session = New-SSHSession -ComputerName $dc.H -Credential $cred -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop
        $sid = $session.SessionId
        
        # Get enrollment key
        $cmd = 'python3 -c "import json; c=json.load(open(\"~/ME_CAM-DEV/config/config.json\")); k=c.get(\"security\",{}).get(\"enrollment_key\",\"NOT_FOUND\"); print(k if k!=\"NOT_FOUND\" else \"GENERATE_NEW\")"'
        
        $out = Invoke-SSHCommand -SessionId $sid -Command $cmd -TimeOut 10 -ErrorAction SilentlyContinue
        $key = ($out.Output | Select-Object -First 1).Trim()
        
        if ($key -eq "GENERATE_NEW" -or [string]::IsNullOrEmpty($key)) {
            Write-Host "  Security Key: [Needs to be generated - see below]" -ForegroundColor Red
            Write-Host "  Action: Use recover_login.py to generate key" -ForegroundColor Yellow
        } else {
            Write-Host "  Security Key: $key" -ForegroundColor Green
        }
        
        # Get device name
        $nameCmd = 'python3 -c "import json; c=json.load(open(\"~/ME_CAM-DEV/config/config.json\")); print(c.get(\"device_name\",\"UNKNOWN\"))"'
        $nameOut = Invoke-SSHCommand -SessionId $sid -Command $nameCmd -TimeOut 10 -ErrorAction SilentlyContinue
        $devName = ($nameOut.Output | Select-Object -First 1).Trim()
        Write-Host "  Device Name: $devName" -ForegroundColor Cyan
        
        Remove-SSHSession -SessionId $sid | Out-Null
        Write-Host ""
        
    } catch {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "╔═════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ REGISTRATION INSTRUCTIONS                              ║" -ForegroundColor Cyan
Write-Host "╠═════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║ 1. Click 'Already have an account? Login' link          ║" -ForegroundColor White
Write-Host "║ 2. Try credentials: admin / admin                       ║" -ForegroundColor White
Write-Host "║ 3. If that fails, use the Security Key shown above      ║" -ForegroundColor White
Write-Host "╚═════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host "`n╔═════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║ WHY HOSTNAME INSTEAD OF IP?                             ║" -ForegroundColor Magenta
Write-Host "╠═════════════════════════════════════════════════════════╣" -ForegroundColor Magenta
Write-Host "║ • mDNS (.local) is more reliable than IP addresses      ║" -ForegroundColor White
Write-Host "║ • devices remain accessible even if DHCP lease changes  ║" -ForegroundColor White
Write-Host "║ • easier to remember names than IPs                     ║" -ForegroundColor White
Write-Host "║ • works across different networks automatically         ║" -ForegroundColor White
Write-Host "║ • e.g. mecamdev6.local always points to Device 6        ║" -ForegroundColor White
Write-Host "╠═════════════════════════════════════════════════════════╣" -ForegroundColor Magenta
Write-Host "║ If you need IP addresses:                               ║" -ForegroundColor White
Write-Host "║   nslookup mecamdev6.local                              ║" -ForegroundColor Cyan
Write-Host "║   ping mecamdev6.local -4                               ║" -ForegroundColor Cyan
Write-Host "╚═════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
