Import-Module Posh-SSH -ErrorAction Stop

$bundleZip = Join-Path $PSScriptRoot "mecam_recovery_bundle.zip"
$bundleItems = @(
    "main.py",
    "web",
    "src",
    "config",
    "scripts",
    "etc/systemd/system/mecamera.service",
    "requirements.txt",
    "requirements-webrtc.txt"
)

if (Test-Path $bundleZip) {
    Remove-Item $bundleZip -Force
}

Push-Location $PSScriptRoot
try {
    $existingItems = @($bundleItems | Where-Object { Test-Path $_ })
    if ($existingItems.Count -eq 0) {
        throw "No bundle source items found in workspace."
    }
    Compress-Archive -Path $existingItems -DestinationPath $bundleZip -CompressionLevel Fastest -Force
} finally {
    Pop-Location
}

$devices = @(
    @{ N = 3; Host = 'mecamdev3.local'; Ip = '10.2.1.5'; Password = 'Kidcudi123'; Profile = 'device3' },
    @{ N = 5; Host = 'mecamdev5.local'; Ip = '10.2.1.6'; Password = 'Kidcudi12345'; Profile = 'device5' },
    @{ N = 7; Host = 'mecamdev7.local'; Ip = '10.2.1.7'; Password = 'Kidcudi1234567'; Profile = 'device7' },
    @{ N = 8; Host = 'mecamdev8.local'; Ip = '10.2.1.8'; Password = 'Kidcudi12345678'; Profile = 'device8' }
)

function Connect-Device($d) {
    $cred = [pscredential]::new('pi', (ConvertTo-SecureString $d.Password -AsPlainText -Force))
    foreach ($target in @($d.Ip, $d.Host)) {
        try {
            $s = New-SSHSession -ComputerName $target -Credential $cred -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop
            return @{ Session = $s; Target = $target }
        } catch {
            continue
        }
    }
    return $null
}

function Ensure-RepoPresent($d, $sid) {
    $check = Invoke-SSHCommand -SessionId $sid -Command "test -d /home/pi/ME_CAM-DEV && echo REPO_OK || echo REPO_MISSING" -TimeOut 30
    if (($check.Output -join "`n") -match "REPO_OK") {
        return
    }

    Write-Host "D$($d.N): ME_CAM-DEV missing, uploading recovery bundle..." -ForegroundColor Yellow
    Set-SCPItem -SessionId $sid -Path $bundleZip -Destination "/tmp/mecam_recovery_bundle.zip" -Force

    $extract = @"
set -e
mkdir -p /home/pi/ME_CAM-DEV
python3 -c "import zipfile; zipfile.ZipFile('/tmp/mecam_recovery_bundle.zip').extractall('/home/pi/ME_CAM-DEV')"
chown -R pi:pi /home/pi/ME_CAM-DEV || true
echo BUNDLE_EXTRACTED
"@
    $out = Invoke-SSHCommand -SessionId $sid -Command $extract -TimeOut 120
    $out.Output | ForEach-Object { Write-Host $_ }
}

foreach ($d in $devices) {
    Write-Host "`n=== D$($d.N) recovery ===" -ForegroundColor Cyan

    $ping = Test-Connection -ComputerName $d.Ip -Count 1 -Quiet -ErrorAction SilentlyContinue
    if (-not $ping) {
        Write-Host "D$($d.N) offline at $($d.Ip). Check power/Wi-Fi first." -ForegroundColor Red
        continue
    }

    $conn = Connect-Device $d
    if (-not $conn) {
        Write-Host "D$($d.N) reachable by ping but SSH failed (password or SSH service)." -ForegroundColor Yellow
        continue
    }

    $sid = $conn.Session.SessionId
    Write-Host "Connected via $($conn.Target)" -ForegroundColor Green

    try {
        Ensure-RepoPresent -d $d -sid $sid
    } catch {
        Write-Host "D$($d.N): bundle upload/extract failed: $($_.Exception.Message)" -ForegroundColor Red
        Remove-SSHSession -SessionId $sid | Out-Null
        continue
    }

    $cmd = @"
set -e
cd /home/pi
cd /home/pi/ME_CAM-DEV
if [ ! -f /etc/systemd/system/mecamera.service ]; then
  sudo cp etc/systemd/system/mecamera.service /etc/systemd/system/mecamera.service || true
fi
sudo apt-get install -y python3-venv python3-pip >/dev/null 2>&1 || true
if [ -f scripts/generate_config.py ]; then
  python3 scripts/generate_config.py --profile $($d.Profile) --device-number $($d.N) --force || true
fi
if [ ! -d venv ]; then
  python3 -m venv venv --system-site-packages
fi
. venv/bin/activate
python -m pip install --upgrade pip >/dev/null 2>&1 || true
pip install -r requirements.txt >/tmp/mecam_pip_install.log 2>&1 || true
sudo hostnamectl set-hostname $($d.Host -replace '\.local$','') || true
sudo systemctl enable avahi-daemon 2>/dev/null || true
sudo systemctl restart avahi-daemon 2>/dev/null || true
sudo systemctl daemon-reload || true
sudo systemctl restart mecamera || true
sleep 2
echo HOSTNAME=`$(hostname)
echo IPS=`$(hostname -I)
echo SERVICE=`$(systemctl is-active mecamera 2>/dev/null || true)
echo API=`$(curl -s -m 5 http://localhost:8080/api/health 2>/dev/null || true)
"@

    try {
        $out = Invoke-SSHCommand -SessionId $sid -Command $cmd -TimeOut 240
        $out.Output | ForEach-Object { Write-Host $_ }
    } catch {
        Write-Host "Recovery command failed on D$($d.N): $($_.Exception.Message)" -ForegroundColor Red
    }

    Remove-SSHSession -SessionId $sid | Out-Null
}

Write-Host "`nDone. If .local still fails for D7/D8, use IP URLs:" -ForegroundColor Cyan
Write-Host "D7: http://10.2.1.7:8080" -ForegroundColor Yellow
Write-Host "D8: http://10.2.1.8:8080" -ForegroundColor Yellow

if (Test-Path $bundleZip) {
    Remove-Item $bundleZip -Force -ErrorAction SilentlyContinue
}
