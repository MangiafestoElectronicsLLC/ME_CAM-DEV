#!/bin/bash
# SMS & Motion Detection Setup for ME_CAM (Both main.py and main_lite.py)
# =========================================================================

echo "=== SMS & Motion Detection Configuration ==="
echo ""
echo "MOTION DETECTION:"
echo "  ✓ Enabled in BOTH main.py and main_lite.py"
echo "  ✓ Lightweight detection (processes every 5 frames)"
echo "  ✓ Saved to: logs/motion_events.json"
echo "  ✓ API: /api/motion/events (get recent events)"
echo "  ✓ API: /api/motion/log (log new event)"
echo ""
echo "SMS ALERT PROVIDERS (Choose one):"
echo "  1. TWILIO (Recommended)"
echo "     - Free trial: 100+ SMS/month"
echo "     - Setup: https://www.twilio.com/console"
echo "     - Config needed:"
echo "         account_sid: Found in Twilio console"
echo "         auth_token: Found in Twilio console"
echo "         phone_from: Your Twilio phone number (e.g., +1234567890)"
echo ""
echo "  2. AWS SNS"
echo "     - No setup needed if already using AWS"
echo "     - Config: AWS region + IAM credentials"
echo ""
echo "  3. PLIVO"
echo "     - Similar to Twilio"
echo "     - Setup: https://www.plivo.com"
echo ""
echo "  4. GENERIC HTTP"
echo "     - Use any webhook service"
echo "     - POST to your custom endpoint"
echo ""
echo "CONFIGURATION:"
echo "  1. Edit config/config_default.json or ~/ME_CAM/config.json"
echo "  2. Fill in 'notifications.sms' section:"
echo ""
echo '    "sms": {'
echo '      "enabled": true,'
echo '      "provider": "twilio",'
echo '      "rate_limit_minutes": 5,'
echo '      "motion_threshold": 0.5,'
echo '      "phone_to": "+1234567890",'
echo '      "twilio": {'
echo '        "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",'
echo '        "auth_token": "your_auth_token_here",'
echo '        "phone_from": "+1987654321"'
echo '      }'
echo '    }'
echo ""
echo "MOTION EVENTS:"
echo "  - Automatically logged when camera detects motion"
echo "  - Stored in: logs/motion_events.json"
echo "  - Accessible via:"
echo "    - Dashboard: http://[IP]:8080 → 🚨 Motion Events section"
echo "    - API: curl http://localhost:8080/api/motion/events?hours=24"
echo ""
echo "TESTING SMS:"
echo "  # Test endpoint to trigger SMS (manual)"
echo "  curl -X POST http://localhost:8080/api/motion/log \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"type\": \"motion\", \"confidence\": 0.9}'"
echo ""
echo "MEMORY USAGE:"
echo "  main_lite.py:"
echo "    - Motion detection: ~5-10MB overhead"
echo "    - SMS service: ~2-5MB overhead"
echo "    - Total LITE MODE: Still ~150MB (Pi Zero 2W friendly ✓)"
echo ""
echo "  main.py:"
echo "    - Motion detection: Integrated"
echo "    - SMS service: Integrated"
echo "    - Total: ~400MB (Pi 3B+ or higher)"
echo ""
echo "API ENDPOINTS:"
echo "  POST /api/motion/log        - Log a motion event"
echo "  GET  /api/motion/events     - Get motion events (query: hours, limit, type)"
echo ""
echo "For more details, see:"
echo "  - notes.txt (PART 6: SMS & Motion Detection)"
echo "  - src/core/sms_notifier.py (SMS implementation)"
echo "  - src/core/motion_logger.py (Motion persistence)"
