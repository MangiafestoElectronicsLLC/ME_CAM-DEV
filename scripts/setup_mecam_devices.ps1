#!/usr/bin/env pwsh

##############################################################################
# ME_CAM Setup Helper - Windows PowerShell
# 
# Purpose: Setup multiple Raspberry Pi devices with ME_CAM from Windows
# Features:
#   - Copy setup script to Pi
#   - Run automated setup
#   - Monitor logs
#   - Test connectivity
#
# Usage: .\setup_mecam_devices.ps1
#
# Author: MangiafestoElectronics LLC
# Date: Feb 2026
##############################################################################

#Requires -Version 5.0

$ErrorActionPreference = "Continue"

# Color helpers
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "[SUCCESS] $args" -ForegroundColor Green }
function Write-Warn { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }

##############################################################################
# Main Menu
##############################################################################

function Show-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   ME_CAM Setup Helper - Windows            ║" -ForegroundColor Cyan
    Write-Host "║   Raspberry Pi Camera System               ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Setup Single Device"
    Write-Host "2. Setup Multiple Devices"
    Write-Host "3. Check Device Status"
    Write-Host "4. View Device Logs"
    Write-Host "5. Reboot Device"
    Write-Host "6. Exit"
    Write-Host ""
}

##############################################################################
# Setup Single Device
##############################################################################

function Setup-SingleDevice {
    param(
        [string]$Hostname,
        [string]$Username,
        [string]$Password,
        [int]$DeviceNumber
    )
    
    if (-not $Hostname) {
        Write-Info "Enter Pi hostname or IP (e.g., mecamdev6.local, 10.2.1.100):"
        $Hostname = Read-Host
    }
    
    if (-not $Username) {
        Write-Info "Enter SSH username [default: pi]:"
        $user_input = Read-Host
        $Username = if ($user_input) { $user_input } else { "pi" }
    }
    
    if (-not $Password) {
        Write-Info "Enter SSH password:"
        $secpasswd = Read-Host -AsSecureString
        $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUni($secpasswd))
    }
    
    # Test connectivity
    Write-Info "Testing connectivity to $Hostname..."
    
    # Simple TCP test on port 22
    $socket = New-Object Net.Sockets.TcpClient
    try {
        $socket.Connect($Hostname, 22)
        if ($socket.Connected) {
            Write-Success "Connected to $Hostname"
        }
        $socket.Close()
    }
    catch {
        Write-Error "Cannot connect to $Hostname. Check hostname/IP and WiFi connection."
        return $false
    }
    
    # Copy setup script
    Write-Info "Copying setup script to $Hostname..."
    
    $scriptPath = Join-Path $PSScriptRoot ".." "scripts" "auto_setup_mecam.sh"
    
    if (-not (Test-Path $scriptPath)) {
        Write-Error "Setup script not found at: $scriptPath"
        return $false
    }
    
    try {
        # Use scp to copy (requires openssh or git bash)
        & scp -q $scriptPath "$Username@${Hostname}`:~/" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Script copied successfully"
        }
        else {
            Write-Warn "SCP may not be available. Trying alternative method..."
            # Alternative: use SSH to fetch from GitHub
            $cmd = "curl -sSL https://raw.githubusercontent.com/MangiafestoElectronicsLLC/ME_CAM-DEV/main/scripts/auto_setup_mecam.sh -o ~/auto_setup_mecam.sh"
            & ssh "$Username@$Hostname" $cmd
        }
    }
    catch {
        Write-Error "Failed to copy script: $_"
        return $false
    }
    
    # Run setup script
    Write-Info "Running setup script on $Hostname..."
    Write-Warn "This will take 10-15 minutes. Please be patient..."
    
    if ($DeviceNumber) {
        # For automated setup (would need script modifications to accept args)
        # For now, run interactively
        Write-Info "Note: You will be prompted for device number on the Pi"
    }
    
    try {
        & ssh "$Username@$Hostname" "bash ~/auto_setup_mecam.sh"
    }
    catch {
        Write-Error "SSH command failed: $_"
        return $false
    }
    
    Write-Success "Setup complete for $Hostname!"
    Write-Info "Next steps:"
    Write-Info "  1. Reboot: ssh $Username@$Hostname 'sudo reboot'"
    Write-Info "  2. Wait 2 minutes"
    Write-Info "  3. Access at: http://$Hostname:8080"
    
    return $true
}

##############################################################################
# Setup Multiple Devices
##############################################################################

