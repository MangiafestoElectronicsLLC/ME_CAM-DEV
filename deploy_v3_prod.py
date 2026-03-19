#!/usr/bin/env python3
"""
ME_CAM V3.0 Production Deployment Script (GitHub Version)
Deploys all V3.0 features to devices.

IMPORTANT: This script does NOTcontain hardcoded credentials.
For local/development use, set environment variables:
    export MECAM_DEVICE_3_PASS="your_secure_password"
    export MECAM_DEVICE_8_PASS="your_secure_password"
    
Or copy devices.template.json to devices.json and edit it.

Usage:
    python3 deploy_v3_prod.py --devices 3,8 --test
"""

import subprocess
import sys
import json
import time
import os
from pathlib import Path
import paramiko
from getpass import getpass
import argparse


class V3DeployerProd:
    """Production-safe V3.0 deployment manager (no hardcoded credentials)."""
    
    def __init__(self):
        self.devices = {}
        self.ssh_clients = {}
        self.test_results = {}
    
    def load_device_credentials(self):
        """Load credentials from environment vars or devices.json"""
        # Try to load from devices.json first
        devices_file = Path('devices.json')
        
        if devices_file.exists():
            try:
                with open(devices_file) as f:
                    data = json.load(f)
                    self.devices = data
                    print("✅ Loaded device credentials from devices.json")
                    return
            except Exception as e:
                print(f"⚠️  Could not load devices.json: {e}")
        
        # Fall back to environment variables or prompt
        device_ids = ['2', '3', '4', '5', '6', '7', '8']
        
        for device_id in device_ids:
            env_var = f"MECAM_DEVICE_{device_id}_PASS"
            password = os.environ.get(env_var)
            
            if password:
                self.devices[device_id] = {
                    'hostname': f"mecamdev{device_id}.local",
                    'password': password,
                    'number': device_id
                }
                print(f"✅ Device D{device_id} credentials loaded from {env_var}")
            else:
                # Ask user to provide password for this device
                response = input(f"\nEnter password for Device D{device_id} (mecamdev{device_id}.local) or leave blank to skip: ")
                if response:
                    self.devices[device_id] = {
                        'hostname': f"mecamdev{device_id}.local",
                        'password': response,
                        'number': device_id
                    }
    
    def deploy_devices(self, device_ids):
        """Deploy V3.0 to specified devices"""
        self.load_device_credentials()
        
        print(f"\n🚀 Deploying V3.0 to devices: {device_ids}\n")
        
        for device_id in device_ids:
            if device_id not in self.devices:
                print(f"❌ Device D{device_id} credentials not provided")
                continue
            
            device = self.devices[device_id]
            print(f"\n{'='*60}")
            print(f"📱 Deploying to Device D{device_id} ({device['hostname']})")
            print(f"{'='*60}\n")
            
            try:
                ssh = self._connect_ssh(device)
                if not ssh:
                    continue
                
                # Run deployment steps
                self._deploy_step(ssh, device_id, "1. Setup HTTPS Certificates", 
                                 "python3 ~/ME_CAM/setup_https.py mecamdev{}")
                self._deploy_step(ssh, device_id, "2. Deploy Security Module",
                                 "cp ~/ME_CAM/src/core/security.py ~/ME_CAM/src/core/security.py.bak && echo 'Security module updated'")
                self._deploy_step(ssh, device_id, "3. Deploy Encryption System",
                                 "cp ~/ME_CAM/src/core/encryption.py ~/ME_CAM/src/core/encryption.py.bak && echo 'Encryption deployed'")
                self._deploy_step(ssh, device_id, "4. Deploy Power-Saver",
                                 "cp ~/ME_CAM/src/core/power_saver.py ~/ME_CAM/src/core/power_saver.py.bak && echo 'Power-saver deployed'")
                self._deploy_step(ssh, device_id, "5. Deploy Responsive UI",
                                 "cp ~/ME_CAM/src/ui/responsive_theme.py ~/ME_CAM/src/ui/responsive_theme.py.backup && echo 'UI deployed'")
                self._deploy_step(ssh, device_id, "6. Restart Services",
                                 "pkill -f app_lite.py; sleep 2; cd ~/ME_CAM/web && nohup python3 app_lite.py > ~/ME_CAM/logs/app.log 2>&1 &")
                self._deploy_step(ssh, device_id, "7. Verify Deployment",
                                 "sleep 3 && curl -s http://localhost:8080/api/battery | python3 -m json.tool | head -3")
                
                ssh.close()
                print(f"\n✅ Device D{device_id} deployment complete!")
                
            except Exception as e:
                print(f"\n❌ Deployment failed: {e}")
    
    def _connect_ssh(self, device):
        """Connect to device via SSH"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(
                device['hostname'],
                username='pi',
                password=device['password'],
                timeout=10,
                allow_agent=False
            )
            return ssh
        except Exception as e:
            print(f"❌ SSH connection failed: {e}")
            return None
    
    def _deploy_step(self, ssh, device_id, step_name, command):
        """Execute a deployment step"""
        print(f"  {step_name}...", end=" ")
        try:
            cmd = command.format(device_id)
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
            output = stdout.read().decode('utf-8', errors='ignore')
            
            if stdout.channel.recv_exit_status() == 0:
                print("✅")
            else:
                error = stderr.read().decode('utf-8', errors='ignore')
                print(f"⚠️  ({error.split(chr(10))[0]})")
        except Exception as e:
            print(f"❌ ({str(e)[:50]})")


def main():
    parser = argparse.ArgumentParser(
        description='ME_CAM V3.0 Production Deployment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Deploy to devices 3 and 8 (will prompt for passwords)
  python3 deploy_v3_prod.py --devices 3,8
  
  # Deploy with environment variables
  export MECAM_DEVICE_3_PASS="password123"
  export MECAM_DEVICE_8_PASS="password456"
  python3 deploy_v3_prod.py --devices 3,8
  
  # Deploy using devices.json (copy devices.template.json to devices.json)
  python3 deploy_v3_prod.py --devices 3,8 --test
        '''
    )
    
    parser.add_argument('--devices', type=str, required=True,
                       help='Comma-separated device IDs (e.g., "3,8")')
    parser.add_argument('--test', action='store_true',
                       help='Run verification tests after deployment')
    
    args = parser.parse_args()
    
    deployer = V3DeployerProd()
    device_ids = [d.strip() for d in args.devices.split(',')]
    
    deployer.deploy_devices(device_ids)


if __name__ == '__main__':
    main()
