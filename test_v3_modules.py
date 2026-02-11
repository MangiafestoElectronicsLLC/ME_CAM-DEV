#!/usr/bin/env python3
"""
Test script for v3.0 modules
Run on Device 1 to verify new code works
"""

import sys
import traceback

print("="*60)
print("ME_CAM v3.0 Module Testing")
print("="*60)

# Test 1: Import detection module
print("\n[TEST 1] Testing TFLite Detector Import...")
try:
    from src.detection.tflite_detector import TFLiteDetector, SmartMotionDetector, DetectionTracker
    print("✅ PASS - TFLite detector modules imported successfully")
    print(f"   - TFLiteDetector: {TFLiteDetector}")
    print(f"   - SmartMotionDetector: {SmartMotionDetector}")
    print(f"   - DetectionTracker: {DetectionTracker}")
except Exception as e:
    print(f"❌ FAIL - Could not import: {e}")
    traceback.print_exc()

# Test 2: Import WebRTC module
print("\n[TEST 2] Testing WebRTC Module Import...")
try:
    from src.streaming.webrtc_peer import WebRTCStreamer
    print("✅ PASS - WebRTC module imported successfully")
    print(f"   - WebRTCStreamer: {WebRTCStreamer}")
except Exception as e:
    print(f"❌ FAIL - Could not import: {e}")
    print("   Note: aiortc and av packages may not be installed yet")
    traceback.print_exc()

# Test 3: Import Remote Access module
print("\n[TEST 3] Testing Remote Access Module Import...")
try:
    from src.networking.remote_access import TailscaleHelper, CloudflareHelper
    print("✅ PASS - Remote access modules imported successfully")
    print(f"   - TailscaleHelper: {TailscaleHelper}")
    print(f"   - CloudflareHelper: {CloudflareHelper}")
except Exception as e:
    print(f"❌ FAIL - Could not import: {e}")
    traceback.print_exc()

# Test 4: Check for required packages
print("\n[TEST 4] Checking Python Package Dependencies...")
missing_packages = []

try:
    import numpy
    print(f"✅ numpy: {numpy.__version__}")
except ImportError:
    print("❌ numpy: NOT INSTALLED")
    missing_packages.append("numpy")

try:
    import cv2
    print(f"✅ opencv: {cv2.__version__}")
except ImportError:
    print("❌ opencv: NOT INSTALLED")
    missing_packages.append("python3-opencv (system package)")

try:
    import flask
    print(f"✅ flask: {flask.__version__}")
except ImportError:
    print("❌ flask: NOT INSTALLED")
    missing_packages.append("flask")

try:
    import aiohttp
    print(f"✅ aiohttp: {aiohttp.__version__}")
except ImportError:
    print("⚠️  aiohttp: NOT INSTALLED (needed for Phase 1)")
    missing_packages.append("aiohttp")

try:
    import aiortc
    print(f"✅ aiortc: {aiortc.__version__}")
except ImportError:
    print("⚠️  aiortc: NOT INSTALLED (needed for WebRTC)")
    missing_packages.append("aiortc")

try:
    import av
    print(f"✅ av: {av.__version__}")
except ImportError:
    print("⚠️  av: NOT INSTALLED (needed for WebRTC)")
    missing_packages.append("av")

# Test 5: Check system utilities
print("\n[TEST 5] Checking System Utilities...")
import subprocess

def check_command(cmd):
    try:
        result = subprocess.run([cmd, "--version"], capture_output=True, timeout=2)
        return result.returncode == 0
    except:
        return False

if check_command("rpicam-jpeg"):
    print("✅ rpicam-jpeg: AVAILABLE")
else:
    print("❌ rpicam-jpeg: NOT FOUND")

if check_command("tailscale"):
    print("✅ tailscale: INSTALLED")
else:
    print("⚠️  tailscale: NOT INSTALLED (optional for Phase 1)")

if check_command("cloudflared"):
    print("✅ cloudflared: INSTALLED")
else:
    print("⚠️  cloudflared: NOT INSTALLED (optional for Phase 1)")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

if missing_packages:
    print(f"\n⚠️  Missing {len(missing_packages)} packages:")
    for pkg in missing_packages:
        print(f"   - {pkg}")
    print("\nTo install missing packages:")
    print("   cd ~/ME_CAM-DEV")
    print("   source venv/bin/activate")
    print("   pip install aiohttp aiortc av")
else:
    print("\n✅ All core packages available!")

print("\nNext Steps:")
print("1. Install Phase 1 dependencies: pip install aiohttp aiortc av")
print("2. Test Tailscale: curl -fsSL https://tailscale.com/install.sh | sh")
print("3. Review IMPLEMENTATION_GUIDE_V3.md for integration steps")
print("\n" + "="*60)
