Import-Module Posh-SSH -ErrorAction Stop

$items = @('main.py','main_lite.py','src','web','scripts','utils','cloud','notifications','setup_mode')
$targets = @(
  @{N='5';IP='10.2.1.6';P='Kidcudi12345'},
  @{N='6';IP='10.2.1.20';P='Kidcudi123456'}
)

foreach($t in $targets){
  Write-Host ""
  Write-Host "=== Push core to D$($t.N) ==="
  $cred=[pscredential]::new('pi',(ConvertTo-SecureString $t.P -AsPlainText -Force))
  foreach($i in $items){
    $p = Join-Path (Get-Location) $i
    if(Test-Path $p){
      try {
        Set-SCPItem -ComputerName $t.IP -Credential $cred -AcceptKey -Path $p -Destination '/home/pi/ME_CAM-DEV' -Force -ErrorAction Stop | Out-Null
        Write-Host "  copied $i"
      } catch {
        Write-Host "  failed $i :: $($_.Exception.Message)"
      }
    }
  }

  try {
    $s=New-SSHSession -ComputerName $t.IP -Credential $cred -AcceptKey -ConnectionTimeout 12 -ErrorAction Stop
    $cmd = "ls -la /home/pi/ME_CAM-DEV/src/utils/pi_detect.py 2>/dev/null || echo NO_PI_DETECT; /home/pi/ME_CAM-DEV/venv/bin/pip install --upgrade pip >/dev/null 2>&1 || true; /home/pi/ME_CAM-DEV/venv/bin/pip install loguru Flask 2>&1 | tail -12; echo '$($t.P)' | sudo -S systemctl restart mecamera; sleep 8; systemctl is-active mecamera"
    $o=Invoke-SSHCommand -SessionId $s.SessionId -Command $cmd -TimeOut 300
    $o.Output | ForEach-Object { Write-Host "  $_" }
    if(($o.Output -join "`n") -notmatch "active"){
      $l=Invoke-SSHCommand -SessionId $s.SessionId -Command "journalctl -u mecamera -n 12 --no-pager" -TimeOut 20
      $l.Output | ForEach-Object { Write-Host "  LOG: $_" }
    }
    Remove-SSHSession -SessionId $s.SessionId | Out-Null
  } catch {
    Write-Host "  SSH CMD failed: $($_.Exception.Message)"
  }
}

Write-Host "DONE"
