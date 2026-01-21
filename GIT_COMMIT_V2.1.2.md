# ME_CAM v2.1.2 - Professional GitHub Release Guide

**Date:** January 21, 2026  
**Target Repositories:**  
- https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV (Development)
- https://github.com/MangiafestoElectronicsLLC/ME_CAM (Production)

---

## Pre-Commit Checklist

### 1. Files to Stage for Commit

#### Core Updates (Must Commit)
- [x] `INSTALL.md` - Updated for Bookworm, system packages approach
- [x] `QUICKSTART.md` - Updated with latest OS requirements
- [x] `requirements.txt` - Python 3.13 compatible versions with comments
- [x] `PI_ZERO_2W_SETUP.md` - Complete Pi Zero 2W setup with auto-detection
- [x] `DEPLOYMENT_GUIDE_COMPLETE.md` - Professional deployment guide
- [x] `PRIVATE_SETUP_NOTES.md` - Personal notes (exclude from commit!)
- [x] `PI_ZERO_AUTOBOOT_SETUP.md` - Auto-boot configuration guide
- [x] `FIX_BULLSEYE_PI_ZERO.sh` - Bullseye repo fix script
- [x] `RELEASE_NOTES_V2.1.2.md` - Detailed release notes

#### Exclude from Commit
- [ ] `PRIVATE_SETUP_NOTES.md` - Contains personal network info
- [ ] `QUICK_DEPLOY_NOW.txt` - Temporary deployment notes
- [ ] Any files with personal IP addresses or passwords

### 2. Update .gitignore

```bash
# Add to .gitignore if not already there
echo "PRIVATE_SETUP_NOTES.md" >> .gitignore
echo "QUICK_DEPLOY_NOW.txt" >> .gitignore
echo "QUICK_DEPLOY_NOW.md" >> .gitignore
```

---

## Commit Strategy

### Step 1: Clean Working Directory

```bash
cd ~/Downloads/ME_CAM-DEV/ME_CAM-DEV

# Check what's changed
git status

# Verify no sensitive files
git diff --name-only
```

### Step 2: Stage Files for Commit

```bash
# Add documentation updates
git add INSTALL.md
git add QUICKSTART.md
git add requirements.txt
git add PI_ZERO_2W_SETUP.md
git add DEPLOYMENT_GUIDE_COMPLETE.md
git add PI_ZERO_AUTOBOOT_SETUP.md
git add FIX_BULLSEYE_PI_ZERO.sh
git add RELEASE_NOTES_V2.1.2.md
git add CHANGELOG.md

# Add updated .gitignore
git add .gitignore

# Verify what's staged
git status
```

### Step 3: Create Professional Commit

```bash
git commit -m "v2.1.2: Pi Zero 2W Optimization & Bookworm Migration

🎯 Major Updates:
- Complete Bookworm OS migration (Bullseye deprecated)
- Pi Zero 2W optimization with system packages approach
- Auto-detection for Pi Zero/3/4/5 hardware
- Hardware-based mode selection (lite vs regular)

📚 Documentation Overhaul:
- Updated INSTALL.md with Bookworm requirements
- New PI_ZERO_2W_SETUP.md with flash-to-boot guide
- Added DEPLOYMENT_GUIDE_COMPLETE.md for professional setup
- New PI_ZERO_AUTOBOOT_SETUP.md for systemd configuration
- Updated QUICKSTART.md with latest OS warnings

🐛 Critical Fixes:
- Fixed Bullseye archived repos issue (FIX_BULLSEYE_PI_ZERO.sh)
- System packages approach eliminates 30+ min numpy compilation
- Python 3.13 compatible package versions in requirements.txt
- Added --system-site-packages flag for venv creation

⚡ Performance:
- Instant installation with pre-compiled system packages
- Reduced setup time from 60+ minutes to 15 minutes on Pi Zero 2W
- Smart launcher script auto-detects Pi model
- Optimized for 512MB RAM (Pi Zero 2W)

🔧 Technical Changes:
- requirements.txt: Updated to Flask 3.0.0, numpy 2.0.0 compatible
- Installation now uses python3-numpy, python3-pil, python3-opencv
- Added hardware detection startup script (start_mecam.sh)
- Systemd service configuration for auto-boot

📖 New Files:
- PI_ZERO_2W_SETUP.md: Complete setup guide with Raspberry Pi Imager steps
- DEPLOYMENT_GUIDE_COMPLETE.md: Professional deployment documentation
- PI_ZERO_AUTOBOOT_SETUP.md: Auto-boot configuration guide
- FIX_BULLSEYE_PI_ZERO.sh: Automated Bullseye repo fix script
- RELEASE_NOTES_V2.1.2.md: Comprehensive release documentation

🔒 Security:
- Updated .gitignore to exclude personal setup notes
- No credentials or personal network info in commits

✅ Tested On:
- Raspberry Pi Zero 2W (512MB RAM) with IMX708 camera
- Raspberry Pi OS Bookworm 64-bit (Latest)
- Python 3.13

Breaking Changes:
- Bullseye OS no longer supported (use Bookworm)
- Must install system packages before pip packages
- Requires --system-site-packages flag for venv"
```

