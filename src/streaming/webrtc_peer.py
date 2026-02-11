"""
WebRTC Peer Connection for Remote Camera Access
================================================
Enables low-latency video streaming with automatic NAT traversal via STUN/TURN servers.
Works from cellular data, coffee shops, anywhere without port forwarding.

Architecture:
  Pi (Broadcaster) ←→ [STUN/TURN] ←→ Browser (Viewer)
  
No server needed - direct peer-to-peer connection negotiated via signaling.
"""

import asyncio
import json
from loguru import logger
from typing import Optional, Dict, List, Callable
import av
import numpy as np

# Note: aiortc requires manual installation
# pip install aiortc>=1.5.0
try:
    from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer, RTCSessionDescription
    from aiortc.contrib.media import MediaPlayer, MediaRecorder
    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False
    logger.warning("[WebRTC] aiortc not installed - WebRTC disabled. Install: pip install aiortc")


class WebRTCStreamer:
    """
    Manages WebRTC peer connections for camera streaming.
    
    Usage:
        streamer = WebRTCStreamer(stun_servers=[...], turn_servers=[...])
        offer = await streamer.create_offer()  # Send to browser
        await streamer.set_remote_description(answer)  # Receive answer
        await streamer.add_video_track(video_source)
    """
    
    def __init__(self, 
                 stun_servers: Optional[List[str]] = None,
                 turn_servers: Optional[List[Dict]] = None,
                 enable_data_channel: bool = True):
        """
        Initialize WebRTC peer connection.
        
        Args:
            stun_servers: List of STUN server URLs (default: Google's public STUN)
            turn_servers: List of TURN server configs (optional for NAT traversal)
            enable_data_channel: Allow metadata/control messages
        """
        if not AIORTC_AVAILABLE:
            raise RuntimeError("aiortc not installed")
        
        self.logger = logger.bind(name="WebRTC")
        
        # Configure ICE servers for NAT traversal
        ice_servers = [
            RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
            RTCIceServer(urls=["stun:stun1.l.google.com:19302"]),
            RTCIceServer(urls=["stun:stun2.l.google.com:19302"]),
        ]
        
        if turn_servers:
            for turn_config in turn_servers:
                ice_servers.append(RTCIceServer(**turn_config))
        
        self.config = RTCConfiguration(iceServers=ice_servers)
        self.pc = RTCPeerConnection(configuration=self.config)
        self.logger.info(f"[INIT] WebRTC peer with {len(ice_servers)} ICE servers")
        
        self.video_track = None
        self.enable_data_channel = enable_data_channel
        self.data_channel = None
        self._video_frame_callback: Optional[Callable] = None
        
        # Setup event handlers
        self.pc.on("connectionstatechange", self._on_connection_state_change)
        self.pc.on("iceconnectionstatechange", self._on_ice_connection_state_change)
        if enable_data_channel:
            self.pc.on("datachannel", self._on_data_channel)
    
    async def create_offer(self) -> Dict:
        """
        Create SDP offer to send to WebRTC client.
        
        Returns:
            {'type': 'offer', 'sdp': '...'}
        """
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        
        self.logger.info("[OFFER] SDP offer created, waiting for answer")
        return {
            "type": self.pc.localDescription.type,
            "sdp": self.pc.localDescription.sdp
        }
    
    async def set_remote_description(self, answer: Dict) -> None:
        """
        Accept SDP answer from WebRTC client.
        
        Args:
            answer: {'type': 'answer', 'sdp': '...'}
        """
        description = RTCSessionDescription(sdp=answer["sdp"], type=answer["type"])
        await self.pc.setRemoteDescription(description)
        self.logger.success("[ANSWER] Remote description set, connection establishing")
    
    async def add_video_track(self, video_source_path: str) -> None:
        """
        Add video track from file or stream.
        
        Args:
            video_source_path: Path to video file or device stream
        """
        try:
            # Option 1: Stream from libcamera-vid FIFO
            if video_source_path.startswith("/tmp/") and "fifo" in video_source_path:
                # Named pipe from libcamera-vid --listen tcp://
                self.logger.info(f"[VIDEO] Connecting to camera FIFO: {video_source_path}")
                player = MediaPlayer(video_source_path, options={
                    "video_size": "640x480",
                    "pixel_format": "h264",
                })
            else:
                # Option 2: File-based testing
                player = MediaPlayer(video_source_path)
            
            self.video_track = player.video
            self.pc.addTrack(self.video_track)
            self.logger.success("[VIDEO] Video track added to peer connection")
            
        except Exception as e:
            self.logger.error(f"[VIDEO] Failed to add video: {e}")
            raise
    
    async def add_custom_video_source(self, 
                                      frame_generator: Callable) -> None:
        """
        Add video from custom frame generator (numpy arrays).
        
        Usage:
            async def frame_source():
                while True:
                    frame = capture_frame()  # Returns numpy array (BGR, uint8)
                    yield frame
                    await asyncio.sleep(1/30)  # 30 FPS
            
            await streamer.add_custom_video_source(frame_source())
        """
        from aiortc import VideoStreamTrack
        
        class CustomVideoTrack(VideoStreamTrack):
            def __init__(self, generator):
                super().__init__()
                self.generator = generator
            
            async def recv(self):
                frame_data = await self.generator.__anext__()
                
                # Convert numpy array to av.Frame
                # frame_data should be (H, W, 3) BGR uint8
                img = av.VideoFrame.from_ndarray(frame_data, format="bgr24")
                img.pts = self.pts
                img.time_base = self.time_base
                return img
        
        self.video_track = CustomVideoTrack(frame_generator)
        self.pc.addTrack(self.video_track)
        self.logger.success("[VIDEO] Custom video source added")
    
    async def close(self) -> None:
        """Close WebRTC connection and cleanup resources."""
        await self.pc.close()
        self.logger.info("[CLOSE] Peer connection closed")
    
    def set_data_channel_callback(self, callback: Callable) -> None:
        """
        Register callback for messages from browser.
        
        Callback receives: {'type': 'message', 'data': '...'}
        """
        self._data_channel_callback = callback
    
    async def send_data_message(self, message: str) -> None:
        """Send message to browser via data channel."""
        if self.data_channel and self.data_channel.readyState == "open":
            self.data_channel.send(message)
    
    # ===== Event Handlers =====
    
    async def _on_connection_state_change(self):
        """Log connection state changes."""
        state = self.pc.connectionState
        self.logger.info(f"[STATE] Connection: {state}")
        
        if state == "failed":
            self.logger.error("[STATE] Connection failed - check STUN/TURN servers")
        elif state == "connected":
            self.logger.success("[STATE] Peer connection ACTIVE ✓")
        elif state == "closed":
            self.logger.warning("[STATE] Connection closed")
    
    async def _on_ice_connection_state_change(self):
        """Log ICE connection state."""
        state = self.pc.iceConnectionState
        self.logger.debug(f"[ICE] State: {state}")
    
    def _on_data_channel(self, channel):
        """Handle incoming data channel."""
        self.data_channel = channel
        self.logger.info(f"[DATA] Channel '{channel.label}' opened")
        
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                    if hasattr(self, '_data_channel_callback'):
                        self._data_channel_callback(data)
                except json.JSONDecodeError:
                    self.logger.warning(f"[DATA] Invalid JSON: {message}")


