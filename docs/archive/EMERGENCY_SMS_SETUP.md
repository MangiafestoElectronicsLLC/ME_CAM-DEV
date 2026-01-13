# Quick Emergency SMS Setup

## For Phone Number: 585-227-4686

### Step 1: Determine Your Carrier
You need to know your phone carrier to use email-to-SMS gateway.

### Step 2: Configure Email in ME_CAM

1. **Go to web dashboard:** `http://10.2.1.4:8080`
2. **Login** with U123
3. **Go to Config/Settings**
4. **Enable Email** and enter:

#### If using Gmail:
```
SMTP Server: smtp.gmail.com
SMTP Port: 587
Username: your-gmail@gmail.com
Password: [App Password - see below]
From Address: your-gmail@gmail.com
To Address: 5852274686@[carrier-gateway]
```

#### Carrier SMS Gateways (replace [carrier-gateway]):
- **Verizon:** `5852274686@vtext.com`
- **AT&T:** `5852274686@txt.att.net`
- **T-Mobile:** `5852274686@tmomail.net`
- **Sprint:** `5852274686@messaging.sprintpcs.com`
- **US Cellular:** `5852274686@email.uscc.net`

### Step 3: Get Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in to your Gmail account
3. Create app password for "Mail"
4. Copy the 16-character password
5. Use this password (NOT your regular Gmail password)

### Step 4: Test Configuration

Run on your Pi:
```bash
cd ~/ME_CAM/ME_CAM-DEV
source venv/bin/activate

python3 << 'EOF'
from cloud.email_notifier import EmailNotifier

# Replace with YOUR values:
notifier = EmailNotifier(
    enabled=True,
    smtp_host='smtp.gmail.com',
    smtp_port=587,
    username='your-email@gmail.com',
    password='your-app-password',
    from_addr='your-email@gmail.com',
    to_addr='5852274686@vtext.com'  # Change vtext.com to YOUR carrier
)

notifier.send_alert(
    "TEST - ME_CAM Emergency",
    "This is a test message. If you receive this, emergency alerts are working!"
)
print("Test message sent!")
EOF
```

### Alternative: Use Email Instead of SMS

If SMS gateway doesn't work, configure to send to regular email:
```
To Address: your-email@gmail.com
```

You'll receive email instead of text message.

## Troubleshooting

### Not receiving messages?

1. **Check spam folder** - first message might go to spam
2. **Verify carrier gateway** - wrong gateway = no message
3. **Check Gmail app password** - must use app password, not regular password
4. **Check phone number format** - must be 10 digits, no dashes/spaces: `5852274686`

### Gmail Security Error?

Enable "Less secure app access" or use App Passwords:
https://support.google.com/accounts/answer/185833

### Still not working?

**Use a free SMS API service:**
- Twilio (free trial): https://www.twilio.com
- SendGrid SMS
- AWS SNS

Or just use email - most reliable option.