### Step 4: Create Git Tag

```bash
# Create annotated tag
git tag -a v2.1.2 -m "ME_CAM v2.1.2 - Pi Zero 2W Optimization

Major release focusing on:
- Bookworm OS migration
- Pi Zero 2W performance optimization
- System packages installation approach
- Comprehensive setup documentation
- Hardware auto-detection"

# Verify tag
git tag -l -n5 v2.1.2
```

### Step 5: Push to GitHub

```bash
# Push commits
git push origin main

# Push tags
git push origin v2.1.2
```

---

## Creating GitHub Release

### Navigate to Repository
1. Go to https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV
2. Click "Releases" → "Draft a new release"

### Release Configuration

**Tag:** `v2.1.2`  
**Release Title:** `v2.1.2 - Pi Zero 2W Optimization & Bookworm Migration`

**Description:**

````markdown
# ME_CAM v2.1.2 - Pi Zero 2W Optimization & Bookworm Migration

**Release Date:** January 21, 2026  
**Status:** ✅ Production Ready  
**Target Platform:** Raspberry Pi Zero 2W, Pi 3/4/5  
**OS Required:** Raspberry Pi OS Bookworm 64-bit (Latest)

---

## 🎯 What's New

### Major Updates

✨ **Complete Bookworm OS Migration**
- Bullseye repos archived (January 2026) - no longer supported
- Full migration to Raspberry Pi OS Bookworm 64-bit
- Python 3.13 compatibility
- Updated all dependencies for modern OS

✨ **Pi Zero 2W Optimization**
- System packages approach eliminates 30+ minute numpy compilation
- Installation time reduced from 60+ minutes to 15 minutes
- Optimized for 512MB RAM constraints
- Hardware auto-detection chooses correct mode (lite vs regular)

✨ **Smart Hardware Detection**
- Auto-detects Pi model on boot (Zero 2W, Pi 3/4/5)
- Automatically launches correct mode (lite or regular)
- Single startup script works across all Pi models
- No manual configuration needed

### Documentation Overhaul

📚 **New Setup Guides:**
- `PI_ZERO_2W_SETUP.md` - Complete flash-to-boot guide with Raspberry Pi Imager steps
- `DEPLOYMENT_GUIDE_COMPLETE.md` - Professional deployment documentation
- `PI_ZERO_AUTOBOOT_SETUP.md` - Systemd auto-boot configuration
- `FIX_BULLSEYE_PI_ZERO.sh` - Automated Bullseye repo fix (for legacy systems)

📚 **Updated Documentation:**
- `INSTALL.md` - Completely rewritten for Bookworm
- `QUICKSTART.md` - Updated with OS requirements and warnings
- `requirements.txt` - Python 3.13 compatible packages with installation notes

---

## 🚀 Quick Start

### For New Installations (Recommended)

```bash
# 1. Flash Raspberry Pi OS Bookworm 64-bit using Raspberry Pi Imager
# 2. SSH into Pi
ssh pi@mecamera.local

# 3. One-command installation
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-dev build-essential \
  python3-numpy python3-pil python3-opencv \
  python3-picamera2 libcamera-apps

cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV

python3 -m venv venv --system-site-packages
source venv/bin/activate

pip install Flask==3.0.0 Werkzeug==3.0.0 cryptography==41.0.0 \
  qrcode[pil]==7.4.2 psutil==5.9.5 yagmail==0.15.293 \
  pydrive2==1.19.0 loguru==0.7.2

# 4. Test
python main_lite.py  # For Pi Zero 2W
# Or
python main.py  # For Pi 3/4/5

# 5. Access dashboard
# http://[your-pi-ip]:8080
```

**Total time:** ~15 minutes on Pi Zero 2W

---

## 🐛 Bug Fixes

### Critical Fixes
- ✅ Fixed Bullseye archived repos issue (January 2026)
- ✅ Eliminated numpy/Pillow compilation hanging on Pi Zero 2W
- ✅ Fixed Python 3.13 compatibility issues
- ✅ Resolved git missing in Bookworm Lite

### Installation Fixes
- ✅ System packages approach for instant installation
- ✅ `--system-site-packages` flag prevents import errors
- ✅ Proper venv configuration for system libraries access

---

## ⚡ Performance Improvements

| Metric | Before (Bullseye) | After (Bookworm) |
|--------|-------------------|------------------|
| **numpy install** | 30+ minutes (compile) | Instant (system pkg) |
| **Pillow install** | 20+ minutes (compile) | Instant (system pkg) |
| **opencv install** | 60+ minutes (compile) | Instant (system pkg) |
| **Total setup time** | 60-90 minutes | 15 minutes |
| **Python version** | 3.9 (old) | 3.13 (modern) |

---

## 🔧 Technical Changes

### Package Updates
- Flask: `2.2.5` → `3.0.0`
- Werkzeug: `2.2.3` → `3.0.0`
- cryptography: `39.0.0` → `41.0.0`
- numpy: `1.19.5` → `2.0.0` (via system package)
- Pillow: `9.5.0` → `10.0.0` (via system package)