class WebRTCSignalingServer:
    """
    Simple signaling server for WebRTC SDP exchange.
    
    In a production system, this would:
    1. Handle multiple concurrent peer connections
    2. Store SDPs in temporary storage (Redis/DB)
    3. Facilitate offer/answer exchange between Pi and browsers
    
    For ME_CAM, integration with Flask:
    
    @app.route('/webrtc/offer', methods=['POST'])
    async def webrtc_offer():
        offer = request.json
        streamer = WebRTCStreamer()
        await streamer.set_remote_description(offer)
        my_offer = await streamer.create_offer()
        return jsonify(my_offer)
    """
    
    def __init__(self):
        self.connections: Dict[str, WebRTCStreamer] = {}
        self.logger = logger.bind(name="WebRTCSignal")
    
    async def create_peer(self, peer_id: str, 
                         stun_servers: Optional[List[str]] = None) -> WebRTCStreamer:
        """Create new peer connection."""
        streamer = WebRTCStreamer(stun_servers=stun_servers)
        self.connections[peer_id] = streamer
        self.logger.info(f"[PEER] Created connection: {peer_id}")
        return streamer
    
    async def close_peer(self, peer_id: str) -> None:
        """Close peer connection."""
        if peer_id in self.connections:
            await self.connections[peer_id].close()
            del self.connections[peer_id]
            self.logger.info(f"[PEER] Closed connection: {peer_id}")


# ===== Demo/Testing =====

async def demo_webrtc():
    """Demo: Create WebRTC connection and print SDP offer."""
    if not AIORTC_AVAILABLE:
        print("Install aiortc: pip install aiortc")
        return
    
    streamer = WebRTCStreamer()
    offer = await streamer.create_offer()
    
    print("\n" + "="*60)
    print("WebRTC Offer (send to browser):")
    print("="*60)
    print(json.dumps(offer, indent=2))
    print("="*60)
    
    # Simulate receiving answer
    answer = {
        "type": "answer",
        "sdp": "v=0\no=- 0 0 IN IP4 127.0.0.1\ns=-\nt=0 0\n..."  # Placeholder
    }
    
    await streamer.set_remote_description(answer)
    await streamer.close()


if __name__ == "__main__":
    # Test: python3 -m src.streaming.webrtc_peer
    print("[!] WebRTC module loaded")
    print("[!] Use in Flask app: from src.streaming.webrtc_peer import WebRTCStreamer")
