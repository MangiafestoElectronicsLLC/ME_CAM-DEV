#!/bin/bash
# Quick IMX519 config fix for Device 3

echo "Backing up config..."
sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.bak

echo "Cleaning bad IMX519 config..."
sudo sed -i '/dtoverlay=imx519,cam0/d' /boot/firmware/config.txt
sudo sed -i '/dtparam=i2c_arm_baudrate=400000/d' /boot/firmware/config.txt

echo "Adding clean IMX519 config..."
sudo tee -a /boot/firmware/config.txt > /dev/null << 'EOF'

# IMX519 Camera - Clean Config
camera_auto_detect=1
dtoverlay=imx519
dtparam=i2c_arm=on
start_x=1
gpu_mem=256
EOF

echo "Config updated. Rebooting in 3 seconds..."
sleep 3
sudo reboot
