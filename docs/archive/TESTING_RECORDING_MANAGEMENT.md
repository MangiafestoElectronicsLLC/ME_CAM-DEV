# Testing Recording Management System on Pi Zero 2 W

## Prerequisites
- Pi running with ME_CAM installed
- Latest code pulled
- Web server running (`python3 main.py`)

## Test Steps

### Step 1: Start the Web Server
```bash
# On Pi
cd ~/ME_CAM
python3 main.py
```

Wait for output:
```
[INFO] Starting Flask web server...
[INFO] Web server running on http://0.0.0.0:8080
```

### Step 2: Access Dashboard
- Open browser: `http://<pi-ip>:8080`
- Login with credentials (default: U123/pass)
- Should see live camera feed working

### Step 3: Test Storage API Endpoint
- Open browser developer console (F12)
- Run in console:
```javascript
fetch('/api/storage')
  .then(r => r.json())
  .then(data => console.log(data))
```

Expected output:
```json
{
  "ok": true,
  "used_gb": 0,
  "available_gb": 62.75,
  "total_gb": 64,
  "file_count": 0
}
```

### Step 4: Test Recordings API Endpoint
Run in console:
```javascript
fetch('/api/recordings')
  .then(r => r.json())
  .then(data => console.log(data))
```

Expected output:
```json
{
  "ok": true,
  "count": 0,
  "storage_used_gb": 0,
  "recordings": []
}
```

### Step 5: Create Test Recording
To test the UI properly, create a test video file:

```bash
# On Pi, create a dummy video file in recordings directory
cd ~/ME_CAM
mkdir -p recordings
dd if=/dev/zero bs=1M count=10 of=recordings/test_video_2024-01-15_14-32-45.mp4
```

This creates a 10MB dummy file.

### Step 6: Refresh Dashboard
- Go to Dashboard page
- Scroll to "Recordings & Storage" section
- Should see:
  - Storage Used: ~0.01 GB
  - Available: ~62.75 GB
  - Total: ~64 GB
  - Files: 1
  - Table with test_video file listed

### Step 7: Test Download
- Click green "Download" button next to test file
- File should download to your computer
- Check downloads folder - file should be there

### Step 8: Test Delete
- Click red "Delete" button next to test file
- Confirm deletion
- Table should refresh and show 0 files
- Storage used should show 0 GB

### Step 9: Test Refresh Button
- Create another test file:
```bash
dd if=/dev/zero bs=1M count=5 of=~/ME_CAM/recordings/test2_2024-01-15_14-45-00.mp4
```

- Click "Refresh" button in dashboard
- New file should appear in table

### Step 10: Test Clear All
- Create multiple test files (optional):
```bash
for i in {1..3}; do
  dd if=/dev/zero bs=1M count=$((i*5)) of=~/ME_CAM/recordings/test${i}_2024-01-15_14-$((30+i))-00.mp4
done
```

- Click "Clear All Recordings" button
- Confirm in popup
- All files should be deleted
- Table should show "No recordings saved yet"

## Testing Motion Detection Recording (Future)

When motion detection is re-enabled:
1. Motion events will automatically create recordings
2. Files appear in dashboard automatically
3. Storage usage updates in real-time
4. Oldest files can be manually deleted to free space

## Common Issues

### API Returns 401 Unauthorized
- You're not logged in
- Log out and log back in

### API Returns 404
- Recordings directory doesn't exist
- Create it: `mkdir -p ~/ME_CAM/recordings`

### Storage shows 0 GB
- Check directory exists: `ls -la ~/ME_CAM/recordings`
- Check permissions: `chmod 755 ~/ME_CAM/recordings`

### Download doesn't work
- Check file exists: `ls -la ~/ME_CAM/recordings/`
- Check permissions: `chmod 644 ~/ME_CAM/recordings/*.mp4`

### Delete fails
- Check write permissions
- Try: `chmod 755 ~/ME_CAM/recordings`

## Performance Notes

### Pi Zero 2 W Expectations
- Storage API: <100ms response
- Recordings API: <500ms (depends on number of files)
- Download: Limited by network speed (typical home WiFi: 5-10 MB/s)
- Delete: <100ms per file

### Optimization Tips
- Limit number of files (avoid keeping 1000+ recordings)
- Use external storage if available
- Consider moving old files to external drive instead of deleting

## Success Indicators

✅ Dashboard loads without errors
✅ Storage section shows correct GB values
✅ Recordings table displays (empty or with files)
✅ Download button works (file transfers to computer)
✅ Delete button works (file removed from table)
✅ Refresh button updates list
✅ Clear All button removes all files
✅ API endpoints respond with correct JSON

## Next Steps

1. Test with actual motion detection recordings
2. Monitor storage usage over time
3. Set up automated backup of important recordings
4. Consider adding scheduled cleanup script

## Additional Notes

- All timestamps are in UTC (check timezone settings)
- File sizes shown in MB (mega) not MiB
- Storage bar shows percentage of total disk used
- Download preserves original filename
- Delete is permanent (no trash/recycle)
