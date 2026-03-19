Import-Module Posh-SSH -ErrorAction Stop

$devices = @(
    @{ N = '1'; Targets = @('mecamdev1.local', '10.2.1.3'); P = 'Kidcudi1' },
    @{ N = '2'; Targets = @('mecamdev2.local', '10.2.1.2'); P = 'Kidcudi123' },
    @{ N = '3'; Targets = @('mecamdev3.local', '10.2.1.5'); P = 'Kidcudi123' },
    @{ N = '4'; Targets = @('mecamdev4.local', '10.2.1.9'); P = 'Kidcudi1234' },
    @{ N = '5'; Targets = @('mecamdev5.local', '10.2.1.6'); P = 'Kidcudi12345' },
    @{ N = '6'; Targets = @('mecamdev6.local', '10.2.1.20'); P = 'Kidcudi123456' }
)

$summary = @()

foreach ($d in $devices) {
    $cred = [pscredential]::new('pi', (ConvertTo-SecureString $d.P -AsPlainText -Force))
    $session = $null
    $targetUsed = ''

    foreach ($t in $d.Targets) {
        try {
            $session = New-SSHSession -ComputerName $t -Credential $cred -AcceptKey -ConnectionTimeout 12 -ErrorAction Stop
            $targetUsed = $t
            break
        }
        catch {
            continue
        }
    }

    if (-not $session) {
        Write-Host "D$($d.N): unreachable" -ForegroundColor Red
        $summary += [pscustomobject]@{
            Device  = "D$($d.N)"
            Host    = 'unreachable'
            Status  = 'FAILED'
            Service = 'unknown'
            Ffmpeg  = 'unknown'
            Tts     = 'unknown'
            Aplay   = 'unknown'
            Health  = 'unknown'
            Notes   = 'SSH unreachable'
        }
        continue
    }

    $sid = $session.SessionId

    $remoteCmd = @'
set -e
sudo systemctl stop mecamera 2>/dev/null || true
sudo systemctl stop mecam-lite 2>/dev/null || true
sudo systemctl stop mecamera-lite 2>/dev/null || true
cd /home/pi/ME_CAM-DEV
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
for d in \
  /home/pi/ME_CAM-DEV/motion_videos \
  /home/pi/ME_CAM-DEV/recordings \
  /home/pi/ME_CAM-DEV/recordings_encrypted \
  /home/pi/ME_CAM-DEV/encrypted_videos \
  /home/pi/ME_CAM-DEV/web/static/motion_events \
  /home/pi/ME_CAM-DEV/web/static/motion_videos \
  /home/pi/motion_thumbnails \
  /tmp/me_cam_cache; do
  mkdir -p "$d"
  rm -rf "$d"/* 2>/dev/null || true
done
rm -f /home/pi/ME_CAM-DEV/logs/*.log 2>/dev/null || true
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y ffmpeg espeak-ng alsa-utils curl jq
sudo systemctl daemon-reload
sudo systemctl restart mecamera 2>/dev/null || true
sudo systemctl restart mecam-lite 2>/dev/null || true
sudo systemctl restart mecamera-lite 2>/dev/null || true
sleep 3
echo "svc=$(systemctl is-active mecamera 2>/dev/null || true)"
echo "svc_lite=$(systemctl is-active mecam-lite 2>/dev/null || true)"
echo "svc_lite2=$(systemctl is-active mecamera-lite 2>/dev/null || true)"
echo "ffmpeg=$(command -v ffmpeg >/dev/null 2>&1 && echo ok || echo missing)"
echo "tts=$(command -v espeak-ng >/dev/null 2>&1 && echo ok || echo missing)"
echo "aplay=$(command -v aplay >/dev/null 2>&1 && echo ok || echo missing)"
echo "health=$(curl -s -m 5 http://localhost:8080/api/health || true)"
echo "battery=$(curl -s -m 5 http://localhost:8080/api/battery || true)"
'@

    try {
        $out = Invoke-SSHCommand -SessionId $sid -Command $remoteCmd -TimeOut 420 -ErrorAction Stop
        $txt = ($out.Output -join "`n")

        $svc = ([regex]::Match($txt, 'svc=([^\r\n]*)').Groups[1].Value)
        $svcLite = ([regex]::Match($txt, 'svc_lite=([^\r\n]*)').Groups[1].Value)
        $svcLite2 = ([regex]::Match($txt, 'svc_lite2=([^\r\n]*)').Groups[1].Value)
        $ff = ([regex]::Match($txt, 'ffmpeg=([^\r\n]*)').Groups[1].Value)
        $tts = ([regex]::Match($txt, 'tts=([^\r\n]*)').Groups[1].Value)
        $apl = ([regex]::Match($txt, 'aplay=([^\r\n]*)').Groups[1].Value)
        $health = ([regex]::Match($txt, 'health=([^\r\n]*)').Groups[1].Value)

        $serviceReady = ($svc -eq 'active' -or $svcLite -eq 'active' -or $svcLite2 -eq 'active')
        $ok = ($serviceReady -and $ff -eq 'ok' -and $tts -eq 'ok' -and $apl -eq 'ok' -and -not [string]::IsNullOrWhiteSpace($health))
        $status = if ($ok) { 'READY' } else { 'CHECK' }

        Write-Host "D$($d.N) [$targetUsed] $status svc=$svc/$svcLite/$svcLite2 ffmpeg=$ff tts=$tts aplay=$apl" -ForegroundColor $(if ($ok) { 'Green' } else { 'Yellow' })

        $summary += [pscustomobject]@{
            Device  = "D$($d.N)"
            Host    = $targetUsed
            Status  = $status
            Service = "$svc/$svcLite/$svcLite2"
            Ffmpeg  = $ff
            Tts     = $tts
            Aplay   = $apl
            Health  = if ([string]::IsNullOrWhiteSpace($health)) { 'missing' } else { 'ok' }
            Notes   = ''
        }
    }
    catch {
        Write-Host "D$($d.N) [$targetUsed] maintenance failed: $($_.Exception.Message)" -ForegroundColor Red
        $summary += [pscustomobject]@{
            Device  = "D$($d.N)"
            Host    = $targetUsed
            Status  = 'FAILED'
            Service = 'unknown'
            Ffmpeg  = 'unknown'
            Tts     = 'unknown'
            Aplay   = 'unknown'
            Health  = 'unknown'
            Notes   = $_.Exception.Message
        }
    }
    finally {
        if ($sid) {
            Remove-SSHSession -SessionId $sid | Out-Null
        }
    }
}

$summary | Format-Table -AutoSize
$summary | ConvertTo-Json -Depth 5 | Set-Content .\maintenance_1_6_results.json -Encoding UTF8
Write-Host 'Wrote maintenance_1_6_results.json'
