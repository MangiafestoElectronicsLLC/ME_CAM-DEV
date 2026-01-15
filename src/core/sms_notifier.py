"""SMS/Text message alerting system for motion events"""
import requests
import os
from datetime import datetime, timedelta
from threading import RLock, Thread
import json
from loguru import logger

_lock = RLock()

# SMS rate limiting to avoid spam
SMS_SENT_FILE = "logs/sms_sent.json"


def ensure_sms_dir():
    """Ensure SMS tracking directory exists"""
    os.makedirs(os.path.dirname(SMS_SENT_FILE), exist_ok=True)


def load_sms_history():
    """Load SMS send history for rate limiting"""
    ensure_sms_dir()
    if not os.path.exists(SMS_SENT_FILE):
        return []
    try:
        with open(SMS_SENT_FILE, 'r') as f:
            return json.load(f)
    except:
        return []


def save_sms_history(history):
    """Save SMS send history"""
    ensure_sms_dir()
    try:
        with open(SMS_SENT_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"[SMS] Error saving history: {e}")


def is_rate_limited(phone_number, min_interval_minutes=5):
    """Check if SMS sending is rate limited for this phone"""
    with _lock:
        try:
            history = load_sms_history()
            cutoff_time = (datetime.now() - timedelta(minutes=min_interval_minutes)).timestamp()
            
            # Find recent SMS to this number
            recent_sms = [
                s for s in history
                if s.get('phone') == phone_number and s.get('timestamp', 0) > cutoff_time
            ]
            
            return len(recent_sms) > 0
        except Exception as e:
            logger.error(f"[SMS] Error checking rate limit: {e}")
            return False


