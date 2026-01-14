"""Motion activity logging system with timestamps and event history"""
import json
import os
from datetime import datetime, timedelta
from threading import RLock
from loguru import logger

MOTION_LOG_FILE = "logs/motion_events.json"
_lock = RLock()


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


def log_motion_event(event_type="motion", confidence=0.0, details=None):
    """
    Log a motion detection event with timestamp
    
    Args:
        event_type: "motion", "person", "face", "intrusion", "security_alert"
        confidence: detection confidence (0.0-1.0)
        details: dict with additional info (location, duration, thumbnail, etc)
    """
    with _lock:
        try:
            events = load_motion_events()
            
            # Limit to last 1000 events to avoid huge files
            if len(events) > 1000:
                events = events[-1000:]
            
            event = {
                "timestamp": datetime.now().isoformat(),
                "unix_timestamp": datetime.now().timestamp(),
                "type": event_type,
                "confidence": round(confidence, 3),
                "details": details or {}
            }
            
            events.append(event)
            save_motion_events(events)
            
            logger.info(f"[MOTION_LOG] Event logged: {event_type} ({confidence:.2%}) at {event['timestamp']}")
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
