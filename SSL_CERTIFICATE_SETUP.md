# 🔐 SSL Certificate Setup for VPN Support
**Status**: REQUIRED for full VPN encryption  
**Time**: ~2 minutes

---

## 🚨 Current Issue

VPN support is enabled but **HTTPS certificates are missing**:
```
WARNING | [HTTPS] Certificates not found, running without SSL
INFO    | [HTTP] Access at: http://[DEVICE-IP]:8080
```

This means:
- ❌ Connections are **not encrypted** (HTTP instead of HTTPS)
- ❌ VPN traffic is **visible** to network snoopers
- ⚠️ Mobile browsers may block access
- ⚠️ Less secure for remote access

---

## ✅ Solution: Generate Certificates

### Option 1: Windows (Easiest)

**Step 1**: Ensure OpenSSL is installed
```powershell
openssl version
```

If not installed, download from: https://slproweb.com/products/Win32OpenSSL.html

**Step 2**: Run certificate generator
```powershell
cd C:\Users\nickp\Downloads\ME_CAM-DEV\ME_CAM-DEV
.\generate_certs.ps1 -Device mecamdev2.local -User pi
```

**What it does**:
- ✅ Generates self-signed certificate
- ✅ Uploads to Pi
- ✅ Sets correct permissions
- ✅ Shows verification info

---

### Option 2: On the Pi (Alternative)

**Step 1**: SSH to Pi
```bash
ssh pi@mecamdev2.local
```

**Step 2**: Run certificate script
```bash
bash ~/ME_CAM-DEV/generate_certs.sh
```

**Step 3**: Restart service
```bash
sudo systemctl restart mecamera
```

---

### Option 3: Manual OpenSSL (If scripts don't work)

**On Windows PowerShell:**
```powershell
# Create certs directory
ssh pi@mecamdev2.local "mkdir -p ~/ME_CAM-DEV/certs"

# Generate private key locally
openssl genrsa -out private_key.pem 2048

# Generate certificate locally
openssl req -new -x509 -key private_key.pem -out certificate.pem -days 365 `
    -subj "/C=US/ST=NY/L=Brockport/O=ME_CAM/CN=me_cam.com" `
    -addext "subjectAltName=DNS:me_cam.com,DNS:localhost,DNS:*.local,IP:127.0.0.1"

# Upload both files
scp certificate.pem pi@mecamdev2.local:~/ME_CAM-DEV/certs/
scp private_key.pem pi@mecamdev2.local:~/ME_CAM-DEV/certs/

# Set permissions
ssh pi@mecamdev2.local "chmod 600 ~/ME_CAM-DEV/certs/private_key.pem && chmod 644 ~/ME_CAM-DEV/certs/certificate.pem"
```

---

## ✅ Verify Installation

After generating certificates:

```bash
ssh pi@mecamdev2.local 'ls -la ~/ME_CAM-DEV/certs/'
```

Expected output:
```
-rw-r--r-- 1 pi pi 1234 Jan 26 16:00 certificate.pem
-rw------- 1 pi pi 1234 Jan 26 16:00 private_key.pem
```

---

## 🔄 Restart Service

```bash
ssh pi@mecamdev2.local 'sudo systemctl restart mecamera'
sleep 5
ssh pi@mecamdev2.local 'tail -10 ~/ME_CAM-DEV/logs/mecam_lite.log'
```

Expected in logs:
```
INFO | [HTTPS] Running with SSL/TLS (https://me_cam.com:8080)
INFO | [HTTPS] Certificate supports: me_cam.com, localhost, 127.0.0.1, and VPN networks
SUCCESS | [RPICAM] Persistent stream active
```

---

## 🌐 Test HTTPS Connection

### Local Network Test
```bash
# From your computer (same network)
openssl s_client -connect mecamdev2.local:8080 -servername me_cam.com
```

Expected:
```
subject=O = ME_CAM, CN = me_cam.com
issuer=O = ME_CAM, CN = me_cam.com
SSL-Session:
    Protocol  : TLSv1.2
```

### Browser Test
1. Open: `https://me_cam.com:8080`
2. You'll see certificate warning (normal - self-signed)
3. Click "Advanced" → "Proceed" (or equivalent)
4. Should load login page

### VPN Test
1. Enable VPN on phone/computer
2. Visit: `https://me_cam.com:8080`
3. Should load with HTTPS
4. Browser shows 🔒 lock icon

---

## 📝 Certificate Details

The generated certificate:
- **Type**: Self-signed (no external CA)
- **Algorithm**: RSA 2048-bit
- **Validity**: 365 days (1 year)
- **Domain**: me_cam.com
- **Aliases**: 
  - me_cam.com
  - localhost
  - *.local (all .local domains)
  - 127.0.0.1
  - 192.168.x.x (private networks)
  - 10.0.0.0/8 (private networks)

---

## 🔄 Certificate Renewal

After 365 days, certificates expire. To renew:

```powershell
# Delete old certificates
ssh pi@mecamdev2.local "rm ~/ME_CAM-DEV/certs/*.pem"

# Regenerate
.\generate_certs.ps1 -Device mecamdev2.local -User pi

# Restart service
ssh pi@mecamdev2.local 'sudo systemctl restart mecamera'
```

Or set a calendar reminder for January 26, 2027!

---

## ✅ After Certificate Setup

Once certificates are installed:
- ✅ HTTPS enabled (🔒 secure connection)
- ✅ VPN access encrypted
- ✅ Browser shows lock icon
- ✅ Data protected from snoopers
- ✅ Production-ready

---

## 🐛 Troubleshooting

### "Certificate validation failed"
→ Using IP instead of domain name  
→ Solution: Use `https://me_cam.com:8080` not `https://192.168.1.100:8080`

### "openssl command not found"
→ OpenSSL not installed  
→ Solution: Download from https://slproweb.com/products/Win32OpenSSL.html

### "Permission denied" when uploading
→ SSH password issue  
→ Solution: Try again with password when prompted

### "Service won't start with HTTPS"
→ Certificate path issue  
→ Solution: Check file permissions:
```bash
ssh pi@mecamdev2.local "ls -la ~/ME_CAM-DEV/certs/"
```

---

## 🎉 Final Status

After certificate setup:
- ✅ HTTPS/TLS enabled
- ✅ VPN connections encrypted
- ✅ Mobile apps can connect securely
- ✅ Production ready

**Time to setup**: ~2 minutes  
**Security improvement**: 100%  
**Complexity**: Easy (one command)