class SMSNotifier:
    """Send SMS alerts for motion events"""
    
    def __init__(self, config=None):
        """
        Initialize SMS notifier with configuration
        
        Config format:
        {
            "enabled": true,
            "provider": "twilio",  # or "sns", "plivo", "generic_http"
            "twilio": {
                "account_sid": "...",
                "auth_token": "...",
                "phone_from": "+1234567890",
                "phone_to": "+1987654321"
            },
            "generic_http": {
                "url": "http://...",
                "auth_token": "..."
            },
            "rate_limit_minutes": 5,
            "motion_threshold": 0.5
        }
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", False)
        self.provider = self.config.get("provider", "twilio")
        self.rate_limit_minutes = self.config.get("rate_limit_minutes", 5)
        self.motion_threshold = self.config.get("motion_threshold", 0.5)
        
        if self.enabled:
            logger.info(f"[SMS] Notifier initialized with provider: {self.provider}")
    
    def send_sms(self, phone_number, message):
        """Send SMS to phone number (non-blocking)"""
        if not self.enabled:
            logger.debug("[SMS] SMS notifications disabled")
            return False
        
        # Rate limiting check
        if is_rate_limited(phone_number, self.rate_limit_minutes):
            logger.info(f"[SMS] Rate limited for {phone_number} (min interval: {self.rate_limit_minutes}m)")
            return False
        
        # Send in background thread to avoid blocking
        thread = Thread(target=self._send_sms_async, args=(phone_number, message), daemon=True)
        thread.start()
        return True
    
    def _send_sms_async(self, phone_number, message):
        """Actually send SMS (runs in background)"""
        try:
            success = False
            
            if self.provider == "twilio":
                success = self._send_twilio(phone_number, message)
            elif self.provider == "sns":
                success = self._send_sns(phone_number, message)
            elif self.provider == "plivo":
                success = self._send_plivo(phone_number, message)
            elif self.provider == "generic_http":
                success = self._send_generic_http(phone_number, message)
            
            # Track SMS if successful
            if success:
                with _lock:
                    history = load_sms_history()
                    history.append({
                        "phone": phone_number,
                        "timestamp": datetime.now().timestamp(),
                        "datetime": datetime.now().isoformat(),
                        "message_preview": message[:50]
                    })
                    # Keep only last 1000 SMS
                    if len(history) > 1000:
                        history = history[-1000:]
                    save_sms_history(history)
                    logger.success(f"[SMS] Sent to {phone_number}")
            else:
                logger.error(f"[SMS] Failed to send to {phone_number}")
                
        except Exception as e:
            logger.error(f"[SMS] Error sending SMS: {e}")
    
    def _send_twilio(self, phone_number, message):
        """Send via Twilio"""
        try:
            config = self.config.get("twilio", {})
            account_sid = config.get("account_sid")
            auth_token = config.get("auth_token")
            phone_from = config.get("phone_from")
            
            if not all([account_sid, auth_token, phone_from]):
                logger.error("[SMS] Twilio config incomplete")
                return False
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            
            response = requests.post(
                url,
                data={"From": phone_from, "To": phone_number, "Body": message},
                auth=(account_sid, auth_token),
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return True
            else:
                logger.error(f"[SMS] Twilio error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"[SMS] Twilio send error: {e}")
            return False
    
    def _send_sns(self, phone_number, message):
        """Send via AWS SNS"""
        try:
            import boto3
            client = boto3.client("sns")
            response = client.publish(
                PhoneNumber=phone_number,
                Message=message
            )
            return response.get("MessageId") is not None
        except Exception as e:
            logger.error(f"[SMS] SNS send error: {e}")
            return False
    
    def _send_plivo(self, phone_number, message):
        """Send via Plivo"""
        try:
            config = self.config.get("plivo", {})
            auth_id = config.get("auth_id")
            auth_token = config.get("auth_token")
            phone_from = config.get("phone_from")
            
            if not all([auth_id, auth_token, phone_from]):
                logger.error("[SMS] Plivo config incomplete")
                return False
            
            url = f"https://api.plivo.com/v1/Account/{auth_id}/Message/"
            
            response = requests.post(
                url,
                data={
                    "src": phone_from,
                    "dst": phone_number,
                    "text": message
                },
                auth=(auth_id, auth_token),
                timeout=10
            )
            
            return response.status_code in [200, 201]
            
        except Exception as e:
            logger.error(f"[SMS] Plivo send error: {e}")
            return False
    
    def _send_generic_http(self, phone_number, message):
        """Send via generic HTTP endpoint"""
        try:
            config = self.config.get("generic_http", {})
            url = config.get("url")
            auth_token = config.get("auth_token")
            
            if not url:
                logger.error("[SMS] Generic HTTP URL not configured")
                return False
            
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            response = requests.post(
                url,
                json={"phone": phone_number, "message": message},
                headers=headers,
                timeout=10
            )
            
            return response.status_code in [200, 201]
            
        except Exception as e:
            logger.error(f"[SMS] Generic HTTP send error: {e}")
            return False
    
    def notify_motion(self, phone_number, event_type="motion", confidence=0.0, location="Unknown"):
        """Send motion detection SMS alert"""
        if not self.enabled:
            return False
        
        # Check threshold
        if confidence < self.motion_threshold:
            return False
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🚨 ME_CAM Alert: {event_type.upper()} detected\nTime: {timestamp}\nLocation: {location}\nConfidence: {confidence:.0%}"
        
        return self.send_sms(phone_number, message)
    
    def notify_intrusion(self, phone_number, location="Unknown"):
        """Send intrusion alert SMS"""
        if not self.enabled:
            return False
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🚨 SECURITY ALERT: Intrusion detected at {location}\nTime: {timestamp}\nImmediate action may be required!"
        
        return self.send_sms(phone_number, message)


# Global SMS notifier instance
_sms_notifier = None


def get_sms_notifier():
    """Get or create SMS notifier instance"""
    global _sms_notifier
    if _sms_notifier is None:
        from .config_manager import get_config
        try:
            config = get_config()
            sms_config = config.get("notifications", {}).get("sms", {})
            _sms_notifier = SMSNotifier(sms_config)
        except Exception as e:
            logger.error(f"[SMS] Error initializing: {e}")
            _sms_notifier = SMSNotifier()
    return _sms_notifier


def reset_sms_notifier():
    """Reset SMS notifier (for config changes)"""
    global _sms_notifier
    _sms_notifier = None
