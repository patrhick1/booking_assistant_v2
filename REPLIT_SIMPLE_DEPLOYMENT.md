# 🚀 Replit Deployment Guide - Simple Version

## Quick Deploy to Replit

### Option 1: Upload Existing Project
1. **Create new Replit** → Choose "Import from GitHub" or "Upload files"
2. **Upload your project files** (zip the BookingAssistant folder)
3. **Replit will auto-detect** the configuration from `.replit` and `replit.nix`

### Option 2: Manual Setup
1. **Create new Python Replit**
2. **Upload these essential files:**
   ```
   📁 src/ (entire folder)
   📄 replit_unified_app.py
   📄 requirements.txt
   📄 .env
   📄 .replit
   📄 replit.nix
   ```

## 🔧 Configuration Files

### `.replit` (Already configured)
```ini
run = "python replit_unified_app.py"
language = "python3"
entrypoint = "replit_unified_app.py"
```

### `replit.nix` (Already configured)
```nix
{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.python311Packages.pip
  ];
}
```

### `requirements.txt` (Your existing file)
```txt
fastapi
uvicorn
python-dotenv
langchain
langchain-openai
langgraph
psycopg2-binary
astrapy
requests
# ... other dependencies
```

## 🌍 Environment Variables in Replit

### Required Variables:
1. **Go to Replit Secrets** (🔒 icon in sidebar)
2. **Add these secrets:**

```env
# Email Services
MAILODOSO_IMAP_HOST=imap.apollo.maildoso.com
MAILODOSO_IMAP_PORT=993
MAILODOSO_USER=podcastguestlaunch@maildoso.email
MAILODOSO_PASSWORD=your_password

# Google Services
GOOGLE_APPLICATION_CREDENTIALS=src/service-account-key.json
GDRIVE_CLIENT_ROOT_FOLDER_ID=your_folder_id
GMAIL_TARGET_EMAIL=aidrian@podcastguestlaunch.com

# OpenAI
OPENAI_API_KEY=sk-proj-your-key

# Database (if using)
PGDATABASE=neondb
PGUSER=neondb_owner
PGPASSWORD=your_db_password
PGHOST=your-host.neon.tech
PGPORT=5432

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url

# Vector Database
ASTRA_DB_APPLICATION_TOKEN=your_token
ASTRA_DB_API_ENDPOINT=your_endpoint
ASTRA_DB_KEYSPACE=PGL
ASTRA_DB_COLLECTION=email_threads
```

## 🚀 How It Works on Replit

### The Unified App (`replit_unified_app.py`):
1. **Combines everything** - Email polling + Web interface + API
2. **Background processing** - Automatically checks emails every 2 minutes
3. **Web dashboard** - Shows status and allows manual testing
4. **API endpoints** - For webhook integrations

### Key Features:
- ✅ **Auto-starts** when Replit runs
- ✅ **Background email polling** (like `run_assistant.py`)
- ✅ **Web interface** at the Replit URL
- ✅ **API endpoints** for external integrations
- ✅ **Webhook support** for real-time email processing

## 📱 Using Your Deployed App

### 1. Web Interface:
- **Your Replit URL** → Shows dashboard with status
- **Test email processing** with the "Test" button
- **Monitor stats** and uptime

### 2. API Endpoints:
```bash
# Process email via webhook
POST https://your-replit-url.repl.co/process-email
{
  "email_text": "Email content...",
  "subject": "Subject line",
  "sender_name": "John Doe",
  "sender_email": "john@example.com"
}

# Check status
GET https://your-replit-url.repl.co/status

# Health check
GET https://your-replit-url.repl.co/health
```

## 🔧 Deployment Steps

### 1. Prepare Files
```bash
# On your local machine
zip -r bookingassistant.zip . -x "*.git*" "*__pycache__*" "*.pyc"
```

### 2. Create Replit
1. Go to [replit.com](https://replit.com)
2. Click "Create Repl"
3. Choose "Import from ZIP"
4. Upload your zip file

### 3. Add Secrets
1. Click the 🔒 "Secrets" tab
2. Add all environment variables from your `.env` file
3. **Important:** Upload `service-account-key.json` to the `src/` folder

### 4. Install Dependencies
```bash
# Replit usually auto-installs, but if needed:
pip install -r requirements.txt
```

### 5. Run!
```bash
# Click the "Run" button or:
python replit_unified_app.py
```

## 🎯 Expected Behavior

### After deployment:
1. **App starts** → Shows "Starting BookingAssistant for Replit..."
2. **Background polling begins** → Checks emails every 2 minutes
3. **Web interface available** → Visit your Replit URL
4. **Dashboard shows:**
   - ✅ System status (Active/Inactive)
   - 📊 Emails processed count
   - 🕐 Last check time
   - 🧪 Test email button

### Logs will show:
```
🚀 Starting BookingAssistant for Replit...
🚀 Starting background email polling...
🔍 Checking for new emails...
No new emails found.
```

## 🚨 Common Issues & Solutions

### 1. **Import Errors**
- **Problem:** `ModuleNotFoundError`
- **Solution:** Check `requirements.txt` and run `pip install -r requirements.txt`

### 2. **Environment Variables**
- **Problem:** `ValueError: Required environment variable`
- **Solution:** Add all secrets in Replit Secrets tab

### 3. **Google Service Account**
- **Problem:** `FileNotFoundError: service-account-key.json`
- **Solution:** Upload the JSON file to `src/` folder in Replit

### 4. **Database Connection**
- **Problem:** Database errors
- **Solution:** Verify PostgreSQL credentials in Secrets

## 🎉 Success Indicators

✅ **Web interface loads** at your Replit URL  
✅ **Background polling active** (shows in logs)  
✅ **Test email processing works** (click Test button)  
✅ **No error messages** in console  
✅ **Email checking every 2 minutes**  

## 🔄 Updating Your Deployment

1. **Make changes locally**
2. **Re-zip and re-upload** to Replit
3. **Or edit files directly** in Replit editor
4. **Restart** by clicking "Run" again

Your simple email assistant is now running 24/7 on Replit! 🎉