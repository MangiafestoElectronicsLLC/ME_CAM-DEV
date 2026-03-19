Import-Module Posh-SSH -ErrorAction SilentlyContinue

function Run-Device {
    param($Name, $IP, $Pass)

    Write-Host ""
    Write-Host "=== D$Name [$IP] extract+restart ==="
    $cred=[pscredential]::new('pi',(ConvertTo-SecureString $Pass -AsPlainText -Force))

    try {
        $s=New-SSHSession -ComputerName $IP -Credential $cred -AcceptKey -ConnectionTimeout 12 -ErrorAction Stop
    } catch {
        Write-Host "  UNREACHABLE: $($_.Exception.Message)"
        return
    }

    $cmd = @"
cd /home/pi/ME_CAM-DEV
if [ -f runtime_bundle.tar ]; then
  tar -xf runtime_bundle.tar
  rc=$?
  if [ $rc -eq 0 ]; then
    echo EXTRACT_OK
    rm -f runtime_bundle.tar
  else
    echo EXTRACT_FAIL
  fi
else
  echo NO_BUNDLE
fi

if [ -f main.py ]; then echo MAIN_OK; else echo MAIN_MISSING; fi
if [ -f web/app_lite.py ]; then echo APP_OK; else echo APP_MISSING; fi

echo '$Pass' | sudo -S systemctl restart mecamera >/dev/null 2>&1
sleep 8
systemctl is-active mecamera
"@

    try {
        $o=Invoke-SSHCommand -SessionId $s.SessionId -Command $cmd -TimeOut 120 -ErrorAction Stop
        $o.Output | ForEach-Object { Write-Host "  $_" }

        if(($o.Output -join "`n") -notmatch "active") {
            $l=Invoke-SSHCommand -SessionId $s.SessionId -Command "journalctl -u mecamera -n 20 --no-pager | tail -12" -TimeOut 20
            $l.Output | ForEach-Object { Write-Host "  LOG: $_" }
        }
    } catch {
        Write-Host "  CMD ERROR: $($_.Exception.Message)"
    }

    Remove-SSHSession -SessionId $s.SessionId | Out-Null
}

Run-Device -Name '5' -IP '10.2.1.6' -Pass 'Kidcudi12345'
Run-Device -Name '6' -IP '10.2.1.20' -Pass 'Kidcudi123456'

Write-Host ""
Write-Host "DONE"
