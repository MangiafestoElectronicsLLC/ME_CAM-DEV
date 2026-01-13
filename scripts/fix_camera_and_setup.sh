#!/bin/bash
# Complete fix and setup script for ME_CAM on Raspberry Pi Zero 2 W

echo "=========================================="
echo "ME_CAM Camera Fix & Setup Script"
echo "=========================================="

# Step 1: Kill all processes holding the camera
echo ""
echo "Step 1: Stopping all camera-related processes..."
sudo systemctl stop me_cam.service 2>/dev/null || true
sudo systemctl stop mecamera.service 2>/dev/null || true
sudo systemctl disable me_cam.service 2>/dev/null || true
sudo systemctl disable mecamera.service 2>/dev/null || true

# Kill the specific setup_server.py process that's holding the camera
echo "Killing setup_server.py process..."
sudo pkill -9 -f "setup_mode/setup_server.py" || true

# Kill any python processes related to ME_CAM
echo "Killing all ME_CAM Python processes..."
sudo pkill -9 -f "main.py" || true
sudo pkill -9 -f "web.app" || true
sudo pkill -9 -f "camera_pipeline" || true

# Kill any libcamera processes
echo "Killing libcamera processes..."
sudo pkill -9 -f "libcamera" || true

# Wait for processes to die
sleep 3

# Step 2: Verify camera is released
echo ""
echo "Step 2: Checking for remaining processes..."
ps aux | grep -E "python.*ME_CAM|libcamera" | grep -v grep
if [ $? -eq 0 ]; then
    echo "WARNING: Some processes still running. Attempting force kill..."
    sudo pkill -9 python3 || true
    sleep 2
fi

# Step 3: Backup old installation (if needed)
echo ""
echo "Step 3: Backing up old installation..."
if [ -d ~/ME_CAM_BACKUP ]; then
    echo "Removing previous backup..."
    rm -rf ~/ME_CAM_BACKUP
fi
if [ -d ~/ME_CAM ]; then
    echo "Creating backup at ~/ME_CAM_BACKUP..."
    mv ~/ME_CAM ~/ME_CAM_BACKUP
fi

# Step 4: Fresh installation
echo ""
echo "Step 4: Setting up fresh ME_CAM installation..."
mkdir -p ~/ME_CAM/ME_CAM-DEV
cd ~/ME_CAM/ME_CAM-DEV

# Step 5: Fix permissions
echo ""
echo "Step 5: Setting correct permissions..."
sudo chown -R pi:pi ~/ME_CAM
sudo chmod -R 755 ~/ME_CAM

# Step 6: Test camera hardware
echo ""
echo "Step 6: Testing camera hardware..."
echo "Running quick camera test..."
libcamera-hello --list-cameras
if [ $? -ne 0 ]; then
    echo "ERROR: Camera not detected!"
    echo "Please check:"
    echo "  1. Camera cable is properly connected"
    echo "  2. Camera interface is enabled in raspi-config"
    echo "  3. Try rebooting the Pi"
    exit 1
fi

echo ""
echo "Taking test photo..."
libcamera-still -t 2000 -o ~/test_camera.jpg 2>&1
if [ -f ~/test_camera.jpg ]; then
    echo "SUCCESS: Camera is working! Test photo saved at ~/test_camera.jpg"
    rm ~/test_camera.jpg
else
    echo "WARNING: Camera test photo failed, but camera was detected"
fi

echo ""
echo "=========================================="
echo "Camera fix complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Copy your project files to ~/ME_CAM/ME_CAM-DEV/"
echo "2. cd ~/ME_CAM/ME_CAM-DEV"
echo "3. python3 -m venv venv"
echo "4. source venv/bin/activate"
echo "5. pip install --upgrade pip"
echo "6. pip install -r requirements.txt"
echo "7. python3 main.py"
echo ""
echo "If camera is still busy, REBOOT with: sudo reboot"
