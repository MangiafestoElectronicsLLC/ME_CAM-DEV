#!/bin/bash
# ME_CAM Device Update Script
# Run this on devices 1 and 2

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                ME_CAM Device Update Script                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

DEVICE_NAME=$(hostname)
echo "📱 Device: $DEVICE_NAME"
echo "🕐 Time: $(date)"
echo ""

# Step 1: Check if in right directory
echo "📂 Checking repository..."
if [ ! -d "~/ME_CAM-DEV/.git" ]; then
    echo "❌ Not in ME_CAM-DEV directory!"
    echo "Run: cd ~/ME_CAM-DEV"
    exit 1
fi

cd ~/ME_CAM-DEV
echo "✓ In correct directory"
echo ""

# Step 2: Show current status
echo "📊 Current Status:"
echo "Branch: $(git branch --show-current)"
echo "Last commit: $(git log -1 --oneline)"
echo ""

# Step 3: Pull latest
echo "⬇️  Pulling latest from GitHub..."
git pull origin main
if [ $? -ne 0 ]; then
    echo "❌ Git pull failed!"
    exit 1
fi
echo "✓ Pull complete"
echo ""

# Step 4: Activate venv
echo "🐍 Activating Python environment..."
source venv/bin/activate
echo "✓ venv activated"
echo ""

# Step 5: Check dependencies
echo "📦 Checking Python packages..."
python3 -c "import flask, picamera2, cv2, loguru; print('✓ All packages OK')"
if [ $? -ne 0 ]; then
    echo "⚠️  Installing missing packages..."
    pip install -q Flask==3.0.0 Werkzeug==3.0.0
fi
echo ""

# Step 6: Stop old app if running
echo "🛑 Stopping old app instance..."
pkill -f 'python.*main_lite.py'
sleep 2
echo "✓ Old app stopped"
echo ""

# Step 7: Check camera
echo "📷 Checking camera..."
vcgencmd get_camera
echo ""

# Step 8: Start new app
echo "▶️  Starting ME_CAM app..."
nohup python main_lite.py > /tmp/mecam.log 2>&1 &
PID=$!
sleep 3

if kill -0 $PID 2>/dev/null; then
    echo "✓ App started (PID: $PID)"
    echo "✓ Listening on http://$(hostname -I | awk '{print $1}'):8080"
else
    echo "❌ App failed to start"
    echo "Tail of log:"
    tail -20 /tmp/mecam.log
    exit 1
fi
echo ""

# Step 9: Verify app
echo "🔍 Verifying app..."
sleep 2
if curl -s http://localhost:8080/ | grep -q "ME_CAM"; then
    echo "✓ App responding correctly"
else
    echo "⚠️  App may not be fully ready yet"
fi
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✓ UPDATE COMPLETE                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Device: $DEVICE_NAME"
echo "Access: http://$(hostname -I | awk '{print $1}'):8080"
echo "Version: 2.1-LITE"
echo ""
echo "Logs: tail -f /tmp/mecam.log"
echo ""
