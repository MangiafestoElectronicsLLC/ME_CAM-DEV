#!/bin/bash
# ============================================================
# ME Camera LITE MODE Installation Script
# Optimized for Pi Zero 2W (512MB RAM)
# ============================================================

set -e

echo "════════════════════════════════════════════════════════"
echo "   ME CAMERA LITE MODE - Pi Zero 2W Installation"
echo "════════════════════════════════════════════════════════"
echo ""

# Detect Pi model
PI_MODEL=$(cat /proc/cpuinfo | grep "Model" | cut -d: -f2 | xargs)
echo "📟 Detected: $PI_MODEL"

# Check if Pi Zero 2W
if [[ "$PI_MODEL" == *"Zero 2"* ]]; then
    echo "✅ Pi Zero 2W detected - LITE MODE recommended"
    USE_LITE=true
else
    echo "ℹ️  Not Pi Zero 2W - Standard mode available, but LITE mode also works"
    read -p "Use LITE MODE anyway? (y/n): " choice
    if [[ "$choice" == "y" ]]; then
        USE_LITE=true
    else
        USE_LITE=false
        echo "⚠️  Use standard installation instead: ./scripts/setup.sh"
        exit 0
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "STEP 1: Checking Prerequisites"
echo "════════════════════════════════════════════════════════"

# Check if in ME_CAM-DEV directory
if [ ! -f "main_lite.py" ]; then
    echo "❌ Error: Not in ME_CAM-DEV directory or main_lite.py not found"
    exit 1
fi

echo "✅ Prerequisites OK"
echo ""

echo "════════════════════════════════════════════════════════"
echo "STEP 2: Installing Dependencies (Lightweight)"
echo "════════════════════════════════════════════════════════"

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    if [ ! -f "venv/bin/activate" ]; then
        echo "❌ Failed to create virtual environment"
        echo "Installing python3-venv package..."
        sudo apt-get update
        sudo apt-get install -y python3-venv
        
        echo "Retrying venv creation..."
        python3 -m venv venv
        
        if [ ! -f "venv/bin/activate" ]; then
            echo "❌ Still failed. Using system Python instead."
            SYSTEM_PYTHON=true
        else
            echo "✅ Virtual environment created"
        fi
    else
        echo "✅ Virtual environment created"
    fi
else
    echo "✅ Virtual environment already exists"
fi

# Activate venv if available
if [ "$SYSTEM_PYTHON" != "true" ] && [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️ Using system Python (no venv)"
fi

# Install minimal dependencies only
echo "Installing Flask and essentials..."
pip3 install --upgrade pip || pip install --upgrade pip
pip3 install Flask==2.2.5 Pillow==9.5.0 loguru==0.7.0 || pip install Flask==2.2.5 Pillow==9.5.0 loguru==0.7.0

# Install picamera2 if available (for camera support)
echo "Installing picamera2 for camera support..."
sudo apt-get update -qq
sudo apt-get install -y python3-picamera2 || echo "⚠️  picamera2 not available, camera will be disabled"

echo "✅ Dependencies installed"
echo ""

echo "════════════════════════════════════════════════════════"
echo "STEP 3: Configuring LITE MODE Service"
echo "════════════════════════════════════════════════════════"

# Stop existing service if running
sudo systemctl stop mecamera 2>/dev/null || true
sudo systemctl disable mecamera 2>/dev/null || true

# Install LITE MODE service
sudo cp etc/systemd/system/mecamera-lite.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mecamera-lite
sudo systemctl start mecamera-lite

echo "✅ Service configured and started"
echo ""

echo "════════════════════════════════════════════════════════"
echo "STEP 4: Verifying Installation"
echo "════════════════════════════════════════════════════════"

sleep 3

# Check service status
if sudo systemctl is-active --quiet mecamera-lite; then
    echo "✅ Service ACTIVE"
else
    echo "❌ Service FAILED"
    echo "Checking logs..."
    sudo journalctl -u mecamera-lite -n 20 --no-pager
    exit 1
fi

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo ""
echo "════════════════════════════════════════════════════════"
echo "   ✅ LITE MODE INSTALLATION COMPLETE!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📷 ME Camera LITE MODE is now running!"
echo ""
echo "Access your camera:"
echo "  • Local network:  http://$IP_ADDR:8080"
echo "  • HTTPS:          https://$IP_ADDR:8080"
echo "  • Domain name:    https://me_cam.com:8080"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Features enabled:"
echo "  ✅ Camera streaming (lightweight, ~20 FPS)"
echo "  ✅ Battery monitoring"
echo "  ✅ Storage management"
echo "  ✅ HTTPS support"
echo "  ✅ Auto-boot on startup"
echo ""
echo "Memory optimized for Pi Zero 2W (512MB RAM)"
echo "Background services disabled for minimal footprint"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status mecamera-lite    # Check status"
echo "  sudo journalctl -u mecamera-lite -f    # View logs"
echo "  sudo systemctl restart mecamera-lite   # Restart"
echo ""
echo "To set up domain access (me_cam.com):"
echo "  See: notes.txt PART 7 (HTTPS & Domain Setup)"
echo ""
echo "════════════════════════════════════════════════════════"
