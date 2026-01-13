#!/bin/bash
# Auto-fix script for camera busy issue

echo "Creating backup..."
cp web/app.py web/app.py.backup_$(date +%Y%m%d_%H%M%S)

echo "Applying fix..."

# Create a temporary Python script to do the replacement
cat > /tmp/fix_app.py << 'FIXSCRIPT'
import sys

with open('web/app.py', 'r') as f:
    content = f.read()

# Fix 1: Comment out watchdog.start() and set to None
content = content.replace(
    'watchdog = CameraWatchdog()\nwatchdog.start()',
    '# watchdog = CameraWatchdog()\n# watchdog.start()\nwatchdog = None  # Disabled to allow libcamera streaming'
)

# Fix 2: Update watchdog.status() calls
content = content.replace(
    'status = watchdog.status()',
    'status = watchdog.status() if watchdog else {"active": False, "timestamp": time.time()}'
)

# Fix 3: Update API status endpoint
content = content.replace(
    'def api_status():\n    return jsonify(watchdog.status())',
    'def api_status():\n    return jsonify(watchdog.status() if watchdog else {"active": False, "timestamp": time.time()})'
)

with open('web/app.py', 'w') as f:
    f.write(content)

print("Fix applied successfully!")
FIXSCRIPT

python3 /tmp/fix_app.py

echo ""
echo "Fix complete! Backup saved as web/app.py.backup_*"
echo ""
echo "Now run: python3 main.py"
