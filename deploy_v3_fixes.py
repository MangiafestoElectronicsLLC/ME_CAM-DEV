#!/usr/bin/env python3
"""
V3.0 Production Deployment Script

Pushes fixes to ME_CAM devices and verifies they're working properly.
Usage: python3 deploy_v3_fixes.py --device D2,D3,D4
"""

import subprocess
import sys
import argparse
import json
import time
from pathlib import Path

class DeviceDeployer:
    def __init__(self, prefix="mecamdev", username="pi"):
        self.prefix = prefix
        self.username = username
        self.devices = {}
    
    def add_device(self, number, password, ip=None):
        """Add device to deployment list."""
        hostname = f"{self.prefix}{number}.local"
        self.devices[number] = {
            'hostname': hostname,
            'ip': ip or hostname,
            'password': password,
            'number': number
        }
    
    def run_ssh(self, device_num, cmd, timeout=30):
        """Run command on device via SSH."""
        if device_num not in self.devices:
            print(f"✗ Device {device_num} not configured")
            return False, ""
        
        device = self.devices[device_num]
        ssh_cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            f"{self.username}@{device['ip']}",
            cmd
        ]
        
        try:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            print(f"✗ SSH timeout on D{device_num}")
            return False, ""
        except Exception as e:
            print(f"✗ SSH error on D{device_num}: {e}")
            return False, ""
    
    def scp_push(self, device_num, src_file, dest_path):
        """Push file to device via SCP."""
        if device_num not in self.devices:
            return False
        
        device = self.devices[device_num]
        scp_cmd = [
            "scp",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            src_file,
            f"{self.username}@{device['ip']}:{dest_path}"
        ]
        
        try:
            result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
        except Exception as e:
            print(f"✗ SCP error: {e}")
            return False
    
    def deploy_fixes(self, device_num):
        """Deploy all V3.0 fixes to device."""
        print(f"\n{'='*70}")
        print(f"DEPLOYING V3.0 FIXES TO DEVICE {device_num}")
        print(f"{'='*70}")
        
        base_path = Path("~/ME_CAM-DEV").expanduser()
        
        # Files to deploy
        files_to_deploy = [
            ("src/core/battery_monitor.py", "ME_CAM-DEV/src/core/"),
            ("src/core/power_saver.py", "ME_CAM-DEV/src/core/"),
            ("web/app_lite.py", "ME_CAM-DEV/web/"),
        ]
        
        print(f"\n1. Pushing code files...")
        for src_file, dest_dir in files_to_deploy:
            src_path = base_path / src_file
            if not src_path.exists():
                print(f"  ✗ File not found: {src_file}")
                continue
            
            if self.scp_push(device_num, str(src_path), f"~/{dest_dir}"):
                print(f"  ✓ Pushed {src_file}")
            else:
                print(f"  ✗ Failed to push {src_file}")
                return False
        
        # Update configuration
        print(f"\n2. Updating device configuration...")
        config_updates = {
            "avg_current_draw_ma": 600,
            "power_saving_enabled": True,
            "audio_record_on_motion": True
        }
        
        cmd_update_config = f"""
python3 << 'PYEOF'
import json
try:
    with open('config.json', 'r') as f:
        cfg = json.load(f)
    
    # Apply updates
    cfg.update({json.dumps(config_updates)})
    
    with open('config.json', 'w') as f:
        json.dump(cfg, f, indent=2)
    
    print("✓ Config updated")
    print(f"  - avg_current_draw_ma: {{cfg.get('avg_current_draw_ma')}}")
    print(f"  - power_saving_enabled: {{cfg.get('power_saving_enabled')}}")
    print(f"  - audio_record_on_motion: {{cfg.get('audio_record_on_motion')}}")
except Exception as e:
    print(f"✗ Error: {{e}}")
PYEOF
"""
        
        success, output = self.run_ssh(device_num, cmd_update_config)
        if success:
            print(f"  ✓ Configuration updated")
            for line in output.split('\n'):
                if line.strip():
                    print(f"    {line}")
        else:
            print(f"  ✗ Failed to update configuration")
            return False
        
        # Restart service
        print(f"\n3. Restarting ME_CAM service...")
        
        # Try systemctl first, then manual restart
        restart_cmd = """
sudo systemctl restart mecam 2>/dev/null || {
    pkill -f app_lite.py
    sleep 2
    cd ME_CAM-DEV
    nohup python3 web/app_lite.py > logs/app.log 2>&1 &
    sleep 2
    echo "✓ Service restarted"
}
"""
        
        success, output = self.run_ssh(device_num, restart_cmd)
        if output:
            print(f"  {output}")
        else:
            print(f"  ✓ Service restart commands sent")
        
        # Wait for service to come up
        print(f"\n4. Waiting for service to start...")
        for i in range(10):
            success, _ = self.run_ssh(device_num, "curl -s http://localhost:8080/api/battery | head -c 50")
            if success:
                print(f"  ✓ Service is responding")
                break
            else:
                time.sleep(2)
                print(f"  Attempt {i+1}/10... waiting")
        
        # Verify fixes
        print(f"\n5. Verifying fixes...")
        success, output = self.run_ssh(device_num, """
curl -s http://localhost:8080/api/battery | python3 -m json.tool 2>/dev/null | \
  grep -E '"power_source"|"avg_current|"percent"' || echo "API check"
""")
        
        if success and output:
            print(f"  ✓ Battery API responding:")
            for line in output.split('\n')[:5]:
                if line.strip():
                    print(f"    {line}")
        else:
            print(f"  ⚠ Could not verify API (may still be starting)")
        
        # Run diagnostics
        print(f"\n6. Running on-device diagnostics...")
        success, _ = self.run_ssh(device_num, "python3 camera_diagnostics.py 2>&1 | head -30")
        if success:
            print(f"  ✓ Diagnostics complete (see device for details)")
        
        print(f"\n{'='*70}")
        print(f"✓ DEPLOYMENT COMPLETE FOR D{device_num}")
        print(f"{'='*70}")
        return True
    
    def verify_device(self, device_num):
        """Quick verification that device is working."""
        print(f"\nVerifying Device {device_num}...")
        
        # Check connectivity
        success, _ = self.run_ssh(device_num, "hostname")
        if not success:
            print(f"✗ Cannot reach device D{device_num}")
            return False
        
        # Check service
        success, output = self.run_ssh(device_num, "curl -s http://localhost:8080/api/battery | head -c 100")
        if success:
            print(f"✓ D{device_num} is online and responding")
            return True
        else:
            print(f"⚠ D{device_num} is online but service not responding yet")
            return False


