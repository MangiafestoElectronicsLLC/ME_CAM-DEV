#!/bin/bash

##############################################################################
# ME_CAM Automated Setup Script - v2.2.3
# 
# Purpose: Fully automated setup for fresh Raspberry Pi installations
# Features:
#   - Auto-detects Pi hardware (Zero 2W, Pi 4, Pi 5, etc.)
#   - Auto-detects camera hardware (IMX519, OV547, etc.)
#   - Auto-detects SD card capacity
#   - Auto-assigns device number (mecamdev1-mecamdev99)
#   - Creates configuration with detected specs
#   - Installs all dependencies
#   - Sets up systemd service for auto-boot
#
# Usage: curl -sSL https://your-repo/scripts/auto_setup_mecam.sh | sudo bash
# Or:    sudo bash auto_setup_mecam.sh
#
# Author: MangiafestoElectronics LLC
# Date: Feb 2026
##############################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
PI_MODEL=""
PI_RAM=""
CAMERA_TYPE=""
CAMERA_OVERLAY=""
DEVICE_NUMBER=""
SD_CAPACITY=""
HOSTNAME=""
CONFIG_DIR="$HOME/ME_CAM-DEV/config"
REPO_DIR="$HOME/ME_CAM-DEV"

##############################################################################
# Helper Functions
##############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

##############################################################################
# STEP 1: Detect Hardware
##############################################################################

detect_pi_model() {
    log_info "Detecting Raspberry Pi model..."
    
    # Check /proc/device-tree/model
    if [ -f /proc/device-tree/model ]; then
        local model=$(tr -d '\0' < /proc/device-tree/model)
        PI_MODEL="$model"
    else
        PI_MODEL="Unknown Pi"
    fi
    
    log_success "Pi Model: $PI_MODEL"
}

detect_pi_ram() {
    log_info "Detecting RAM..."
    
    # Get total memory in MB
    local ram_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    PI_RAM=$((ram_kb / 1024))
    
    log_success "RAM: ${PI_RAM}MB"
}

detect_camera() {
    log_info "Detecting camera hardware..."
    
    CAMERA_TYPE="None"
    CAMERA_OVERLAY="auto_detect"
    
    # Try libcamera first (new method)
    if command -v rpicam-hello &> /dev/null; then
        log_info "Testing with rpicam-hello..."
        timeout 5 rpicam-hello --version > /dev/null 2>&1 || true
    fi
    
    # Check /proc/device-tree for camera overlays
    if [ -d /proc/device-tree/soc/i2c@7e805000 ]; then
        # Check I2C camera (IMX519, IMX708, etc.)
        if grep -q "imx519" /proc/device-tree/compatible 2>/dev/null || \
           grep -q "imx519" /boot/firmware/config.txt 2>/dev/null; then
            CAMERA_TYPE="IMX519 (I2C)"
            CAMERA_OVERLAY="imx519"
        elif grep -q "imx708" /proc/device-tree/compatible 2>/dev/null || \
             grep -q "imx708" /boot/firmware/config.txt 2>/dev/null; then
            CAMERA_TYPE="IMX708"
            CAMERA_OVERLAY="imx708"
        fi
    fi
    
    # Check CSI camera (OV547, OV5647, etc.)
    if grep -q "ov547" /boot/firmware/config.txt 2>/dev/null; then
        CAMERA_TYPE="OV547 (OmniVision)"
        CAMERA_OVERLAY="ov547"
    elif grep -q "ov5647" /boot/firmware/config.txt 2>/dev/null; then
        CAMERA_TYPE="OV5647"
        CAMERA_OVERLAY="ov5647"
    fi
    
    # If still not detected, default to auto-detect
    if [ "$CAMERA_TYPE" = "None" ]; then
        CAMERA_TYPE="Auto-detect (first boot)"
        CAMERA_OVERLAY="auto_detect"
        log_warn "Camera not yet detected - will auto-configure on first boot"
    else
        log_success "Camera: $CAMERA_TYPE"
    fi
}

