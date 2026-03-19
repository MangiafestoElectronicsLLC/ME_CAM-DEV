#!/usr/bin/env python3
"""
ME_CAM V3.0 SSH Test & Interactive Device Management

Test V3.0 features directly on devices via SSH.
Interactive shell for running commands and diagnostics.

Usage: python3 test_devices_ssh.py --device D2
"""

import paramiko
import sys
import time
from pathlib import Path
import json


class DeviceSSH:
    """SSH connection to ME_CAM device."""
    
    def __init__(self, device_num, password, hostname=None):
        self.device_num = device_num
        self.device_name = f"D{device_num}"
        self.hostname = hostname or f"mecamdev{device_num}.local"
        self.password = password
        self.client = None
        self.connected = False
    
    def connect(self):
        """Connect to device via SSH."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.client.connect(
                hostname=self.hostname,
                username='pi',
                password=self.password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            self.connected = True
            print(f"✓ {self.device_name} connected ({self.hostname})")
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def run_cmd(self, cmd, timeout=10):
        """Execute command and return output."""
        if not self.connected:
            print(f"✗ Not connected")
            return None
        
        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            return {
                'success': not error,
                'output': output,
                'error': error
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    def check_battery(self):
        """Check battery status via API."""
        result = self.run_cmd("curl -s http://localhost:8080/api/battery | python3 -m json.tool")
        
        if result['success'] and result['output']:
            try:
                data = json.loads(result['output'])
                print(f"\n🔋 BATTERY STATUS:")
                print(f"  Percent: {data.get('percent')}%")
                print(f"  Power Source: {data.get('power_source', 'unknown')}")
                print(f"  Runtime: {data.get('runtime_hours')}h {data.get('runtime_minutes')}m")
                print(f"  Display: {data.get('display_text')}")
                return data
            except json.JSONDecodeError:
                print(f"Could not parse JSON: {result['output'][:100]}")
        else:
            print(f"API error: {result['error']}")
        
        return None
    
    def check_device_info(self):
        """Check device information."""
        result = self.run_cmd("curl -s http://localhost:8080/api/device_info | python3 -m json.tool")
        
        if result['success'] and result['output']:
            try:
                data = json.loads(result['output'])
                print(f"\n📱 DEVICE INFO:")
                print(f"  Model: {data.get('model')}")
                print(f"  RAM: {data.get('ram_mb')}MB")
                print(f"  Storage: {data.get('storage_used')}GB / {data.get('storage_total')}GB")
                print(f"  WiFi: {data.get('wifi_signal')} dBm")
                print(f"  Version: {data.get('version')}")
                return data
            except json.JSONDecodeError:
                print(f"Could not parse JSON")
        else:
            print(f"API error: {result['error']}")
        
        return None
    
    def check_services(self):
        """Check if services are running."""
        print(f"\n⚙️ SERVICES:")
        
        # Check Flask app
        result = self.run_cmd("pgrep -f 'app_lite.py'")
        if result['output']:
            print(f"  ✓ Flask app running (PID: {result['output']})")
        else:
            print(f"  ✗ Flask app not running")
        
        # Check system service
        result = self.run_cmd("sudo systemctl is-active mecam")
        if result['success']:
            print(f"  ✓ systemd service: {result['output']}")
        else:
            print(f"  ? systemd service status unknown")
        
        # Check if listening
        result = self.run_cmd("ss -tln | grep 8080")
        if result['output']:
            print(f"  ✓ Listening on port 8080")
        else:
            print(f"  ✗ Not listening on port 8080")
    
    def check_camera(self):
        """Check camera status."""
        print(f"\n📷 CAMERA:")
        
        # Check OS detection
        result = self.run_cmd("rpicam-hello --list-cameras")
        if "Available" in result['output']:
            print(f"  ✓ Camera detected by OS")
        else:
            print(f"  ✗ Camera NOT detected by OS")
            print(f"    Output: {result['output'][:100]}")
        
        # Check logs for errors
        result = self.run_cmd("tail -5 ~/ME_CAM-DEV/logs/app.log | grep -i camera")
        if result['output']:
            print(f"  Recent logs: {result['output'][:100]}")
    
    def check_security(self):
        """Check V3.0 security features."""
        print(f"\n🔒 SECURITY:")
        
        # Check HTTPS certificates
        result = self.run_cmd("ls -la ~/ME_CAM-DEV/certs/")
        if "certificate.crt" in result['output']:
            print(f"  ✓ HTTPS certificate present")
        else:
            print(f"  ✗ HTTPS certificate missing")
        
        # Check encryption module
        result = self.run_cmd("ls ~/ME_CAM-DEV/src/core/encryption.py")
        if result['success']:
            print(f"  ✓ Encryption module installed")
        else:
            print(f"  ✗ Encryption module missing")
        
        # Check security module
        result = self.run_cmd("ls ~/ME_CAM-DEV/src/core/security.py")
        if result['success']:
            print(f"  ✓ Security module installed")
        else:
            print(f"  ✗ Security module missing")
    
    def check_power_saver(self):
        """Check power-saver integration."""
        print(f"\n⚡ POWER SAVER:")
        
        result = self.run_cmd("ls ~/ME_CAM-DEV/src/core/power_saver.py")
        if result['success']:
            print(f"  ✓ Power-saver module installed")
        else:
            print(f"  ✗ Power-saver module missing")
        
        # Check config
        result = self.run_cmd("grep power_saving ~/ME_CAM-DEV/config.json")
        if result['output']:
            print(f"  ✓ Power-saver configured: {result['output']}")
    
    def view_logs(self, lines=20):
        """View recent app logs."""
        print(f"\n📋 RECENT LOGS ({lines} lines):")
        print("-" * 70)
        
        result = self.run_cmd(f"tail -{lines} ~/ME_CAM-DEV/logs/app.log")
        if result['output']:
            for line in result['output'].split('\n')[-lines:]:
                print(line)
        else:
            print("No logs available")
    
    def restart_app(self):
        """Restart the application."""
        print(f"\nRestarting {self.device_name}...", end=" ", flush=True)
        
        result = self.run_cmd("""
