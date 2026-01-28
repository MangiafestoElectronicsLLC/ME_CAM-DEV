#!/bin/bash
# Quick status check for Device 3
echo "=== Device 3 Status Check ==="
echo ""

# Check camera
echo "[1] Camera Detection:"
vcgencmd get_camera
echo ""

# Check cameras available
echo "[2] Available Cameras:"
rpicam-hello --list-cameras 2>&1 || echo "ERROR: rpicam-hello failed (camera might not be detected)"
echo ""

# Check kernel messages
echo "[3] IMX519 Kernel Status (last 5 lines):"
dmesg | grep -i imx519 | tail -5
echo ""

# Check I2C bus
echo "[4] I2C Bus 10 (CSI):"
i2cdetect -y 10 2>&1 | head -5
echo ""

# Check if app is running
echo "[5] ME_CAM App Status:"
pgrep -af "python.*main_lite" && echo "✓ App is running" || echo "✗ App is NOT running"
echo ""

# Web service check
echo "[6] Web Service:"
curl -s http://localhost:8080/api/status 2>&1 | head -3 || echo "✗ Web service not responding"

