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
            $session = New-SSHSession -ComputerName $t -Credential $cred -AcceptKey -ConnectionTimeout 10 -ErrorAction Stop
            $targetUsed = $t
            break
        }
        catch {
            continue
        }
    }

    if (-not $session) {
        Write-Host "D$($d.N): unreachable" -ForegroundColor Red
        $summary += [pscustomobject]@{ Device = "D$($d.N)"; Host = 'unreachable'; Reachable = $false; Service = 'unknown'; Health = 'unknown'; MotionFiles = 'unknown'; Notes = 'SSH unreachable' }
        continue
    }

    $sid = $session.SessionId

        try {
                $cleanupCmd = @'
cd /home/pi/ME_CAM-DEV
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
for d in /home/pi/ME_CAM-DEV/motion_videos /home/pi/ME_CAM-DEV/recordings /home/pi/ME_CAM-DEV/recordings_encrypted /home/pi/ME_CAM-DEV/encrypted_videos /home/pi/ME_CAM-DEV/web/static/motion_events /home/pi/ME_CAM-DEV/web/static/motion_videos /home/pi/motion_thumbnails /tmp/me_cam_cache; do
    mkdir -p "$d"
    rm -rf "$d"/* 2>/dev/null || true
done
rm -f /home/pi/ME_CAM-DEV/logs/*.log 2>/dev/null || true
sudo systemctl restart mecamera 2>/dev/null || sudo systemctl restart mecam-lite 2>/dev/null || true
sleep 2
echo "SVC=$(systemctl is-active mecamera 2>/dev/null || systemctl is-active mecam-lite 2>/dev/null || true)"
echo "HEALTH=$(curl -s -m 5 http://localhost:8080/api/health 2>/dev/null || true)"
count=0
for d in /home/pi/ME_CAM-DEV/motion_videos /home/pi/ME_CAM-DEV/recordings /home/pi/ME_CAM-DEV/recordings_encrypted /home/pi/ME_CAM-DEV/encrypted_videos /home/pi/ME_CAM-DEV/web/static/motion_events /home/pi/ME_CAM-DEV/web/static/motion_videos /home/pi/motion_thumbnails; do
    c=$(ls -1 "$d" 2>/dev/null | wc -l)
    count=$((count + c))
done
echo "MOTION_FILES=$count"
'@

        $out = Invoke-SSHCommand -SessionId $sid -Command $cleanupCmd -TimeOut 120 -ErrorAction Stop
        $txt = ($out.Output -join "`n")

        $svc = ([regex]::Match($txt, 'SVC=([^\r\n]*)').Groups[1].Value)
        $health = ([regex]::Match($txt, 'HEALTH=([^\r\n]*)').Groups[1].Value)
        $motionFiles = ([regex]::Match($txt, 'MOTION_FILES=([^\r\n]*)').Groups[1].Value)

        Write-Host "D$($d.N) [$targetUsed] svc=$svc motion_files=$motionFiles" -ForegroundColor Green

        $summary += [pscustomobject]@{
            Device = "D$($d.N)"
            Host = $targetUsed
            Reachable = $true
            Service = if ($svc) { $svc } else { 'unknown' }
            Health = if ([string]::IsNullOrWhiteSpace($health)) { 'missing' } else { 'ok' }
            MotionFiles = if ($motionFiles) { $motionFiles } else { 'unknown' }
            Notes = ''
        }
    }
    catch {
        Write-Host "D$($d.N) [$targetUsed] cleanup failed: $($_.Exception.Message)" -ForegroundColor Yellow
        $summary += [pscustomobject]@{ Device = "D$($d.N)"; Host = $targetUsed; Reachable = $true; Service = 'unknown'; Health = 'unknown'; MotionFiles = 'unknown'; Notes = $_.Exception.Message }
    }
    finally {
        if ($sid) { Remove-SSHSession -SessionId $sid | Out-Null }
    }
}

$summary | Format-Table -AutoSize
$summary | ConvertTo-Json -Depth 4 | Set-Content .\maintenance_cleanup_1_6_results.json -Encoding UTF8
Write-Host 'Wrote maintenance_cleanup_1_6_results.json'
