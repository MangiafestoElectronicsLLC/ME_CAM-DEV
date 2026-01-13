# Emergency Features Guide - ME_CAM

## Overview

ME_CAM now includes comprehensive emergency notification features for both **medical monitoring** (seizure detection, falls) and **security alerts** (theft, break-ins). The system uses AI-enhanced motion detection with intelligent camera coordination to prevent conflicts between live streaming and recording.

---

## 🚨 Emergency Modes

### 1. **Manual Mode** (Default)
- Emergency alerts only when you press the SOS button
- No automatic detection
- Safest option for testing

### 2. **Medical Monitoring Mode**
- AI detects unusual motion patterns (seizures, falls, prolonged inactivity)
- Automatically alerts your wife/family
- Includes video evidence of the event
- **Use Case**: Monitoring elderly, epilepsy patients, medical conditions

### 3. **Security Mode**
- Detects intrusions, break-ins, theft
- Sends alerts with video to property owner
- Can forward to police and insurance companies
- **Use Case**: Home security, store monitoring, vehicle surveillance

### 4. **Both Medical & Security**
- Combined monitoring
- Different alert recipients for different event types

---

## 📋 Setup Instructions

### Step 1: Update Your Pi

SSH into your Raspberry Pi:

```bash
ssh pi@raspberrypi.local
cd ~/ME_CAM-DEV
git pull origin main
```

### Step 2: Install New Dependencies

The new features should work with existing dependencies, but verify:

```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Restart the Service

```bash
sudo systemctl restart mecamera
sudo systemctl status mecamera
```

---

## ⚙️ Configuration

### Access Settings Page

1. Open browser: `http://raspberrypi.local:8080`
2. Login with your credentials
3. Click **⚙️ Configure** at bottom of dashboard
4. Scroll to **🚨 Emergency Contacts** section (red border)

### Emergency Contacts Configuration

#### **Device Location**
- Enter physical location: "Living Room", "Front Door", "Bedroom", etc.
- This is included in all emergency alerts

