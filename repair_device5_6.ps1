param(
    [string]$User = "pi",
    [string]$Profile = "device4",
    [string]$Device5Host = "mecamdev5.local",
    [string]$Device6Host = "mecamdev6.local"
)

$ErrorActionPreference = "Stop"

$devices = @(
    @{ Number = 5; Host = $Device5Host },
    @{ Number = 6; Host = $Device6Host }
)

$failed = @()
$sshOptions = @('-o', 'StrictHostKeyChecking=accept-new', '-o', 'UserKnownHostsFile=$HOME/.ssh/known_hosts')

foreach ($device in $devices) {
    $deviceNumber = [int]$device.Number
    $hostName = [string]$device.Host
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "Repairing Device $deviceNumber ($hostName)" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan

    try {
        Write-Host "Uploading repair script..." -ForegroundColor Yellow
        & scp @sshOptions .\repair_device5_6.sh "$User@${hostName}:~/repair_device5_6.sh"
        if ($LASTEXITCODE -ne 0) {
            throw "SCP failed for $hostName"
        }

        Write-Host "Running repair script..." -ForegroundColor Yellow
        & ssh @sshOptions "$User@${hostName}" "chmod +x ~/repair_device5_6.sh ; ~/repair_device5_6.sh $deviceNumber $Profile"
        if ($LASTEXITCODE -ne 0) {
            throw "Repair failed on $hostName"
        }

        Write-Host "Device $deviceNumber repair completed." -ForegroundColor Green
    }
    catch {
        Write-Host "Device $deviceNumber failed: $($_.Exception.Message)" -ForegroundColor Red
        $failed += "Device $deviceNumber ($hostName)"
        continue
    }
}

if ($failed.Count -gt 0) {
    Write-Host "Completed with failures:" -ForegroundColor Yellow
    $failed | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
    exit 1
}

Write-Host "All repairs completed for devices 5 and 6." -ForegroundColor Green
