"""
Firebase Cloud Messaging Service - Production Ready
==============================================
Features:
- Firebase Admin SDK integration
- Device token management
- Rich notifications with images
- Topic-based messaging
- Batch notifications
- Android and iOS support
"""

import os
import json
from datetime import datetime
from threading import Lock
from typing import Optional, Dict, List
from loguru import logger

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    firebase_admin = None
    credentials = None
    messaging = None
    FIREBASE_AVAILABLE = False
    logger.warning("[FCM] firebase-admin not available - FCM disabled")


class FirebaseCloudMessaging:
    """
    Production-ready Firebase Cloud Messaging service
    
    Features:
    - Device token registration
    - Individual and batch notifications
    - Topic subscriptions (broadcast to groups)
    - Rich notifications with images
    - Data payloads for app actions
    - Platform-specific configurations (Android/iOS)
    """
    
    def __init__(self,
                 base_dir: str,
                 service_account_path: Optional[str] = None):
        """
        Initialize Firebase Cloud Messaging
        
        Args:
            base_dir: Base directory for config/logs
            service_account_path: Path to Firebase service account JSON
        """
        self.base_dir = base_dir
        self.tokens_file = os.path.join(base_dir, "config", "fcm_device_tokens.json")
        
        # Thread safety
        self.tokens_lock = Lock()
        
        # Device tokens storage
        self.device_tokens = {}  # {device_id: token_info}
        
        # Create directories
        os.makedirs(os.path.dirname(self.tokens_file), exist_ok=True)
        
        # Initialize Firebase
        self.fcm_enabled = False
        if FIREBASE_AVAILABLE and service_account_path:
            self._init_firebase(service_account_path)
        
        # Load device tokens
        self._load_tokens()
        
        logger.info(f"[FCM] Initialized - Enabled: {self.fcm_enabled}, "
                   f"Devices: {len(self.device_tokens)}")
    
    def _init_firebase(self, service_account_path: str):
        """Initialize Firebase Admin SDK"""
        try:
            if not os.path.exists(service_account_path):
                logger.warning(f"[FCM] Service account not found: {service_account_path}")
                return
            
            # Check if already initialized
            try:
                firebase_admin.get_app()
                logger.info("[FCM] Firebase already initialized")
                self.fcm_enabled = True
                return
            except ValueError:
                pass  # Not initialized yet
            
            # Initialize Firebase
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            
            self.fcm_enabled = True
            logger.success("[FCM] Firebase initialized")
            
        except Exception as e:
            logger.error(f"[FCM] Firebase init failed: {e}")
            self.fcm_enabled = False
    
    def register_device(self,
                       device_id: str,
                       fcm_token: str,
                       device_name: Optional[str] = None,
                       platform: Optional[str] = None,
                       user_id: Optional[str] = None) -> bool:
        """
        Register a device for FCM notifications
        
        Args:
            device_id: Unique device identifier
            fcm_token: FCM registration token from device
            device_name: Optional device name
            platform: 'android' or 'ios'
            user_id: Optional user identifier
        
        Returns:
            True if successful
        """
        try:
            # Create device record
            device_info = {
                'device_id': device_id,
                'fcm_token': fcm_token,
                'device_name': device_name,
                'platform': platform,
                'user_id': user_id,
                'registered_at': datetime.utcnow().isoformat(),
                'last_used': None,
                'notification_count': 0,
                'status': 'active'
            }
            
            with self.tokens_lock:
                self.device_tokens[device_id] = device_info
                self._save_tokens()
            
            logger.success(f"[FCM] Registered device: {device_id} ({device_name})")
            return True
            
        except Exception as e:
            logger.error(f"[FCM] Register device failed: {e}")
            return False
    
    def unregister_device(self, device_id: str) -> bool:
        """Unregister a device"""
        try:
            with self.tokens_lock:
                if device_id in self.device_tokens:
                    del self.device_tokens[device_id]
                    self._save_tokens()
                    logger.info(f"[FCM] Unregistered device: {device_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"[FCM] Unregister device failed: {e}")
            return False
    
    def get_devices(self, user_id: Optional[str] = None) -> List[Dict]:
        """Get all devices or filter by user_id"""
        with self.tokens_lock:
            devices = list(self.device_tokens.values())
            if user_id:
                devices = [d for d in devices if d.get('user_id') == user_id]
            return devices
    
    def send_notification(self,
                         device_ids: List[str],
                         title: str,
                         body: str,
                         image_url: Optional[str] = None,
                         data: Optional[Dict] = None,
                         android_priority: str = 'high',
                         ios_badge: Optional[int] = None) -> Dict[str, bool]:
        """
        Send push notification to devices
        
        Args:
            device_ids: List of device IDs to notify
            title: Notification title
            body: Notification body text
            image_url: Image URL for rich notification
            data: Custom data payload for app
            android_priority: 'normal' or 'high'
            ios_badge: Badge count for iOS
        
        Returns:
            Dictionary mapping device_id to success boolean
        """
        if not self.fcm_enabled:
            logger.warning("[FCM] FCM not enabled")
            return {}
        
        results = {}
        
        for device_id in device_ids:
            # Get device token
            with self.tokens_lock:
                device_info = self.device_tokens.get(device_id)
            
            if not device_info:
                logger.warning(f"[FCM] Device not found: {device_id}")
                results[device_id] = False
                continue
            
            fcm_token = device_info['fcm_token']
            platform = device_info.get('platform', 'android')
            
            # Send notification
            success = self._send_fcm_message(
                fcm_token,
                title,
                body,
                image_url,
                data,
                platform,
                android_priority,
                ios_badge
            )
            
            results[device_id] = success
            
            # Update device stats
            if success:
                with self.tokens_lock:
                    device_info['last_used'] = datetime.utcnow().isoformat()
                    device_info['notification_count'] += 1
                    self._save_tokens()
            else:
                # Mark token as potentially invalid
                with self.tokens_lock:
                    device_info['status'] = 'error'
                    self._save_tokens()
        
        return results
    
    def _send_fcm_message(self,
                         fcm_token: str,
                         title: str,
                         body: str,
                         image_url: Optional[str],
                         data: Optional[Dict],
                         platform: str,
                         android_priority: str,
                         ios_badge: Optional[int]) -> bool:
        """Send a single FCM message"""
        try:
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Build data payload
            data_payload = data or {}
            data_payload['timestamp'] = str(int(datetime.utcnow().timestamp()))
            
            # Platform-specific configuration
            android_config = messaging.AndroidConfig(
                priority=android_priority,
                notification=messaging.AndroidNotification(
                    icon='camera_icon',
                    color='#FF5722',  # Red-orange for alerts
                    sound='default',
                    channel_id='mecam_alerts'
                )
            )
            
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        badge=ios_badge,
                        sound='default',
                        category='MECAM_ALERT'
                    )
                )
            )
            
            # Create message
            message = messaging.Message(
                notification=notification,
                data={k: str(v) for k, v in data_payload.items()},  # FCM requires string values
                token=fcm_token,
                android=android_config if platform == 'android' else None,
                apns=apns_config if platform == 'ios' else None
            )
            
            # Send message
            response = messaging.send(message)
            logger.debug(f"[FCM] Sent notification: {title} (response: {response})")
            return True
            
        except messaging.UnregisteredError:
            logger.warning("[FCM] Token unregistered")
            return False
            
        except messaging.SenderIdMismatchError:
            logger.error("[FCM] Sender ID mismatch")
            return False
            
        except Exception as e:
            logger.error(f"[FCM] Send failed: {e}")
            return False
    
    def send_batch_notifications(self,
                                device_ids: List[str],
                                title: str,
                                body: str,
                                **kwargs) -> Dict[str, bool]:
        """
        Send notifications in batch (more efficient)
        
        Args:
            device_ids: List of device IDs
            title: Notification title
            body: Notification body
            **kwargs: Additional arguments passed to _send_fcm_message
        
        Returns:
            Dictionary mapping device_id to success boolean
        """
        if not self.fcm_enabled:
            logger.warning("[FCM] FCM not enabled")
            return {}
        
        # Get FCM tokens
        tokens = []
        device_id_map = {}
        
        with self.tokens_lock:
            for device_id in device_ids:
                device_info = self.device_tokens.get(device_id)
                if device_info:
                    fcm_token = device_info['fcm_token']
                    tokens.append(fcm_token)
                    device_id_map[fcm_token] = device_id
        
        if not tokens:
            logger.warning("[FCM] No valid tokens found")
            return {}
        
        try:
            # Build messages
            messages = []
            for token in tokens:
                device_id = device_id_map[token]
                device_info = self.device_tokens[device_id]
                platform = device_info.get('platform', 'android')
                
                # Build message (simplified for batch)
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                        image=kwargs.get('image_url')
                    ),
                    data=kwargs.get('data', {}),
                    token=token
                )
                messages.append(message)
            
            # Send batch
            batch_response = messaging.send_all(messages)
            
            logger.info(f"[FCM] Batch sent: {batch_response.success_count}/{len(messages)} successful")
            
            # Map results back to device IDs
            results = {}
            for i, response in enumerate(batch_response.responses):
                token = tokens[i]
                device_id = device_id_map[token]
                success = response.success
                results[device_id] = success
                
                # Update device stats
                with self.tokens_lock:
                    device_info = self.device_tokens[device_id]
                    if success:
                        device_info['last_used'] = datetime.utcnow().isoformat()
                        device_info['notification_count'] += 1
                    else:
                        device_info['status'] = 'error'
                    self._save_tokens()
            
            return results
            
        except Exception as e:
            logger.error(f"[FCM] Batch send failed: {e}")
            return {}
    
    def subscribe_to_topic(self, device_ids: List[str], topic: str) -> bool:
        """Subscribe devices to a topic for broadcast messaging"""
        if not self.fcm_enabled:
            return False
        
        try:
            # Get FCM tokens
            tokens = []
            with self.tokens_lock:
                for device_id in device_ids:
                    device_info = self.device_tokens.get(device_id)
                    if device_info:
                        tokens.append(device_info['fcm_token'])
            
            if not tokens:
                return False
            
            # Subscribe to topic
            response = messaging.subscribe_to_topic(tokens, topic)
            logger.info(f"[FCM] Subscribed {response.success_count} devices to topic: {topic}")
            return response.success_count > 0
            
        except Exception as e:
            logger.error(f"[FCM] Subscribe to topic failed: {e}")
            return False
    
    def send_to_topic(self,
                     topic: str,
                     title: str,
                     body: str,
                     **kwargs) -> bool:
        """Send notification to all devices subscribed to a topic"""
        if not self.fcm_enabled:
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=kwargs.get('image_url')
                ),
                data=kwargs.get('data', {}),
                topic=topic
            )
            
            response = messaging.send(message)
            logger.success(f"[FCM] Sent to topic '{topic}': {response}")
            return True
            
        except Exception as e:
            logger.error(f"[FCM] Send to topic failed: {e}")
            return False
    
    def _load_tokens(self):
        """Load device tokens from disk"""
        try:
            if os.path.exists(self.tokens_file):
                with open(self.tokens_file, 'r') as f:
                    self.device_tokens = json.load(f)
                logger.info(f"[FCM] Loaded {len(self.device_tokens)} device tokens")
        except Exception as e:
            logger.error(f"[FCM] Load tokens failed: {e}")
    
    def _save_tokens(self):
        """Save device tokens to disk"""
        try:
            with open(self.tokens_file, 'w') as f:
                json.dump(self.device_tokens, f, indent=2)
        except Exception as e:
            logger.error(f"[FCM] Save tokens failed: {e}")


# Global instance
_fcm_service = None

def get_fcm_service(base_dir: str = None, **kwargs) -> FirebaseCloudMessaging:
    """Get or create global FCM service instance"""
    global _fcm_service
    if _fcm_service is None:
        if base_dir is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        _fcm_service = FirebaseCloudMessaging(base_dir, **kwargs)
    return _fcm_service