### New Features
- Hardware detection startup script (`start_mecam.sh`)
- Systemd service templates for auto-boot
- Raspberry Pi Imager configuration examples
- Comprehensive troubleshooting guides

---

## 📋 Breaking Changes

⚠️ **OS Requirement:**
- Bullseye is **no longer supported** (repos archived)
- Must use **Raspberry Pi OS Bookworm 64-bit** (Latest)
- Re-flash required if using Bullseye

⚠️ **Installation Process:**
- Must install system packages **before** pip packages
- Must use `--system-site-packages` flag when creating venv
- Cannot skip system package installation step

---

## 📖 Documentation

See the following guides for detailed instructions:

- **New Users:** Start with `QUICKSTART.md`
- **Pi Zero 2W:** See `PI_ZERO_2W_SETUP.md`
- **Detailed Setup:** See `DEPLOYMENT_GUIDE_COMPLETE.md`
- **Auto-Boot:** See `PI_ZERO_AUTOBOOT_SETUP.md`
- **Troubleshooting:** All guides include troubleshooting sections

---

## ✅ Tested Configurations

- ✅ Raspberry Pi Zero 2W (512MB RAM) with IMX708 camera
- ✅ Raspberry Pi OS Bookworm 64-bit (Latest - January 2026)
- ✅ Python 3.13
- ✅ Flask 3.0.0
- ✅ System packages: numpy, opencv, Pillow

---

## 🔒 Security Notes

- No credentials or personal information in source code
- `.gitignore` updated to exclude sensitive files
- SSL/TLS support maintained
- User authentication system functional

---

## 📦 Installation Methods

### Method 1: Fresh Installation (Recommended)
1. Flash latest Bookworm OS
2. Follow `PI_ZERO_2W_SETUP.md`
3. One-command installation
4. 15-minute setup time

### Method 2: Existing Bullseye System (Not Recommended)
1. Run `FIX_BULLSEYE_PI_ZERO.sh` to update repos
2. Follow updated `INSTALL.md`
3. **Note:** Better to re-flash with Bookworm

---

## 🙏 Acknowledgments

Thanks to all testers and users who reported Bullseye installation issues!

---

## 📞 Support

- **Issues:** https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/issues
- **Wiki:** https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/wiki
- **Discussions:** https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/discussions

---

## License

See [LICENSE](LICENSE) file for details.
````

### Attach Files (Optional)
- Release notes PDF
- Installation script
- Configuration templates

### Click "Publish Release"

---

## Updating ME_CAM Repository (Production)

### 1. Sync Changes to Production Repo

```bash
# Clone production repo (if not already cloned)
cd ~/Downloads
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM.git
cd ME_CAM

# Copy updated files from ME_CAM-DEV
cp ../ME_CAM-DEV/ME_CAM-DEV/INSTALL.md .
cp ../ME_CAM-DEV/ME_CAM-DEV/QUICKSTART.md .
cp ../ME_CAM-DEV/ME_CAM-DEV/requirements.txt .
cp ../ME_CAM-DEV/ME_CAM-DEV/PI_ZERO_2W_SETUP.md .
cp ../ME_CAM-DEV/ME_CAM-DEV/DEPLOYMENT_GUIDE_COMPLETE.md .
cp ../ME_CAM-DEV/ME_CAM-DEV/RELEASE_NOTES_V2.1.2.md .

# Stage and commit
git add .
git commit -m "v2.1.2: Documentation updates for Bookworm migration

Synced documentation from ME_CAM-DEV:
- Updated INSTALL.md for Bookworm OS
- Updated QUICKSTART.md with OS requirements
- Updated requirements.txt with Python 3.13 packages
- Added PI_ZERO_2W_SETUP.md
- Added DEPLOYMENT_GUIDE_COMPLETE.md
- Added RELEASE_NOTES_V2.1.2.md

See ME_CAM-DEV v2.1.2 release for full details."

# Tag and push
git tag -a v2.1.2 -m "v2.1.2 - Documentation updates"
git push origin main
git push origin v2.1.2
```

### 2. Update README.md in ME_CAM

Add prominent notice at top of README:

```markdown
## ⚠️ IMPORTANT - OS Requirement

**Use Raspberry Pi OS Bookworm 64-bit (Latest) - NOT Bullseye**

Bullseye repositories were archived in January 2026 and are no longer supported.

See [INSTALL.md](INSTALL.md) for updated installation instructions.
```

---

## Post-Release Checklist

- [ ] Verify release appears on GitHub
- [ ] Test fresh installation from release
- [ ] Update project wiki (if exists)
- [ ] Announce release in discussions/forum
- [ ] Update any external documentation links
- [ ] Close related issues
- [ ] Update project board/milestones

---

## Rollback Plan (if needed)

```bash
# Revert to previous version
git revert HEAD
git push origin main

# Or delete tag
git tag -d v2.1.2
git push origin :refs/tags/v2.1.2
```

---

## Notes

- This is a **documentation-heavy** release
- No breaking code changes to core application
- Focus is on installation process improvements
- Targets Pi Zero 2W users specifically
- Addresses major pain point (Bullseye repo issues)
