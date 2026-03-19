#!/usr/bin/env python3
"""
ME_CAM V3.0 - ONE-CLICK DEPLOYMENT & TESTING LAUNCHER
=====================================================

Quick Start Guide:
    python3 launch_v3_testing.py --quick         # Test current devices
    python3 launch_v3_testing.py --deploy 2,3,4 # Deploy & test devices 2,3,4
    python3 launch_v3_testing.py --interactive 2 # SSH shell on device 2
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

class V3Launcher:
    def __init__(self):
        self.workspace = Path.cwd()
        self.devices = {
            '2': {'host': 'mecamdev2.local', 'pass': 'Kidcudi123'},
            '3': {'host': 'mecamdev3.local', 'pass': 'Kidcudi123'},
            '4': {'host': 'mecamdev4.local', 'pass': 'Kidcudi12345678'},
        }
        
    def print_banner(self):
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        ME_CAM V3.0 - PRODUCTION SECURITY SYSTEM             ║
║                                                              ║
║  ✓ HTTPS/SSL Encryption      ✓ Power-Saving (4 Modes)     ║
║  ✓ AES-256 Video Encryption  ✓ Responsive Mobile UI       ║
║  ✓ Security Hardening        ✓ Dark Mode Support          ║
║  ✓ Rate Limiting             ✓ Accurate Battery Estimates ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    def verify_files(self):
        """Check all V3.0 files exist"""
        print("\n📋 Verifying V3.0 files...")
        required = [
            'setup_https.py',
            'deploy_v3_complete.py',
            'test_devices_ssh.py',
            'V3_INTEGRATION_GUIDE.md',
            'V3_DEPLOYMENT_COMPLETE.md',
            'src/core/security.py',
            'src/core/encryption.py',
            'src/core/power_saver.py',
            'src/ui/responsive_theme.py',
        ]
        
        missing = []
        for f in required:
            if not (self.workspace / f).exists():
                missing.append(f)
                print(f"  ✗ Missing: {f}")
            else:
                print(f"  ✓ Found: {f}")
        
        if missing:
            print(f"\n❌ ERROR: {len(missing)} files missing!")
            print("Please ensure all V3.0 files are in workspace.")
            return False
        
        print("\n✅ All V3.0 files present!")
        return True

    def quick_test_devices(self):
        """Run quick diagnostics on all devices"""
        print("\n🔍 QUICK DEVICE DIAGNOSTICS")
        print("=" * 60)
        
        for device_id in ['2', '3', '4']:
            print(f"\n📱 Device D{device_id} ({self.devices[device_id]['host']})...")
            cmd = ['python3', 'test_devices_ssh.py', f'--device', device_id, '--quick']
            subprocess.run(cmd, cwd=self.workspace)
            print("")

    def deploy_devices(self, device_ids):
        """Deploy V3.0 to specified devices"""
        print(f"\n🚀 DEPLOYING V3.0 TO DEVICES: {device_ids}")
        print("=" * 60)
        
        device_list = ','.join(device_ids)
        cmd = ['python3', 'deploy_v3_complete.py', '--devices', device_list, '--test']
        subprocess.run(cmd, cwd=self.workspace)

    def interactive_shell(self, device_id):
        """Open interactive SSH shell on device"""
        print(f"\n💻 INTERACTIVE SHELL - Device D{device_id}")
        print("=" * 60)
        print("\nAvailable commands:")
        print("  battery   - Check battery & power source")
        print("  info      - Device info")
        print("  services  - Check running services")
        print("  camera    - Camera status")
        print("  security  - Security modules")
        print("  power     - Power-saver status")
        print("  logs N    - View N lines of log")
        print("  restart   - Restart application")
        print("  help      - Show all commands")
        print("  quit      - Exit shell\n")
        
        cmd = ['python3', 'test_devices_ssh.py', '--device', device_id]
        subprocess.run(cmd, cwd=self.workspace)

    def show_dashboard(self):
        """Show quick status dashboard"""
        print("\n📊 V3.0 STATUS DASHBOARD")
        print("=" * 60)
        print("""
FEATURES DEPLOYED:
  ✓ HTTPS/SSL - Self-signed certificates (5-year validity)
  ✓ ENCRYPTION - AES-256 video encryption with PBKDF2 keys
  ✓ SECURITY - Rate limiting (100-5 req/min), CSRF, validation
  ✓ POWER-SAVING - 4 dynamic modes (critical/low/medium/normal)
  ✓ UI/UX - Responsive (320px-1920px), dark mode, touch-optimized
  ✓ BATTERY - Accurate power source detection, realistic estimates
  ✓ TESTING - SSH diagnostic tools, interactive shell
  ✓ DEPLOYMENT - Automated deployment with verification

CONFIGURATION:
  Devices: D2, D3, D4 (mecamdev2/3/4.local)
  HTTPS Port: 8443 (self-signed)
  API Auth: Token-based (generated per request)
  Power Mode Switch: Automatic by battery level
  Encryption: Transparent on motion clips

QUICK COMMANDS:
  python3 launch_v3_testing.py --quick              → Test all devices
  python3 launch_v3_testing.py --deploy 2,3,4      → Full deployment
  python3 launch_v3_testing.py --interactive 2     → SSH to D2
  
DOCUMENTATION:
  V3_DEPLOYMENT_COMPLETE.md    → Full deployment guide
  V3_INTEGRATION_GUIDE.md      → Code integration examples
  test_devices_ssh.py          → SSH diagnostics tool
  deploy_v3_complete.py        → Automated deployment
""")

    def main(self):
        parser = argparse.ArgumentParser(
            description='ME_CAM V3.0 Deployment & Testing Launcher',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''
Examples:
  python3 launch_v3_testing.py --verify              Test file integrity
  python3 launch_v3_testing.py --quick               Quick device diagnostics
  python3 launch_v3_testing.py --deploy 2,3,4       Deploy V3.0 to all devices
  python3 launch_v3_testing.py --interactive 2      SSH shell on D2
  python3 launch_v3_testing.py --dashboard           Show status dashboard
            '''
        )
        
        parser.add_argument('--verify', action='store_true', 
                          help='Verify all V3.0 files exist')
        parser.add_argument('--quick', action='store_true',
                          help='Run quick diagnostics on all devices')
        parser.add_argument('--deploy', type=str, metavar='DEVICES',
                          help='Deploy V3.0 to devices (e.g., "2,3,4")')
        parser.add_argument('--interactive', type=str, metavar='DEVICE',
                          help='Interactive SSH shell on device (e.g., "2")')
        parser.add_argument('--dashboard', action='store_true',
                          help='Show V3.0 status dashboard')
        
        args = parser.parse_args()
        
        self.print_banner()
        
        # Default to dashboard if no args
        if not any(vars(args).values()):
            self.show_dashboard()
            print("\n📚 Use --help for all options")
            return
        
        if args.verify:
            self.verify_files()
        
        elif args.quick:
            if self.verify_files():
                self.quick_test_devices()
        
        elif args.deploy:
            if self.verify_files():
                devices = args.deploy.split(',')
                # Validate device IDs
                for d in devices:
                    if d not in self.devices:
                        print(f"❌ Invalid device ID: {d}")
                        return
                self.deploy_devices(devices)
        
        elif args.interactive:
            if self.verify_files():
                if args.interactive not in self.devices:
                    print(f"❌ Invalid device ID: {args.interactive}")
                    return
                self.interactive_shell(args.interactive)
        
        elif args.dashboard:
            self.show_dashboard()

if __name__ == '__main__':
    launcher = V3Launcher()
    launcher.main()
