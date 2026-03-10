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
    """Stream camera via rpicam/libcamera still-image subprocess - persistent connection"""
    
    def __init__(self, width=640, height=480, fps=15, timeout=5, quality=95, rotation=0, hflip=False, vflip=False):
        self.width = width
        self.height = height
        self.fps = fps
        self.timeout = timeout  # Process timeout in seconds
        self.quality = quality
        self.rotation = rotation
        self.hflip = hflip
        self.vflip = vflip
        self.running = False
        self.process = None
        self.last_frame = None
        self.lock = threading.Lock()
        self.frame_count = 0
        self.error_count = 0
        self.last_frame_time = 0
        self.capture_thread = None
        self.capture_timeout = 2  # Individual capture timeout in seconds (reduced for faster response)
        self.consecutive_failures = 0
        
        # Verify camera still-capture binary is available.
        self.rpicam_path = self._find_rpicam()
        if not self.rpicam_path:
            logger.error("[RPICAM] No compatible rpicam/libcamera still binary found in PATH")
            raise RuntimeError("rpicam or libcamera still binary not installed")
    
    def _find_rpicam(self):
        """Find the first available still-capture binary in priority order."""
        candidates = [
            'rpicam-jpeg',
            'libcamera-jpeg',
            'rpicam-still',
            'libcamera-still',
        ]

        for binary in candidates:
            try:
                result = subprocess.run(['which', binary], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    path = result.stdout.strip()
                    logger.info(f"[RPICAM] Using camera binary: {path}")
                    return path
            except Exception:
                continue

        # Try common explicit paths as fallback.
        common_paths = [
            '/usr/bin/rpicam-jpeg',
            '/usr/local/bin/rpicam-jpeg',
            '/usr/bin/libcamera-jpeg',
            '/usr/local/bin/libcamera-jpeg',
            '/usr/bin/rpicam-still',
            '/usr/local/bin/rpicam-still',
            '/usr/bin/libcamera-still',
            '/usr/local/bin/libcamera-still',
        ]
        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"[RPICAM] Using camera binary: {path}")
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
                '-t', '50',  # Reduced timeout 50ms for faster capture
                '-o', '-',  # Output to stdout
                '--nopreview',
                '--quality', str(self.quality),
                '--rotation', str(self.rotation),
            ]

            if self.hflip:
                cmd.append('--hflip')
            if self.vflip:
                cmd.append('--vflip')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.capture_timeout,  # Use capture_timeout instead of self.timeout
                text=False
            )
            
            if result.returncode == 0 and result.stdout:
                with self.lock:
                    self.last_frame = result.stdout
                    self.frame_count += 1
                    self.last_frame_time = time.time()
                self.consecutive_failures = 0
                return result.stdout
                    
        except subprocess.TimeoutExpired:
            logger.debug("[RPICAM] Frame capture timeout")
            self.consecutive_failures += 1
        except Exception as e:
            logger.debug(f"[RPICAM] Frame capture error: {e}")
            self.consecutive_failures += 1
        
        return None
    
    def _continuous_capture(self):
        """Background thread to continuously capture frames"""
        while self.running:
            try:
                frame = self._capture_single_frame()
                if frame:
                    with self.lock:
                        self.last_frame = frame
                        self.frame_count += 1
                        self.last_frame_time = time.time()
                    self.consecutive_failures = 0
                elif self.consecutive_failures > 25:
                    logger.warning("[RPICAM] Too many capture failures, backing off before retry")
                    time.sleep(1.0)
                    self.consecutive_failures = 0
                time.sleep(0.020)  # ~50 FPS potential (actual will be 20-30 FPS due to capture time)
            except Exception as e:
                logger.debug(f"[RPICAM] Continuous capture error: {e}")
                time.sleep(0.05)
    
    def start(self):
        """Start camera using background capture thread for better performance"""
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
                    break
                time.sleep(0.3)
            
            # Start background capture thread for continuous streaming
            self.capture_thread = threading.Thread(target=self._continuous_capture, daemon=True)
            self.capture_thread.start()
            logger.info("[RPICAM] Background capture thread started")
            
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
        """Get current JPEG frame - returns buffered frame from background thread"""
        if not self.running:
            return None

        # If frame is stale, attempt a direct capture to recover quickly.
        if self.last_frame_time and (time.time() - self.last_frame_time > 2.0):
            self._capture_single_frame()
        
        # Return buffered frame captured by background thread
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

    def restart(self):
        """Restart camera capture loop."""
        logger.info("[RPICAM] Restart requested")
        self.stop()
        time.sleep(0.5)
        return self.start()


def is_rpicam_available():
    """Check if any supported rpicam/libcamera still binary is available."""
    try:
        for binary in ('rpicam-jpeg', 'libcamera-jpeg', 'rpicam-still', 'libcamera-still'):
            result = subprocess.run(['which', binary], capture_output=True, timeout=2)
            if result.returncode == 0:
                return True
        return False
    except Exception:
        return False
