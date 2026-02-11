#!/usr/bin/env python3
"""
Simple v3.0 Integration - Adds WebRTC and remote access API endpoints
This creates a minimal integration without modifying existing code
"""

# Copy this code and append it to the end of web/app_lite.py
# (before the final "return app" line)

V3_INTEGRATION_CODE = '''
    # ============= V3.0 FEATURES =============
    
    @app.route("/api/v3/status", methods=["GET"])
    def api_v3_status():
        """Check v3.0 feature availability"""
        status = {
            "version": "3.0",
            "webrtc": False,
            "ai_detection": False,
            "remote_access": False
        }
        
        # Check WebRTC
        try:
            from src.streaming.webrtc_peer import WebRTCStreamer
            status["webrtc"] = True
        except:
            pass
        
        # Check AI detection
        try:
            from src.detection.tflite_detector import SmartMotionDetector
            status["ai_detection"] = True
        except:
            pass
        
        # Check remote access
        try:
            from src.networking.remote_access import TailscaleHelper
            status["remote_access"] = True
        except:
            pass
        
        return jsonify(status)
    
    @app.route("/api/remote/access-info", methods=["GET"])
    def api_remote_access_info():
        """Get information for remote access"""
        import socket
        
        info = {
            "local_ip": None,
            "tailscale_ip": None,
            "hostname": socket.gethostname(),
            "vpn_ready": True,
            "ports": {
                "http": 8080,
                "https": 8443
            }
        }
        
        # Get local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info["local_ip"] = s.getsockname()[0]
            s.close()
        except:
            pass
        
        # Try to get Tailscale IP
        try:
            from src.networking.remote_access import TailscaleHelper
            helper = TailscaleHelper()
            if helper.is_installed():
                ts_ip = helper.get_tailscale_ip()
                if ts_ip:
                    info["tailscale_ip"] = ts_ip
        except:
            pass
        
        return jsonify(info)
    
    @app.route("/api/test/vpn", methods=["GET"])
    def api_test_vpn():
        """Test endpoint to verify VPN/remote access"""
        import socket
        
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        return jsonify({
            "success": True,
            "message": "VPN access working",
            "client_ip": client_ip,
            "server_time": datetime.now().isoformat(),
            "authenticated": 'user' in session
        })
'''

if __name__ == "__main__":
    print("="*60)
    print("v3.0 Simple Integration Code")
    print("="*60)
    print("\nCopy the code below and add it to web/app_lite.py")
    print("(before the final 'return app' line)\n")
    print(V3_INTEGRATION_CODE)
    print("\n" + "="*60)
    print("After adding the code:")
    print("1. Save the file")
    print("2. Restart service: sudo systemctl restart mecamera")
    print("3. Test: curl http://localhost:8080/api/v3/status")
    print("="*60)
