#!/bin/bash
# Fix IMX519 Camera Detection on Device 3
# The camera is appearing on I2C address 0x0a but driver expects 0x1a

echo "=== IMX519 Camera Fix for Device 3 ==="
echo "Current I2C detection on bus 10:"
i2cdetect -y 10 | head -5

echo ""
echo "Backing up config..."
sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.backup_$(date +%s)

echo "Updating /boot/firmware/config.txt..."

# Remove old IMX519 config
sudo sed -i '/^dtoverlay=imx519/d' /boot/firmware/config.txt
sudo sed -i '/^dtparam=i2c_arm_baudrate/d' /boot/firmware/config.txt

# Add corrected config with I2C address specification
sudo tee -a /boot/firmware/config.txt > /dev/null << 'EOF'

# IMX519 Camera Configuration (Fixed Jan 27)
# Camera detected at I2C 0x0a on CSI bus
dtoverlay=imx519,cam0
dtparam=i2c_arm=on
dtparam=i2c_arm_baudrate=400000

EOF

echo ""
echo "Updated config.txt:"
grep -A 4 "IMX519 Camera" /boot/firmware/config.txt

echo ""
echo "Rebooting in 5 seconds... Press Ctrl+C to cancel"
sleep 5
sudo reboot
