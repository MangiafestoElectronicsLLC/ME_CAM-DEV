Import-Module Posh-SSH -ErrorAction Stop

function Inspect-Device {
    param($Name, $IP, $Pass)
    Write-Host ""
    Write-Host "=== D$Name [$IP] ==="
    $cred=[pscredential]::new('pi',(ConvertTo-SecureString $Pass -AsPlainText -Force))
    try {
        $s=New-SSHSession -ComputerName $IP -Credential $cred -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop
    } catch {
        Write-Host "UNREACHABLE: $($_.Exception.Message)"
        return
    }

    $o=Invoke-SSHCommand -SessionId $s.SessionId -Command "ls -la /home/pi/ME_CAM-DEV | head -30; echo ---MAIN---; ls -la /home/pi/ME_CAM-DEV/main.py 2>/dev/null || echo NO_MAIN; echo ---WEB---; ls -la /home/pi/ME_CAM-DEV/web/app_lite.py 2>/dev/null || echo NO_APP; echo ---BUNDLE---; ls -la /home/pi/ME_CAM-DEV/runtime_bundle.tar 2>/dev/null || echo NO_BUNDLE" -TimeOut 25
    $o.Output | ForEach-Object { Write-Host $_ }

    Remove-SSHSession -SessionId $s.SessionId | Out-Null
}

Inspect-Device -Name '5' -IP '10.2.1.6' -Pass 'Kidcudi12345'
Inspect-Device -Name '6' -IP '10.2.1.20' -Pass 'Kidcudi123456'
Write-Host "DONE"
