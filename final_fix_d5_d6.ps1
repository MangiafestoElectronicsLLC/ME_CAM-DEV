Import-Module Posh-SSH -ErrorAction Stop

# D5
Write-Host "=== D5 Fix ==="
$cred5=[pscredential]::new('pi',(ConvertTo-SecureString 'Kidcudi12345' -AsPlainText -Force))
try {
    $s5=New-SSHSession -ComputerName '10.2.1.6' -Credential $cred5 -AcceptKey -ConnectionTimeout 12 -ErrorAction Stop
    $cmd5=@'
/home/pi/ME_CAM-DEV/venv/bin/pip install loguru Flask Werkzeug flask-cors qrcode requests urllib3 PyYAML cryptography 2>&1 | tail -20
/home/pi/ME_CAM-DEV/venv/bin/python3 -c "import loguru, flask; print('PY_OK')"
echo "Kidcudi12345" | sudo -S systemctl restart mecamera
sleep 8
systemctl is-active mecamera
'@
    $o5=Invoke-SSHCommand -SessionId $s5.SessionId -Command $cmd5 -TimeOut 300
    $o5.Output | ForEach-Object { Write-Host "  $_" }
    if(($o5.Output -join "`n") -notmatch "active"){
      $l5=Invoke-SSHCommand -SessionId $s5.SessionId -Command "journalctl -u mecamera -n 15 --no-pager" -TimeOut 20
      $l5.Output | ForEach-Object { Write-Host "  LOG: $_" }
    }
    Remove-SSHSession -SessionId $s5.SessionId | Out-Null
} catch { Write-Host "  D5 error: $($_.Exception.Message)" }

# D6
Write-Host "=== D6 Fix ==="
$cred6=[pscredential]::new('pi',(ConvertTo-SecureString 'Kidcudi123456' -AsPlainText -Force))
try {
    Set-SCPItem -ComputerName '10.2.1.20' -Credential $cred6 -AcceptKey -Path (Join-Path (Get-Location) 'main.py') -Destination '/home/pi/ME_CAM-DEV' -Force -ErrorAction Stop | Out-Null
    $s6=New-SSHSession -ComputerName '10.2.1.20' -Credential $cred6 -AcceptKey -ConnectionTimeout 12 -ErrorAction Stop
    $cmd6=@'
ls -la /home/pi/ME_CAM-DEV/main.py
/home/pi/ME_CAM-DEV/venv/bin/pip install loguru Flask Werkzeug flask-cors qrcode requests urllib3 PyYAML cryptography 2>&1 | tail -20
/home/pi/ME_CAM-DEV/venv/bin/python3 -c "import loguru, flask; print('PY_OK')"
echo "Kidcudi123456" | sudo -S systemctl restart mecamera
sleep 8
systemctl is-active mecamera
'@
    $o6=Invoke-SSHCommand -SessionId $s6.SessionId -Command $cmd6 -TimeOut 300
    $o6.Output | ForEach-Object { Write-Host "  $_" }
    if(($o6.Output -join "`n") -notmatch "active"){
      $l6=Invoke-SSHCommand -SessionId $s6.SessionId -Command "journalctl -u mecamera -n 15 --no-pager" -TimeOut 20
      $l6.Output | ForEach-Object { Write-Host "  LOG: $_" }
    }
    Remove-SSHSession -SessionId $s6.SessionId | Out-Null
} catch { Write-Host "  D6 error: $($_.Exception.Message)" }

Write-Host "DONE"
