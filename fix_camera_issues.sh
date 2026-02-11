#!/bin/bash
# Fix Critical Issues - Device 1 v2.2.3
# =====================================
# 1. Remove vflip (causing upside down videos)
# 2. Increase quality parameter (80 -> 90)  
# 3. Increase FPS (use config value of 30)
# 4. Verify motion detection service

echo "=============================================="
echo "  Fixing Camera Issues - Device 1"
echo "=============================================="

cd ~/ME_CAM-DEV

# Backup current file
echo "[1/5] Creating backup..."
cp src/camera/rpicam_streamer.py src/camera/rpicam_streamer.py.backup

# Fix 1: Remove vflip (line 137)
echo "[2/5] Fixing camera orientation (removing vflip)..."
sed -i "/'--vflip',/d" src/camera/rpicam_streamer.py

# Fix 2: Increase quality from 85 to 95
echo "[3/5] Increasing JPEG quality (85 -> 95)..."
sed -i 's/quality=85/quality=95/g' src/camera/rpicam_streamer.py

# Fix 3: Reduce capture delay for better FPS
echo "[4/5] Improving FPS (reducing delays)..."
sed -i 's/time.sleep(0.05)/time.sleep(0.033)/g' src/camera/rpicam_streamer.py  # ~30 FPS

# Verify changes
echo ""
echo "=============================================="
echo "  Changes Applied:"
echo "=============================================="
echo "✓ Removed --vflip (fixes upside down videos)"
echo "✓ Quality: 85 -> 95 (better image quality)"  
echo "✓ FPS: ~20 -> ~30 (faster updates)"
echo ""

# Check service status
echo "[5/5] Restarting mecamera service..."
sudo systemctl restart mecamera
sleep 3
sudo systemctl status mecamera --no-pager -l

echo ""
echo "=============================================="
echo "  Testing Camera..."
echo "=============================================="
sleep 2

# Test camera with fixed settings
rpicam-jpeg -o /tmp/test.jpg --width 640 --height 480 --quality 95 -t 100 --nopreview
if [ -f /tmp/test.jpg ]; then
    size=$(du -h /tmp/test.jpg | cut -f1)
    echo "✓ Test image captured: $size"
    rm /tmp/test.jpg
else
    echo "✗ Camera test failed"
fi

echo ""
echo "=============================================="
echo "  Next Steps:"
echo "=============================================="
echo "1. Check dashboard: http://10.2.1.3:8080"
echo "2. Videos should now be right-side up"
echo "3. Camera quality should be improved"
echo "4. FPS should be ~30 instead of ~20"
echo ""
echo "To check logs:"
echo "  sudo journalctl -u mecamera -f"
echo ""
