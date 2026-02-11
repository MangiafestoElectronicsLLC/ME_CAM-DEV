#!/usr/bin/env python3
"""
Quick demo to test Tailscale and remote access helpers
"""

import sys
sys.path.insert(0, '/home/pi/ME_CAM-DEV')

from src.networking.remote_access import TailscaleHelper, CloudflareHelper

print("="*60)
print("Remote Access Helpers Test")
print("="*60)

# Test Tailscale Helper
print("\n[TEST 1] Tailscale Helper")
print("-" * 40)
ts = TailscaleHelper()

print(f"Installed: {ts.is_installed()}")
if ts.is_installed():
    print(f"Enabled: {ts.is_enabled()}")
    status = ts.get_status()
    print(f"Status: {status}")
    ip = ts.get_tailscale_ip()
    if ip:
        print(f"✅ Tailscale IP: {ip}")
    else:
        print("⚠️  No Tailscale IP (not connected)")
else:
    print("⚠️  Tailscale not installed")
    print("   Install: curl -fsSL https://tailscale.com/install.sh | sh")

# Test Cloudflare Helper
print("\n[TEST 2] Cloudflare Helper")
print("-" * 40)
cf = CloudflareHelper()

print(f"Installed: {cf.is_installed()}")
if not cf.is_installed():
    print("⚠️  Cloudflared not installed")
    print("   Install: See IMPLEMENTATION_GUIDE_V3.md Phase 1.2")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("✅ All remote access modules loaded successfully")
print("\nTo enable Tailscale:")
print("  curl -fsSL https://tailscale.com/install.sh | sh")
print("  sudo tailscale up")
print("\nTo enable Cloudflare Tunnel:")
print("  See IMPLEMENTATION_GUIDE_V3.md for setup steps")
print("="*60)
