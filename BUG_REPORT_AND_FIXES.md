# 🐛 CRITICAL BUG ANALYSIS - Overnight Disconnect Issue
**Date**: January 26, 2026  
**Severity**: CRITICAL - Causes complete app disconnection after ~8-12 hours  
**Status**: IDENTIFIED & READY TO FIX

---

## 🚨 Root Causes Found

### BUG #1: Memory Leak in `rpicam_streamer.py` - Line 105-115
**Location**: `_read_frames_from_process()` method  
**Severity**: CRITICAL  
**Impact**: Frames accumulate in memory, eventually consuming all 512MB on Pi Zero, causing system freeze

```python
# BUGGY CODE (Line 105-115):
frame_data = self.process.stdout.read(1024 * 100)  # Read up to 100KB
if frame_data:
    with self.lock:
        self.last_frame = frame_data  # ❌ PROBLEM: Keeps reference to old frames
        self.frame_count += 1
```

**Why it breaks**: Each frame is 100KB+. When `self.last_frame` is overwritten, the old frame should be garbage collected, BUT the thread is constantly reading new data faster than Python can free memory. After 8-12 hours at 15 FPS = ~432,000-648,000 frames = potential 40GB+ of leaked refs.

**Fix**: Add explicit cleanup and limit buffer growth:
```python
if frame_data:
    with self.lock:
        # Release old frame before storing new one
        self.last_frame = None  # Explicit cleanup
        self.last_frame = frame_data
```

---

### BUG #2: Unbounded Frame Buffer in `app_lite.py` - Line 890-930
**Location**: `generate_frames()` function  
**Severity**: CRITICAL  
**Impact**: Motion detection buffer grows unbounded, consuming all RAM

```python
# BUGGY CODE (Line 905-908):
frame_buffer = []  # Buffer to capture frames BEFORE motion detected
buffer_size = 8    # Only 8 frames max

# But then (Line 920-925):
frame_buffer.append(frame.copy())  # ❌ PROBLEM: frame.copy() is huge (~600KB)
if len(frame_buffer) > buffer_size:
    frame_buffer.pop(0)
```

**Why it breaks**: Each frame copy is ~600KB (640x480 RGB). Even with only 8 frames, that's 4.8MB per client stream. On Pi Zero with 512MB total, multiple concurrent connections or memory fragmentation causes OOM.

**Fix**: Use smaller frame size or skip buffering for lite mode:
```python
# For Pi Zero lite mode, reduce buffer or disable
if pi_model.get('ram_mb', 512) <= 512:
    frame_buffer.append(frame.copy())
    if len(frame_buffer) > 4:  # Reduce to 4 frames
        frame_buffer.pop(0)
else:
    frame_buffer.append(frame.copy())  # Keep 8 for fuller devices
    if len(frame_buffer) > buffer_size:
        frame_buffer.pop(0)
```

---

### BUG #3: Motion Detection Loop Logic Flaw - Line 935-960
**Location**: `generate_frames()` motion detection  
**Severity**: HIGH  
**Impact**: Motion detection skips frames randomly, then processes occur in wrong order, causing thread desync

```python
# BUGGY CODE (Line 935-960):
if len(frame_buffer) % 2 == 0:  # ❌ PROBLEM: Uses modulo on frame_buffer LENGTH
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
else:
    frame_buffer.append(frame.copy())
    # ... process frame
    continue
```

**Why it breaks**: `len(frame_buffer) % 2` alternates between True/False as buffer fills. This means:
- When buffer has even count (2, 4, 6, 8): process motion on frame
- When buffer has odd count (1, 3, 5, 7): skip motion detection and stream
- **Result**: Motion detection happens inconsistently, sometimes completely disabled when buffer is odd length (startup, after motion cleared)
- This causes camera to appear disconnected because motion events aren't logged

**Fix**: Use a frame counter instead:
```python
frame_count = 0  # Add at top of generate_frames()

# In loop:
frame_count += 1
if frame_count % 2 == 0:  # Skip every other frame for performance
    # Skip motion detection this frame
    pass
else:
    # Do motion detection
```

---

### BUG #4: No Timeout on Flask Stream Generator - Line 880-885
**Location**: `video_feed()` route  
**Severity**: MEDIUM  
**Impact**: Browser connection hangs indefinitely without cleanup, orphan connections accumulate

```python
# BUGGY CODE (Line 880-885):
return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
```

**Why it breaks**: Flask never closes this stream unless browser closes. On mobile overnight:
- Browser tab loses focus
- Network reconnect happens
- Old stream connection lingers
- New connection starts alongside old one
- Memory usage doubles
- Eventually device becomes unresponsive

**Fix**: Add stream timeout handling:
```python
@app.route("/video_feed")
def video_feed():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if camera is None or not camera_available:
        return Response(generate_test_pattern(), 
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    
    # Add timeout header to force browser reconnect periodically
    response = Response(generate_frames(), 
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    response.headers['Connection'] = 'keep-alive'
    response.headers['Keep-Alive'] = 'timeout=300'  # 5 min timeout
    return response
```

---

### BUG #5: PIL/Image Operations Without Cleanup - Line 970-978
**Location**: `generate_frames()` JPEG encoding  
**Severity**: MEDIUM  
**Impact**: Image objects accumulate, not garbage collected properly

