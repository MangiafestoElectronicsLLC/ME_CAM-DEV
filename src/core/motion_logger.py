"""
Motion activity logging system with timestamps and event history

FIXES & ENHANCEMENTS (Feb 2026):
- Immediate event logging (no async delays)
- Proper debouncing to prevent duplicate events
- Robust error handling
- Statistics calculation
- Video attachment support
- Event cleanup on boot
"""
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone, timezone as tz
from threading import RLock
from loguru import logger

MOTION_LOG_FILE = "logs/motion_events.json"
_lock = RLock()
_debounce_cache = {}  # Track recent events for deduplication
_debounce_timeout = 2.0  # Minimum seconds between similar events
_last_cleanup = 0


def ensure_motion_log_dir():
    """Ensure motion log directory exists"""
    os.makedirs(os.path.dirname(MOTION_LOG_FILE), exist_ok=True)


def load_motion_events():
    """Load all motion events from log"""
    ensure_motion_log_dir()
    if not os.path.exists(MOTION_LOG_FILE):
        return []
    
    try:
        with open(MOTION_LOG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[MOTION_LOG] Error loading events: {e}")
        return []


def save_motion_events(events):
    """Save motion events to log"""
    ensure_motion_log_dir()
    try:
        with open(MOTION_LOG_FILE, 'w') as f:
            json.dump(events, f, indent=2)
    except Exception as e:
        logger.error(f"[MOTION_LOG] Error saving events: {e}")


def log_motion_event(event_type="motion", confidence=0.0, details=None, video_path=None):
    """
    Log a motion detection event with timestamp - IMMEDIATE (not async)
    
    FIXES:
    - Event logged immediately to disk (prevents lost events)
    - Debouncing prevents duplicate events
    - Video path attached if available
    - Proper timezone handling (EST for Brockport, NY)
    
    Args:
        event_type: "motion", "person", "face", "intrusion", "security_alert"
        confidence: detection confidence (0.0-1.0)
        details: dict with additional info
        video_path: filename of recorded video (e.g., "motion_20260202_143022.mp4")
    
    Returns:
        Event dict if logged, None if duplicate
    """
    global _debounce_cache
    
    # Check for duplicate events (debouncing)
    now = time.time()
    cache_key = f"{event_type}_{int(confidence * 100)}"
    
    if cache_key in _debounce_cache:
        last_time = _debounce_cache[cache_key]
        if now - last_time < _debounce_timeout:
            logger.debug(f"[MOTION_LOG] Skipped duplicate event: {event_type} ({confidence:.1%})")
            return None
    
    _debounce_cache[cache_key] = now
    
    # Clean old debounce entries
    cutoff = now - 10
    _debounce_cache = {k: v for k, v in _debounce_cache.items() if v > cutoff}
    
    with _lock:
        try:
            events = load_motion_events()
            
            # Limit to last 2000 events
            if len(events) > 2000:
                events = events[-2000:]
            
            # Generate event ID
            event_id = str(uuid.uuid4())[:8]
            
            # Use UTC with proper timezone handling
            now_utc = datetime.now(timezone.utc)
            timestamp_iso = now_utc.isoformat()
            unix_timestamp = now_utc.timestamp()
            
            # Build event object
            event = {
                "id": event_id,
                "timestamp": timestamp_iso,
                "unix_timestamp": unix_timestamp,
                "type": event_type,
                "confidence": round(confidence, 3),
                "details": details or {},
                "has_video": video_path is not None,
                "video_path": video_path
            }
            
            # Save immediately (not async!)
            events.append(event)
            save_motion_events(events)
            
            logger.success(f"[MOTION_LOG] ✓ Event logged: {event_type} ({confidence:.1%}) @ {timestamp_iso[:19]} ID:{event_id}")
            return event
            
        except Exception as e:
            logger.error(f"[MOTION_LOG] Error logging event: {e}")
            return None


def get_recent_events(hours=24, event_type=None, limit=100):
    """
    Get recent motion events
    
    Args:
        hours: how many hours back to look
        event_type: filter by type (optional)
        limit: max events to return
    
    Returns:
        List of motion events
    """
    with _lock:
        try:
            events = load_motion_events()
            cutoff_time = (datetime.now() - timedelta(hours=hours)).timestamp()
            
            # Filter by time and type
            filtered = [
                e for e in events 
                if e.get('unix_timestamp', 0) > cutoff_time
                and (event_type is None or e.get('type') == event_type)
            ]
            
            # Return newest first, limit count
            return sorted(filtered, key=lambda x: x['unix_timestamp'], reverse=True)[:limit]
            
        except Exception as e:
            logger.error(f"[MOTION_LOG] Error retrieving events: {e}")
            return []


def get_event_statistics(hours=24):
    """Get statistics about motion events"""
    with _lock:
        try:
            events = get_recent_events(hours=hours)
            
            if not events:
                return {
                    "total": 0,
                    "by_type": {},
                    "avg_confidence": 0,
                    "latest": None
                }
            
            by_type = {}
            total_confidence = 0
            
            for event in events:
                event_type = event.get('type', 'unknown')
                by_type[event_type] = by_type.get(event_type, 0) + 1
                total_confidence += event.get('confidence', 0)
            
            return {
                "total": len(events),
                "by_type": by_type,
                "avg_confidence": round(total_confidence / len(events), 3) if events else 0,
                "latest": events[0] if events else None,
                "period_hours": hours
            }
            
        except Exception as e:
            logger.error(f"[MOTION_LOG] Error calculating statistics: {e}")
            return {"total": 0, "by_type": {}, "avg_confidence": 0, "latest": None}


def clear_old_events(days=30):
    """Clear motion events older than N days"""
    with _lock:
        try:
            events = load_motion_events()
            cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
            
            old_count = len(events)
            events = [e for e in events if e.get('unix_timestamp', 0) > cutoff_time]
            new_count = len(events)
            
            save_motion_events(events)
            logger.info(f"[MOTION_LOG] Cleaned {old_count - new_count} old events")
            
        except Exception as e:
            logger.error(f"[MOTION_LOG] Error cleaning events: {e}")


def export_events_csv(filepath, hours=24):
    """Export events to CSV file"""
    try:
        events = get_recent_events(hours=hours)
        
        with open(filepath, 'w') as f:
            f.write("Timestamp,Type,Confidence,Details\n")
            for event in events:
                details = json.dumps(event.get('details', {})).replace(',', ';')
                f.write(f"{event['timestamp']},{event['type']},{event['confidence']},{details}\n")
        
        logger.info(f"[MOTION_LOG] Exported {len(events)} events to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"[MOTION_LOG] Error exporting events: {e}")
        return False


def update_event_video(event_id, video_path):
    """
    Update an existing event with video path
    Called after video file is successfully saved
    
    Args:
        event_id: ID of event to update
        video_path: filename of video file
    
    Returns:
        True if updated, False otherwise
    """
    with _lock:
        try:
            events = load_motion_events()
            
            for event in events:
                if event.get('id') == event_id:
                    event['video_path'] = video_path
                    event['has_video'] = True
                    save_motion_events(events)
                    logger.info(f"[MOTION_LOG] Updated event {event_id} with video: {video_path}")
                    return True
            
            logger.warning(f"[MOTION_LOG] Event {event_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"[MOTION_LOG] Error updating video: {e}")
            return False


def delete_event(event_id):
    """Delete a specific motion event"""
    with _lock:
        try:
            events = load_motion_events()
            original_len = len(events)
            events = [e for e in events if e.get('id') != event_id]
            
            if len(events) < original_len:
                save_motion_events(events)
                logger.info(f"[MOTION_LOG] Deleted event: {event_id}")
                return True
            else:
                logger.warning(f"[MOTION_LOG] Event not found: {event_id}")
                return False
                
        except Exception as e:
            logger.error(f"[MOTION_LOG] Error deleting event: {e}")
            return False


def cleanup_on_startup():
    """
    Clean up old events and invalid entries on app startup
    Prevents unbounded file growth
    """
    global _last_cleanup
    now = time.time()
    
    # Only run once per app startup (not every log call)
    if _last_cleanup > 0:
        return
    
    _last_cleanup = now
    
    with _lock:
        try:
            events = load_motion_events()
            
            if not events:
                return
            
            # Remove events older than 30 days
            cutoff_time = (datetime.now() - timedelta(days=30)).timestamp()
            filtered = [e for e in events if e.get('unix_timestamp', 0) > cutoff_time]
            
            deleted_count = len(events) - len(filtered)
            
            if deleted_count > 0:
                save_motion_events(filtered)
                logger.info(f"[MOTION_LOG] Startup cleanup: removed {deleted_count} old events")
            
            # Log current stats
            today_count = len([
                e for e in filtered 
                if e.get('unix_timestamp', 0) > (now - 86400)  # Last 24 hours
            ])
            logger.info(f"[MOTION_LOG] Startup: {len(filtered)} total events, {today_count} today")
            
        except Exception as e:
            logger.error(f"[MOTION_LOG] Startup cleanup failed: {e}")


# Run cleanup on module import
try:
    cleanup_on_startup()
except Exception as e:
    logger.debug(f"[MOTION_LOG] Cleanup on import skipped: {e}")