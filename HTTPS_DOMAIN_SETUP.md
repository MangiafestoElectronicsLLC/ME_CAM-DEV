# ME_CAM.com HTTPS Setup Guide

## What You Have
- ✅ HTTPS enabled (self-signed SSL certificates)
- ✅ IP Access: https://10.2.1.47:8080
- ❌ Domain Name: NOT YET (requires hosts file setup)

## To Access via ME_CAM.com

### Windows Setup (Required for domain to work locally)

Run as Administrator:

```powershell
# Open PowerShell as Administrator, then paste:
Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" -Value "`n10.2.1.47   ME_CAM.com" -Force
Write-Host "✓ ME_CAM.com added to hosts file"
```

Then access: **https://ME_CAM.com:8080**

### Alternative: Manual Edit

1. Open Notepad **as Administrator**
2. File → Open → `C:\Windows\System32\drivers\etc\hosts`
3. Go to bottom and add:
   ```
   10.2.1.47   ME_CAM.com
   ```
4. Save (Ctrl+S)

### In Your Browser

1. Go to: `https://ME_CAM.com:8080`
2. You'll see a security warning (self-signed cert) - this is normal
3. Click **"Advanced"** → **"Proceed to ME_CAM.com (unsafe)"**
4. Login with: **admin / admin**
5. ✅ You're in!

## Features Now Working

✅ Battery display (shows 100% if healthy power, 0% if undervolt)
✅ Multi-device management (add devices manually)
✅ HTTPS encryption
✅ Domain access (after hosts file setup)

## Test Checklist

- [ ] Add second device via multicam page
- [ ] Check battery shows correct status
- [ ] Test HTTPS domain access
- [ ] Verify TEST MODE camera display

