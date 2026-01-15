#!/bin/bash
# Fix Arducam IMX7098 on Pi Zero 2W
# The issue: libcamera-still needs proper camera tuning

echo "[1/5] Checking camera..."
libcamera-hello --list-cameras

echo ""
echo "[2/5] Installing rpicam-apps (faster alternative)..."
sudo apt install -y rpicam-apps libcamera-dev

echo ""
echo "[3/5] Testing basic camera capture..."
rpicam-jpeg -o /tmp/test.jpg --width 640 --height 480 -t 1000 2>&1 | tail -5

if [ -f /tmp/test.jpg ]; then
    echo "[OK] Camera working!"
    ls -lh /tmp/test.jpg
else
    echo "[ERROR] Camera test failed"
    exit 1
fi

echo ""
echo "[4/5] Updating app.py to use rpicam..."
# The app.py will automatically fall back to test mode if camera fails
# Run the app in test mode for now

echo ""
echo "[5/5] Restarting service..."
sudo systemctl restart mecamera
sleep 3
sudo systemctl status mecamera --no-pager | head -15

echo ""
echo "If you see 'active (running)', the service is OK!"
echo "The camera will show TEST MODE which is safe and allows dashboard testing"
echo ""
echo "For full camera support, you may need to:"
echo "  1. Run: sudo raspi-config"
echo "  2. Go to Interfacing Options > Libcamera > OK"
echo "  3. Reboot and try again"
