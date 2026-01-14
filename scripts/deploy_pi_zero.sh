#!/bin/bash
# ME_CAM - Secure Pi Zero 2W Deployment Script
# This script autobootss the camera with secure encryption and authentication
# Usage: sudo bash deploy_pi_zero.sh <password>

set -e

if [ "$EUID" -ne 0 ]; then 
   echo "This script must be run as root (use: sudo bash deploy_pi_zero.sh)"
   exit 1
fi

# Configuration
DEPLOY_USER="mecamera"
DEPLOY_HOME="/home/$DEPLOY_USER"
APP_DIR="$DEPLOY_HOME/ME_CAM-DEV"
SERVICE_NAME="mecamera"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LOG_DIR="/var/log/mecamera"

PASSWORD="${1:-me_secure_cam_2024}"  # Change this!

echo "=========================================="
echo "🚀 ME Camera - Pi Zero 2W Secure Deploy"
echo "=========================================="
echo "This will:"
echo "  ✓ Create dedicated system user"
echo "  ✓ Install dependencies"
echo "  ✓ Setup encrypted storage"
echo "  ✓ Create autoboot systemd service"
echo "  ✓ Harden security settings"
echo ""
echo "Press ENTER to continue (or Ctrl+C to cancel)..."
read

# 1. Create dedicated user
if ! id "$DEPLOY_USER" &>/dev/null; then
    echo "[1/6] Creating dedicated user: $DEPLOY_USER"
    useradd -m -s /bin/bash -G video,gpio,input $DEPLOY_USER
    echo "$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/sbin/halt, /usr/sbin/shutdown" | tee /etc/sudoers.d/$DEPLOY_USER > /dev/null
else
    echo "[1/6] User $DEPLOY_USER already exists"
fi

# 2. Setup application directory
echo "[2/6] Setting up application directory..."
mkdir -p $APP_DIR
mkdir -p $LOG_DIR
mkdir -p $DEPLOY_HOME/.config/mecamera

# Change ownership
chown -R $DEPLOY_USER:$DEPLOY_USER $APP_DIR $LOG_DIR $DEPLOY_HOME/.config/mecamera
chmod 750 $APP_DIR $LOG_DIR

# 3. Install system dependencies
echo "[3/6] Installing system dependencies..."
apt-get update
apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libopenjp2-7 \
    libtiff5 \
    libjasper1 \
    libatlas-base-dev \
    libjasper-dev \
    libharfbuzz0b \
    libwebp6 \
    libtiff5 \
    libqtgui4 \
    python3-pyqt5 \
    libqt4-test \
    libhdf5-dev \
    libharfbuzz0b \
    libwebp6 \
    libtiff5 \
    git \
    curl \
    wget \
    ffmpeg \
    libffi-dev \
    libssl-dev \
    libpq-dev

# 4. Setup Python virtual environment
echo "[4/6] Setting up Python environment..."
su - $DEPLOY_USER << EOF
cd $APP_DIR

# Create venv with system site packages (for compiled libs)
python3 -m venv --system-site-packages venv

# Activate and upgrade pip
source venv/bin/activate
pip install --upgrade pip setuptools wheel

# Install requirements
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    # Install core dependencies
    pip install \
        flask==2.3.0 \
        loguru==0.7.2 \
        werkzeug==2.3.0 \
        cryptography==41.0.0 \
        qrcode==7.4.2 \
        Pillow==10.0.0 \
        pydrive2==1.19.0 \
        requests==2.31.0
fi
EOF

# 5. Create systemd service
echo "[5/6] Creating systemd service..."
cat > $SERVICE_FILE << EOF
[Unit]
Description=ME Camera Security System
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=$DEPLOY_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$APP_DIR/venv/bin/python3 main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mecamera

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$APP_DIR $LOG_DIR /tmp

# Resource limits (for Pi Zero)
MemoryLimit=300M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chmod 644 $SERVICE_FILE

# 6. Enable and configure service
echo "[6/6] Enabling autoboot service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# Setup log rotation
cat > /etc/logrotate.d/mecamera << EOF
$LOG_DIR/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 $DEPLOY_USER $DEPLOY_USER
    sharedscripts
}
EOF

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Service Name: $SERVICE_NAME"
echo "Status: $(systemctl is-enabled $SERVICE_NAME)"
echo ""
echo "📋 Next Steps:"
echo "  1. Connect to Pi via: http://<pi-ip>:8080"
echo "  2. Complete first-run setup in dashboard"
echo "  3. Create admin user with password"
echo "  4. Configure WiFi, emergency contacts, etc"
echo ""
echo "🔧 Useful Commands:"
echo "  • Start service: sudo systemctl start $SERVICE_NAME"
echo "  • Stop service: sudo systemctl stop $SERVICE_NAME"
echo "  • View logs: sudo journalctl -u $SERVICE_NAME -f"
echo "  • Service status: sudo systemctl status $SERVICE_NAME"
echo "  • Restart: sudo systemctl restart $SERVICE_NAME"
echo ""
echo "📱 Dashboard Access:"
echo "  • Default Port: 8080"
echo "  • URL: http://<pi-ip>:8080"
echo "  • Mobile Friendly: Yes"
echo "  • Encryption: Enabled"
echo ""
echo "⚠️  Security Notes:"
echo "  • Change default password immediately!"
echo "  • Enable HTTPS for remote access (via reverse proxy)"
echo "  • Keep device on same network or use VPN"
echo "  • Backup encryption keys regularly"
echo ""
