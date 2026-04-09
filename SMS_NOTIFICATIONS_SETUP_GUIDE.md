# SMS/Phone Notifications Setup Guide
## Get Instant Motion Alerts on Your Phone

This guide shows you how to enable SMS/text message notifications when motion is detected by your ME_CAM system.

---

## 🎯 Quick Start (Recommended: Twilio)

### Step 1: Sign Up for Twilio (FREE Trial)
1. Go to [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Sign up for a **free account** (no credit card needed for trial)
3. Get **$15 in free credit** (enough for ~500 SMS messages)

### Step 2: Get Your Credentials
After signing up, note these from your Twilio dashboard:

```
Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Auth Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Phone From: +1234567890 (your Twilio number)
Phone To: +1987654321 (your personal phone)
```

### Step 3: Configure ME_CAM

**Option A: Via Web Interface (Easiest)**
1. Open `https://me_cam.com:8080/config`
2. Scroll to **SMS Notifications** section
3. Enable SMS notifications
4. Enter your Twilio credentials
5. Click **Save Configuration**

**Option B: Via Configuration File**
Edit `hub_config.json`:

```json
{
  "notifications": {
    "sms": {
      "enabled": true,
      "provider": "twilio",
      "twilio": {
        "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "auth_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "phone_from": "+1234567890",
        "phone_to": "+1987654321"
      },
      "rate_limit_minutes": 5,
      "motion_threshold": 0.5
    }
  }
}
```

### Step 4: Enable Motion Alerts
In the web config page:
1. Check ✅ **Send motion alerts to emergency contact**
2. Set **Emergency Phone Number** to your number
3. Adjust **Motion Sensitivity** (0.5 = medium)
4. Click **Save**

### Step 5: Test It!
1. Wave your hand in front of the camera
2. You should receive an SMS within 5-10 seconds:

```
🚨 ME Camera: Motion detected at Living Room - 02:45:30 PM
```

---

## 📱 SMS Provider Options

### Option 1: Twilio (Recommended ⭐)
**Best for:** Most users, reliable, easy setup

**Pricing:**
- Free trial: $15 credit (~500 SMS)
- Pay-as-you-go: $0.0075 per SMS
- Monthly: 1,000 SMS = ~$7.50/month

**Setup:**
```json
"provider": "twilio",
"twilio": {
  "account_sid": "ACxxxxx",
  "auth_token": "xxxxx",
  "phone_from": "+15551234567",
  "phone_to": "+15559876543"
}
```

**Pros:**
- ✅ Free trial
- ✅ Reliable delivery
- ✅ Detailed logs
- ✅ No monthly fee (pay-per-use)

---

### Option 2: AWS SNS
**Best for:** AWS users, scalable

**Pricing:**
- First 1M requests free (for new accounts)
- $0.00645 per SMS (US)

**Setup:**
```bash
# Install AWS CLI
pip3 install boto3

# Configure credentials
aws configure
```

```json
"provider": "sns",
"sns": {
  "region": "us-east-1",
  "access_key": "AKIAxxxxx",
  "secret_key": "xxxxx"
}
```

**Pros:**
- ✅ No phone number needed
- ✅ Direct to mobile
- ✅ High reliability

---

### Option 3: Plivo
**Best for:** International SMS, bulk messaging

**Pricing:**
- Free trial: $10 credit
- US SMS: $0.0055 per message
- International: Varies by country

**Setup:**
```json
"provider": "plivo",
"plivo": {
  "auth_id": "MAxxxxx",
  "auth_token": "xxxxx",
  "phone_from": "+15551234567",
  "phone_to": "+15559876543"
}
```

---

### Option 4: Generic HTTP API (Custom)
**Best for:** Self-hosted solutions, custom integrations

**Example: Self-hosted SMS gateway**
```json
"provider": "generic_http",
"generic_http": {
  "url": "http://your-sms-gateway.com/send",
  "auth_token": "your_api_key",
  "method": "POST"
}
```

**Works with:**
- Gammu SMSD
- Kannel
- PlaySMS
- Custom webhooks

---

## ⚙️ Configuration Options

### SMS Settings Explained

```json
{
  "enabled": true,              // Turn SMS on/off
  "provider": "twilio",         // Which service to use
  "rate_limit_minutes": 5,      // Minimum time between SMS (anti-spam)
  "motion_threshold": 0.5,      // Confidence level to trigger SMS (0-1)
  "send_motion_to_emergency": true  // Auto-send on motion
}
```

### Rate Limiting
Prevents SMS spam and saves money:

```python
# Default: Max 1 SMS per 5 minutes
"rate_limit_minutes": 5

# Aggressive: 1 SMS per minute (expensive!)
"rate_limit_minutes": 1

# Conservative: 1 SMS per 30 minutes
"rate_limit_minutes": 30
```

### Motion Sensitivity
Control when SMS is sent:

```python
# High sensitivity (many alerts)
"motion_threshold": 0.3

# Medium (balanced - default)
"motion_threshold": 0.5

# Low sensitivity (only strong motion)
"motion_threshold": 0.8
```

---

## 📝 SMS Message Formats

Your ME_CAM sends professional, informative alerts:

### Motion Detection Alert
```
🚨 ME Camera: Motion detected at Living Room - 02:45:30 PM
```

### Security Alert (Manual trigger)
```
🚨 ALERT: Security breach detected
Device: Camera-001
Time: 2026-01-20 14:45:30
```

### Intrusion Alert (Advanced)
```
🚨 SECURITY ALERT: Intrusion detected at Front Door
Time: 2026-01-20 14:45:30
Immediate action may be required!
```

---

## 🧪 Testing Your SMS Setup

### Test 1: Configuration Check
```bash
cd ~/ME_CAM-DEV
python3 << EOF
from src.core import get_sms_notifier
sms = get_sms_notifier()
print(f"SMS Enabled: {sms.enabled}")
print(f"Provider: {sms.provider}")
EOF
```

### Test 2: Send Test Message
From Python:
```python
from src.core import get_sms_notifier

sms = get_sms_notifier()
sms.send_sms("+15559876543", "🧪 Test message from ME_CAM")
```

Or via web interface:
1. Go to Config page
2. Enter test phone number
3. Click **Send Test SMS**

### Test 3: Motion Detection
1. Enable motion alerts in config
2. Wave in front of camera
3. Check phone within 10 seconds

---

## 💰 Cost Estimates

### Typical Home Use (Twilio):

**Light use:** 10 alerts/day
- 300 SMS/month
- Cost: ~$2.25/month

**Medium use:** 30 alerts/day
- 900 SMS/month
- Cost: ~$6.75/month

**Heavy use:** 100 alerts/day
- 3,000 SMS/month
- Cost: ~$22.50/month

**Tip:** Adjust `rate_limit_minutes` to control costs!

---

## 🔧 Advanced Configuration

### Multiple Recipients
Modify `hub_config.json`:
```json
"sms": {
  "recipients": [
    "+15551234567",  // Primary
    "+15559876543"   // Secondary
  ]
}
```

Then in code:
```python
for phone in recipients:
    sms.send_sms(phone, message)
```

### Custom Message Templates
Edit `src/core/sms_notifier.py`:
```python
def notify_motion(self, phone_number, event_type="motion", confidence=0.0, location="Unknown"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Custom message
    message = f"🎥 {location}: {event_type} ({confidence:.0%})\n"
    message += f"⏰ {timestamp}\n"
    message += f"📍 View: https://me_cam.com:8080"
    
    return self.send_sms(phone_number, message)
```

### Emergency Escalation
```python
# Send to multiple contacts after X minutes of continuous motion
if continuous_motion_duration > 300:  # 5 minutes
    for contact in emergency_contacts:
        sms.send_sms(contact, "⚠️ URGENT: Continuous motion detected!")
```

---

## 🐛 Troubleshooting

### SMS Not Sending

**1. Check Configuration:**
```bash
tail -f logs/mecam_lite.log | grep SMS
```

**2. Verify Credentials:**
```python
from src.core import get_sms_notifier
sms = get_sms_notifier()
print(f"Enabled: {sms.enabled}")
print(f"Provider: {sms.provider}")
```

**3. Check Rate Limiting:**
```bash
cat logs/sms_sent.json
```

**4. Test Manually:**
```python
from src.core.sms_notifier import SMSNotifier

config = {
    "enabled": True,
    "provider": "twilio",
    "twilio": {
        "account_sid": "ACxxxxx",
        "auth_token": "xxxxx",
        "phone_from": "+15551234567",
        "phone_to": "+15559876543"
    }
}

sms = SMSNotifier(config)
result = sms.send_sms("+15559876543", "Test from ME_CAM")
print(f"Sent: {result}")
```

### Common Errors

**Error: "Twilio config incomplete"**
```bash
# Check your config file
cat hub_config.json | grep -A 10 sms

# Verify all required fields are present
```

**Error: "Rate limited"**
```bash
# Clear rate limit history
rm logs/sms_sent.json

# Or wait for rate limit to expire
```

**Error: "SMS notifications disabled"**
```bash
# Enable in config
python3 << EOF
from src.core import get_config, save_config
cfg = get_config()
cfg['sms_enabled'] = True
cfg['send_motion_to_emergency'] = True
save_config(cfg)
EOF
```

---

## 📊 SMS Logs and History

### View Recent SMS:
```bash
cat logs/sms_sent.json | jq '.'
```

### Count Today's SMS:
```bash
python3 << EOF
import json
from datetime import datetime

with open('logs/sms_sent.json') as f:
    history = json.load(f)

today = datetime.now().date()
today_sms = [s for s in history if datetime.fromisoformat(s['datetime']).date() == today]
print(f"SMS sent today: {len(today_sms)}")
EOF
```

---

## 🌟 Best Practices

1. **Set Reasonable Rate Limits**
   - 5-10 minutes prevents spam
   - Saves money
   - Avoids annoying recipients

2. **Adjust Motion Sensitivity**
   - Start at 0.5 (medium)
   - Increase if too many false alerts
   - Decrease if missing real motion

3. **Test Before Deployment**
   - Send test messages
   - Verify phone receives them
   - Check message format

4. **Monitor Costs**
   - Check Twilio dashboard weekly
   - Review `sms_sent.json`
   - Adjust rate limits if needed

5. **Have Backup Contacts**
   - Configure multiple phone numbers
   - Use emergency escalation
   - Consider email backup

---

## 🎉 Quick Setup Summary

1. **Sign up:** [Twilio.com](https://www.twilio.com) (free $15 credit)
2. **Get credentials:** Account SID, Auth Token, Phone numbers
3. **Configure:** Web UI at `https://me_cam.com:8080/config`
4. **Enable:** Check boxes for SMS and motion alerts
5. **Test:** Wave at camera, receive SMS in 10 seconds
6. **Done!** You now have SMS motion alerts

---

## 🆘 Still Need Help?

Check the logs:
```bash
tail -f logs/mecam_lite.log | grep -i sms
```

Test SMS independently:
```bash
curl -X POST https://api.twilio.com/2010-04-01/Accounts/ACxxxxx/Messages.json \
  -u ACxxxxx:auth_token \
  -d "From=+15551234567" \
  -d "To=+15559876543" \
  -d "Body=Test from command line"
```

---

**Your ME_CAM is now ready to send instant motion alerts to your phone! 📱🚨**
