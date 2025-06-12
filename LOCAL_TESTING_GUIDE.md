# 🖥️ BookingAssistant - Local Testing Guide (Windows 11)

## Overview
Complete guide for testing the BookingAssistant system on your local Windows 11 machine before deployment to Replit. This covers prompt management via dashboard and Slack email notifications.

## Prerequisites Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and configure:

```bash
# Core API Keys (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Neon PostgreSQL Database (Required)
PGDATABASE=neondb
PGUSER=neondb_owner  
PGPASSWORD=npg_xIkjLGvn4t0R
PGHOST=ep-ghggfhfd-a6uiiall.us-west-2.aws.neon.tech
PGPORT=5432

# Google Services (Required for document extraction)
GDRIVE_CLIENT_ROOT_FOLDER_ID=your_google_drive_folder_id
GMAIL_SERVICE_ACCOUNT_FILE=path/to/service-account-key.json
GMAIL_TARGET_EMAIL=example@youremaildomain.com

# AstraDB Vector Database (Required)
ASTRA_DB_APPLICATION_TOKEN=your_astra_token
ASTRA_DB_API_ENDPOINT=your_astra_endpoint

# Slack Integration (Required for notifications)
SLACK_WEBHOOK_URL=your_slack_webhook_url_here
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# Dashboard Security (Required - Change for production!)
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=BookingAssistant2022!
DASHBOARD_SECRET_KEY=your_secret_key_here_minimum_32_characters

# Testing Mode (set to "false" to enable Slack/Gmail)
TESTING_MODE=false
```

## Testing Options

### Option 1: Complete System Test (3 Terminals)

**Terminal 1: Secure Dashboard**
```bash
python secure_dashboard_app.py
```
- Access: http://localhost:8001/login
- Login: admin / BookingAssistant2022!
- Features: Prompt management, analytics, metrics

**Terminal 2: Slack Interaction Endpoint**
```bash
python start_slack_endpoint.py
```
- Runs on: http://localhost:8002
- Handles Slack button interactions and feedback

**Terminal 3: Email Processing (Choose one)**

**For Production Email Polling:**
```bash
python run_assistant.py
```
- Polls Gmail and Maildoso every 60 seconds
- Processes real incoming emails
- Sends Slack notifications for review

**For Single Email Testing:**
```bash
python test_complete_functionality.py
```
- Tests entire pipeline with 5 sample emails
- No real email polling
- Safe for testing without external calls

**For API Testing:**
```bash
curl -X POST http://localhost:8001/start_agent_v2 \
  -H "Content-Type: application/json" \
  -d '{"email":"Test email content","sender_email":"test@example.com","subject":"Test Subject","sender_name":"Test User"}'
```

### Option 2: Testing Mode (Safe Testing)

Set `TESTING_MODE=true` in `.env` to:
- Skip Slack notifications 
- Skip Gmail draft creation
- Test pipeline logic only

```bash
python test_complete_functionality.py
```

### Option 3: Individual Component Testing

**Database Connection:**
```bash
python test_neon_connection.py
```

**Dashboard Endpoints:**
```bash
python test_dashboard_endpoints.py
```

**Slack Integration:**
```bash
python test_phase3_feedback.py
```

**Security Setup:**
```bash
python test_security_setup.py
```

## Prompt Manager Testing

### 1. Access Dashboard
- Go to http://localhost:8001/login
- Login with admin credentials
- Navigate to prompt management section

### 2. View Existing Prompts
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8001/api/prompts
```

**Available Prompts:**
- `classification_fewshot` - Email classification
- `draft_generation_prompt` - Main draft generation  
- `slack_notification_prompt` - Slack message format
- `query_for_relevant_email_prompt` - Vector search queries
- `rejection_strategy_prompt` - Rejection analysis
- `soft_rejection_drafting_prompt` - Soft rejection responses
- `draft_editing_prompt` - Draft refinement
- `continuation_decision_prompt` - Processing decisions
- `client_gdrive_extract_prompt` - Document extraction

### 3. Create New Prompt Version
```bash
curl -X POST http://localhost:8001/api/prompts/draft_generation_prompt/versions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Your new prompt content","description":"Test version"}'
```

### 4. Activate Different Version
```bash
curl -X POST http://localhost:8001/api/prompts/draft_generation_prompt/activate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version_id":"your_version_id"}'
```

## Slack Bot Setup & Testing

### 1. Create Slack App
1. Go to https://api.slack.com/apps
2. Create new app "BookingAssistant"
3. Enable **Incoming Webhooks**
4. Add webhook URL to `.env`

### 2. Interactive Components (Optional)
For button interactions:
1. Enable **Interactive Components**
2. Set Request URL: `http://your-domain:8002/slack/interactions`
3. Set **Event Subscriptions** URL: `http://your-domain:8002/slack/events`

