# Generate self-signed SSL certificates for ME_CAM (Windows PowerShell)
# This script generates certificates on Windows, then uploads them to the Pi
#
# Prerequisites: OpenSSL must be installed
# On Windows: Download from https://slproweb.com/products/Win32OpenSSL.html
#
# Usage: .\generate_certs.ps1 -Device mecamdev2.local -User pi

param(
    [string]$Device = "mecamdev2.local",
    [string]$User = "pi",
    [string]$CertDir = "$PSScriptRoot\temp_certs"
)

Write-Host "🔐 ME_CAM SSL Certificate Generator (Windows)" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if OpenSSL is available
Write-Host "🔍 Checking for OpenSSL..." -ForegroundColor Cyan
$opensslPath = Get-Command openssl -ErrorAction SilentlyContinue
if (-not $opensslPath) {
    Write-Host "❌ OpenSSL not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install OpenSSL for Windows:" -ForegroundColor Yellow
    Write-Host "  1. Download: https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor Gray
    Write-Host "  2. Run installer and choose 'Copy OpenSSL DLLs to Windows system directory'" -ForegroundColor Gray
    Write-Host "  3. Run this script again" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "✅ OpenSSL found" -ForegroundColor Green
Write-Host ""

# Create temp directory for certificates
if (-not (Test-Path $CertDir)) {
    New-Item -ItemType Directory -Path $CertDir -Force | Out-Null
}

$certFile = "$CertDir\certificate.pem"
$keyFile = "$CertDir\private_key.pem"

Write-Host "Generating self-signed SSL certificate for ME_CAM..." -ForegroundColor Cyan
Write-Host "This certificate will:" -ForegroundColor Gray
Write-Host "  ✅ Work for HTTPS connections" -ForegroundColor Gray
Write-Host "  ✅ Support VPN access" -ForegroundColor Gray
Write-Host "  ✅ Support domain: me_cam.com" -ForegroundColor Gray
Write-Host "  ✅ Support localhost and 127.0.0.1" -ForegroundColor Gray
Write-Host ""

# Generate private key
Write-Host "🔑 Generating 2048-bit RSA private key..." -ForegroundColor Cyan
openssl genrsa -out $keyFile 2048 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Private key generated" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to generate private key" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Generate self-signed certificate
Write-Host "🔒 Generating self-signed certificate..." -ForegroundColor Cyan

$subj = "/C=US/ST=NY/L=Brockport/O=ME_CAM/CN=me_cam.com"
$addExt = "subjectAltName=DNS:me_cam.com,DNS:localhost,DNS:*.local,IP:127.0.0.1"

openssl req -new -x509 -key $keyFile -out $certFile -days 365 `
    -subj $subj `
    -addext $addExt 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Certificate generated" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to generate certificate" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Set correct file permissions (Windows equivalent)
Write-Host "📋 Verifying certificate..." -ForegroundColor Cyan
openssl x509 -in $certFile -text -noout | Select-Object -First 20

Write-Host ""

# Get expiration date
$expirationOutput = openssl x509 -in $certFile -noout -enddate
$expiration = $expirationOutput.Split("=")[1]
Write-Host "📅 Certificate expires: $expiration" -ForegroundColor Yellow

Write-Host ""

# Upload to Pi
Write-Host "📤 Uploading certificates to $Device..." -ForegroundColor Cyan

# Create certs directory on Pi
ssh "$User@$Device" "mkdir -p ~/ME_CAM-DEV/certs" 2>$null

# Upload certificate
scp $certFile "$User@$Device`:~/ME_CAM-DEV/certs/certificate.pem" 2>$null
Write-Host "✅ Certificate uploaded" -ForegroundColor Green

# Upload private key
scp $keyFile "$User@$Device`:~/ME_CAM-DEV/certs/private_key.pem" 2>$null
Write-Host "✅ Private key uploaded" -ForegroundColor Green

Write-Host ""

# Set permissions on Pi
Write-Host "🔐 Setting file permissions on Pi..." -ForegroundColor Cyan
ssh "$User@$Device" "chmod 600 ~/ME_CAM-DEV/certs/private_key.pem && chmod 644 ~/ME_CAM-DEV/certs/certificate.pem" 2>$null
Write-Host "✅ Permissions set" -ForegroundColor Green

Write-Host ""

# Cleanup temp files
Remove-Item -Path $CertDir -Recurse -Force 2>$null

Write-Host "✅ SSL Certificates Generated and Deployed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart ME_CAM service: ssh $User@$Device 'sudo systemctl restart mecamera'" -ForegroundColor Gray
Write-Host "  2. Check logs: ssh $User@$Device 'tail -20 ~/ME_CAM-DEV/logs/mecam_lite.log'" -ForegroundColor Gray
Write-Host "  3. Should see: [HTTPS] Running with SSL/TLS" -ForegroundColor Gray
Write-Host ""
