#!/bin/bash
# Automated Device 3 Camera Fix Script
# Run on Device 3 (or push via SCP)

set -e

echo "========================================="
echo "Device 3 - IMX519 Camera Auto-Fix"
echo "========================================="
echo ""

# Function to print section headers
section() {
    echo ""
    echo ">>> $1"
    echo ""
}

# Function to check if command succeeded
check_result() {
    if [ $? -eq 0 ]; then
        echo "✓ $1"
    else
        echo "✗ $1 (FAILED)"
    fi
}

# --- DIAGNOSTIC PHASE ---
section "CURRENT STATUS"

echo "Camera Detection:"
vcgencmd get_camera
echo ""

echo "Kernel Status:"
dmesg | grep -i "imx519" | tail -2 || echo "No IMX519 messages found"
echo ""

echo "I2C Bus 10 (CSI):"
sudo i2cdetect -y 10 2>/dev/null | grep -A 1 "00:"
echo ""

# --- CONFIGURATION PHASE ---
section "UPDATING CONFIGURATION"

# Backup current config
BACKUP_FILE="/boot/firmware/config.txt.backup_$(date +%s)"
echo "Creating backup: $BACKUP_FILE"
sudo cp /boot/firmware/config.txt "$BACKUP_FILE"
check_result "Backup created"

# Remove old IMX519 settings
echo "Removing old IMX519 configuration..."
sudo sed -i '/^# IMX519 Camera/d' /boot/firmware/config.txt
sudo sed -i '/^dtoverlay=imx519/d' /boot/firmware/config.txt
sudo sed -i '/^dtparam=i2c_arm/d' /boot/firmware/config.txt
check_result "Old config removed"

# Add new configuration
echo "Writing optimized configuration..."
sudo tee -a /boot/firmware/config.txt > /dev/null << 'EOF'

# IMX519 Camera Configuration - Auto-Fixed Jan 27
# Camera uses I2C address 0x0a on CSI bus (non-standard)
dtoverlay=imx519,cam0
dtparam=i2c_arm=on
dtparam=i2c_arm_baudrate=100000
gpu_mem=256
start_x=1

EOF
check_result "New config written"

# --- VERIFICATION ---
section "CONFIGURATION VERIFICATION"

echo "Current IMX519 settings:"
grep -A 5 "IMX519 Camera" /boot/firmware/config.txt

# --- SUMMARY ---
section "NEXT STEPS"

echo "1. Rebooting in 5 seconds..."
echo "   Press Ctrl+C to cancel"
echo ""
echo "2. After reboot, test with:"
echo "   $ vcgencmd get_camera"
echo "   (Should show: supported=1 detected=1)"
echo ""
echo "3. If still not detected, check:"
echo "   $ dmesg | grep imx519"
echo "   $ i2cdetect -y 10"
echo ""

sleep 5
echo "Rebooting now..."
sudo reboot

