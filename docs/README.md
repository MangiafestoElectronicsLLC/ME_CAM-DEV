# 📖 ME_CAM Documentation Index

Welcome to ME_CAM v2.0 - A professional Raspberry Pi camera surveillance system!

---

## 🎯 Start Here

**New to ME_CAM?** Read these first:

1. **[README.md](README.md)** ← Start here!
   - Project overview
   - Key features
   - Quick installation
   - Performance comparison

2. **[INSTALLATION.md](docs/INSTALL.md)**
   - Step-by-step installation
   - Hardware requirements
   - Initial configuration
   - Troubleshooting

3. **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)**
   - Quick deployment guide
   - Verification steps
   - This week's tasks
   - Common issues

---

## 📚 Complete Documentation

### For General Users
| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview & features |
| [docs/INSTALL.md](docs/INSTALL.md) | Complete installation guide |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Quick deployment & verification |

### For Performance
| Document | Purpose |
|----------|---------|
| [docs/PERFORMANCE_GUIDE.md](docs/PERFORMANCE_GUIDE.md) | How to optimize (15x faster!) |
| [PERFORMANCE_IMPROVEMENTS.md](PERFORMANCE_IMPROVEMENTS.md) | What's new in v2.0 |

### For Deployment
| Document | Purpose |
|----------|---------|
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment guide |
| [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md) | Complete project reference |

### For Understanding Changes
| Document | Purpose |
|----------|---------|
| [REORGANIZATION_SUMMARY.md](REORGANIZATION_SUMMARY.md) | What was reorganized |
| [docs/REORGANIZATION.md](docs/REORGANIZATION.md) | Detailed structure changes |

### For Development
| Document | Purpose |
|----------|---------|
| [notes.txt](notes.txt) | Developer notes & troubleshooting |
| [docs/archive/](docs/archive/) | Old documentation & reference |

---

## 🗂️ File Organization

```
ME_CAM-DEV/
├── README.md ..................... Project overview (START HERE!)
├── DEPLOYMENT_CHECKLIST.md ........ Quick deployment guide
├── REORGANIZATION_SUMMARY.md ...... What changed in v2.0
├── PERFORMANCE_IMPROVEMENTS.md .... New features
├── LICENSE ....................... MIT License
│
├── docs/
│   ├── README.md ................. Documentation index
│   ├── INSTALL.md ................ Installation guide
│   ├── DEPLOYMENT.md ............. Production deployment
│   ├── PERFORMANCE_GUIDE.md ....... Speed optimization
│   ├── PROJECT_GUIDE.md .......... Complete reference
│   ├── REORGANIZATION.md ......... Structure details
│   └── archive/ .................. Old documentation
│
├── src/                        # ALL SOURCE CODE (organized)
│   ├── core/ ..................... Configuration, auth, utilities
│   ├── camera/ ................... Camera streaming modules
│   ├── detection/ ................ Motion & AI detection
│   └── utils/ .................... Cloud, notifications
│
├── web/                       # Web Dashboard (Flask)
│   ├── app.py
│   ├── templates/
│   └── static/
│
├── config/ ....................... Configuration
├── scripts/ ....................... Setup & maintenance
├── etc/ ........................... System files
├── logs/ .......................... Application logs
└── recordings/ .................... Video storage
```

---

## ✨ Quick Reference

### Access Dashboard
```
http://raspberrypi.local:8080
```

### View Logs
```bash
# Real-time
sudo journalctl -u mecamera -f

# Application logs
tail -f logs/mecam.log
```

### Restart Service
```bash
sudo systemctl restart mecamera
```

### Update Code
```bash
cd ~/ME_CAM-DEV && git pull origin main && sudo systemctl restart mecamera
```

### Enable Fast Streaming (15x faster!)
```
Settings → Performance → ✓ Use Fast Streaming → Save
```

---

## 🚀 Performance Overview

| Feature | v1.x | v2.0 | Improvement |
|---------|------|------|-------------|
| **Streaming FPS** | 1-2 | 15-30 | **15x faster** ⚡ |
| **Frame Latency** | 850ms | 35ms | **24x faster** ⚡ |
| **CPU Usage** | 45% | 18% | **60% less** ⚡ |
| **Motion Detection** | Every 2s | Every 0.2s | **10x faster** ⚡ |
| **File Organization** | Messy (45+ files) | Clean (organized) | **Professional** ✨ |

---

## 🎯 Common Tasks

### First Time Setup
1. Read: [README.md](README.md)
2. Install: [docs/INSTALL.md](docs/INSTALL.md)
3. Deploy: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
4. Configure: Dashboard setup wizard

### Speed Up Camera
1. Read: [docs/PERFORMANCE_GUIDE.md](docs/PERFORMANCE_GUIDE.md)
2. Install: `sudo ./scripts/install_fast_camera.sh`
3. Enable: Settings → Performance → ✓ Use Fast Streaming
4. Result: 15x faster streaming! ⚡

### Setup Emergency Alerts
1. Settings → Emergency Contacts
2. Enter carrier SMS gateway
3. Configure Gmail App Password
4. Test: Click 🚨 SOS Alert button

### Monitor System
1. Logs: `sudo journalctl -u mecamera -f`
2. Dashboard: http://raspberrypi.local:8080
3. Storage: Check Dashboard → Storage section
4. Health: Check logs weekly

---

## 📞 Support

### If Something Doesn't Work

1. **Check Logs First**
   ```bash
   sudo journalctl -u mecamera -n 50
   tail -f logs/mecam.log
   ```

2. **Check Relevant Guide**
   - Can't install? → [docs/INSTALL.md](docs/INSTALL.md)
   - Slow dashboard? → [docs/PERFORMANCE_GUIDE.md](docs/PERFORMANCE_GUIDE.md)
   - Deployment issues? → [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
   - Understanding changes? → [REORGANIZATION_SUMMARY.md](REORGANIZATION_SUMMARY.md)

3. **Restart Service**
   ```bash
   sudo systemctl restart mecamera
   ```

4. **Factory Reset** (if all else fails)
   ```bash
   ./scripts/factory_reset.sh
   ```

---

## 📊 What's Inside

### Source Code (src/)
- **core/** - Configuration, authentication, battery monitoring, etc.
- **camera/** - Fast streaming (15-30 FPS), fallback streaming
- **detection/** - Motion detection, AI person detection, face recognition
- **utils/** - Cloud integration, email notifications

### Web Dashboard (web/)
- Real-time camera feed
- Motion detection & recording
- Storage management
- Emergency alerts
- User authentication
- Mobile-friendly interface

### Maintenance (scripts/)
- Initial setup
- Fast camera installation
- Factory reset
- Auto-update

---

## ✅ New in v2.0

✅ **Professional Structure** - Clean organized src/ directory  
✅ **15x Faster Streaming** - 15-30 FPS with picamera2  
✅ **Better Documentation** - 5 focused guides  
✅ **Advanced Storage** - Smart cleanup, date organization  
✅ **Cleaner Root** - 8 files (was 45+)  
✅ **Production Ready** - Systemd service, auto-start  

---

## 🎉 You're All Set!

Everything is organized and documented. 

**Next step:** Read [README.md](README.md) and deploy to your Raspberry Pi!

```bash
cd ~/ME_CAM-DEV && git pull origin main && sudo systemctl restart mecamera
```

---

**Questions?** Check the documentation or view logs:
```bash
tail -f logs/mecam.log
```

**Version**: 2.0.0  
**Updated**: January 13, 2026  
**Status**: Production Ready ✅
