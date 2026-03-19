#!/usr/bin/env python3
"""
ME_CAM Camera Diagnostics - Comprehensive camera health check

Run this on any device to diagnose camera detection and functionality issues.
Usage: python3 camera_diagnostics.py
"""

import subprocess
import sys
import json
import os
from pathlib import Path

class Diagnostics:
    def __init__(self):
        self.results = {
            'device_info': {},
            'camera_detection': {},
            'libcamera': {},
            'rpicam_tools': {},
            'python_modules': {},
            'recommended_fixes': []
        }
        self.passed = 0
        self.failed = 0
    
    def run_command(self, cmd, shell=False):
        """Run shell command and return output."""
        try:
            if isinstance(cmd, str):
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "TIMEOUT"
        except Exception as e:
            return -1, "", str(e)
    
    def check(self, name, condition, details=""):
        """Record a check result."""
        if condition:
            self.passed += 1
            status = "✓ PASS"
        else:
            self.failed += 1
            status = "✗ FAIL"
        print(f"  {status}: {name}")
        if details:
            print(f"         {details}")
        return condition
    
    def run_diagnostics(self):
        """Run all diagnostics."""
        print("\n" + "="*70)
        print("ME_CAM CAMERA DIAGNOSTICS v1.0")
        print("="*70 + "\n")
        
        # Device info
        print("📊 DEVICE INFORMATION")
        print("-" * 70)
        self.check_device_info()
        
        # Camera detection
        print("\n📷 CAMERA DETECTION")
        print("-" * 70)
        self.check_camera_detection()
        
        # Libcamera
        print("\n📹 LIBCAMERA SYSTEM")
        print("-" * 70)
        self.check_libcamera()
        
        # RpiCAM tools
        print("\n🎬 RPICAM TOOLS")
        print("-" * 70)
        self.check_rpicam_tools()
        
        # Python modules
        print("\n🐍 PYTHON MODULES")
        print("-" * 70)
        self.check_python_modules()
        
        # Device config
        print("\n⚙️ DEVICE CONFIGURATION")
        print("-" * 70)
        self.check_device_config()
        
        # Summary
        self.print_summary()
    
    def check_device_info(self):
        """Check device information."""
        # Model
        code, out, err = self.run_command("cat /proc/device-tree/model", shell=True)
        model = out if code == 0 else "Unknown"
        print(f"  Device: {model}")
        self.results['device_info']['model'] = model
        
        # RAM
        code, out, err = self.run_command("grep MemTotal /proc/meminfo | awk '{print $2 / 1024 \" MB\"}'", shell=True)
        ram = out if code == 0 else "Unknown"
        print(f"  RAM: {ram}")
        
        # OS
        code, out, err = self.run_command("cat /etc/os-release | grep PRETTY_NAME | cut -d'\"' -f2", shell=True)
        os_info = out if code == 0 else "Unknown"
        print(f"  OS: {os_info}")
    
    def check_camera_detection(self):
        """Check if cameras are detected by system."""
        # vcgencmd check
        code, out, err = self.run_command("vcgencmd get_camera")
        vcgencmd_ok = self.check("vcgencmd tool available", code == 0, out if code == 0 else err)
        self.results['camera_detection']['vcgencmd'] = out if code == 0 else f"ERROR: {err}"
        
        # Parse vcgencmd output
        if vcgencmd_ok and out:
            self.check("Camera detected (supported=1)", "supported=1" in out, f"Output: {out}")
            self.check("Camera detected (detected=1)", "detected=1" in out, f"Output: {out}")
        
        # Check /dev/video* devices
        code, out, err = self.run_command("ls -la /dev/video* 2>/dev/null || echo 'None found'", shell=True)
        video_devices = out if code == 0 else "None"
        has_video = len(video_devices.strip().split('\n')) > 1
        self.check("Video device nodes (/dev/video*)", has_video, f"Found: {video_devices}")
        self.results['camera_detection']['video_devices'] = video_devices
    
    def check_libcamera(self):
        """Check libcamera system."""
        # Check if libcamera-hello available
        code, out, err = self.run_command("which libcamera-hello")
        libcam_available = self.check(
            "libcamera-hello tool installed",
            code == 0,
            out if code == 0 else "Not in PATH"
        )
        
        # Try to list cameras with rpicam-hello
        print("\n  Running rpicam-hello --list-cameras (this may take 10-15 seconds)...")
        code, out, err = self.run_command(["rpicam-hello", "--list-cameras"], shell=False)
        
        cameras_detected = "Available cameras" in out or "libcamera" in out.lower()
        self.check(
            "rpicam-hello can detect cameras",
            cameras_detected,
            f"Output: {out[:200] if out else err[:200]}"
        )
        self.results['libcamera']['rpicam_output'] = out if code == 0 else err
        
        if not cameras_detected:
            print("\n  ⚠️  NO CAMERAS DETECTED! Possible causes:")
            print("     1. Camera ribbon cable not fully seated (MOST LIKELY)")
            print("     2. Camera module power issue")
            print("     3. Wrong camera model (check config)")
            print("     4. Defective camera or ribbon")
    
    def check_rpicam_tools(self):
        """Check rpicam capture tools."""
        tools = ["rpicam-jpeg", "rpicam-raw", "rpicam-still"]
        
        for tool in tools:
            code, out, err = self.run_command(f"which {tool}", shell=True)
            self.check(
                f"{tool} available",
                code == 0,
                out if code == 0 else "Not in PATH"
            )
            self.results['rpicam_tools'][tool] = "Available" if code == 0 else "Missing"
    
    def check_python_modules(self):
        """Check Python dependencies."""
        modules = {
            'cv2': 'opencv-python (for motion detection)',
            'picamera2': 'picamera2 (camera interface)',
            'numpy': 'numpy (image processing)',
            'flask': 'flask (web server)',
            'PIL': 'pillow (image format)',
        }
        
        for module, description in modules.items():
            try:
                __import__(module)
                self.check(f"{module}", True, description)
                self.results['python_modules'][module] = "Installed"
            except ImportError:
                self.check(f"{module}", False, description)
                self.results['python_modules'][module] = "Missing"
                self.results['recommended_fixes'].append(f"Install: pip3 install {description.split('(')[0].strip()}")
    
    def check_device_config(self):
        """Check device configuration."""
        config_path = Path.home() / "ME_CAM-DEV" / "config.json"
        
        if config_path.exists():
            self.check("config.json exists", True, str(config_path))
            try:
                with open(config_path, 'r') as f:
                    cfg = json.load(f)
                
                # Check camera settings
                camera_cfg = cfg.get('camera', {})
                print(f"  Camera settings:")
                print(f"    - Resolution: {camera_cfg.get('resolution', 'Not set')}")
                print(f"    - FPS: {camera_cfg.get('stream_fps', 'Not set')}")
                print(f"    - Quality: {camera_cfg.get('stream_quality', 'Not set')}%")
                print(f"    - Camera type: {camera_cfg.get('camera_type', 'Not set')}")
                
                # Check motion settings
                motion_enabled = cfg.get('motion_record_enabled', False)
                self.check("Motion recording enabled", motion_enabled)
                
                # Check audio settings
                audio_enabled = cfg.get('audio_record_on_motion', True)
                self.check("Audio recording on motion enabled", audio_enabled)
            except json.JSONDecodeError as e:
                self.check("config.json is valid JSON", False, str(e))
        else:
            self.check("config.json exists", False, f"Not found at {config_path}")
    
    def print_summary(self):
        """Print diagnostic summary."""
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0
        
        print("\n" + "="*70)
        print(f"SUMMARY: {self.passed}/{total} checks passed ({percentage:.0f}%)")
        print("="*70)
        
        if self.failed == 0:
            print("\n✓ All diagnostics passed! Camera should be working.")
        else:
            print(f"\n✗ {self.failed} issues found. See recommendations below.\n")
            
            # Recommendations
            if self.results['recommended_fixes']:
                print("RECOMMENDED FIXES:")
                print("-" * 70)
                for fix in self.results['recommended_fixes']:
                    print(f"  • {fix}")
            
            # Common issues
            print("\nCOMMON ISSUES & FIXES:")
            print("-" * 70)
            
            if "available=0" in self.results['camera_detection'].get('vcgencmd', '') or \
               "detected=0" in self.results['camera_detection'].get('vcgencmd', ''):
                print("\n  🔧 CAMERA NOT DETECTED:")
                print("     1. Power off device: sudo shutdown -h now")
                print("     2. Wait 30 seconds")
                print("     3. Reseat CSI ribbon cable:")
                print("        - Locate CSI connector on Pi (between USB and audio jack)")
                print("        - Pull ribbon cable straight out gently")
                print("        - Ensure blue side faces DOWN on Pi")
                print("        - Push ribbon in firmly until you hear/feel a click")
                print("     4. Power on and wait 2 minutes")
                print("     5. Run this diagnostic again")
            
            if "rpicam-hello" in self.results['rpicam_tools'] and \
               self.results['rpicam_tools']['rpicam-hello'] == "Missing":
                print("\n  🔧 RPICAM TOOLS MISSING:")
                print("     sudo apt update && sudo apt install -y libraspberrypi-bin")
            
            if self.results['python_modules'].get('cv2') == "Missing":
                print("\n  🔧 OPENCV MISSING:")
                print("     pip3 install opencv-contrib-python")
        
        # Save results
        results_file = Path.home() / "ME_CAM-DEV" / "diagnostics_results.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📝 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")


if __name__ == '__main__':
    diag = Diagnostics()
    try:
        diag.run_diagnostics()
    except KeyboardInterrupt:
        print("\n\nDiagnostics interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        sys.exit(1)
