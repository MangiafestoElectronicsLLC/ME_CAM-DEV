$hostsPath = "$env:WINDIR\System32\drivers\etc\hosts"
$entries = @(
    @{ Ip = '10.2.1.5'; Host = 'mecamdev3.local' },
    @{ Ip = '10.2.1.6'; Host = 'mecamdev5.local' },
    @{ Ip = '10.2.1.7'; Host = 'mecamdev7.local' },
    @{ Ip = '10.2.1.8'; Host = 'mecamdev8.local' },
    @{ Ip = '10.2.1.20'; Host = 'mecamdev6.local' }
)

if (-not (Test-Path $hostsPath)) {
    Write-Host "Hosts file not found: $hostsPath" -ForegroundColor Red
    exit 1
}

$content = Get-Content $hostsPath -ErrorAction Stop
$changed = $false

foreach ($e in $entries) {
    $line = "$($e.Ip) `t$($e.Host)"
    $exists = $content | Where-Object { $_ -match "(^|\s)$([regex]::Escape($e.Host))(\s|$)" }
    if (-not $exists) {
        Add-Content -Path $hostsPath -Value $line -ErrorAction Stop
        Write-Host "Added: $line" -ForegroundColor Green
        $changed = $true
    } else {
        Write-Host "Exists: $($e.Host)" -ForegroundColor Yellow
    }
}

if ($changed) {
    ipconfig /flushdns | Out-Null
    Write-Host "DNS cache flushed." -ForegroundColor Green
}

Write-Host "Done." -ForegroundColor Cyan