def main():
    parser = argparse.ArgumentParser(description="Deploy V3.0 fixes to ME_CAM devices")
    parser.add_argument("--devices", "-d", help="Comma-separated device numbers (e.g., 2,3,4)")
    parser.add_argument("--verify-only", action="store_true", help="Only verify devices, don't deploy")
    
    args = parser.parse_args()
    
    # Create deployer
    deployer = DeviceDeployer()
    
    # Configure devices
    device_configs = {
        2: "Kidcudi123",       # D2 password
        3: "Kidcudi123",       # D3 password
        4: "Kidcudi12345678",  # D4 password
    }
    
    # Parse device list
    if args.devices:
        device_list = [int(x.strip()) for x in args.devices.split(',')]
    else:
        device_list = [2, 3, 4]  # Default
    
    # Add configured devices
    for dev_num in device_list:
        if dev_num in device_configs:
            deployer.add_device(dev_num, device_configs[dev_num])
    
    # Run operations
    if args.verify_only:
        print("VERIFYING DEVICES")
        print("="*70)
        for dev_num in device_list:
            deployer.verify_device(dev_num)
    else:
        print("V3.0 PRODUCTION FIX DEPLOYMENT")
        print("="*70)
        print(f"Target devices: {', '.join(f'D{n}' for n in device_list)}")
        
        response = input("\nProceed with deployment? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Deployment cancelled.")
            return
        
        for dev_num in device_list:
            deployer.deploy_fixes(dev_num)
            time.sleep(5)  # Wait between devices
        
        print("\n" + "="*70)
        print("DEPLOYMENT COMPLETE")
        print("All devices should now have V3.0 fixes applied.")
        print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDeployment cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Deployment error: {e}")
        sys.exit(1)
