# GitHub Install Guide

This path is for running the ME_CAM runtime directly on Raspberry Pi hardware from this repository.

## 1. Prepare the device

- Flash a fresh Raspberry Pi OS Lite 32-bit image when targeting Pi Zero 2W
- Boot the device, enable SSH, and connect it to your network
- Update the system packages

```bash
sudo apt update
sudo apt upgrade -y
```

## 2. Install base tooling

```bash
sudo apt install -y git python3-venv
```

If camera packages are available for your image, install them through apt rather than pip.

## 3. Clone the repository

```bash
cd /home/pi
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
```

## 4. Create configuration

```bash
cp config/config_default.json config/config.json
```

Edit `config/config.json` for your device name, storage behavior, and feature flags.

## 5. Install Python dependencies

Recommended for Pi deployments:

```bash
python3 -m venv --system-site-packages venv
. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

For Pi Zero 2W or constrained devices, prefer the lite installation path when suitable:

```bash
sudo bash scripts/install_lite_mode.sh
```

## 6. Install the service

```bash
sudo cp etc/systemd/system/mecamera.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mecamera
```

## 7. Verify the runtime

```bash
sudo systemctl status mecamera
curl http://127.0.0.1:8080/api/status
curl http://127.0.0.1:8080/api/health
```

## 8. Secure the deployment

- Change or create credentials before exposing the device to any shared network
- Rotate enrollment keys if you are using hosted onboarding flows
- Keep reverse proxy or HTTPS configuration outside the repo-specific defaults
- Remove local test artifacts before committing or tagging a release

## 9. Troubleshooting baseline

- If apt is corrupted on the device, reflash rather than layering fixes on a broken image
- If camera packages are missing, verify you are on the recommended Raspberry Pi OS Lite path
- If Pi Zero 2W performance is poor, stay on the lite runtime and avoid optional V3 modules
