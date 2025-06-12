# 💬 Slack Notifications Setup Guide

## Overview

This guide shows you how to enable Slack notifications in the BookingAssistant system. Slack notifications provide real-time alerts when emails are processed and allow human review and approval of generated responses.

## 🚀 Quick Setup (Previous Iteration)

### Method 1: Enable in Current System

In the previous iteration (before dashboard), Slack notifications are controlled by environment variables:

1. **Set Environment Variables** in your `.env` file:
```bash
# Slack Integration
SLACK_WEBHOOK_URL=your_slack_webhook_url_here
TESTING_MODE=false
```

2. **Run the Assistant:**
```bash
python run_assistant.py
```

That's it! The system will automatically send Slack notifications when processing emails.

## 🔧 Detailed Slack App Setup

### Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name: "BookingAssistant" 
4. Choose your workspace

### Step 2: Set Up Incoming Webhooks

1. In your app settings, go to **"Incoming Webhooks"**
2. Turn on **"Activate Incoming Webhooks"**
3. Click **"Add New Webhook to Workspace"**
4. Choose the channel where you want notifications (e.g., #email-processing)
5. **Copy the Webhook URL** - this is your `SLACK_WEBHOOK_URL`

### Step 3: Configure Permissions (Optional)

1. Go to **"OAuth & Permissions"**
2. Add these **Bot Token Scopes**:
   - `incoming-webhook` (required)
   - `chat:write` (for future features)
   - `chat:write.public` (for future features)

### Step 4: Install App to Workspace

1. Go to **"Install App"**
2. Click **"Install to Workspace"**
3. Authorize the app

### Step 5: Update Environment Variables

Add to your `.env` file:
```bash
# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
TESTING_MODE=false
```

## 📱 What Slack Notifications Look Like

### Basic Notification (Previous Iteration)
```
📧 New Email Processed

From: client@example.com
Subject: Podcast Guest Request
Classification: Conditional

Generated Response:
[Preview of the AI-generated response...]

Links:
• Attio Campaign: [Link]
• Client Drive: [Link]
```

### Enhanced Notification (Current Iteration)
```
📧 New Email Response Ready
From: client@example.com
Subject: Podcast Guest Request
Session: abc12345...

AI Analysis: [Generated analysis summary]

Generated Draft:
[Draft content preview...]

⭐⭐⭐⭐⭐ Quality Rating Buttons (1-5 stars)

✅ Approve & Send | ✏️ Edit Draft | ❌ Reject

📊 Attio Campaign | 📁 Client Drive | 💬 Add Feedback
```

## 🔄 Enabling Slack in Different Versions

### Previous Iteration (Simple)

**File: `src/utils.py`**
```python
def send_interactive_message(message, draft, sender_email, subject, attio_url="", gdrive_url=""):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL not set")
        return 400
    
    # Send simple notification
    payload = {
        "text": f"📧 New Email from {sender_email}",
        "blocks": [
            # ... notification blocks
        ]
    }
    
    response = requests.post(webhook_url, json=payload)
    return response.status_code
```

**Enable by:**
1. Setting `SLACK_WEBHOOK_URL` in `.env`
2. Setting `TESTING_MODE=false`
3. Running `python run_assistant.py`

### Current Iteration (Enhanced)

**File: `src/slack_feedback_service.py`**
```python
def create_enhanced_interactive_message(self, message, draft, sender_email, subject, session_id):
    # Enhanced notification with feedback buttons
    status_code = slack_feedback.create_enhanced_interactive_message(...)
    return status_code
```

**Enable by:**
1. Setting up secure dashboard: `python secure_dashboard_app.py`
2. Configuring Slack app with interaction endpoints
3. Setting webhook URL in environment variables

## 🛠️ Troubleshooting Slack Notifications

### Common Issues

**1. No Notifications Received**
```bash
# Check environment variables
python -c "import os; print('Webhook URL:', os.getenv('SLACK_WEBHOOK_URL')[:50] + '...' if os.getenv('SLACK_WEBHOOK_URL') else 'Not set')"

# Check testing mode
python -c "import os; print('Testing Mode:', os.getenv('TESTING_MODE', 'not set'))"
```

**2. Webhook URL Invalid**
- Verify the URL starts with `https://hooks.slack.com/services/`
- Make sure you copied the complete URL
- Test the webhook manually:
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message from BookingAssistant"}' \
  YOUR_WEBHOOK_URL
```

**3. Permissions Error**
- Check that the app is installed in your workspace
- Verify the channel permissions where notifications are sent
- Ensure the app has `incoming-webhook` scope

**4. Testing Mode Enabled**
```bash
# Disable testing mode
echo "TESTING_MODE=false" >> .env
```

### Debug Mode

Enable debug logging by adding to your `.env`:
```bash
# Debug Slack notifications
SLACK_DEBUG=true
```

This will print detailed information about Slack API calls.

## 🚀 Advanced Slack Features

### Interactive Buttons (Current Version)

The enhanced version includes interactive buttons for:
- **Quality Rating**: 1-5 stars for draft quality
- **Approve/Edit/Reject**: Action buttons for draft management
- **Feedback Collection**: Additional comments and suggestions

### Slack App Configuration for Interactive Features

1. **Enable Interactive Components**:
   - Go to **"Interactive Components"**
   - Set Request URL: `https://your-domain.com:8002/slack/interactions`

2. **Set Up Event Subscriptions**:
   - Go to **"Event Subscriptions"**
   - Set Request URL: `https://your-domain.com:8002/slack/events`

### Multiple Notification Channels

Configure different channels for different types of notifications:

```bash
# Multiple webhook URLs
SLACK_WEBHOOK_URL_APPROVALS=https://hooks.slack.com/services/.../approvals
SLACK_WEBHOOK_URL_ERRORS=https://hooks.slack.com/services/.../errors
SLACK_WEBHOOK_URL_METRICS=https://hooks.slack.com/services/.../metrics
```

## 📊 Monitoring Slack Integration

### Health Checks

Check if Slack integration is working:
```bash
# Test webhook connectivity
python -c "
import requests
import os
webhook_url = os.getenv('SLACK_WEBHOOK_URL')
if webhook_url:
    response = requests.post(webhook_url, json={'text': 'Test from BookingAssistant'})
    print(f'Status: {response.status_code}')
else:
    print('No webhook URL configured')
"
```

### Analytics

The dashboard tracks Slack notification metrics:
- **Notification Success Rate**: How many notifications were sent successfully
- **Response Time**: Time from email processing to Slack notification
- **User Interactions**: Button clicks and feedback responses

## 🔐 Security Considerations

### Webhook URL Security

- **Keep webhook URLs secret** - they provide access to your Slack workspace
- **Use HTTPS only** - never use HTTP webhook URLs
- **Rotate URLs periodically** - regenerate webhook URLs regularly
- **Monitor usage** - check for unexpected activity

### Data Privacy

- **Email content** is sent to Slack - ensure this complies with your privacy policies
- **Client information** may be included in notifications
- **Consider data retention** policies for Slack messages

## 🎯 Testing Slack Integration

### Quick Test Script

```python
#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_slack_webhook():
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL not configured")
        return False
    
    test_payload = {
        "text": "🧪 Test notification from BookingAssistant",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Test Successful!* Your Slack integration is working correctly."
                }
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=test_payload)
        if response.status_code == 200:
            print("✅ Slack notification sent successfully!")
            return True
        else:
            print(f"❌ Slack notification failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return False

if __name__ == "__main__":
    test_slack_webhook()
```

Save as `test_slack.py` and run: `python test_slack.py`

---

🎉 **Your Slack notifications are now configured and ready to keep you informed about email processing in real-time!**