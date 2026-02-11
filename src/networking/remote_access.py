"""
Tailscale VPN Integration for ME_CAM
=====================================
Provides zero-configuration remote access without port forwarding.

How it works:
1. Install Tailscale on Pi: curl -fsSL https://tailscale.com/install.sh | sh
2. Enable for ME_CAM: tailscale up
3. Users connect to Pi's Tailscale IP (e.g., 100.64.1.50) from anywhere
4. Dashboard shows persistent URL + QR code for quick access

Advantages over WebRTC:
- Works for ALL traffic (not just video)
- SSH access, file transfer, etc.
- No STUN/TURN server dependency
- Encrypted end-to-end

Can be used alongside WebRTC for redundancy.
"""

import subprocess
import json
import os
import asyncio
from loguru import logger
from typing import Optional, Dict
from pathlib import Path


class TailscaleHelper:
    """
    Manage Tailscale VPN integration for ME_CAM.
    
    Usage:
        ts = TailscaleHelper()
        
        if not ts.is_installed():
            ts.install()  # One-time setup
        
        if ts.is_enabled():
            ip = ts.get_tailscale_ip()
            print(f"Access camera at: http://{ip}:8080")
    """
    
    def __init__(self):
        self.logger = logger.bind(name="Tailscale")
        self.tailscale_path = "/usr/bin/tailscale"
        self.tailscaled_path = "/usr/sbin/tailscaled"
    
    def is_installed(self) -> bool:
        """Check if Tailscale is installed on system."""
        return os.path.exists(self.tailscale_path) and os.path.exists(self.tailscaled_path)
    
    async def install(self) -> bool:
        """
        Install Tailscale on Raspberry Pi.
        
        Returns:
            True if installation successful
        """
        self.logger.info("[INSTALL] Starting Tailscale installation...")
        
        try:
            # Download and run installer
            cmd = "curl -fsSL https://tailscale.com/install.sh | sudo sh"
            result = await self._run_command(cmd)
            
            if result.returncode == 0:
                self.logger.success("[INSTALL] Tailscale installed successfully")
                return True
            else:
                self.logger.error(f"[INSTALL] Failed: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"[INSTALL] Error: {e}")
            return False
    
    async def enable(self, accept_routes: bool = True, 
                     advertise_exit_node: bool = False) -> bool:
        """
        Enable Tailscale and authorize device.
        
        Args:
            accept_routes: Accept subnet routes from other devices
            advertise_exit_node: Advertise this device as exit node (for gateway)
        
        Returns:
            True if enabled successfully
        """
        if not self.is_installed():
            self.logger.error("[ENABLE] Tailscale not installed")
            return False
        
        self.logger.info("[ENABLE] Starting Tailscale daemon...")
        
        cmd = "sudo systemctl start tailscaled"
        await self._run_command(cmd)
        
        # Build tailscale up command
        up_cmd = "sudo tailscale up"
        if accept_routes:
            up_cmd += " --accept-routes"
        if advertise_exit_node:
            up_cmd += " --advertise-exit-node"
        
        self.logger.info(f"[ENABLE] Executing: {up_cmd}")
        self.logger.warning("[ENABLE] Visit the URL below to authorize this device:")
        
        result = await self._run_command(up_cmd)
        
        if result.returncode == 0:
            self.logger.success("[ENABLE] Tailscale enabled")
            return True
        
        return False
    
    def is_enabled(self) -> bool:
        """Check if Tailscale daemon is running."""
        try:
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "tailscaled"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.debug(f"[STATUS] Check failed: {e}")
            return False
    
    def get_tailscale_ip(self) -> Optional[str]:
        """
        Get Tailscale IP address (e.g., 100.64.1.50).
        
        Returns:
            Tailscale IP string, or None if not connected
        """
        try:
            result = subprocess.run(
                ["sudo", "tailscale", "ip", "-4"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                ip = result.stdout.strip()
                self.logger.debug(f"[IP] Tailscale IP: {ip}")
                return ip
            
            return None
        
        except Exception as e:
            self.logger.warning(f"[IP] Failed to get IP: {e}")
            return None
    
    def get_device_name(self) -> Optional[str]:
        """
        Get Tailscale device name (short hostname).
        
        Returns:
            Device name from Tailscale, or None if offline
        """
        try:
            result = subprocess.run(
                ["sudo", "tailscale", "status", "--json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                status = json.loads(result.stdout)
                if "Self" in status and "HostName" in status["Self"]:
                    return status["Self"]["HostName"]
            
            return None
        
        except Exception as e:
            self.logger.warning(f"[DEVICE] Failed to get name: {e}")
            return None
    
    def get_status(self) -> Dict:
        """
        Get full Tailscale status.
        
        Returns:
            {'online': bool, 'ip': str, 'device': str, 'peers': int}
        """
        try:
            result = subprocess.run(
                ["sudo", "tailscale", "status", "--json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                status = json.loads(result.stdout)
                
                return {
                    'online': status.get("BackendState") == "Running",
                    'ip': self.get_tailscale_ip(),
                    'device': status.get("Self", {}).get("HostName", "unknown"),
                    'peers': len([p for p in status.get("Peer", {}).values() if p.get("Online")])
                }
            
            return {'online': False, 'ip': None, 'device': None, 'peers': 0}
        
        except Exception as e:
            self.logger.error(f"[STATUS] Error: {e}")
            return {'online': False, 'ip': None, 'device': None, 'peers': 0}
    
    async def disable(self) -> bool:
        """Disable Tailscale."""
        try:
            await self._run_command("sudo systemctl stop tailscaled")
            self.logger.info("[DISABLE] Tailscale disabled")
            return True
        except Exception as e:
            self.logger.error(f"[DISABLE] Error: {e}")
            return False
    
    @staticmethod
    async def _run_command(cmd: str) -> subprocess.CompletedProcess:
        """Run shell command asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: subprocess.run(cmd, shell=True, capture_output=True, text=True)
        )


class CloudflareHelper:
    """
    Cloudflare Tunnel integration (alternative to Tailscale).
    
    Advantages:
    - No VPN needed
    - Public HTTPS URL (e.g., mycamera-abc123.me-cam.com)
    - Works with any domain registrar
    
    Disadvantages:
    - Requires Cloudflare account
    - Slightly higher latency
    - Cloudflare sees traffic (not end-to-end encrypted)
    
    Usage:
        cf = CloudflareHelper()
        cf.install()
        cf.create_tunnel(domain="mycamera.me-cam.com")
    """
    
    def __init__(self):
        self.logger = logger.bind(name="Cloudflare")
        self.cloudflared_path = "/usr/local/bin/cloudflared"
    
    def is_installed(self) -> bool:
        """Check if cloudflared is installed."""
        return os.path.exists(self.cloudflared_path)
    
    async def install(self) -> bool:
        """
        Install cloudflared tunnel client.
        
        Returns:
            True if successful
        """
        self.logger.info("[INSTALL] Installing Cloudflare Tunnel...")
        
        try:
            cmd = (
                "curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/"
                "cloudflared-linux-arm -o /tmp/cloudflared && "
                "chmod +x /tmp/cloudflared && "
                "sudo mv /tmp/cloudflared /usr/local/bin/"
            )
            
            result = await self._run_command(cmd)
            
            if result.returncode == 0:
                self.logger.success("[INSTALL] Cloudflare Tunnel installed")
                return True
            else:
                self.logger.error(f"[INSTALL] Failed: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"[INSTALL] Error: {e}")
            return False
    
    async def create_tunnel(self, name: str, 
                           domain: str = None) -> bool:
        """
        Create Cloudflare tunnel for ME_CAM.
        
        Args:
            name: Tunnel name (e.g., "me-cam-device-1")
            domain: Domain to route to this tunnel (e.g., "camera.me-cam.com")
        
        Returns:
            True if created successfully
        """
        self.logger.info(f"[TUNNEL] Creating tunnel '{name}'...")
        
        try:
            # Step 1: Login (opens browser)
            login_cmd = "sudo cloudflared tunnel login"
            await self._run_command(login_cmd)
            self.logger.info("[TUNNEL] Check browser to authorize Cloudflare account")
            
            # Step 2: Create tunnel
            create_cmd = f"sudo cloudflared tunnel create {name}"
            result = await self._run_command(create_cmd)
            
            if result.returncode != 0:
                self.logger.error(f"[TUNNEL] Creation failed: {result.stderr}")
                return False
            
            self.logger.success(f"[TUNNEL] Tunnel '{name}' created")
            
            # Step 3: Create config
            if domain:
                config_dir = Path.home() / ".cloudflared"
                config_dir.mkdir(exist_ok=True)
                
                config_path = config_dir / "config.yml"
                config_content = f"""tunnel: {name}
credentials-file: {config_dir}/{name}.json

ingress:
  - hostname: {domain}
    service: http://localhost:8080
  - service: http_status:404
"""
                
                with open(config_path, 'w') as f:
                    f.write(config_content)
                
                self.logger.success(f"[TUNNEL] Config created at {config_path}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"[TUNNEL] Error: {e}")
            return False
    
    async def start_tunnel(self, name: str) -> bool:
        """Start Cloudflare tunnel."""
        cmd = f"sudo cloudflared tunnel run {name}"
        
        self.logger.info(f"[START] Starting tunnel '{name}'...")
        result = await self._run_command(cmd)
        
        if result.returncode == 0:
            self.logger.success("[START] Tunnel running")
            return True
        
        return False
    
    @staticmethod
    async def _run_command(cmd: str) -> subprocess.CompletedProcess:
        """Run shell command asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: subprocess.run(cmd, shell=True, capture_output=True, text=True)
        )


# ===== Flask Integration =====

def create_remote_access_blueprintdata() -> Dict:
    """
    Create Flask blueprint for remote access configuration.
    
    Example usage in app_lite.py:
    
        from src.networking.remote_access import create_remote_access_blueprint
        
        remote_bp = create_remote_access_blueprint()
        app.register_blueprint(remote_bp, url_prefix='/api/remote')
    """
    from flask import Blueprint, jsonify, request
    
    bp = Blueprint('remote_access', __name__)
    
    ts = TailscaleHelper()
    cf = CloudflareHelper()
    
    @bp.route('/tailscale/status', methods=['GET'])
    def tailscale_status():
        """Get Tailscale connection status."""
        status = ts.get_status()
        return jsonify(status)
    
    @bp.route('/tailscale/ip', methods=['GET'])
    def tailscale_ip():
        """Get Tailscale IP address."""
        ip = ts.get_tailscale_ip()
        if ip:
            return jsonify({'ip': ip, 'url': f'http://{ip}:8080'})
        return jsonify({'error': 'Not connected'}), 404
    
    @bp.route('/cloudflare/status', methods=['GET'])
    def cloudflare_status():
        """Get Cloudflare tunnel status."""
        return jsonify({'installed': cf.is_installed()})
    
    @bp.route('/options', methods=['GET'])
    def remote_options():
        """Get available remote access options."""
        return jsonify({
            'webrtc': {'available': True, 'latency': '200-400ms'},
            'tailscale': {'available': ts.is_enabled(), 'ip': ts.get_tailscale_ip()},
            'cloudflare': {'available': cf.is_installed()}
        })
    
    return bp


if __name__ == "__main__":
    print("[!] Remote access module loaded")
    print("[!] Tailscale: TailscaleHelper()")
    print("[!] Cloudflare: CloudflareHelper()")
