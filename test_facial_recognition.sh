#!/bin/bash
# Facial Recognition Testing Script for ME_CAM Pi Device
# Run this on the Pi to test facial recognition setup

echo "=========================================="
echo "ME_CAM Facial Recognition Testing"
echo "=========================================="
echo ""

# 1. Check Python version
echo "1️⃣ Checking Python version..."
python3 --version
echo ""

# 2. Check if face_recognition is installed
echo "2️⃣ Checking face_recognition library..."
python3 -c "import face_recognition; print('✅ face_recognition installed')" 2>&1 || echo "❌ face_recognition NOT installed"
echo ""

# 3. Check if cv2 is available
echo "3️⃣ Checking OpenCV (cv2)..."
python3 -c "import cv2; print(f'✅ OpenCV {cv2.__version__} installed')" 2>&1 || echo "❌ OpenCV NOT installed"
echo ""

# 4. Check if facial_recognition_pi5.py exists
echo "4️⃣ Checking facial_recognition_pi5.py module..."
if [ -f "ME_CAM-DEV/src/detection/facial_recognition_pi5.py" ]; then
    echo "✅ facial_recognition_pi5.py found"
    wc -l "ME_CAM-DEV/src/detection/facial_recognition_pi5.py"
else
    echo "❌ facial_recognition_pi5.py NOT found"
fi
echo ""

# 5. Check faces directory structure
echo "5️⃣ Checking faces directory structure..."
if [ -d "ME_CAM-DEV/faces" ]; then
    echo "✅ faces/ directory exists"
    find ME_CAM-DEV/faces -type d -o -type f | head -20
else
    echo "❌ faces/ directory NOT found"
fi
echo ""

# 6. List hardware info
echo "6️⃣ Hardware Information..."
echo "Pi Model: $(cat /proc/device-tree/model 2>/dev/null || echo 'Unknown')"
echo "RAM: $(free -h | grep "^Mem:" | awk '{print $2}')"
echo "CPU Cores: $(nproc)"
echo "Camera Status:"
libcamera-hello --list-cameras 2>&1 | head -5 || echo "❌ libcamera not available"
echo ""

echo "=========================================="
echo "Testing Complete!"
echo "=========================================="
