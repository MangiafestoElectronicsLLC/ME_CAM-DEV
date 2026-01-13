"""
Lightweight motion detector using libcamera snapshots
Works alongside web streaming without camera conflicts
"""
import os
import cv2
import numpy as np
import time
import subprocess
from datetime import datetime
from loguru import logger
from threading import Lock
from camera_coordinator import camera_coordinator

class LibcameraMotionDetector:
    """Motion detection using periodic libcamera snapshots"""
    
    def __init__(self, config):
        self.config = config
        self.recordings_dir = config["storage"]["recordings_dir"]
        self.min_area = config["detection"].get("min_motion_area", 500)
        self.sensitivity = config["detection"].get("sensitivity", 0.6)
        
        os.makedirs(self.recordings_dir, exist_ok=True)
        os.makedirs("/tmp/motion_detection", exist_ok=True)
        
        self.last_frame = None
        self.motion_start_time = None
        self.is_recording = False
        self.recording_process = None
        self.lock = Lock()
        
    def capture_frame(self):
        """Capture a single frame for motion analysis"""
        # Use camera coordinator to prevent conflicts with streaming
        with camera_coordinator.access(user="motion_detection", priority="normal") as granted:
            if not granted:
                # Camera busy with streaming - skip this check
                return None
            
            try:
                output_path = "/tmp/motion_detection/current.jpg"
                cmd = [
                    "libcamera-still",
                    "--width", "640",
                    "--height", "480",
                    "-o", output_path,
                    "--nopreview",
                    "-t", "100",
                    "--immediate"
                ]
                
                result = subprocess.run(cmd, timeout=2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if result.returncode == 0 and os.path.exists(output_path):
                    frame = cv2.imread(output_path, cv2.IMREAD_GRAYSCALE)
                    return frame
            except Exception as e:
                logger.warning(f"[MOTION] Frame capture failed: {e}")
            return None
    
    def detect_motion(self, current_frame):
        """Simple frame difference motion detection"""
        if self.last_frame is None:
            self.last_frame = current_frame
            return False
        
        # Calculate frame difference
        frame_diff = cv2.absdiff(self.last_frame, current_frame)
        _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        
        # Dilate to fill gaps
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.dilate(thresh, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Check if any contour is large enough
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                motion_detected = True
                break
        
        self.last_frame = current_frame
        return motion_detected
    
    def start_recording(self):
        """Start video recording using libcamera-vid"""
        with self.lock:
            if self.is_recording:
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.recordings_dir, f"motion_{timestamp}.mp4")
            
            cmd = [
                "libcamera-vid",
                "-t", "30000",  # 30 seconds max
                "--width", "1280",
                "--height", "720",
                "-o", output_file,
                "--nopreview",
                "--codec", "h264"
            ]
            
            try:
                self.recording_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.is_recording = True
                self.motion_start_time = time.time()
                logger.info(f"[MOTION] Recording started: {output_file}")
            except Exception as e:
                logger.error(f"[MOTION] Failed to start recording: {e}")
    
    def stop_recording(self):
        """Stop current recording"""
        with self.lock:
            if not self.is_recording:
                return
            
            try:
                if self.recording_process:
                    self.recording_process.terminate()
                    self.recording_process.wait(timeout=5)
                    logger.info("[MOTION] Recording stopped")
            except Exception as e:
                logger.error(f"[MOTION] Error stopping recording: {e}")
            finally:
                self.is_recording = False
                self.recording_process = None
                self.motion_start_time = None
    
    def check_and_record(self):
        """Main loop: check for motion and manage recording"""
        frame = self.capture_frame()
        if frame is None:
            return
        
        motion = self.detect_motion(frame)
        
        if motion:
            if not self.is_recording:
                self.start_recording()
            else:
                # Extend recording time
                self.motion_start_time = time.time()
        else:
            # Stop recording if no motion for 5 seconds
            if self.is_recording and self.motion_start_time:
                if time.time() - self.motion_start_time > 5:
                    self.stop_recording()
