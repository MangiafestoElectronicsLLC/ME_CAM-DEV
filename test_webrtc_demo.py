#!/usr/bin/env python3
"""
Quick demo to test WebRTC peer connection creation
"""

import asyncio
import sys

# Add project root to path
sys.path.insert(0, '/home/pi/ME_CAM-DEV')

async def test_webrtc():
    print("="*60)
    print("WebRTC Quick Test")
    print("="*60)
    
    try:
        from src.streaming.webrtc_peer import WebRTCStreamer
        
        print("\n[1/4] Creating WebRTC streamer...")
        streamer = WebRTCStreamer()
        print("✅ Streamer created successfully")
        
        print("\n[2/4] Creating SDP offer...")
        offer = await streamer.create_offer()
        print(f"✅ Offer created:")
        print(f"   Type: {offer['type']}")
        print(f"   SDP length: {len(offer['sdp'])} characters")
        print(f"   First 100 chars: {offer['sdp'][:100]}...")
        
        print("\n[3/4] Checking peer connection...")
        print(f"✅ Connection state: {streamer.pc.connectionState}")
        print(f"✅ ICE connection state: {streamer.pc.iceConnectionState}")
        print(f"✅ ICE gathering state: {streamer.pc.iceGatheringState}")
        print(f"✅ Signaling state: {streamer.pc.signalingState}")
        
        print("\n[4/4] Closing connection...")
        await streamer.close()
        print("✅ Connection closed cleanly")
        
        print("\n" + "="*60)
        print("✅ WebRTC Test PASSED - Ready for browser integration")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_webrtc())
    sys.exit(0 if result else 1)