#### **Primary Emergency Contact (Medical)**
- For medical emergencies (seizures, falls, unresponsive)
- Enter phone number using carrier SMS gateway OR email
- **SMS Examples:**
  - Verizon: `5852274686@vtext.com`
  - AT&T: `5852274686@txt.att.net`
  - T-Mobile: `5852274686@tmomail.net`
  - Sprint: `5852274686@messaging.sprintpcs.com`
  
  *(Replace `5852274686` with your wife's phone number, no dashes or spaces)*

- **Email Example:** `wife@example.com`

#### **Property Owner Email (Security)**
- For security alerts (theft, break-in)
- Enter your email address
- Receives video evidence automatically

#### **Additional Security Contacts**
- Comma-separated list
- Police department email: `police@dept.gov`
- Insurance company: `claims@insurance.com`
- Neighbors, security company, etc.

#### **Emergency Detection Mode**
- **Manual**: SOS button only (safest for testing)
- **Medical**: Automatic medical alerts
- **Security**: Automatic intrusion alerts
- **Both**: All alerts enabled

---

## 📧 Email Configuration

Emergency alerts require email to be configured. This works for both email and SMS (via carrier gateways).

### Gmail Setup (Recommended)

1. Go to Settings → **📧 Email Notifications**
2. Check **Enable Email Alerts**
3. Enter:
   - **SMTP Server**: `smtp.gmail.com`
   - **SMTP Port**: `587`
   - **Username**: `your-gmail@gmail.com`
   - **Password**: **[See below for App Password]**
   - **From Address**: `your-gmail@gmail.com`
   - **To Address**: `your-email@gmail.com` (or leave blank, will use emergency contacts)

### Getting Gmail App Password

**IMPORTANT**: You CANNOT use your regular Gmail password. You must create an "App Password":

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in to your Gmail account
3. Select **Mail** as the app
4. Select **Other** as the device, name it "ME_CAM"
5. Click **Generate**
6. Copy the 16-character password (no spaces)
7. Paste this into the ME_CAM password field

### Testing Email

After configuring email:
1. Save settings
2. Go to dashboard
3. Click **🚨 SOS Alert** button
4. Check your phone/email for the alert

---

## 🎯 How Emergency Alerts Work

### Manual SOS Button

**Location**: Dashboard → **Quick Actions** → Red **🚨 SOS Alert** button

**What happens:**
1. You press the button
2. System finds most recent video recording
3. Sends emergency alert email to Primary Emergency Contact
4. Includes video attachment (if available)
5. Email contains:
   - Device name and location
   - Timestamp
   - Emergency contact info
   - Video evidence link

### Automatic Medical Alerts

**When enabled** (Emergency Mode = Medical or Both):

1. Motion detection runs in background (every 5 seconds)
2. AI analyzes motion patterns
3. Detects:
   - Sudden falls (rapid downward motion)
   - Seizure-like movements (rapid repetitive motion)
   - Prolonged stillness after activity
4. Triggers medical emergency alert
5. Sends to **Primary Emergency Contact** (your wife)
6. Includes 30-second video clip of the event

**Alert Format:**
```
Subject: 🚨 MEDICAL EMERGENCY - SEIZURE

URGENT - MEDICAL EMERGENCY DETECTED

Event Type: SEIZURE
Device: Living Room Camera
Location: Living Room
Time: 2026-01-13 18:45:32

Primary Contact: +1-555-0123

This is an automated alert from ME_CAM monitoring system.
Please check on the person immediately.

Video evidence: Attached
```

### Automatic Security Alerts

**When enabled** (Emergency Mode = Security or Both):

1. Motion detection runs in background
2. AI detects person in frame (not just motion)
3. If person detected when nobody should be home:
4. Triggers security alert
5. Sends to **Owner Email** and **Security Contacts**
6. Includes video evidence for police report

**Alert Format:**
```
Subject: 🚨 SECURITY ALERT - THEFT

SECURITY INCIDENT DETECTED

Incident Type: THEFT
Device: Front Door Camera
Location: Front Door
Time: 2026-01-13 02:15:44

Video Evidence: Attached

This alert has been sent to:
- Property Owner: owner@example.com
- Security Contacts: police@dept.gov, insurance@company.com

For police report, reference:
- Device ID: Front Door Camera
- Timestamp: 2026-01-13T02:15:44
- Evidence File: motion_20260113_021544.mp4
```

---

## 🔧 Technical Details

### Camera Coordination

**Problem Solved**: Previously, camera streaming and motion detection conflicted because libcamera can only be accessed by one process at a time.

**Solution**: New `camera_coordinator.py` module:
- Manages queue for camera access
- Streaming gets **high priority** (always works)
- Motion detection gets **normal priority** (waits for streaming to finish)
- Minimum 500ms delay between camera operations
- Prevents device busy errors

**Result**:
- ✅ Live camera streaming works smoothly
- ✅ Motion detection runs every 2-5 seconds
- ✅ No more camera lock conflicts
- ✅ Both features can run simultaneously

### Motion Detection Behavior

- Runs in background thread
- Checks every 2 seconds (configurable)
- Skips frame capture if camera busy with streaming
- When motion detected:
  - Starts 30-second recording
  - Continues recording if motion persists
  - Stops 5 seconds after motion stops
- Saves to `~/ME_CAM-DEV/recordings/`
- Filename: `motion_YYYYMMDD_HHMMSS.mp4`

### Emergency Handler

New `emergency_handler.py` module provides:
- **Cooldown**: 60 seconds between alerts (prevents spam)
- **Video attachment**: Always includes latest recording
- **Google Drive upload**: If enabled, uploads evidence
- **Multiple recipients**: Can send to multiple contacts
- **Event types**: Medical (seizure, fall) and Security (theft, break-in)

---

## 📱 SMS Setup for Wife's Phone

### Determine Carrier

Find out your wife's phone carrier:
- Verizon
- AT&T
- T-Mobile
- Sprint
- US Cellular

### Configure Primary Emergency Contact

In **Emergency Contacts** section:

**Example for Verizon:**
```
Primary Emergency Contact: 5852274686@vtext.com
```

**Example for AT&T:**
```
Primary Emergency Contact: 5852274686@txt.att.net
```

**Example for T-Mobile:**
```
Primary Emergency Contact: 5852274686@tmomail.net
```

**Important:** 
- Use 10-digit phone number only (no dashes, spaces, or +1)
- Must configure Gmail with App Password
- Test by pressing SOS button
- Check wife's phone for text message

### Troubleshooting SMS

**Not receiving texts?**

1. **Check spam/junk folder** - First message might go to spam
2. **Verify carrier gateway** - Wrong gateway = no message
3. **Check Gmail app password** - Must use app password, not regular password
4. **Try email instead** - Use `wife@example.com` instead of SMS gateway
5. **Check phone number** - Must be 10 digits, no formatting

**Still not working?**

Use a free SMS API service:
- Twilio (free trial): https://www.twilio.com
- SendGrid SMS
- AWS SNS

Or just use email - most reliable option.

---

## 🎬 Usage Examples

### Example 1: Medical Monitoring (Seizure Detection)

**Setup:**
1. Device Location: "Living Room"
2. Primary Emergency Contact: `5551234567@vtext.com` (wife's phone)
3. Emergency Mode: **Medical**
4. Email enabled with Gmail App Password

**Result:**
- Camera monitors living room 24/7
- If seizure-like motion detected → Automatic alert to wife's phone
- Wife receives text: "MEDICAL EMERGENCY - Living Room - Check immediately"
- Video clip shows what happened

### Example 2: Security (Theft Detection)

**Setup:**
1. Device Location: "Front Door"
2. Owner Email: `myemail@example.com`
3. Security Contacts: `police@dept.gov, insurance@company.com`
4. Emergency Mode: **Security**

**Result:**
- Camera monitors front door
- If person detected when nobody home → Automatic security alert
- Owner receives email with video evidence
- Police department receives copy for report
- Insurance company receives copy for claim

### Example 3: Combined Medical + Security

**Setup:**
1. Device Location: "Bedroom"
2. Primary Emergency Contact: `wife@example.com`
3. Owner Email: `myemail@example.com`
4. Security Contacts: `neighbor@example.com`
5. Emergency Mode: **Both**

**Result:**
- Medical events → Alert wife
- Security events → Alert owner + neighbor
- All alerts include video evidence

---

## 🔍 Monitoring & Logs

### Check Service Status

```bash
sudo systemctl status mecamera
```

Look for:
- `[MAIN] Motion detection service initialized`
- `[MOTION] Motion detection service started`
- No camera lock errors

### View Live Logs

```bash
sudo journalctl -u mecamera.service -f
```

Or check log file:
```bash
tail -f ~/ME_CAM-DEV/logs/mecam.log
```

### Look for Emergency Events

```bash
grep -i "EMERGENCY" ~/ME_CAM-DEV/logs/mecam.log
```

### Check Camera Coordination

```bash
grep -i "CAMERA" ~/ME_CAM-DEV/logs/mecam.log | tail -20
```

Should see:
- `[CAMERA] Access granted to streaming`
- `[CAMERA] Access granted to motion_detection`
- `[CAMERA] Access released by streaming`
- No timeout errors

---

## ⚡ Quick Deployment

### One-Command Update

```bash
ssh pi@raspberrypi.local "cd ~/ME_CAM-DEV && git pull origin main && sudo systemctl restart mecamera && sleep 3 && sudo systemctl status mecamera"
```

### Verify Everything Works

1. Open dashboard: `http://raspberrypi.local:8080`
2. Check camera feed is displaying
3. Go to **⚙️ Configure**
4. Set up Emergency Contacts
5. Configure Email with Gmail App Password
6. Save Settings
7. Test SOS button
8. Check phone/email for alert

---

## 🛡️ Security Best Practices

1. **Change default PIN** - First thing after setup
2. **Use strong Gmail App Password** - Never share
3. **Test alerts regularly** - Monthly SOS button test
4. **Keep software updated** - `git pull origin main` monthly
5. **Monitor logs** - Check for suspicious activity
6. **Backup recordings** - Enable Google Drive backup
7. **Secure network** - Use WireGuard VPN for remote access

---

## 📞 Support & Troubleshooting

### Camera not displaying?
- Check: `libcamera-still --list-cameras`
- Verify: No other processes using camera
- Restart: `sudo systemctl restart mecamera`

### Motion detection not recording?
- Check logs for camera coordinator messages
- Verify motion_only = true in config
- Test by waving in front of camera
- Wait 30 seconds for recording to save

### Emergency alerts not sending?
- Verify email configuration (use App Password!)
- Test email separately (command line test)
- Check emergency contacts configured
- Check emergency mode is not "manual"

### Camera streaming AND motion both work?
- Yes! Camera coordinator manages access
- Streaming has high priority
- Motion detection waits its turn
- Check logs for "Access granted" messages

---

## 🎓 Next Steps

1. **Configure your emergency contacts** - Set up wife's phone SMS
2. **Test the SOS button** - Verify alerts work
3. **Enable motion detection** - Start recording events
4. **Set emergency mode** - Choose medical, security, or both
5. **Monitor for a week** - Check logs, verify recordings
6. **Adjust sensitivity** - Tune motion detection if needed
7. **Enable Google Drive** - Automatic cloud backup

---

## 📝 Changelog

**Version: Camera Coordinator + Emergency Handler (2026-01-13)**

✅ **NEW**: Camera access coordination (no more conflicts!)
✅ **NEW**: Medical emergency alerts (seizure detection)
✅ **NEW**: Security alerts with video evidence
✅ **NEW**: Configurable emergency modes
✅ **NEW**: SMS support via carrier email gateways
✅ **NEW**: Multiple emergency contacts (medical vs security)
✅ **FIXED**: Camera streaming + motion detection now work simultaneously
✅ **FIXED**: Device busy errors eliminated
✅ **IMPROVED**: Emergency UI with clear configuration options

---

## 🤝 Support

If you need help:
1. Check this guide first
2. Review logs: `tail -100 ~/ME_CAM-DEV/logs/mecam.log`
3. Check service status: `sudo systemctl status mecamera`
4. Review GitHub issues: https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/issues

**Emergency?** If the ME_CAM system fails to alert during an emergency, ALWAYS have a backup plan (medical alert device, 911, etc.). ME_CAM is a supplemental monitoring tool, not a replacement for professional emergency services.

---

**Stay Safe! 🚨**