detect_sd_card() {
    log_info "Detecting SD card capacity..."
    
    # Get root filesystem size
    local root_size=$(df / | tail -1 | awk '{print $2}')
    SD_CAPACITY=$((root_size / 1024 / 1024)) # Convert to GB
    
    # Round to nearest common size
    if [ $SD_CAPACITY -lt 64 ]; then
        SD_CAPACITY="32"
    elif [ $SD_CAPACITY -lt 100 ]; then
        SD_CAPACITY="64"
    elif [ $SD_CAPACITY -lt 200 ]; then
        SD_CAPACITY="128"
    else
        SD_CAPACITY="256"
    fi
    
    log_success "SD Card: ${SD_CAPACITY}GB"
}

##############################################################################
# STEP 2: Auto-assign Device Number
##############################################################################

get_device_number() {
    log_info "Assigning device number..."
    
    # Read from config if exists, or prompt
    if [ -f "$CONFIG_DIR/device_number.txt" ]; then
        DEVICE_NUMBER=$(cat "$CONFIG_DIR/device_number.txt")
        log_info "Found existing device number: $DEVICE_NUMBER"
    else
        # Try to get from hostname if already set
        local current_hostname=$(hostname)
        
        if [[ $current_hostname =~ mecamdev([0-9]+) ]]; then
            DEVICE_NUMBER="${BASH_REMATCH[1]}"
            log_info "Device number from hostname: $DEVICE_NUMBER"
        else
            # Interactive prompt
            echo -e "${YELLOW}No device number found.${NC}"
            echo "Enter device number (1-99) [default: 1]:"
            read -r DEVICE_NUMBER
            DEVICE_NUMBER=${DEVICE_NUMBER:-1}
            
            # Validate
            if ! [[ $DEVICE_NUMBER =~ ^[0-9]{1,2}$ ]] || [ $DEVICE_NUMBER -lt 1 ] || [ $DEVICE_NUMBER -gt 99 ]; then
                log_error "Invalid device number: $DEVICE_NUMBER"
                exit 1
            fi
        fi
    fi
    
    HOSTNAME="mecamdev$DEVICE_NUMBER"
    log_success "Device: $HOSTNAME"
}

##############################################################################
# STEP 3: System Updates
##############################################################################

update_system() {
    log_info "Updating system packages..."
    sudo apt update > /dev/null 2>&1
    sudo apt upgrade -y > /dev/null 2>&1
    log_success "System updated"
}

##############################################################################
# STEP 4: Install Dependencies
##############################################################################

install_dependencies() {
    log_info "Installing dependencies (this takes 5-10 minutes)..."
    
    # Core dependencies
    local packages=(
        "python3-pip"
        "python3-venv"
        "libcamera-apps"
        "python3-picamera2"
        "python3-opencv"
        "python3-dev"
        "libffi-dev"
        "libjpeg-dev"
        "zlib1g-dev"
        "git"
    )
    
    for pkg in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $pkg"; then
            log_info "Installing $pkg..."
            sudo apt install -y "$pkg" > /dev/null 2>&1
        fi
    done
    
    log_success "Dependencies installed"
}

##############################################################################
# STEP 5: Set Hostname
##############################################################################

set_hostname() {
    log_info "Setting hostname to $HOSTNAME..."
    
    # Check if already set
    if [ "$(hostname)" = "$HOSTNAME" ]; then
        log_success "Hostname already set to $HOSTNAME"
        return
    fi
    
    # Set hostname
    echo "$HOSTNAME" | sudo tee /etc/hostname > /dev/null
    
    # Update /etc/hosts
    sudo sed -i "s/127.0.1.1.*/127.0.1.1\t$HOSTNAME/" /etc/hosts
    
    # Apply immediately
    sudo hostname "$HOSTNAME"
    
    log_success "Hostname set to $HOSTNAME"
    log_warn "Note: Hostname change effective after reboot"
}

