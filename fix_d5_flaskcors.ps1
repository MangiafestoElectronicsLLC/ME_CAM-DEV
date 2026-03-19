Import-Module Posh-SSH -ErrorAction Stop
$cred=[pscredential]::new('pi',(ConvertTo-SecureString 'Kidcudi12345' -AsPlainText -Force))
Set-SCPItem -ComputerName '10.2.1.6' -Credential $cred -AcceptKey -Path (Join-Path (Get-Location) 'wheel_tmp\flask_cors-6.0.1-py3-none-any.whl') -Destination '/home/pi/ME_CAM-DEV' -Force | Out-Null
$s=New-SSHSession -ComputerName '10.2.1.6' -Credential $cred -AcceptKey -ConnectionTimeout 12 -ErrorAction Stop
$cmd=@'
/home/pi/ME_CAM-DEV/venv/bin/pip install --no-cache-dir /home/pi/ME_CAM-DEV/flask_cors-6.0.1-py3-none-any.whl 2>&1 | tail -20
/home/pi/ME_CAM-DEV/venv/bin/python3 -c "import loguru, flask_cors; print('PKG_OK')"
echo "Kidcudi12345" | sudo -S systemctl restart mecamera
sleep 8
systemctl is-active mecamera
'@
$o=Invoke-SSHCommand -SessionId $s.SessionId -Command $cmd -TimeOut 240
$o.Output | ForEach-Object { Write-Host $_ }
if(($o.Output -join "`n") -notmatch "active"){
  $l=Invoke-SSHCommand -SessionId $s.SessionId -Command "journalctl -u mecamera -n 20 --no-pager | tail -12" -TimeOut 20
  $l.Output | ForEach-Object { Write-Host "LOG: $_" }
}
Remove-SSHSession -SessionId $s.SessionId | Out-Null
Write-Host "DONE"
