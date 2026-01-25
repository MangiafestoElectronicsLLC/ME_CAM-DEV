"""
RPiCam Streamer - Direct libcamera support via rpicam-apps
===========================================================
Uses rpicam-jpeg subprocess to capture frames and stream as MJPEG.
Compatible with Pi Zero 2W and all Raspberry Pi models.
No conflicts with picamera2 or legacy camera.
"""

import subprocess
import threading
import io
import time
from loguru import logger
import os


class RpicamStreamer:
    """Stream camera via rpicam-jpeg subprocess - highest compatibility"""
    
    def __init__(self, width=640, height=480, fps=15, timeout=5):
        self.width = width
        self.height = height
        self.fps = fps
        self.timeout = timeout
        self.running = False
        self.process = None
        self.last_frame = None
        self.lock = threading.Lock()
        self.frame_count = 0
        
        # Verify rpicam-jpeg is available
        self.rpicam_path = self._find_rpicam()
        if not self.rpicam_path:
            logger.error("[RPICAM] rpicam-jpeg not found in PATH")
            raise RuntimeError("rpicam-jpeg not installed")
    
    def _find_rpicam(self):
        """Find rpicam-jpeg binary"""
        try:
            result = subprocess.run(['which', 'rpicam-jpeg'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                path = result.stdout.strip()
                logger.info(f"[RPICAM] Found at: {path}")
                return path
        except:
            pass
        
        # Try common paths
        for path in ['/usr/bin/rpicam-jpeg', '/usr/local/bin/rpicam-jpeg']:
            if os.path.exists(path):
                logger.info(f"[RPICAM] Found at: {path}")
                return path
        
        return None
    
    def _capture_frames(self):
        """Continuously capture frames from rpicam"""
        while self.running:
            try:
                # Run rpicam-jpeg with output to stdout
                cmd = [
                    self.rpicam_path,
                    '--width', str(self.width),
                    '--height', str(self.height),
                    '-t', '0',  # Run indefinitely
                    '-o', '-',  # Output to stdout
                    '--nopreview',
                    '--quality', '85',
                ]
                
                logger.info(f"[RPICAM] Starting: {' '.join(cmd)}")
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=0
                )
                
                # Read JPEG frames from stdout
                while self.running and self.process:
                    try:
                        # rpicam-jpeg outputs one JPEG per invocation
                        # For continuous streaming, we use a simple workaround:
                        # Call rpicam-jpeg repeatedly with -t parameter
                        break
                    except Exception as e:
                        logger.debug(f"[RPICAM] Frame read error: {e}")
                        break
                
                if self.process:
                    self.process.terminate()
                    self.process.wait(timeout=2)
                    
            except Exception as e:
                logger.error(f"[RPICAM] Capture thread error: {e}")
            
            if self.running:
                time.sleep(0.5)
    
    def _capture_single_frame(self):
        """Capture a single JPEG frame"""
        try:
            cmd = [
                self.rpicam_path,
                '--width', str(self.width),
                '--height', str(self.height),
                '-t', '100',  # Timeout 100ms (quick capture)
                '-o', '-',  # Output to stdout
                '--nopreview',
                '--quality', '85',
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.timeout,
                text=False
            )
            
            if result.returncode == 0 and result.stdout:
                with self.lock:
                    self.last_frame = result.stdout
                    self.frame_count += 1
                return result.stdout
            else:
                if result.stderr:
                    logger.debug(f"[RPICAM] Stderr: {result.stderr.decode()[:200]}")
                    
        except subprocess.TimeoutExpired:
            logger.debug("[RPICAM] Frame capture timeout")
        except Exception as e:
            logger.debug(f"[RPICAM] Frame capture error: {e}")
        
        return None
    
    def start(self):
        """Start camera streaming"""
        try:
            self.running = True
            
            # Pre-warm camera with one frame
            logger.info("[RPICAM] Pre-warming camera...")
            for i in range(3):
                frame = self._capture_single_frame()
                if frame:
                    logger.success(f"[RPICAM] Camera ready - Frame {i+1} captured ({len(frame)} bytes)")
                    return True
                time.sleep(0.2)
            
            logger.warning("[RPICAM] Camera pre-warm failed but continuing...")
            return True
            
        except Exception as e:
            logger.error(f"[RPICAM] Start failed: {e}")
            self.running = False
            return False
    
    def get_jpeg_frame(self):
        """Get current JPEG frame"""
        if not self.running:
            return None
        
        frame = self._capture_single_frame()
        if frame:
            return frame
        
        # Return last frame if capture failed
        with self.lock:
            return self.last_frame
    
    def stop(self):
        """Stop camera streaming"""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                pass
            self.process = None
        logger.info(f"[RPICAM] Stopped after {self.frame_count} frames")


def is_rpicam_available():
    """Check if rpicam-jpeg is available"""
    try:
        result = subprocess.run(['which', 'rpicam-jpeg'], 
                              capture_output=True, timeout=2)
        return result.returncode == 0
    except:
        return False
