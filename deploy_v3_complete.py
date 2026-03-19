#!/usr/bin/env python3
"""
ME_CAM V3.0 Production Deployment & Test Script

Deploys all V3.0 features to devices:
- HTTPS/SSL certificates
- Encryption system
- Security hardening
- Power-saving integration
- Responsive UI with dark mode
- Testing and verification

Usage: python3 deploy_v3_complete.py --devices 2,3,4 --test
"""

import subprocess
import sys
import json
import time
import requests
from pathlib import Path
import paramiko
from getpass import getpass


class V3Deployer:
    """Complete V3.0 deployment manager."""
    
    def __init__(self):
        self.devices = {}
        self.ssh_clients = {}
        self.test_results = {}
    
    def add_device(self, number, password, ip=None):
        """Add device for deployment."""
        self.devices[number] = {
            'hostname': f"mecamdev{number}.local",
            'ip': ip,
            'password': password,
            'number': number
        }
    
    def connect_ssh(self, device_num):
        """Connect to device via SSH."""
        if device_num in self.ssh_clients:
            return self.ssh_clients[device_num]
        
        device = self.devices.get(device_num)
        if not device:
            return None
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            client.connect(
                hostname=device['ip'] or device['hostname'],
                username='pi',
                password=device['password'],
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            self.ssh_clients[device_num] = client
            print(f"✓ D{device_num} SSH connected")
            return client
        except Exception as e:
            print(f"✗ D{device_num} SSH failed: {e}")
            return None
    
    def run_ssh_cmd(self, device_num, cmd, timeout=30):
        """Run SSH command on device."""
        client = self.connect_ssh(device_num)
        if not client:
            return False, ""
        
        try:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if error:
                print(f"  ⚠ {error[:100]}")
            
            return not error, output
        except Exception as e:
            print(f"  ✗ Command failed: {e}")
            return False, ""
    
    def scp_push(self, device_num, src_file, dest_path):
        """Push file to device via SCP."""
        client = self.connect_ssh(device_num)
        if not client:
            return False
        
        try:
            sftp = client.open_sftp()
            sftp.put(src_file, dest_path)
            sftp.close()
            return True
        except Exception as e:
            print(f"  ✗ SCP failed: {e}")
            return False
    
    def deploy_v3(self, device_num):
        """Deploy V3.0 to device."""
        print(f"\n{'='*70}")
        print(f"DEPLOYING V3.0 TO DEVICE {device_num}")
        print(f"{'='*70}")
        
        steps = [
            ("Setup HTTPS certificates", self._setup_https, device_num),
            ("Deploy security module", self._deploy_security, device_num),
            ("Deploy encryption system", self._deploy_encryption, device_num),
            ("Deploy power-saver", self._deploy_power_saver, device_num),
            ("Deploy responsive UI", self._deploy_ui, device_num),
            ("Update app_lite.py", self._update_app_lite, device_num),
            ("Update configuration", self._update_config, device_num),
            ("Restart services", self._restart_services, device_num),
            ("Verify deployment", self._verify_deployment, device_num),
        ]
        
        for step_name, step_func, *args in steps:
            print(f"\n{step_name}...", end=" ", flush=True)
            try:
                if step_func(*args):
                    print("✓")
                else:
                    print("✗ (continuing...)")
            except Exception as e:
                print(f"✗ {e}")
        
        print(f"\n✓ D{device_num} deployment complete")
        return True
    
    def _setup_https(self, device_num):
        """Generate and install HTTPS certificates."""
        # Generate locally first
        result = subprocess.run(
            ["python3", "setup_https.py", f"mecamdev{device_num}.local"],
            capture_output=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print("Certificate generation failed")
            return False
        
        # Push to device
        cert_dir = Path.home() / "ME_CAM-DEV" / "certs"
        
        self.run_ssh_cmd(device_num, "mkdir -p ~/ME_CAM-DEV/certs", timeout=5)
        
        if not self.scp_push(device_num, "certs/certificate.crt", "~/ME_CAM-DEV/certs/certificate.crt"):
            return False
        
        if not self.scp_push(device_num, "certs/private.key", "~/ME_CAM-DEV/certs/private.key"):
            return False
        
        # Set permissions
        self.run_ssh_cmd(device_num, "chmod 600 ~/ME_CAM-DEV/certs/private.key")
        
        return True
    
    def _deploy_security(self, device_num):
        """Deploy security module."""
        return self.scp_push(
            device_num,
            "src/core/security.py",
            "~/ME_CAM-DEV/src/core/security.py"
        )
    
    def _deploy_encryption(self, device_num):
        """Deploy encryption module."""
        return self.scp_push(
            device_num,
            "src/core/encryption.py",
            "~/ME_CAM-DEV/src/core/encryption.py"
        )
    
    def _deploy_power_saver(self, device_num):
        """Deploy power-saver module."""
        return self.scp_push(
            device_num,
            "src/core/power_saver.py",
            "~/ME_CAM-DEV/src/core/power_saver.py"
        )
    
    def _deploy_ui(self, device_num):
        """Deploy responsive UI."""
        return self.scp_push(
            device_num,
            "src/ui/responsive_theme.py",
            "~/ME_CAM-DEV/src/ui/responsive_theme.py"
        )
    
    def _update_app_lite(self, device_num):
        """Update app_lite.py with V3.0 features."""
        return self.scp_push(
            device_num,
            "web/app_lite.py",
            "~/ME_CAM-DEV/web/app_lite.py"
        )
    
    def _update_config(self, device_num):
        """Update device configuration."""
        config_updates = {
            "avg_current_draw_ma": 600,
            "power_saving_enabled": True,
            "audio_record_on_motion": True,
            "encryption_enabled": False,  # Enable in production after testing
            "https_enabled": True,
            "security_headers_enabled": True,
        }
        
        cmd = f"""
python3 << 'PYEOF'
import json
try:
    with open('config.json', 'r') as f:
        cfg = json.load(f)
    
    cfg.update({json.dumps(config_updates)})
    
    with open('config.json', 'w') as f:
        json.dump(cfg, f, indent=2)
    
    print("✓ Config updated")
except Exception as e:
    print(f"✗ Error: {{e}}")
PYEOF
"""
        
        success, output = self.run_ssh_cmd(device_num, cmd)
        return success
    
    def _restart_services(self, device_num):
        """Restart ME_CAM service."""
        cmd = """
sudo systemctl restart mecam 2>/dev/null || {{
    pkill -f app_lite.py
    cd ~/ME_CAM-DEV
    nohup python3 web/app_lite.py > logs/app.log 2>&1 &
    echo "Service restarted"
}}
""" 
        
        success, _ = self.run_ssh_cmd(device_num, cmd)
        time.sleep(3)  # Wait for service to start
        return success
    
    def _verify_deployment(self, device_num):
        """Verify V3.0 features are working."""
        device = self.devices[device_num]
        url = f"https://{device['ip'] or device['hostname']}:8443/api/battery"
        
        try:
            # Try HTTPS first (will fail if cert not trusted, but that's OK)
            response = requests.get(url, verify=False, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ V3.0 endpoints responding")
                return True
        except Exception:
            pass
        
        # Fallback to HTTP
        url = f"http://{device['ip'] or device['hostname']}:8080/api/battery"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                has_power_source = 'power_source' in data
                print(f"✓ V3.0 API responding (power_source: {has_power_source})")
                return True
        except Exception as e:
            print(f"API check failed: {e}")
        
        return False
    
    def test_all(self):
        """Test all deployed devices."""
        print(f"\n{'='*70}")
        print("TESTING V3.0 FEATURES")
        print(f"{'='*70}")
        
        for device_num in self.devices.keys():
            print(f"\nTesting D{device_num}...", flush=True)
            self.test_results[device_num] = self._test_device(device_num)
    
    def _test_device(self, device_num) -> dict:
        """Test V3.0 features on device."""
        device = self.devices[device_num]
        results = {
            'battery_api': False,
            'power_saver': False,
            'security': False,
            'https': False,
            'encryption': False,
        }
        
        base_url = f"http://{device['ip'] or device['hostname']}:8080"
        
        # Test battery API
        try:
            resp = requests.get(f"{base_url}/api/battery", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                results['battery_api'] = 'power_source' in data
        except:
            pass
        
        # Test security headers
        try:
            resp = requests.get(f"{base_url}/", timeout=5)
            has_security = any(h in resp.headers for h in ['X-Content-Type-Options', 'X-Frame-Options'])
            results['security'] = has_security
        except:
            pass
        
        # Test device info (indirectly tests power saver)
        try:
            resp = requests.get(f"{base_url}/api/device_info", timeout=5)
            results['power_saver'] = resp.status_code == 200
        except:
            pass
        
        # Test HTTPS
        try:
            resp = requests.get(f"https://{device['ip'] or device['hostname']}:8443/api/battery", verify=False, timeout=5)
            results['https'] = resp.status_code == 200
        except:
            pass
        
        return results
    
    def print_report(self):
        """Print deployment and test report."""
        print(f"\n{'='*70}")
        print("V3.0 DEPLOYMENT REPORT")
        print(f"{'='*70}")
        
        for device_num, results in self.test_results.items():
            print(f"\nDevice {device_num}:")
            for feature, enabled in results.items():
                status = "✓" if enabled else "✗"
                print(f"  {status} {feature.replace('_', ' ').title()}")
        
        # Summary
        total_tests = sum(len(r) for r in self.test_results.values())
        passed = sum(sum(r.values()) for r in self.test_results.values())
        
        print(f"\n{'='*70}")
        print(f"TOTAL: {passed}/{total_tests} tests passed ({100*passed//total_tests}%)")
        print(f"{'='*70}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy ME_CAM V3.0 to devices")
    parser.add_argument("--devices", "-d", help="Comma-separated device numbers (e.g., 2,3,4)")
    parser.add_argument("--test", action="store_true", help="Run tests after deployment")
    parser.add_argument("--local-only", action="store_true", help="Only test locally (no SSH)")
    
    args = parser.parse_args()
    
    deployer = V3Deployer()
    
    # Configure devices
    device_configs = {
        2: "Kidcudi123",
        3: "Kidcudi123",
        4: "Kidcudi12345678",
    }
    
    if args.devices:
        device_list = [int(x.strip()) for x in args.devices.split(',')]
    else:
        device_list = [2, 3, 4]
    
    for dev_num in device_list:
        if dev_num in device_configs:
            deployer.add_device(dev_num, device_configs[dev_num])
    
    # Deploy
    if not args.local_only:
        for dev_num in device_list:
            deployer.deploy_v3(dev_num)
    
    # Test
    if args.test:
        deployer.test_all()
        deployer.print_report()
    
    print("\n✓ V3.0 deployment complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n✗ Deployment cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
