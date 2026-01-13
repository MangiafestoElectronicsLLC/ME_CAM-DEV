# Recording Management - Quick Start Guide

## What's New?
Your ME_CAM dashboard now has a complete **Recording Management System** that lets you:
- 📊 See how much storage you're using
- 📁 View all saved recordings
- ⬇️ Download recordings to your computer
- 🗑️ Delete recordings to free up space
- 📈 Monitor available disk space

## Quick Steps

### 1. Start the App
```bash
cd ~/ME_CAM
python3 main.py
```

### 2. Open Dashboard
- Go to: `http://<pi-ip>:8080`
- Login (default: U123/pass)

### 3. Find Recordings Section
- Scroll down on dashboard
- Look for: **"📹 Recordings & Storage"**

### 4. View Storage Stats
You'll see:
- **Used**: GB used by recordings
- **Available**: GB free on disk  
- **Total**: Total disk size
- **Files**: Number of recordings

### 5. Manage Recordings
**Download a file:**
1. Find file in table
2. Click green **⬇️ Download** button
3. File saves to your computer

**Delete a file:**
1. Click red **🗑️ Delete** button
2. Confirm deletion
3. File removed from Pi

**Clear all recordings:**
1. Click **🗑️ Clear All Recordings**
2. Confirm (this cannot be undone!)
3. All files deleted

## API Endpoints (Advanced)

If using API directly:

```bash
# Get storage info
curl -H "Authorization: Basic ..." http://<pi-ip>:8080/api/storage

# List recordings
curl -H "Authorization: Basic ..." http://<pi-ip>:8080/api/recordings

# Download file
curl -O http://<pi-ip>:8080/api/download/filename.mp4

# Delete file
curl -X POST http://<pi-ip>:8080/api/delete/filename.mp4
```

## Frequently Asked Questions

**Q: Where are the recordings stored?**
A: `/home/pi/ME_CAM/recordings/` by default. Configured in `config.json`

**Q: Can I recover deleted files?**
A: No, deletion is permanent. Download before deleting if needed.

**Q: Why don't I see any recordings?**
A: Motion detection is currently disabled. Create test files or re-enable motion detection.

**Q: How do I free up space?**
A: Use the Delete buttons to remove old recordings, or Clear All to delete everything.

**Q: Does this work on my phone?**
A: Yes! Dashboard is fully responsive on mobile/tablet.

**Q: Can I download to a USB drive?**
A: Download to computer first, then move to USB. Or use SSH: `scp filename pi@<ip>:/media/usb/`

**Q: What file formats are supported?**
A: MP4, MOV, AVI, MKV (others show but may not download properly)

**Q: Will my files be automatically deleted?**
A: No, you must delete manually. Consider adding cron job for automatic cleanup.

## Performance Tips

- **Slow dashboard load?**
  - Delete old recordings
  - Avoid storing 1000+ files
  - Use faster SD card (Class 10 or better)

- **Slow downloads?**
  - Check WiFi connection quality
  - Use 5GHz band if available
  - Close other network activities

- **Full storage?**
  - Delete old recordings
  - Check disk usage: `df -h`
  - Move files to external storage

## Creating Test Files (for testing)

```bash
# Create a 10MB test video
dd if=/dev/zero bs=1M count=10 of=~/ME_CAM/recordings/test_2024-01-15_14-32-45.mp4

# Create multiple test files
for i in {1..5}; do
  dd if=/dev/zero bs=1M count=$((i*5)) of=~/ME_CAM/recordings/test${i}_2024-01-15_14-$((30+i))-00.mp4
done

# Clean up test files
rm ~/ME_CAM/recordings/test*.mp4
```

## Common Issues

| Issue | Solution |
|-------|----------|
| No recordings appear | Motion detection disabled, create test files or re-enable motion detection |
| Storage shows 0 GB | Check recordings directory exists: `mkdir -p ~/ME_CAM/recordings` |
| Download fails | Check file permissions: `chmod 644 ~/ME_CAM/recordings/*.mp4` |
| Delete fails | Check write permissions: `chmod 755 ~/ME_CAM/recordings` |
| Dashboard slow | Too many files, delete old ones to speed up listing |
| API returns 401 | You're not logged in, log in first |

## Useful Commands

```bash
# List all recordings
ls -lh ~/ME_CAM/recordings/

# Show disk usage
df -h ~/ME_CAM

# Check storage space
du -sh ~/ME_CAM/recordings/

# Delete all recordings (command line)
rm ~/ME_CAM/recordings/*

# Find largest files
find ~/ME_CAM/recordings/ -type f -exec du -h {} + | sort -rh | head -10

# Set directory permissions
chmod 755 ~/ME_CAM/recordings
chmod 644 ~/ME_CAM/recordings/*.mp4
```

## Advanced: Auto-Delete Old Files

Create a cleanup script:
```bash
#!/bin/bash
# Delete recordings older than 7 days
find ~/ME_CAM/recordings/ -type f -mtime +7 -delete
echo "Deleted recordings older than 7 days"
```

Save as `cleanup.sh`, make executable: `chmod +x cleanup.sh`

Add to cron (runs daily at 2 AM):
```bash
crontab -e
# Add line: 0 2 * * * ~/ME_CAM/cleanup.sh
```

## Files You'll Need

- **web/app.py** - Flask app with new API endpoints
- **web/templates/dashboard.html** - Dashboard with recording UI
- **web/static/style.css** - Styling (no changes needed)
- **config/config_default.json** - Settings (no changes needed)

## Documentation Files

Detailed guides are available:
- `RECORDING_MANAGEMENT_README.md` - Full user guide
- `TESTING_RECORDING_MANAGEMENT.md` - Testing instructions
- `RECORDING_MANAGEMENT_IMPLEMENTATION.md` - Technical details
- `CHANGES_SUMMARY.md` - Code changes overview

## Support

If something doesn't work:
1. Check web server is running: `python3 main.py`
2. View logs: Last output from `python3 main.py`
3. Check permissions: `ls -l ~/ME_CAM/recordings/`
4. Verify disk space: `df -h`
5. Try refresh: Reload dashboard in browser (F5)

## Next: Motion Detection

Once recording management is working, you can:
1. Re-enable motion detection service
2. Recordings auto-save on motion events
3. Use deletion UI to clean up old files
4. Monitor storage usage

## Summary

✅ Recording management system complete
✅ Dashboard shows storage stats
✅ Download/delete functionality ready
✅ All security checks in place
✅ Works on Pi Zero 2 W

Your ME_CAM system now has full recording management capabilities!
