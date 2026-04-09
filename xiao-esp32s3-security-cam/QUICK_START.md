# XIAO ESP32S3 Sense Quick Start

## 1) Arduino IDE prerequisites

Install Board Manager package:
- `esp32 by Espressif Systems`

Install Library Manager package:
- `WiFiManager` by tzapu

## 2) Board settings (important)

- Board: `XIAO_ESP32S3`
- PSRAM: `OPI PSRAM`
- USB CDC On Boot: `Enabled`
- Upload Speed: `921600` (use `115200` if unstable)
- Partition Scheme: `default_8MB`

## 3) Flash

1. Open `security_cam_single_file.ino`
2. Upload
3. Open Serial Monitor at `115200`

## 4) First-time Wi-Fi setup (no code edits)

If the board has no saved Wi-Fi credentials:
1. Phone/laptop will see AP named like `xiao-cam-XXXXXX-setup`
2. Connect to it
3. Captive portal opens
4. Choose your Wi-Fi and enter password
5. Device reboots and connects

## 5) View camera

From Serial Monitor copy IP and hostname.
Open any of:
- `http://<ip>/`
- `http://<ip>/stream`
- `http://<ip>/capture`
- `http://<ip>/status`
- `http://<hostname>.local/stream`

## 6) Motion events

- PIR input pin: `GPIO2`
- On motion trigger, a JPG snapshot is stored in LittleFS
- Event endpoints:
  - `http://<ip>/events`
  - `http://<ip>/latest`

## 7) Change Wi-Fi later

- Open `http://<ip>/wifi-reset`
- Device erases saved credentials and reboots into setup AP mode

## 8) Notes

- This implementation saves motion snapshots, not continuous video clips.
- For person-detection and full motion clips, keep using Pi/Frigate/OpenCV pipeline.

## 9) If you see `Camera init failed: 0xffffffff`

1. Confirm **PSRAM = OPI PSRAM** in board options
2. Keep **Partition Scheme = default_8MB**
3. Re-upload and press reset once
4. Watch serial for `SPIFFS mounted` then IP output