### 3. Test Slack Integration
```bash
python -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv()

webhook_url = os.getenv('SLACK_WEBHOOK_URL')
response = requests.post(webhook_url, json={'text': '🧪 Test from BookingAssistant'})
print(f'Status: {response.status_code}')
"
```

## Expected Workflow

### 1. Process Test Email
When you run `run_assistant.py` or send a test email:

**Console Output:**
```
📧 PROCESSING EMAIL FROM: test@example.com
📝 SUBJECT: Podcast Guest Request
👤 SENDER: Test User
================================================================
✅ Classification: Conditional
📁 Document Status: Success
📧 Draft Status: SKIPPED (Testing Mode)
💬 Slack Status: Enhanced Slack notification sent (Status: 200)
📈 Session ID: abc123...
```

### 2. Slack Notification
You'll receive an interactive Slack message with:
- ⭐ Quality rating buttons (1-5 stars)
- ✅ Approve & Send | ✏️ Edit Draft | ❌ Reject
- 📊 Attio Campaign | 📁 Client Drive links
- 💬 Add Feedback option

### 3. Dashboard Analytics
Visit http://localhost:8001/dashboard to see:
- Real-time processing metrics
- Classification analytics
- Draft quality scores
- Session timeline
- Prompt performance data

## Windows 11 Specific Notes

### PowerShell Commands
```powershell
# Set environment variables for current session
$env:TESTING_MODE="false"
$env:OPENAI_API_KEY="your_key_here"

# Start services in separate windows
Start-Process python -ArgumentList "secure_dashboard_app.py"
Start-Process python -ArgumentList "start_slack_endpoint.py"
Start-Process python -ArgumentList "run_assistant.py"
```

### Windows Firewall
Allow Python through Windows Firewall for ports:
- 8001 (Dashboard)
- 8002 (Slack endpoint)

### VS Code Integration
Add to VS Code settings for better development:
```json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true
}
```

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
- Check PostgreSQL credentials in `.env`
- Verify network connectivity to Neon
- Run `python test_neon_connection.py`

**2. Slack Notifications Not Working**
- Verify `SLACK_WEBHOOK_URL` in `.env`
- Test webhook manually with curl
- Check `TESTING_MODE` is set to `false`

**3. OpenAI API Errors**
- Verify `OPENAI_API_KEY` in `.env`
- Check API quota and billing
- Test with small request first

**4. Google Services Failed**
- Check `GMAIL_SERVICE_ACCOUNT_FILE` path
- Verify service account permissions
- Enable Gmail API in Google Cloud Console

**5. Import Errors**
- Run `pip install -r requirements.txt`
- Check Python version (3.8+)
- Verify virtual environment activation

### Debug Commands

**Check Environment:**
```bash
python -c "import os; print('DB Host:', os.getenv('PGHOST', 'NOT SET'))"
python -c "import os; print('OpenAI:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
```

**Test Services:**
```bash
python test_complete_functionality.py  # Full pipeline test
python test_neon_connection.py         # Database test
python test_dashboard_endpoints.py     # Dashboard test
```

**Check Logs:**
- Dashboard logs: Terminal running `secure_dashboard_app.py`
- Slack endpoint logs: Terminal running `start_slack_endpoint.py`
- Processing logs: Terminal running `run_assistant.py`

## Next Steps

After successful local testing:

1. **Validate All Features Work**
   - Prompt management via dashboard ✓
   - Email processing with classification ✓
   - Slack notifications with buttons ✓
   - Document extraction from Google Drive ✓
   - Draft generation and editing ✓

2. **Prepare for Replit Deployment**
   - Export environment variables to Replit
   - Update database credentials for production
   - Configure Slack app URLs for Replit domain
   - Test all endpoints work from external URLs

3. **Production Configuration**
   - Change default dashboard credentials
   - Update webhook URLs in Slack app
   - Set up monitoring and alerts
   - Configure backup procedures

---

🎉 **Your BookingAssistant is now ready for full local testing with prompt management and Slack integration!**