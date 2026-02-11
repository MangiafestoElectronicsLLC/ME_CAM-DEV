# FIX PC CAMERA FLIP - CLEAR BROWSER CACHE

## ✅ CSS Fixed on Device 1

The rotation has been removed from the CSS file.

## 🔧 Clear Your Browser Cache NOW

### Chrome/Edge:
1. Press: **Ctrl + Shift + Delete**
2. Select: **Cached images and files**
3. Time range: **Last hour**
4. Click: **Clear data**
5. Reload: http://10.2.1.3:8080
6. Press: **Ctrl + Shift + R** (hard refresh)

### Firefox:
1. Press: **Ctrl + Shift + Delete**
2. Select: **Cache**
3. Time range: **Last hour**
4. Click: **Clear Now**
5. Reload: http://10.2.1.3:8080
6. Press: **Ctrl + F5** (hard refresh)

### Still Flipped After Cache Clear?

Try these steps:

**Step 1: Force Cache Bypass**
```
Open in private/incognito window
http://10.2.1.3:8080
```

**Step 2: Check CSS Loaded Correctly**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Refresh page
4. Look for `lite.css` in the list
5. Click it and verify no `rotate(180deg)` appears

**Step 3: If Still Flipped**
```powershell
# Restart browser completely
# Then reload dashboard
```

---

## 📱 Tailscale Remote Access Setup

Since you want to access from work WiFi:

### On Your Work PC:
1. Download Tailscale: https://tailscale.com/download/windows
2. Install and run
3. Sign in with: **zmanja42@gmail.com** (same account as Pi)
4. Once connected, access: **http://100.114.144.82:8080**

### How It Works:
- **At home:** http://10.2.1.3:8080 (local network)
- **At work:** http://100.114.144.82:8080 (via Tailscale VPN)
- **On phone:** http://100.114.144.82:8080 (via Tailscale app)

### Benefits:
✅ No port forwarding needed
✅ Encrypted connection
✅ Works on any network (work, cafe, cellular)
✅ Secure - only you can access
✅ Same experience as local network

---

## Test Plan:

1. **Clear browser cache** (Ctrl+Shift+Delete)
2. **Hard refresh** (Ctrl+Shift+R)
3. **Check camera** - should be right-side up ✅
4. **Install Tailscale** on work PC
5. **Test at work:** http://100.114.144.82:8080

Camera should now be correct on both PC and mobile!
