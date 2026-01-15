#!/bin/bash
# ME_CAM-DEV Quick Deploy to Pi Zero 2W
# Usage: bash DEPLOY_PI.sh 10.2.1.47 pi

PI_IP="${1:-10.2.1.47}"
PI_USER="${2:-pi}"
TARGET="${PI_USER}@${PI_IP}"
PROJECT="ME_CAM-DEV"

echo "================================================"
echo "  ME_CAM-DEV Deployment to Pi Zero 2W"
echo "================================================"
echo "Target: ${TARGET}"
echo ""

# Test connection
echo "[1/8] Testing connection to Pi..."
if ! ping -n 1 ${PI_IP} > /dev/null 2>&1; then
    echo "ERROR: Cannot reach ${PI_IP}"
    exit 1
fi
echo "✓ Connection OK"

# Stop existing service
echo "[2/8] Stopping existing service..."
ssh ${TARGET} "sudo systemctl stop mecamera 2>/dev/null || true"
echo "✓ Service stopped"

# Backup existing installation
echo "[3/8] Backing up existing installation..."
ssh ${TARGET} "if [ -d ~/${PROJECT} ]; then mv ~/${PROJECT} ~/${PROJECT}.backup.$(date +%s); fi"
echo "✓ Backup complete"

# Create project directory
echo "[4/8] Creating project directory..."
ssh ${TARGET} "mkdir -p ~/${PROJECT}"
echo "✓ Directory created"

# Transfer files (using rsync if available, otherwise tar)
echo "[5/8] Transferring files..."
if command -v rsync &> /dev/null; then
    rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' \
          --exclude='logs' --exclude='recordings' --exclude='encrypted_videos' \
          ./ ${TARGET}:~/${PROJECT}/
else
    # Fallback to tar
    tar -czf /tmp/${PROJECT}.tar.gz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
        --exclude='.venv' --exclude='logs' --exclude='recordings' --exclude='encrypted_videos' .
    scp /tmp/${PROJECT}.tar.gz ${TARGET}:~/
    ssh ${TARGET} "cd ~/${PROJECT} && tar -xzf ~/${PROJECT}.tar.gz && rm ~/${PROJECT}.tar.gz"
    rm /tmp/${PROJECT}.tar.gz
fi
echo "✓ Files transferred"

# Setup Python environment
echo "[6/8] Setting up Python environment (5-10 min)..."
ssh ${TARGET} << 'ENDSSH'
    cd ~/ME_CAM-DEV
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Handle NumPy compatibility
    if pip list | grep -q 'numpy 2'; then
        pip install 'numpy<2' > /dev/null 2>&1
        pip uninstall opencv-python opencv-python-headless -y > /dev/null 2>&1
        pip install opencv-python-headless > /dev/null 2>&1
    fi
    
    echo "✓ Python environment ready"
ENDSSH

# Run setup script
echo "[7/8] Running setup script..."
ssh ${TARGET} "cd ~/${PROJECT} && chmod +x setup.sh && ./setup.sh"
echo "✓ Setup complete"

# Install systemd service
echo "[8/8] Installing systemd service..."
ssh ${TARGET} << 'ENDSSH'
    cd ~/ME_CAM-DEV
    
    # Copy service file
    sudo cp etc/systemd/system/mecamera.service /etc/systemd/system/
    
    # Reload and start
    sudo systemctl daemon-reload
    sudo systemctl enable mecamera
    sudo systemctl start mecamera
    
    # Wait for startup
    sleep 3
    
    echo "✓ Service installed and started"
ENDSSH

echo ""
echo "================================================"
echo "  Deployment Complete!"
echo "================================================"
echo ""
echo "Access Dashboard: http://${PI_IP}:8080"
echo "Default PIN: 1234"
echo ""
echo "Check Status:"
echo "  ssh ${TARGET} 'sudo systemctl status mecamera'"
echo ""
echo "View Logs:"
echo "  ssh ${TARGET} 'tail -f ~/ME_CAM-DEV/logs/mecam.log'"
echo ""
echo "================================================"
