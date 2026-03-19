#!/usr/bin/env powershell
# Extract enrollment key from D6

Import-Module Posh-SSH

$device_h = 'mecamdev6.local'
$device_p = 'Kidcudi123456'

try {
    $cred = [pscredential]::new('pi', (ConvertTo-SecureString $device_p -AsPlainText -Force))
    $session = New-SSHSession -ComputerName $device_h -Credential $cred -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop
    $sid = $session.SessionId
    
    $cmd = "cat ~/ME_CAM-DEV/config/config.json | python3 -c `"import json, sys; d=json.load(sys.stdin); print(d.get('security',{}).get('enrollment_key','NOT_FOUND'))`""
    $out = Invoke-SSHCommand -SessionId $sid -Command $cmd -TimeOut 15 -ErrorAction Stop
    $key = ($out.Output | Select-Object -First 1).Trim()
    
    Remove-SSHSession -SessionId $sid | Out-Null
    
    Write-Host ""
    Write-Host "D6 ENROLLMENT KEY (Customer Security Key):" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "Key: $key" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Register at: http://mecamdev6.local:8080" -ForegroundColor Cyan
    Write-Host "Use key above in Customer Security Key field" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
