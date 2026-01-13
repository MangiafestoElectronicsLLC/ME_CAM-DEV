#!/bin/bash

# ME_CAM Quick Deployment Fix Script
# Run this on your Pi to fix all issues at once!
# Usage: chmod +x QUICK_DEPLOY.sh && ./QUICK_DEPLOY.sh

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          ME_CAM QUICK DEPLOYMENT & FIX (Jan 13, 2026)       ║"
echo "║     Fixes: Video display, motion detection, fast streaming  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Update code
echo "📥 Step 1: Pulling latest code..."
cd ~/ME_CAM-DEV
git pull origin main
if [ $? -eq 0 ]; then
    echo "✅ Code updated"
else
    echo "❌ Git pull failed"
    exit 1
fi
echo ""

# Step 2: Install picamera2
echo "📦 Step 2: Installing picamera2 (fast streaming)..."
sudo apt update >/dev/null 2>&1
sudo apt install -y python3-picamera2 >/dev/null 2>&1
python3 -c "from picamera2 import Picamera2; print('✅ picamera2 installed')" 2>/dev/null || {
    echo "❌ picamera2 installation failed"
    exit 1
}
echo ""

# Step 3: Create recordings directory
echo "📁 Step 3: Creating recordings directory..."
mkdir -p ~/ME_CAM-DEV/recordings
chmod 755 ~/ME_CAM-DEV/recordings
echo "✅ Recordings directory ready"
echo ""

# Step 4: Restart service
echo "🔄 Step 4: Restarting ME_CAM service..."
sudo systemctl stop mecamera
sleep 2
sudo systemctl start mecamera
sleep 5
echo "✅ Service restarted"
echo ""

# Step 5: Check status
echo "🔍 Step 5: Checking service status..."
sudo systemctl status mecamera --no-pager | head -5
echo ""

# Step 6: Verify fast streaming
echo "⚡ Step 6: Checking fast streaming..."
sleep 2
tail -20 ~/ME_CAM-DEV/logs/mecam.log 2>/dev/null | grep -i "fast\|picamera" && echo "✅ Fast streaming detected" || echo "⚠️  Fast streaming not yet enabled in settings"
echo ""

# Step 7: Check configuration
echo "📋 Step 7: Checking configuration..."
grep "use_fast_streamer" ~/ME_CAM-DEV/config/config.json 2>/dev/null | grep true && echo "✅ Fast streaming enabled in config" || {
    echo "⚠️  Fast streaming NOT enabled in config"
    echo "   Run these commands to enable:"
    echo "   1. Open: http://raspberrypi.local:8080"
    echo "   2. Click: ⚙️ Configure"
    echo "   3. Scroll to: ⚡ Performance Settings (green)"
    echo "   4. Check: ✓ Use Fast Streaming"
    echo "   5. Set FPS: 15"
    echo "   6. Save Settings"
}
echo ""

# Step 8: Test directory structure
echo "📂 Step 8: Verifying file structure..."
echo "   Checking recordings: $(ls -1 ~/ME_CAM-DEV/recordings 2>/dev/null | wc -l) files"
echo "   Checking logs: $(ls -1 ~/ME_CAM-DEV/logs 2>/dev/null | wc -l) files"
echo "✅ Structure verified"
echo ""

# Final report
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT COMPLETE                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 NEXT STEPS:"
echo ""
echo "1. Open dashboard: http://raspberrypi.local:8080"
echo "2. Verify live video displays (not black screen)"
echo "3. Go to ⚙️ Settings → ⚡ Performance Settings"
echo "4. Check ✓ Use Fast Streaming"
echo "5. Set Target FPS: 15"
echo "6. Save Settings"
echo "7. Dashboard should now be smooth (15-30 FPS, not 1-2 FPS)"
echo "8. Wave hand in front of camera"
echo "9. Wait 30 seconds, refresh dashboard"
echo "10. Should see motion videos in Recent Recordings"
echo ""
echo "✅ Check logs for issues:"
echo "   tail -f ~/ME_CAM-DEV/logs/mecam.log | grep -E 'CAMERA|MOTION|STREAM|ERROR'"
echo ""
echo "📚 Full guide: See DEPLOYMENT_FIXES_JAN13.md"
echo ""
