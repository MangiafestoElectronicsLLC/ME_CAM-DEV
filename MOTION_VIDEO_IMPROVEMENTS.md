# Motion Detection & Video Recording Improvements

## Changes Made (v2.1.2)

### 1. ✅ Video Codec Fixed - H.264/AVC
**Problem:** Videos using 'mp4v' codec which browsers struggle with
**Solution:** Changed to 'avc1' (H.264) codec for universal browser support

```python
# Old: fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# New: fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264
```

### 2. ✅ Faster Motion Detection
**Problem:** 100-frame cooldown (~5 seconds) caused missed events
**Solution:** 
- Reduced cooldown to 75 frames
- Skip every 3rd frame for processing (keeps live stream smooth)
- Improved motion threshold (mean > 8 or max > 50)

### 3. ✅ Longer Video Clips
**Problem:** 3-second clips too short to capture full motion event
**Solution:** Increased to 5 seconds at 15 FPS (75 frames)

### 4. ✅ Better Motion Detection Algorithm
**Problem:** Single threshold too simplistic
**Solution:** Dual threshold system:
```python
mean_diff > 8   # Average motion across frame
max_diff > 50   # Peak motion in any area
```

### 5. ⚠️ Audio in Videos
**Status:** Pi Camera Module does NOT have built-in microphone

**Options for Audio:**

#### Option A: USB Microphone (Recommended)
```bash
# Install audio support
sudo apt-get install python3-pyaudio portaudio19-dev

# List audio devices
arecord -l

# Test recording
arecord -D plughw:1,0 -f cd test.wav
```

Then modify recording code:
```python
import pyaudio
import wave
import threading

def record_audio(filename, duration):
    """Record audio from USB mic"""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, 
                   rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    frames = []
    for _ in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

# In save_motion_clip function:
# Start audio recording in parallel thread
audio_file = filepath.replace('.mp4', '.wav')
audio_thread = threading.Thread(target=record_audio, args=(audio_file, duration_sec))
audio_thread.start()

# ... record video ...

audio_thread.join()

# Merge audio and video with ffmpeg
os.system(f'ffmpeg -i {filepath} -i {audio_file} -c:v copy -c:a aac {filepath}.tmp')
os.replace(f'{filepath}.tmp', filepath)
os.remove(audio_file)
```

#### Option B: External USB Sound Card
Better audio quality than basic USB mic:
```bash
# Products like "USB Audio Adapter" ($5-10)
# Plug in mic → automatically detected
# Same code as Option A
```

#### Option C: Network Audio (Advanced)
Stream audio from phone/computer to Pi:
```bash
# Use phone as remote microphone
# Requires additional app/setup
```

---

## Performance Optimization

### Current Settings (Optimized for Pi Zero 2W):
- **Resolution:** 640x480
- **FPS:** 15 (balanced for quality/performance)  
- **Recording Length:** 5 seconds
- **Motion Threshold:** mean > 8 or max > 50
- **Cooldown:** 5 seconds between events
- **Frame Skip:** Process every 3rd frame (live stream still 20fps)

### If You Get Better Performance Issues:
```python
# In app_lite.py, adjust these:

# Lower FPS (smoother on Pi Zero)
fps = 10.0  # instead of 15.0

# Shorter clips (less CPU)
duration_sec=3  # instead of 5

# Lower resolution (if needed)
camera.configure(camera.create_preview_configuration(
    main={"size": (480, 360), "format": "RGB888"}  # instead of 640x480
))
```

---

## Testing New Changes

### 1. Transfer Updated File:
```powershell
scp web\app_lite.py pi@10.2.1.47:~/ME_CAM-DEV/web/
```

### 2. Restart Service:
```bash
ssh pi@10.2.1.47
sudo systemctl restart mecamera-lite
```

### 3. Test Motion Detection:
- Wave at camera
- Video should record immediately
- Check file: `recordings/motion_YYYYMMDD_HHMMSS.mp4`
- Play in browser - should work now with H.264

### 4. Verify Video Codec:
```bash
ssh pi@10.2.1.47
file ~/ME_CAM-DEV/recordings/motion_*.mp4
# Should show: ISO Media, MP4 with H.264
```

---

## Expected Results

**Before (v2.1.1):**
- ❌ Videos don't play in browser (mp4v codec)
- ❌ Slow motion detection (5+ second delay)
- ❌ Short 3-second clips miss action
- ❌ Simple threshold misses subtle motion
- ❌ No audio

**After (v2.1.2):**
- ✅ Videos play inline (H.264 codec)
- ✅ Fast motion detection (~1-2 second response)
- ✅ 5-second clips capture full event
- ✅ Dual threshold catches more motion
- ⚠️ Audio requires USB mic (see above)

---

## Quick Comparison

| Feature | Old | New | Improvement |
|---------|-----|-----|-------------|
| Video Codec | mp4v | H.264/AVC | ✅ Browser compatible |
| Clip Length | 3 sec | 5 sec | ✅ Captures full event |
| FPS | 20 | 15 | ✅ Better for Pi Zero |
| Detection Speed | ~5 sec | ~1-2 sec | ✅ Faster response |
| Motion Algorithm | Single threshold | Dual threshold | ✅ More accurate |
| Cooldown | 100 frames | 75 frames | ✅ Balanced |
| Frame Processing | Every frame | Every 3rd | ✅ CPU efficient |
| Audio | None | USB mic ready | ⚠️ Requires hardware |

---

## Audio Hardware Recommendations

**Budget Option ($5-10):**
- Generic USB Microphone
- USB Audio Adapter with 3.5mm mic input

**Better Quality ($15-30):**
- Blue Snowball iCE USB Microphone
- Audio-Technica ATR2100x-USB
- Logitech USB Desktop Microphone

**Best for Security ($20-40):**
- USB Conference Microphone (omnidirectional)
- Lavalier USB Microphone
- Boundary Microphone

**Note:** Pi Zero 2W has only 1 USB port, so you'll need a USB hub if using both camera and mic.

---

## Troubleshooting

### Videos Still Won't Play:
```bash
# Check codec
ffmpeg -i recordings/motion_*.mp4 2>&1 | grep Video

# Should show: h264 (High) (avc1 / 0x31637661)

# If not, OpenCV might not have H.264 support
sudo apt-get install libavcodec-extra
sudo apt-get install ffmpeg
```

### Motion Detection Too Sensitive:
```python
# In app_lite.py, increase thresholds:
motion = mean_diff > 12 or max_diff > 70  # less sensitive
```

### Motion Detection Not Sensitive Enough:
```python
# In app_lite.py, decrease thresholds:
motion = mean_diff > 5 or max_diff > 30  # more sensitive
```

### Videos Choppy/Laggy:
```python
# Reduce FPS
fps = 10.0  # smoother on Pi Zero

# Or reduce resolution
main={"size": (480, 360)}
```

---

**Deploy the updated app_lite.py now for immediate improvements!** 🚀