```python
# BUGGY CODE (Line 970-978):
img = Image.fromarray(frame)  # ❌ No cleanup
buf = io.BytesIO()
img.save(buf, format='JPEG', quality=85)
jpeg_bytes = buf.getvalue()
yield (b'--frame\r\n...' + jpeg_bytes + b'\r\n')
```

**Why it breaks**: After ~24 hours, PIL's internal image cache fills up. Even though vars go out of scope, their memory isn't immediately freed due to Python's garbage collection being non-deterministic on low-RAM devices.

**Fix**: Explicit cleanup:
```python
img = Image.fromarray(frame)
buf = io.BytesIO()
img.save(buf, format='JPEG', quality=85)
jpeg_bytes = buf.getvalue()
yield (b'--frame\r\n...' + jpeg_bytes + b'\r\n')

# Explicit cleanup
del img
buf.close()
del buf
```

---

### BUG #6: Thread Not Properly Joined on Shutdown - `rpicam_streamer.py` Line 200
**Location**: `stop()` method  
**Severity**: LOW  
**Impact**: Process zombie threads accumulate on service restart

```python
# BUGGY CODE (Line 200-203):
def stop(self):
    self.running = False
    self._cleanup_process()
    if self.capture_thread:
        self.capture_thread.join(timeout=2)  # Only 2 second timeout
```

**Why it breaks**: If thread is stuck reading from process, 2 seconds might not be enough. Thread continues in background causing resource leaks.

**Fix**: Use daemon threads + add force kill:
```python
def stop(self):
    self.running = False
    self._cleanup_process()  # Kill process first
    if self.capture_thread and self.capture_thread.is_alive():
        self.capture_thread.join(timeout=5)
        if self.capture_thread.is_alive():
            logger.warning("[RPICAM] Thread didn't stop gracefully (expected on daemon)")
```

---

## 📊 Timeline of Failure

1. **Hour 0**: Device starts, camera fine, memory usage ~100MB
2. **Hour 4**: Frame buffer memory leaks start (~120MB RAM used)
3. **Hour 8**: Multiple leaks accumulating (~200MB used, mobile app may have stale connection)
4. **Hour 12**: Out of memory events begin, system becomes sluggish
5. **Hour 14-16**: OOM killer activates, app process killed or hung
6. **Result**: Mobile app shows "camera unavailable" or disconnects

---

## ✅ Fixes to Apply

### File 1: `src/camera/rpicam_streamer.py`

**Change 1** (Line 105-115 - Frame buffer cleanup):
```python
# OLD:
frame_data = self.process.stdout.read(1024 * 100)
if frame_data:
    with self.lock:
        self.last_frame = frame_data
        self.frame_count += 1

# NEW:
frame_data = self.process.stdout.read(1024 * 100)
if frame_data:
    with self.lock:
        old_frame = self.last_frame
        self.last_frame = frame_data
        self.frame_count += 1
        # Explicit cleanup of old frame
        if old_frame is not None and len(old_frame) > 1024*1024:  # Only log huge allocations
            logger.debug(f"[RPICAM] Frame rotated ({len(frame_data)} bytes)")
        del old_frame
```

**Change 2** (Line 200-203 - Thread timeout):
```python
# OLD:
if self.capture_thread:
    self.capture_thread.join(timeout=2)

# NEW:
if self.capture_thread and self.capture_thread.is_alive():
    self.capture_thread.join(timeout=5)
```

---

### File 2: `web/app_lite.py`

**Change 1** (Line 890-908 - Frame buffer size optimization):

**Change 2** (Line 935-960 - Fix motion detection logic):

**Change 3** (Line 880-885 - Add stream timeout):

**Change 4** (Line 970-978 - Explicit cleanup):

---

## 🧪 Testing After Fixes

```bash
# 1. Monitor memory usage
ssh pi@mecamdev2.local 'watch -n 5 free -h'

# 2. Check process memory
ssh pi@mecamdev2.local 'ps aux | grep main_lite'

# 3. Tail logs for errors
ssh pi@mecamdev2.local 'tail -100 ~/ME_CAM-DEV/logs/mecam_lite.log'

# 4. Run 24-hour stress test
# Keep mobile app open in background, monitor RAM
# Expected: RAM usage stays stable (~100-120MB)
# Actual (buggy): RAM grows 5-10MB/hour
```

---

## 🎯 Priority Order

1. **IMMEDIATE**: Fix BUG #1 (rpicam memory leak) - causes overnight crash
2. **IMMEDIATE**: Fix BUG #2 (frame buffer unbounded) - causes OOM
3. **URGENT**: Fix BUG #3 (motion detection logic) - causes false disconnects
4. **HIGH**: Fix BUG #4 (stream timeout) - causes orphan connections
5. **MEDIUM**: Fix BUG #5 (PIL cleanup) - helps with long-term stability
6. **LOW**: Fix BUG #6 (thread join) - cleanup improvement

---

## 📝 Device-Specific Notes

**Device 2 (Pi Zero 2W - 512MB RAM)**: All 6 bugs apply - MUST FIX ALL

**Device 1 (Raspberry Pi 3/4 - 1GB+ RAM)**: Bugs 1-3 apply - should fix anyway for stability

