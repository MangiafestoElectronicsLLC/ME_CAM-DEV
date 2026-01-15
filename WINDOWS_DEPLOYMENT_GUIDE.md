# Windows Deployment Guide - ME Camera LITE MODE

## Quick Start (From Windows to Pi)

### Prerequisites
- ✅ Windows 10/11 with PowerShell
- ✅ OpenSSH Client installed (Settings > Apps > Optional Features)
- ✅ Raspberry Pi on same network
- ✅ Know Pi's IP address (or hostname)

### Step 1: Deploy LITE MODE to Pi

```powershell
# From ME_CAM-DEV directory
.\deploy_lite_mode.ps1
```

The script will:
1. Find your Pi on network (tries common addresses)
2. Copy all files to Pi via SSH/SCP
3. Run LITE MODE installer automatically
4. Show access URLs when complete

### Step 2: Add Domain Access (Optional)

```batch
# Run as Administrator
.\add-domain-to-hosts.bat
```

Enter your Pi's IP when prompted. This adds `me_cam.com` to Windows hosts file.

### Step 3: Access Camera

Open browser:
- **Local**: `http://[PI-IP]:8080`
- **HTTPS**: `https://[PI-IP]:8080`
- **Domain**: `https://me_cam.com:8080`

Default login:
- Username: `admin`
- Password: `admin123`

---

## Finding Your Pi's IP Address

### Option 1: Check Router
1. Open router admin panel (usually `192.168.1.1` or `192.168.0.1`)
2. Look for DHCP clients or connected devices
3. Find device named "raspberrypi" or "mecamera"

### Option 2: Network Scanner
1. Download [Advanced IP Scanner](https://www.advanced-ip-scanner.com/)
2. Scan your network
3. Look for Raspberry Pi devices

### Option 3: Direct Connection
1. Connect monitor and keyboard to Pi
2. Login and run: `hostname -I`
3. First IP shown is your Pi's address

### Option 4: Try Common Hostnames
```powershell
# Test these in browser
http://raspberrypi.local:8080
http://mecamera.local:8080
```

---

## Troubleshooting

### SSH Connection Failed

**Error**: `ssh: Could not resolve hostname mecamera.local`

**Solutions**:
1. Use IP address instead: `.\deploy_lite_mode.ps1` (script will ask for IP)
2. Install Bonjour Print Services (for .local resolution)
3. Check Pi is powered on and connected to network

### Permission Denied (publickey)

**Error**: `Permission denied (publickey,password)`

**Solution**: Enable password authentication on Pi:
```bash
# On Pi
sudo nano /etc/ssh/sshd_config
# Find: PasswordAuthentication no
# Change to: PasswordAuthentication yes
sudo systemctl restart ssh
```

### Can't Copy Files

**Error**: `scp: command not found`

**Solution**: 
1. Install OpenSSH Client: Settings > Apps > Optional Features > Add OpenSSH Client
2. Restart PowerShell after installation

### Installation Fails on Pi

**Symptoms**: Script hangs or errors during installation

**Solution**: Manual installation via SSH:
```bash
ssh pi@[PI-IP]
cd ~/ME_CAM-DEV
chmod +x scripts/install_lite_mode.sh
./scripts/install_lite_mode.sh
```

### Domain Access Not Working

**Error**: `me_cam.com` doesn't resolve

**Solutions**:
1. Run `add-domain-to-hosts.bat` as **Administrator**
2. Flush DNS: `ipconfig /flushdns`
3. Verify hosts file: `notepad C:\Windows\System32\drivers\etc\hosts`
   - Should contain: `[PI-IP]  me_cam.com`

---

## Manual Deployment (Alternative)

If PowerShell script doesn't work, deploy manually:

### 1. Copy Files to Pi
```powershell
# From Windows
scp -r C:\Users\nickp\Downloads\ME_CAM-DEV\ME_CAM-DEV\* pi@[PI-IP]:~/ME_CAM-DEV/
```

### 2. SSH into Pi
```powershell
ssh pi@[PI-IP]
```

### 3. Run Installer
```bash
cd ~/ME_CAM-DEV
chmod +x scripts/install_lite_mode.sh
./scripts/install_lite_mode.sh
```

---

## Checking LITE MODE Status

### From Windows (Remote)
```powershell
ssh pi@[PI-IP] "sudo systemctl status mecamera-lite"
```

### View Logs
```powershell
ssh pi@[PI-IP] "sudo journalctl -u mecamera-lite -n 50"
```

### Restart Service
```powershell
ssh pi@[PI-IP] "sudo systemctl restart mecamera-lite"
```

---

## Windows-Specific Tips

### PowerShell Execution Policy
If script won't run:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Long Path Support
If file paths too long:
```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### Windows Firewall
Allow SSH connections:
```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "SSH Outbound" -Direction Outbound -Protocol TCP -LocalPort 22 -Action Allow
```

---

## Quick Commands Reference

### Deploy from Windows
```powershell
.\deploy_lite_mode.ps1
```

### Add domain access
```batch
.\add-domain-to-hosts.bat
```

### SSH into Pi
```powershell
ssh pi@[PI-IP]
```

### Check Pi status (from Windows)
```powershell
ssh pi@[PI-IP] "sudo systemctl status mecamera-lite"
```

### View Pi logs (from Windows)
```powershell
ssh pi@[PI-IP] "sudo journalctl -u mecamera-lite -f"
```

### Restart Pi service (from Windows)
```powershell
ssh pi@[PI-IP] "sudo systemctl restart mecamera-lite"
```

---

## Next Steps

After successful deployment:
1. ✅ Access dashboard at `http://[PI-IP]:8080`
2. ✅ Login with `admin` / `admin123`
3. ✅ Change default password
4. ✅ Configure device name and settings
5. ✅ Test camera feed
6. ✅ Set up domain access (optional)
7. ✅ Enable HTTPS (certificates included)

---

**Version**: 2.1-LITE  
**Last Updated**: January 15, 2026  
**Platform**: Windows 10/11 → Raspberry Pi
