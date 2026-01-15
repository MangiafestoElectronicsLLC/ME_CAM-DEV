#!/bin/bash
# ME_CAM-DEV Pi Zero Deployment Script
# Usage: ./deploy_pi_zero.sh [username] [ip_address]

USERNAME="${1:-pi}"
PI_IP="${2:-10.2.1.47}"
PI="${USERNAME}@${PI_IP}"

echo "=========================================="
echo "🚀 ME_CAM-DEV Deployment to Pi Zero"
echo "=========================================="
echo "Target: $PI"
echo ""

# Step 1: Clean old installation
echo "📦 [1/8] Cleaning old installation..."
ssh $PI "
    sudo systemctl stop mecamera 2>/dev/null || true
    sudo systemctl disable mecamera 2>/dev/null || true
    sudo rm -f /etc/systemd/system/mecamera.service
    sudo systemctl daemon-reload
    rm -rf ~/ME_CAM-DEV
    rm -rf ~/.cache/pip
    sudo apt autoremove -y > /dev/null 2>&1
    sudo apt clean > /dev/null 2>&1
    echo '✅ Cleaned'
"

# Step 2: Clone repository
echo "📥 [2/8] Cloning ME_CAM-DEV repository..."
ssh $PI "
    cd ~
    git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
    cd ME_CAM-DEV
    echo '✅ Cloned'
"

# Step 3: Create virtual environment
echo "🐍 [3/8] Creating virtual environment..."
ssh $PI "
    cd ~/ME_CAM-DEV
    python3 -m venv venv
    echo '✅ Virtual environment created'
"

# Step 4: Install dependencies
echo "📚 [4/8] Installing dependencies (this may take 5-10 minutes)..."
ssh $PI "
    cd ~/ME_CAM-DEV
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    pip install -r requirements.txt
    
    # Handle NumPy/OpenCV compatibility
    if pip list | grep -q 'numpy 2'; then
        echo '⚠️  Found NumPy 2.x, downgrading...'
        pip install 'numpy<2' > /dev/null 2>&1
        pip uninstall opencv-python opencv-python-headless opencv-contrib-python -y > /dev/null 2>&1
        pip install opencv-python-headless > /dev/null 2>&1
    fi
    
    echo '✅ Dependencies installed'
"

# Step 5: Run setup script
echo "⚙️  [5/8] Running setup script..."
ssh $PI "
    cd ~/ME_CAM-DEV
    chmod +x setup.sh
    ./setup.sh
    echo '✅ Setup complete'
"

# Step 6: Copy systemd service
echo "🔧 [6/8] Installing systemd service..."
ssh $PI "
    cd ~/ME_CAM-DEV
    sudo cp etc/systemd/system/mecamera.service /etc/systemd/system/
    sudo systemctl daemon-reload
    echo '✅ Service installed'
"

# Step 7: Start service
echo "▶️  [7/8] Starting ME_CAM service..."
ssh $PI "
    sudo systemctl enable mecamera
    sudo systemctl start mecamera
    sleep 2
    sudo systemctl status mecamera --no-pager
    echo '✅ Service started'
"

# Step 8: Verify
echo "✔️  [8/8] Verifying deployment..."
ssh $PI "
    echo ''
    echo '📊 Service Status:'
    sudo systemctl is-active mecamera && echo '   ✅ Service running' || echo '   ❌ Service not running'
    
    echo ''
    echo '📂 Directory Check:'
    [ -d ~/ME_CAM-DEV ] && echo '   ✅ Code cloned' || echo '   ❌ Code missing'
    
    echo ''
    echo '📝 Log Status:'
    [ -f logs/mecam.log ] && echo '   ✅ Logs available' || echo '   ⏳ Logs will appear on first run'
    
    echo ''
    echo '🌐 Access Dashboard at:'
    IP=\$(hostname -I | awk '{print \$1}')
    echo '   http://'\$IP':8080'
    echo '   http://raspberrypi.local:8080'
"

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "📝 Next Steps:"
echo "  1. Open http://raspberrypi.local:8080 in browser"
echo "  2. Complete first-run wizard"
echo "  3. Configure settings (motion, storage, alerts)"
echo "  4. View logs: ssh pi@$PI_IP 'sudo journalctl -u mecamera.service -f'"
echo ""