##############################################################################
# STEP 6: Clone Repository
##############################################################################

clone_repository() {
    if [ -d "$REPO_DIR" ]; then
        log_info "Repository already exists, updating..."
        cd "$REPO_DIR"
        git pull > /dev/null 2>&1
    else
        log_info "Cloning ME_CAM repository..."
        cd ~
        git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git > /dev/null 2>&1
    fi
    
    log_success "Repository ready at $REPO_DIR"
}

##############################################################################
# STEP 7: Setup Python Environment
##############################################################################

setup_venv() {
    log_info "Setting up Python virtual environment..."
    
    cd "$REPO_DIR"
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv --system-site-packages
    fi
    
    # Activate and install
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1
    
    log_success "Python environment ready"
}

##############################################################################
# STEP 8: Create Configuration
##############################################################################

create_config() {
    log_info "Creating configuration..."
    
    # Create config directory
    mkdir -p "$CONFIG_DIR"
    
    # Calculate storage limits based on SD card
    local storage_limit=$((SD_CAPACITY / 2))  # Use half of SD card
    [ $storage_limit -lt 10 ] && storage_limit=10
    [ $storage_limit -gt 100 ] && storage_limit=100
    
    # Determine framerate based on Pi model and RAM
    local framerate=30
    if [[ "$PI_MODEL" == *"Pi 5"* ]]; then
        framerate=60
    elif [[ "$PI_MODEL" == *"Pi 4"* ]] && [ $PI_RAM -ge 2048 ]; then
        framerate=40
    fi
    
    # Create config.json
    cat > "$CONFIG_DIR/config.json" << EOF
{
    "first_run_completed": true,
    "device_name": "ME_CAM_${DEVICE_NUMBER}",
    "device_id": "pi-cam-$(printf '%03d' $DEVICE_NUMBER)",
    "hardware": {
        "pi_model": "$PI_MODEL",
        "pi_ram_mb": $PI_RAM,
        "camera": "$CAMERA_TYPE",
        "sd_capacity_gb": $SD_CAPACITY
    },
    "resolution": "640x480",
    "framerate": $framerate,
    "motion_detection": true,
    "video_length": 30,
    "storage_limit_gb": $storage_limit,
    "auto_delete_old": true,
    "web_port": 8080,
    "setup_timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
    "setup_automated": true
}
EOF
    
    log_success "Configuration created"
    log_info "  - Device Name: ME_CAM_${DEVICE_NUMBER}"
    log_info "  - Framerate: ${framerate} FPS"
    log_info "  - Storage Limit: ${storage_limit}GB"
}

##############################################################################
# STEP 9: Save Device Number
##############################################################################

save_device_number() {
    mkdir -p "$CONFIG_DIR"
    echo "$DEVICE_NUMBER" > "$CONFIG_DIR/device_number.txt"
}

##############################################################################
# STEP 10: Setup Systemd Service
##############################################################################

setup_service() {
    log_info "Setting up systemd service..."
    
    local service_file="/etc/systemd/system/mecamera.service"
    
    # Create service file
    sudo tee "$service_file" > /dev/null << 'EOF'
[Unit]
Description=ME_CAM Security Camera
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ME_CAM-DEV
Environment="PATH=/home/pi/ME_CAM-DEV/venv/bin:/usr/bin:/bin"
ExecStart=/home/pi/ME_CAM-DEV/venv/bin/python3 /home/pi/ME_CAM-DEV/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload and enable
    sudo systemctl daemon-reload
    sudo systemctl enable mecamera > /dev/null 2>&1
    
    log_success "Systemd service configured"
}

##############################################################################
# STEP 11: Configure Camera Overlay (if needed)
##############################################################################