function Setup-MultipleDevices {
    Write-Info "Enter device hostnames (one per line, empty line to finish):"
    Write-Info "Example: mecamdev6.local, mecamdev7.local"
    Write-Host ""
    
    $devices = @()
    $index = 1
    
    while ($true) {
        Write-Host "Device $index hostname (or press Enter to finish):"
        $hostname = Read-Host
        
        if ([string]::IsNullOrWhiteSpace($hostname)) {
            break
        }
        
        $devices += @{ hostname = $hostname; number = $index }
        $index++
    }
    
    if ($devices.Count -eq 0) {
        Write-Warn "No devices entered"
        return
    }
    
    # Get credentials once
    Write-Info "Enter SSH credentials (will be used for all devices):"
    Write-Info "Username [default: pi]:"
    $user_input = Read-Host
    $Username = if ($user_input) { $user_input } else { "pi" }
    
    Write-Info "Password:"
    $secpasswd = Read-Host -AsSecureString
    $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUni($secpasswd))
    
    # Setup each device
    $succeeded = 0
    $failed = 0
    
    foreach ($device in $devices) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "Setting up: $($device.hostname)" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        
        if (Setup-SingleDevice -Hostname $device.hostname -Username $Username -Password $Password -DeviceNumber $device.number) {
            $succeeded++
        }
        else {
            $failed++
        }
        
        if ($failed -eq 0 -and $succeeded -lt $devices.Count) {
            Write-Info "Waiting 30 seconds before next device..."
            Start-Sleep -Seconds 30
        }
    }
    
    # Summary
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Setup Summary" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Success "Completed: $succeeded device(s)"
    if ($failed -gt 0) {
        Write-Warn "Failed: $failed device(s)"
    }
}

##############################################################################
# Check Device Status
##############################################################################

function Check-DeviceStatus {
    Write-Info "Enter Pi hostname or IP:"
    $Hostname = Read-Host
    
    Write-Info "Enter SSH username [default: pi]:"
    $user_input = Read-Host
    $Username = if ($user_input) { $user_input } else { "pi" }
    
    Write-Info "Enter SSH password:"
    $secpasswd = Read-Host -AsSecureString
    $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUni($secpasswd))
    
    Write-Host ""
    Write-Info "Getting status from $Hostname..."
    
    $commands = @(
        @{ name = "Hostname"; cmd = "hostname" },
        @{ name = "IP Address"; cmd = "hostname -I" },
        @{ name = "Uptime"; cmd = "uptime" },
        @{ name = "Camera Service"; cmd = "sudo systemctl status mecamera" },
        @{ name = "Memory Usage"; cmd = "free -h" },
        @{ name = "Disk Usage"; cmd = "df -h /" }
    )
    
    foreach ($cmd in $commands) {
        Write-Host ""
        Write-Host "--- $($cmd.name) ---" -ForegroundColor Cyan
        
        try {
            $output = & ssh "$Username@$Hostname" $cmd.cmd 2>$null
            $output | ForEach-Object { Write-Host $_ }
        }
        catch {
            Write-Error "Failed to execute: $($cmd.name)"
        }
    }
}

##############################################################################
# View Device Logs
##############################################################################

function View-DeviceLogs {
    Write-Info "Enter Pi hostname or IP:"
    $Hostname = Read-Host
    
    Write-Info "Enter SSH username [default: pi]:"
    $user_input = Read-Host
    $Username = if ($user_input) { $user_input } else { "pi" }
    
    Write-Info "Enter SSH password:"
    $secpasswd = Read-Host -AsSecureString
    $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUni($secpasswd))
    
    Write-Info "View logs (this will stream live logs, press Ctrl+C to stop):"
    
    & ssh "$Username@$Hostname" "sudo journalctl -u mecamera -f"
}

##############################################################################
# Reboot Device
##############################################################################

function Reboot-Device {
    Write-Info "Enter Pi hostname or IP:"
    $Hostname = Read-Host
    
    Write-Info "Enter SSH username [default: pi]:"
    $user_input = Read-Host
    $Username = if ($user_input) { $user_input } else { "pi" }
    
    Write-Info "Enter SSH password:"
    $secpasswd = Read-Host -AsSecureString
    $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUni($secpasswd))
    
    Write-Warn "Are you sure you want to reboot $Hostname? (yes/no)"
    $confirm = Read-Host
    
    if ($confirm -eq "yes") {
        Write-Info "Rebooting $Hostname..."
        & ssh "$Username@$Hostname" "sudo reboot" 2>$null
        Write-Success "Reboot command sent. Device will restart in 30 seconds."
        Write-Info "Access will be available again in ~2 minutes"
    }
    else {
        Write-Info "Reboot cancelled"
    }
}

##############################################################################
# Main Loop
##############################################################################

function Main {
    while ($true) {
        Show-Menu
        Write-Host "Enter choice (1-6):"
        $choice = Read-Host
        
        switch ($choice) {
            "1" {
                Write-Host ""
                Setup-SingleDevice
                Write-Host ""
                Read-Host "Press Enter to continue"
            }
            "2" {
                Write-Host ""
                Setup-MultipleDevices
                Write-Host ""
                Read-Host "Press Enter to continue"
            }
            "3" {
                Write-Host ""
                Check-DeviceStatus
                Write-Host ""
                Read-Host "Press Enter to continue"
            }
            "4" {
                Write-Host ""
                View-DeviceLogs
                Write-Host ""
                Read-Host "Press Enter to continue"
            }
            "5" {
                Write-Host ""
                Reboot-Device
                Write-Host ""
                Read-Host "Press Enter to continue"
            }
            "6" {
                Write-Host "Goodbye!" -ForegroundColor Green
                exit 0
            }
            default {
                Write-Warn "Invalid choice. Please try again."
                Start-Sleep -Seconds 2
            }
        }
    }
}

# Run main
Main
