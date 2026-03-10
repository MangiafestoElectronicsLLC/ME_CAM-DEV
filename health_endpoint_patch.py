
@app.route("/api/health")
def api_health():
    """Simple health check endpoint for watchdog"""
    try:
        import socket
        import subprocess
        import time
        hostname = socket.gethostname()
        camera_ok = False
        service_name = "unknown"
        
        # Check if camera is available
        try:
            _ = camera
            camera_ok = True
        except:
            pass
            
        # Detect which service is running
        try:
            result = subprocess.run(['systemctl', 'is-active', 'mecamera-lite'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                service_name = 'mecamera-lite'
            else:
                result = subprocess.run(['systemctl', 'is-active', 'mecamera'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    service_name = 'mecamera'
        except:
            pass
        
        # Check WiFi connection
        wifi_connected = False
        try:
            result = subprocess.run(['iwconfig', 'wlan0'], 
                                  capture_output=True, text=True, timeout=2)
            if 'ESSID:off' not in result.stdout and 'ESSID:"' in result.stdout:
                wifi_connected = True
        except:
            pass
        
        return {
            "ok": True,
            "camera_available": camera_ok,
            "service": service_name,
            "hostname": hostname,
            "wifi_connected": wifi_connected,
            "timestamp": time.time()
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500
