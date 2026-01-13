# Recording Management System - Implementation Guide

## Overview
The ME_CAM project now includes a complete recording management system with storage monitoring and file management capabilities.

## Features Added

### 1. API Endpoints

#### `/api/recordings` (GET)
- Lists all recordings in the recordings directory
- Returns JSON with:
  - `count`: Number of recordings
  - `storage_used_gb`: Total GB used
  - `recordings[]`: Array of recording objects with:
    - `name`: Filename
    - `size_mb`: File size in MB
    - `date`: Creation date (YYYY-MM-DD HH:MM:SS)
    - `timestamp`: Unix timestamp

**Example Response:**
```json
{
  "ok": true,
  "count": 3,
  "storage_used_gb": 1.25,
  "recordings": [
    {
      "name": "motion_2024-01-15_14-32-45.mp4",
      "size_mb": 45.32,
      "date": "2024-01-15 14:32:45",
      "timestamp": 1705339965
    }
  ]
}
```

#### `/api/storage` (GET)
- Returns disk space information
- Returns JSON with:
  - `used_gb`: GB used by recordings
  - `available_gb`: GB free on disk
  - `total_gb`: Total disk capacity
  - `file_count`: Total number of recording files

**Example Response:**
```json
{
  "ok": true,
  "used_gb": 1.25,
  "available_gb": 62.75,
  "total_gb": 64.00,
  "file_count": 3
}
```

#### `/api/download/<filename>` (GET)
- Downloads a specific recording file
- Security check: Prevents directory traversal attacks
- Returns file as attachment

#### `/api/delete/<filename>` (POST)
- Deletes a specific recording file
- Security check: Prevents directory traversal attacks
- Returns: `{"ok": true, "message": "Deleted <filename>"}`

#### `/api/clear-storage` (POST)
- Deletes ALL recordings
- Requires confirmation (handled by JavaScript)
- Returns: `{"ok": true, "deleted": <count>}`

### 2. Dashboard Updates

The dashboard now displays:

#### Storage Summary Section
- **Used**: GB used by recordings
- **Available**: GB free on disk
- **Total**: Total disk capacity
- **Files**: Number of recording files
- **Progress Bar**: Visual representation of disk usage

#### Recordings Table
- Sortable list of all recording files
- Shows: Filename, Size (MB), Date Created
- **Actions per File:**
  - Download button (downloads to your device)
  - Delete button (removes from Pi with confirmation)
- Refresh button to update list
- "Clear All Recordings" button to delete everything

### 3. User Interface

The recordings section features:
- Real-time storage statistics
- Responsive table layout
- Individual download buttons for each file
- Individual delete buttons with confirmation
- Bulk delete option for all files
- Automatic refresh on load
- Manual refresh capability

## How to Use

### Viewing Recordings
1. Go to Dashboard
2. Scroll to "Recordings & Storage" section
3. View storage stats and all saved recordings
4. Click "Refresh" to update the list

### Downloading Recordings
1. In Recordings & Storage section, find the file to download
2. Click the green "Download" button next to the file
3. File downloads to your device

### Deleting Recordings
1. Click the red "Delete" button next to a file
2. Confirm deletion in the popup
3. File is removed from Pi

### Clearing All Recordings
1. Click "Clear All Recordings" button at bottom
2. Confirm in the popup (this cannot be undone)
3. All recording files are deleted

## Storage Management

### Automatic Cleanup
The system does NOT automatically delete old files. Manual management is required.

### Disk Space Alerts
- Storage section shows available space
- If available space is low, consider downloading important files and deleting others

### Recording Locations
- Default: `/home/pi/ME_CAM/recordings/`
- Configured in: `config/config_default.json` under `storage.recordings_dir`

## Security Features

- All API endpoints require authentication (must be logged in)
- File paths are validated to prevent directory traversal attacks
- Delete operations require POST method (prevents accidental deletion via URL)
- Bulk delete requires JavaScript confirmation

## Backend Implementation

### Modified Files
- **web/app.py**: Added 5 new API endpoints + helper functions
- **web/templates/dashboard.html**: Added storage monitoring UI + JavaScript

### Key Functions in app.py
- `api_recordings()`: Line ~440
- `api_storage()`: Line ~473
- `download_recording()`: Line ~511
- `delete_recording()`: Line ~530
- `clear_storage()`: Line ~550

### Dependencies
- Uses `shutil.disk_usage()` for disk space monitoring
- Uses Flask's `send_file()` for downloads
- Uses standard `os` module for file operations

## Troubleshooting

### "No recordings yet" message
- This is normal if no motion was detected or no manual recordings were made
- Motion detection is currently disabled for stability
- You can manually test by creating files in the recordings directory

### Download fails
- Check file permissions on Pi
- Ensure recordings directory is readable
- Check available disk space

### Delete fails
- Ensure you have write permissions in recordings directory
- Check if file is in use by another process
- Try refreshing the page

### Storage shows 0 GB
- Recordings directory may not exist yet
- Check directory path in config.json
- Ensure directory has proper permissions

## Future Enhancements

Potential additions:
- Scheduled automatic deletion of files older than N days
- Cloud backup integration
- Recording compression before storage
- Video playback/preview in dashboard
- Motion detection re-enabled with non-blocking recording
- Storage quota alerts and warnings