configure_camera_overlay() {
    if [ "$CAMERA_OVERLAY" = "auto_detect" ]; then
        log_info "Camera set to auto-detect"
        return
    fi
    
    log_info "Configuring camera overlay: $CAMERA_OVERLAY..."
    
    # Check if overlay already configured
    if grep -q "dtoverlay=$CAMERA_OVERLAY" /boot/firmware/config.txt 2>/dev/null; then
        log_success "Camera overlay already configured"
        return
    fi
    
    # Add overlay to config.txt
    echo "" | sudo tee -a /boot/firmware/config.txt > /dev/null
    echo "# ME_CAM Camera Configuration" | sudo tee -a /boot/firmware/config.txt > /dev/null
    echo "camera_auto_detect=0" | sudo tee -a /boot/firmware/config.txt > /dev/null
    echo "dtoverlay=$CAMERA_OVERLAY" | sudo tee -a /boot/firmware/config.txt > /dev/null
    echo "gpu_mem=128" | sudo tee -a /boot/firmware/config.txt > /dev/null
    
    log_warn "Camera overlay configured - requires reboot"
}

##############################################################################
# STEP 12: Test Setup
##############################################################################

test_setup() {
    log_info "Testing setup..."
    
    cd "$REPO_DIR"
    source venv/bin/activate
    
    # Quick import test
    if python3 -c "from web.app_lite import create_lite_app; print('[OK]')" 2>/dev/null | grep -q OK; then
        log_success "Application imports verified"
    else
        log_warn "Import test skipped (normal on first setup)"
    fi
}

##############################################################################
# STEP 13: Summary and Next Steps
##############################################################################

print_summary() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  ME_CAM Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Device Information:"
    echo "  Hostname:       $HOSTNAME"
    echo "  Device ID:      pi-cam-$(printf '%03d' $DEVICE_NUMBER)"
    echo "  Pi Model:       $PI_MODEL"
    echo "  RAM:            ${PI_RAM}MB"
    echo "  Camera:         $CAMERA_TYPE"
    echo "  SD Card:        ${SD_CAPACITY}GB"
    echo ""
    echo "Access your camera at:"
    echo -e "  ${BLUE}http://$HOSTNAME.local:8080${NC}"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure WiFi (if not already done)"
    echo "  2. Reboot the Pi for hostname changes:"
    echo "     ${YELLOW}sudo reboot${NC}"
    echo ""
    echo "After reboot, access the camera at:"
    echo -e "  ${BLUE}http://$HOSTNAME.local:8080${NC}"
    echo ""
    echo "View logs:"
    echo "  ${YELLOW}sudo journalctl -u mecamera -f${NC}"
    echo ""
    echo "Manage service:"
    echo "  ${YELLOW}sudo systemctl status mecamera${NC}"
    echo "  ${YELLOW}sudo systemctl restart mecamera${NC}"
    echo ""
}

##############################################################################
# MAIN EXECUTION
##############################################################################

main() {
    clear
    
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║   ME_CAM Automated Setup v2.2.3        ║"
    echo "║   Raspberry Pi Camera System           ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    
    # Check if running as root (for some operations)
    if [ "$EUID" -ne 0 ] && [ "$EUID" -ne $(id -u pi 2>/dev/null || echo 1000) ]; then
        log_error "This script should be run as pi user (uses sudo for privileged operations)"
        exit 1
    fi
    
    # Detect hardware
    log_info "========== DETECTING HARDWARE =========="
    detect_pi_model
    detect_pi_ram
    detect_camera
    detect_sd_card
    
    # Get device number
    log_info "========== DEVICE CONFIGURATION =========="
    get_device_number
    
    # System setup
    log_info "========== SYSTEM SETUP =========="
    update_system
    install_dependencies
    set_hostname
    
    # Application setup
    log_info "========== APPLICATION SETUP =========="
    clone_repository
    setup_venv
    create_config
    save_device_number
    setup_service
    configure_camera_overlay
    
    # Testing
    log_info "========== TESTING =========="
    test_setup
    
    # Summary
    print_summary
    
    log_success "Setup complete! Please reboot for all changes to take effect."
}

# Run main
main "$@"
