"""
Emergency Handler - Manages emergency notifications for medical and security events
"""
import os
import time
from datetime import datetime
from loguru import logger
from src.core.config_manager import get_config
from src.utils.cloud.email_notifier import EmailNotifier
from pathlib import Path

class EmergencyHandler:
    """Handle emergency notifications for medical and security events"""
    
    def __init__(self):
        self.last_alert_time = 0
        self.alert_cooldown = 60  # Minimum 60 seconds between alerts (prevent spam)
    
    def trigger_medical_emergency(self, event_type="seizure", video_path=None):
        """
        Trigger medical emergency alert
        
        Args:
            event_type: Type of medical event ("seizure", "fall", "unresponsive")
            video_path: Optional path to video evidence
        """
        cfg = get_config()
        
        # Check cooldown to prevent spam
        if time.time() - self.last_alert_time < self.alert_cooldown:
            logger.warning("[EMERGENCY] Alert cooldown active, skipping duplicate alert")
            return False
        
        logger.critical(f"[EMERGENCY] MEDICAL ALERT - {event_type.upper()}")
        
        # Get emergency contacts
        emergency_phone = cfg.get('emergency_phone', 'Not configured')
        emergency_contacts = cfg.get('emergency_contacts', [])
        
        # Send to primary emergency contact (wife)
        primary_contact = cfg.get('emergency_primary_contact', emergency_phone)
        
        # Compose urgent message
        subject = f"🚨 MEDICAL EMERGENCY - {event_type.upper()}"
        body = f"""URGENT - MEDICAL EMERGENCY DETECTED

Event Type: {event_type.upper()}
Device: {cfg.get('device_name', 'ME_CAM')}
Location: {cfg.get('device_location', 'Unknown')}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Primary Contact: {primary_contact}

This is an automated alert from ME_CAM monitoring system.
Please check on the person immediately.

Video evidence: {"Attached" if video_path else "Not available"}
"""
        
        success = self._send_emergency_notification(subject, body, primary_contact, video_path)
        
        if success:
            self.last_alert_time = time.time()
            logger.info(f"[EMERGENCY] Medical alert sent successfully to {primary_contact}")
        
        return success
    
    def trigger_security_emergency(self, event_type="theft", video_path=None):
        """
        Trigger security emergency alert for theft/break-in
        
        Args:
            event_type: Type of security event ("theft", "break_in", "vandalism")
            video_path: Path to video evidence (required for police/insurance)
        """
        cfg = get_config()
        
        # Check cooldown
        if time.time() - self.last_alert_time < self.alert_cooldown:
            logger.warning("[EMERGENCY] Alert cooldown active, skipping duplicate alert")
            return False
        
        logger.critical(f"[EMERGENCY] SECURITY ALERT - {event_type.upper()}")
        
        # Get security contacts (police, insurance, owner)
        security_contacts = cfg.get('security_contacts', [])
        owner_email = cfg.get('owner_email', cfg.get('email', {}).get('to_address', ''))
        
        # Compose security alert
        subject = f"🚨 SECURITY ALERT - {event_type.upper()}"
        body = f"""SECURITY INCIDENT DETECTED

Incident Type: {event_type.upper()}
Device: {cfg.get('device_name', 'ME_CAM')}
Location: {cfg.get('device_location', 'Unknown')}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Video Evidence: {"Attached" if video_path else "Not available"}

This alert has been sent to:
- Property Owner: {owner_email}
- Security Contacts: {len(security_contacts)} configured

For police report, reference:
- Device ID: {cfg.get('device_name')}
- Timestamp: {datetime.now().isoformat()}
- Evidence File: {os.path.basename(video_path) if video_path else 'N/A'}

Next steps:
1. Review attached video evidence
2. Contact local authorities if needed
3. File insurance claim if applicable
"""
        
        # Send to owner first
        success = self._send_emergency_notification(subject, body, owner_email, video_path)
        
        # Send to additional security contacts
        for contact in security_contacts:
            self._send_emergency_notification(subject, body, contact, video_path)
        
        if success:
            self.last_alert_time = time.time()
            logger.info(f"[EMERGENCY] Security alert sent to {len(security_contacts) + 1} recipients")
        
        return success
    
    def trigger_general_emergency(self, message="Emergency button pressed"):
        """
        Trigger general emergency alert (SOS button)
        
        Args:
            message: Custom emergency message
        """
        cfg = get_config()
        
        logger.critical(f"[EMERGENCY] GENERAL ALERT - {message}")
        
        emergency_phone = cfg.get('emergency_phone', 'Not configured')
        
        subject = "🚨 EMERGENCY ALERT - ME_CAM"
        body = f"""EMERGENCY ALERT

Message: {message}
Device: {cfg.get('device_name', 'ME_CAM')}
Location: {cfg.get('device_location', 'Unknown')}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Emergency Contact: {emergency_phone}

Please respond immediately.
"""
        
        return self._send_emergency_notification(subject, body, emergency_phone)
    
    def _send_emergency_notification(self, subject, body, recipient, video_path=None):
        """
        Send emergency notification via email/SMS
        
        Args:
            subject: Email subject
            body: Email body
            recipient: Recipient email/phone
            video_path: Optional video attachment
        """
        try:
            cfg = get_config()
            email_cfg = cfg.get('email', {})
            
            if not email_cfg.get('enabled', False):
                logger.warning("[EMERGENCY] Email notifications disabled - cannot send alert")
                return False
            
            # Create notifier
            notifier = EmailNotifier(
                enabled=True,
                smtp_host=email_cfg.get('smtp_server', ''),
                smtp_port=email_cfg.get('smtp_port', 587),
                username=email_cfg.get('username', ''),
                password=email_cfg.get('password', ''),
                from_addr=email_cfg.get('from_address', email_cfg.get('username', '')),
                to_addr=recipient or email_cfg.get('to_address', '')
            )
            
            # Send alert
            notifier.send_alert(subject, body)
            
            # If video provided, send via Google Drive link (if enabled)
            if video_path and os.path.exists(video_path):
                self._upload_evidence_to_drive(video_path)
            
            return True
            
        except Exception as e:
            logger.error(f"[EMERGENCY] Failed to send notification: {e}")
            return False
    
    def _upload_evidence_to_drive(self, video_path):
        """Upload video evidence to Google Drive (if configured)"""
        try:
            cfg = get_config()
            gdrive_cfg = cfg.get('google_drive', {})
            
            if not gdrive_cfg.get('enabled', False):
                return
            
            # Import and upload (only if Google Drive enabled)
            from cloud.gdrive_uploader import GDriveUploader
            uploader = GDriveUploader()
            
            if uploader.authenticate():
                file_id = uploader.upload_file(video_path)
                if file_id:
                    logger.info(f"[EMERGENCY] Evidence uploaded to Google Drive: {file_id}")
                    return file_id
            
        except Exception as e:
            logger.warning(f"[EMERGENCY] Could not upload evidence to Drive: {e}")
        
        return None
    
    def get_latest_recording(self):
        """Get path to most recent recording"""
        try:
            cfg = get_config()
            recordings_dir = cfg.get('storage', {}).get('recordings_dir', 'recordings')
            
            if not os.path.exists(recordings_dir):
                return None
            
            # Find most recent .mp4 file
            recordings = list(Path(recordings_dir).glob('*.mp4'))
            if not recordings:
                return None
            
            latest = max(recordings, key=lambda p: p.stat().st_mtime)
            return str(latest)
            
        except Exception as e:
            logger.error(f"[EMERGENCY] Error finding latest recording: {e}")
            return None

# Global singleton
emergency_handler = EmergencyHandler()
