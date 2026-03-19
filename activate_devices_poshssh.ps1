param(
    [string]$User = "pi",
    [string]$RemotePath = "/home/pi/ME_CAM-DEV",
    [hashtable]$HostMap = @{
        1 = "mecamdev1.local"
        2 = "mecamdev2.local"
        3 = "mecamdev3.local"
        4 = "mecamdev4.local"
        5 = "mecamdev5.local"
        6 = "mecamdev6.local"
        7 = "mecamdev7.local"
        8 = "mecamdev8.local"
    }
)

$ErrorActionPreference = "Continue"
Import-Module Posh-SSH -ErrorAction Stop

function Write-Stage($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-WarnMsg($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERR] $msg" -ForegroundColor Red }

function Get-DevicePassword([int]$deviceNumber) {
    switch ($deviceNumber) {
        1 { return "Kidcudi1" }
        2 { return "Kidcudi123" }
        3 { return "Kidcudi123" }
        4 { return "Kidcudi1234" }
        5 { return "Kidcudi12345" }
        6 { return "Device6" }
        7 { return "Kidcudi1234567" }
        8 { return "Kidcudi12345678" }
        default { return $null }
    }
}

function New-DeviceSession([int]$deviceNumber, [string]$deviceHost) {
    $plain = Get-DevicePassword $deviceNumber
    if (-not $plain) { return $null }
    $sec = ConvertTo-SecureString $plain -AsPlainText -Force
    $cred = [System.Management.Automation.PSCredential]::new($User, $sec)

    try {
        return New-SSHSession -ComputerName $deviceHost -Credential $cred -AcceptKey -ConnectionTimeout 8 -ErrorAction Stop
    }
    catch {
        Write-Err "Session failed for device $deviceNumber ($deviceHost): $_"
        return $null
    }
}

function Upload-Targets([int]$deviceNumber, [string]$deviceHost) {
    $plain = Get-DevicePassword $deviceNumber
    $sec = ConvertTo-SecureString $plain -AsPlainText -Force
    $cred = [System.Management.Automation.PSCredential]::new($User, $sec)

    $targets = @("main.py", "web", "src", "config", "scripts", "requirements.txt", "requirements-webrtc.txt")
    foreach ($target in $targets) {
        if (Test-Path $target) {
            try {
                Set-SCPItem -ComputerName $deviceHost -Credential $cred -AcceptKey -Path $target -Destination $RemotePath -Force -ErrorAction Stop | Out-Null
            }
            catch {
                Write-WarnMsg "Upload failed for $target on $deviceHost : $_"
            }
        }
    }
}

function Invoke-Remote($sessionId, [string]$command) {
    try {
        return (Invoke-SSHCommand -SessionId $sessionId -Command $command -TimeOut 120).Output
    }
    catch {
        return @("ERROR: $_")
    }
}

$ok = 0
$fail = 0

foreach ($device in 1..8) {
    $deviceHost = $HostMap[$device]
    if (-not $deviceHost) {
        Write-WarnMsg "No host mapped for device $device"
        $fail++
        continue
    }

    Write-Stage "Device $device ($deviceHost)"
    $session = New-DeviceSession -deviceNumber $device -deviceHost $deviceHost
    if (-not $session) {
        $fail++
        continue
    }

    $sessionId = $session.SessionId
    Write-Ok "SSH connected"

    Upload-Targets -deviceNumber $device -deviceHost $deviceHost

    $setupCmd = @"
set -e
cd $RemotePath
if [ -f scripts/generate_config.py ]; then
  if [ $device -eq 7 ]; then
    python3 scripts/generate_config.py --profile device7 --device-number 7 --force || true
  elif [ $device -eq 4 ]; then
    python3 scripts/generate_config.py --profile device4 --device-number 4 --force || true
  else
    python3 scripts/generate_config.py --profile device3 --device-number $device --force || true
  fi
fi
if [ ! -d venv ]; then
  python3 -m venv venv --system-site-packages
fi
source venv/bin/activate
python -m pip install --upgrade pip >/dev/null 2>&1 || true
pip install -r requirements.txt >/tmp/mecam_pip_install.log 2>&1 || true
sudo systemctl daemon-reload || true
sudo systemctl restart mecamera || true
sleep 2
"@

    [void](Invoke-Remote -sessionId $sessionId -command $setupCmd)

    $validateCmd = @"
echo '--- SERVICE ---'
sudo systemctl is-active mecamera || true
echo '--- API ---'
curl -s -m 5 http://localhost:8080/api/status || true
echo
echo '--- WIFI ---'
curl -s -m 5 http://localhost:8080/api/network/wifi || true
echo
echo '--- BATTERY ---'
curl -s -m 5 http://localhost:8080/api/battery || true
"@

    $out = Invoke-Remote -sessionId $sessionId -command $validateCmd
    $out | ForEach-Object { Write-Host $_ }

    if ((($out -join "`n").Trim()).Length -gt 0) {
        Write-Ok "Activation + validation ran"
        $ok++
    }
    else {
        Write-WarnMsg "Validation output was inconclusive"
        $fail++
    }

    Remove-SSHSession -SessionId $sessionId | Out-Null
}

Write-Stage "Summary"
Write-Host "Successful: $ok" -ForegroundColor Green
Write-Host "Failed/Inconclusive: $fail" -ForegroundColor Yellow
