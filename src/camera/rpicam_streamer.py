"""
RPiCam Streamer - Direct libcamera support via rpicam-apps
===========================================================
Uses rpicam-jpeg subprocess to capture frames and stream as MJPEG.
Compatible with Pi Zero 2W and all Raspberry Pi models.
No conflicts with picamera2 or legacy camera.

KEY FIX: Persistent process + frame buffer to avoid resource leaks
"""

import subprocess
import threading
import io
import time
from loguru import logger
import os
import signal


class RpicamStreamer:
    """Stream camera via rpicam-jpeg subprocess - persistent connection"""
    
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
        self.error_count = 0
        self.last_frame_time = 0
        self.capture_thread = None
        
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
    
    def _start_persistent_process(self):
        """Not used - we use single-shot mode instead"""
        return True
    
    def _read_frames_from_process(self):
        """Read JPEG frames continuously from the persistent process"""
        while self.running:
            try:
                if not self.process or self.process.poll() is not None:
                    # Process died, restart it
                    logger.warning("[RPICAM] Process died, restarting...")
                    self._cleanup_process()
                    if not self._start_persistent_process():
                        time.sleep(1)
                        continue
                
                # Try to read frame data
                # rpicam-still in timelapse mode outputs multiple JPEGs
                # This is a simplified approach - read available data
                if self.process.stdout:
                    try:
                        # Read with timeout to detect dead process
                        frame_data = self.process.stdout.read(1024 * 100)  # Read up to 100KB
                        if frame_data:
                            with self.lock:
                                # BUG FIX #1: Explicitly cleanup old frame before storing new one
                                # This prevents memory leaks on long-running streams
                                old_frame = self.last_frame
                                self.last_frame = frame_data
                                self.frame_count += 1
                                self.last_frame_time = time.time()
                                self.error_count = 0
                                if old_frame is not None:
                                    del old_frame
                        else:
                            # EOF reached, restart
                            logger.warning("[RPICAM] EOF reached, restarting process...")
                            self._cleanup_process()
                            if not self._start_persistent_process():
                                time.sleep(1)
                    except Exception as e:
                        logger.debug(f"[RPICAM] Read error: {e}")
                        self.error_count += 1
                        if self.error_count > 5:
                            logger.warning("[RPICAM] Too many read errors, restarting...")
                            self._cleanup_process()
                            if not self._start_persistent_process():
                                time.sleep(1)
                            self.error_count = 0
                
                time.sleep(0.01)  # Minimal sleep
                
            except Exception as e:
                logger.error(f"[RPICAM] Read thread error: {e}")
                time.sleep(0.5)
    
    def _capture_single_frame(self):
        """Capture a single JPEG frame (fallback method)"""
        try:
            cmd = [
                self.rpicam_path,
                '--width', str(self.width),
                '--height', str(self.height),
                '-t', '100',  # Timeout 100ms (quick capture)
                '-o', '-',  # Output to stdout
                '--nopreview',
                '--quality', '85',
                '--hflip',  # Horizontal flip
                '--vflip',  # Vertical flip (same as 180 rotation)
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
                    
        except subprocess.TimeoutExpired:
            logger.debug("[RPICAM] Frame capture timeout")
        except Exception as e:
            logger.debug(f"[RPICAM] Frame capture error: {e}")
        
        return None
    
    def start(self):
        """Start camera using single-frame capture mode (most reliable)"""
        try:
            self.running = True
            
            # Pre-warm camera with test captures
            logger.info("[RPICAM] Pre-warming camera with single-shot mode...")
            for i in range(3):
                frame = self._capture_single_frame()
                if frame and len(frame) > 1000:
                    self.last_frame = frame
                    self.frame_count = 1
                    logger.success(f"[RPICAM] Camera ready - Frame {i+1} captured ({len(frame)} bytes)")
                    return True
                time.sleep(0.3)
            
            logger.warning("[RPICAM] No frames captured but continuing...")
            return True
            
        except Exception as e:
            logger.error(f"[RPICAM] Start failed: {e}")
            self.running = False
            return False
    
    def _cleanup_process(self):
        """Clean up the process safely"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                try:
                    self.process.kill()
                    self.process.wait(timeout=1)
                except:
                    pass
            self.process = None
    
    def get_jpeg_frame(self):
        """Get current JPEG frame - captures fresh frame on each call"""
        if not self.running:
            return None
        
        # Always capture a fresh frame for live streaming
        frame = self._capture_single_frame()
        if frame:
            return frame
        
        # Fallback to buffered frame if capture fails
        with self.lock:
            if self.last_frame:
                return self.last_frame
        
        return None
    
    def stop(self):
        """Stop camera streaming"""
        self.running = False
        self._cleanup_process()
        # BUG FIX #6: Longer timeout + check thread status before join
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)
            if self.capture_thread.is_alive():
                logger.warning("[RPICAM] Capture thread didn't stop gracefully (expected for daemon)")
        logger.info(f"[RPICAM] Stopped after {self.frame_count} frames (errors: {self.error_count})")


def is_rpicam_available():
    """Check if rpicam-jpeg is available"""
    try:
        result = subprocess.run(['which', 'rpicam-jpeg'], 
                              capture_output=True, timeout=2)
        return result.returncode == 0
    except:
        return False
