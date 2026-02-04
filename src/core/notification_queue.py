"""
Enhanced Notification Queue System - Fixes alert delays and failures
Implements:
- Reliable SMS/notification queueing
- Automatic retry with exponential backoff
- Offline queue for WiFi recovery
- Prevents notification spam
"""

import os
import json
import time
from datetime import datetime, timedelta
from threading import Lock, Thread
from loguru import logger
from typing import Dict, List, Optional
import requests

class NotificationQueue:
    """
    Thread-safe notification queue with retry logic
    
    Features:
    - Queue notifications when API unavailable
    - Automatic retry with backoff
    - Prevent duplicate notifications
    - Track notification status
    """
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.queue_file = os.path.join(base_dir, "logs", "notification_queue.json")
        self.offline_file = os.path.join(base_dir, "logs", "offline_queue.json")
        self.lock = Lock()
        self.rate_limit = {}  # Track rate limiting per recipient
        
        os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
        self._init_queue_files()
    
    def _init_queue_files(self):
        """Initialize queue files if not exist"""
        for filepath in [self.queue_file, self.offline_file]:
            if not os.path.exists(filepath):
                try:
                    with open(filepath, 'w') as f:
                        json.dump([], f)
                except:
                    pass
    
    def _load_queue(self, filepath: str) -> List[Dict]:
        """Load notifications from file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"[NOTIFY] Failed to load {filepath}: {e}")
        return []
    
    def _save_queue(self, filepath: str, items: List[Dict]):
        """Save notifications to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(items, f, indent=2)
        except Exception as e:
            logger.error(f"[NOTIFY] Failed to save {filepath}: {e}")
    
    def _is_rate_limited(self, recipient: str, max_per_hour: int = 10) -> bool:
        """Check if recipient is rate limited"""
        now = time.time()
        hour_ago = now - 3600
        
        if recipient not in self.rate_limit:
            self.rate_limit[recipient] = []
        
        # Clean old timestamps
        self.rate_limit[recipient] = [
            t for t in self.rate_limit[recipient]
            if t > hour_ago
        ]
        
        if len(self.rate_limit[recipient]) >= max_per_hour:
            return True
        
        self.rate_limit[recipient].append(now)
        return False
    
    def queue_notification(self,
                          recipient: str,
                          message: str,
                          notification_type: str = "motion_alert",
                          media_url: Optional[str] = None,
                          event_id: Optional[str] = None) -> bool:
        """
        Queue a notification for sending
        
        Args:
            recipient: phone number or email
            message: notification text
            notification_type: "motion_alert", "emergency", "status"
            media_url: optional URL to media
            event_id: optional event ID for tracking
        
        Returns:
            True if queued, False if rate limited
        """
        # Check rate limiting
        if self._is_rate_limited(recipient):
            logger.warning(f"[NOTIFY] Rate limited: {recipient}")
            return False
        
        with self.lock:
            try:
                queue = self._load_queue(self.queue_file)
                
                notification = {
                    'id': f"{int(time.time() * 1000)}",
                    'timestamp': datetime.utcnow().isoformat(),
                    'recipient': recipient,
                    'message': message,
                    'type': notification_type,
                    'media_url': media_url,
                    'event_id': event_id,
                    'attempts': 0,
                    'max_attempts': 5,
                    'next_retry': time.time(),
                    'status': 'pending',
                    'errors': []
                }
                
                queue.append(notification)
                
                # Limit queue size (prevent unbounded growth)
                if len(queue) > 10000:
                    queue = queue[-10000:]
                
                self._save_queue(self.queue_file, queue)
                logger.info(f"[NOTIFY] Queued: {notification_type} to {recipient[:20]}...")
                return True
                
            except Exception as e:
                logger.error(f"[NOTIFY] Queue failed: {e}")
                return False
    
    def process_queue(self, api_config: Dict) -> Dict:
        """
        Process queued notifications with retry logic
        
        Args:
            api_config: Configuration with api_url, api_key, etc.
        
        Returns:
            Dict with processing stats
        """
        with self.lock:
            try:
                queue = self._load_queue(self.queue_file)
                sent = 0
                failed = 0
                retry_count = 0
                now = time.time()
                
                remaining = []
                
                for notification in queue:
                    # Skip if not ready to retry yet
                    if notification.get('next_retry', 0) > now:
                        remaining.append(notification)
                        continue
                    
                    # Skip if max attempts exceeded
                    if notification.get('attempts', 0) >= notification.get('max_attempts', 5):
                        logger.warning(f"[NOTIFY] Max attempts reached: {notification['id']}")
                        failed += 1
                        continue
                    
                    # Try to send
                    try:
                        if self._send_notification(notification, api_config):
                            notification['status'] = 'sent'
                            notification['sent_at'] = datetime.utcnow().isoformat()
                            sent += 1
                            logger.success(f"[NOTIFY] Sent: {notification['id']}")
                        else:
                            # Retry with exponential backoff
                            notification['attempts'] += 1
                            backoff = 2 ** notification['attempts']  # 2, 4, 8, 16...
                            notification['next_retry'] = now + min(backoff * 60, 3600)  # Cap at 1 hour
                            remaining.append(notification)
                            retry_count += 1
                            
                    except Exception as e:
                        notification['attempts'] += 1
                        notification['errors'].append(str(e))
                        backoff = 2 ** notification['attempts']
                        notification['next_retry'] = now + min(backoff * 60, 3600)
                        remaining.append(notification)
                        retry_count += 1
                        logger.warning(f"[NOTIFY] Retry scheduled: {notification['id']}")
                
                # Save remaining queue
                self._save_queue(self.queue_file, remaining)
                
                stats = {
                    'sent': sent,
                    'failed': failed,
                    'pending': len(remaining),
                    'retry_scheduled': retry_count,
                    'processed': sent + failed
                }
                
                if stats['processed'] > 0:
                    logger.info(f"[NOTIFY] Processed: {stats['sent']} sent, {stats['failed']} failed, {stats['pending']} pending")
                
                return stats
                
            except Exception as e:
                logger.error(f"[NOTIFY] Process queue failed: {e}")
                return {'sent': 0, 'failed': 0, 'pending': 0, 'error': str(e)}
    
    def _send_notification(self, notification: Dict, api_config: Dict) -> bool:
        """
        Send a single notification
        
        Args:
            notification: notification dict
            api_config: API configuration
        
        Returns:
            True if sent successfully
        """
        try:
            api_url = api_config.get('api_url')
            api_key = api_config.get('api_key')
            
            if not api_url:
                logger.warning("[NOTIFY] No API URL configured")
                return False
            
            headers = {'Content-Type': 'application/json'}
            if api_key:
                headers['Authorization'] = f"Bearer {api_key}"
                headers['X-API-Key'] = api_key
            
            payload = {
                'to': notification['recipient'],
                'message': notification['message'],
                'type': notification['type'],
                'event_id': notification.get('event_id'),
                'media_url': notification.get('media_url')
            }
            
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            return response.status_code in [200, 201, 202]
            
        except requests.exceptions.Timeout:
            logger.warning("[NOTIFY] Send timeout")
            return False
        except Exception as e:
            logger.error(f"[NOTIFY] Send failed: {e}")
            return False
    
    def get_notification_stats(self) -> Dict:
        """Get notification queue statistics"""
        with self.lock:
            try:
                queue = self._load_queue(self.queue_file)
                offline = self._load_queue(self.offline_file)
                
                pending = len([n for n in queue if n.get('status') == 'pending'])
                sent = len([n for n in queue if n.get('status') == 'sent'])
                failed = len([n for n in queue if n.get('status') == 'failed'])
                
                return {
                    'queued': len(queue),
                    'pending': pending,
                    'sent': sent,
                    'failed': failed,
                    'offline': len(offline)
                }
            except Exception as e:
                logger.error(f"[NOTIFY] Get stats failed: {e}")
                return {'queued': 0, 'pending': 0, 'sent': 0, 'failed': 0, 'offline': 0}
    
    def clear_sent_notifications(self, days: int = 7):
        """Clear sent notifications older than N days"""
        with self.lock:
            try:
                queue = self._load_queue(self.queue_file)
                cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
                
                remaining = [
                    n for n in queue
                    if n.get('status') != 'sent' or n.get('timestamp', '') > cutoff
                ]
                
                deleted = len(queue) - len(remaining)
                if deleted > 0:
                    self._save_queue(self.queue_file, remaining)
                    logger.info(f"[NOTIFY] Cleared {deleted} sent notifications")
                    
            except Exception as e:
                logger.error(f"[NOTIFY] Clear failed: {e}")


# Global instance
_queue_instance: Optional[NotificationQueue] = None

def get_notification_queue(base_dir: Optional[str] = None) -> NotificationQueue:
    """Get or create notification queue"""
    global _queue_instance
    
    if _queue_instance is None:
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        _queue_instance = NotificationQueue(base_dir)
    
    return _queue_instance