pkill filter -f app_lite.py
sleep 2
cd ~/ME_CAM-DEV
nohup python3 web/app_lite.py > logs/app.log 2>&1 &
echo "restarted"
""", timeout=15)
        
        if "restarted" in result['output']:
            print("✓")
            time.sleep(3)  # Wait for startup
            return True
        else:
            print("✗")
            return False
    
    def run_interactive(self):
        """Start interactive shell."""
        print(f"\nEntering interactive shell for {self.device_name}...")
        print(f"Type 'quit' or 'exit' to return")
        print(f"Type 'help' for available commands")
        print("-" * 70)
        
        commands = {
            'battery': self.check_battery,
            'info': self.check_device_info,
            'services': self.check_services,
            'camera': self.check_camera,
            'security': self.check_security,
            'power': self.check_power_saver,
            'logs': lambda: self.view_logs(30),
            'restart': self.restart_app,
            'help': self._show_help,
        }
        
        while True:
            try:
                cmd = input(f"\n{self.device_name}> ").strip().lower()
                
                if cmd in ['quit', 'exit']:
                    break
                elif cmd in commands:
                    commands[cmd]()
                elif cmd.startswith('raw '):
                    # Run raw command
                    raw_cmd = cmd[4:]
                    result = self.run_cmd(raw_cmd)
                    if result['output']:
                        print(result['output'])
                    if result['error']:
                        print(f"Error: {result['error']}")
                elif cmd:
                    print(f"Unknown command: {cmd}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    @staticmethod
    def _show_help():
        """Show available commands."""
        print("""
Available commands:
  battery         - Check battery status and power source
  info            - Device info (model, RAM, storage)
  services        - Check if services are running
  camera          - Check camera detection status
  security        - Check V3.0 security features
  power           - Check power-saver system
  logs [N]        - View last N lines of logs (default 20)
  restart         - Restart the application
  raw <cmd>       - Run raw shell command
  help            - Show this help
  quit            - Exit interactive shell
        """)
    
    def close(self):
        """Close SSH connection."""
        if self.client:
            self.client.close()
            self.connected = False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ME_CAM devices via SSH")
    parser.add_argument("--device", "-d", help="Device number (e.g., 2, 3, 4)")
    parser.add_argument("--quick", action="store_true", help="Run quick diagnostics")
    parser.add_argument("--logs", type=int, default=20, help="Lines of logs to show")
    
    args = parser.parse_args()
    
    # Device configs
    device_configs = {
        2: "Kidcudi123",
        3: "Kidcudi123", 
        4: "Kidcudi12345678",
    }
    
    if not args.device:
        print("Available devices: 2, 3, 4")
        print("Usage: python3 test_devices_ssh.py --device 2")
        return
    
    device_num = int(args.device.replace('D', ''))
    
    if device_num not in device_configs:
        print(f"Unknown device D{device_num}")
        return
    
    # Connect
    device = DeviceSSH(device_num, device_configs[device_num])
    if not device.connect():
        return
    
    # Run tests
    try:
        if args.quick:
            print(f"\n{'='*70}")
            print(f"QUICK DIAGNOSTICS - {device.device_name}")
            print(f"{'='*70}")
            
            device.check_battery()
            device.check_device_info()
            device.check_services()
            device.check_camera()
            device.check_security()
            device.check_power_saver()
            device.view_logs(args.logs)
            
            print(f"\n{'='*70}")
            print("✓ Diagnostics complete")
            
        else:
            # Interactive mode
            device.run_interactive()
        
    finally:
        device.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
