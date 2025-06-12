# 🚀 Replit Deployment Guide

## Overview

BookingAssistant can be deployed on Replit using a **unified single-port architecture** that combines all services (dashboard, Slack interactions, and email processing) into one FastAPI application.

## 🏗️ Architecture for Replit

### Single Port Solution
```
https://your-repl-name.replit.app/
├── /                          # Dashboard homepage
├── /dashboard                 # Dashboard (alias)
├── /api/*                     # Analytics APIs
├── /slack/interactions        # Slack button handling
├── /slack/events             # Slack events
├── /start_agent_v2           # Email processing
├── /health                   # Health check
└── /docs                     # API documentation
```

### Service Mapping
- **Dashboard** (was port 8001) → `/` and `/dashboard`
- **Slack Endpoint** (was port 8002) → `/slack/*`
- **Main API** → `/start_agent_v2`
- **Analytics** → `/api/*`

## 🚀 Deployment Steps

### 1. Create New Replit

1. Go to [replit.com](https://replit.com)
2. Click **"Create Repl"**
3. Choose **"Import from GitHub"**
4. Enter your repository URL
5. Name your Repl (e.g., "BookingAssistant")

### 2. Configure Environment Variables

In your Replit, go to **Secrets** (🔒 icon) and add:

```bash
# Neon PostgreSQL Database
PGDATABASE=neondb
PGUSER=neondb_owner
PGPASSWORD=your_neon_password
PGHOST=your-neon-host.aws.neon.tech
PGPORT=5432

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Gmail API (Service Account)
GMAIL_SERVICE_ACCOUNT_FILE=service-account-key.json
GMAIL_TARGET_EMAIL=aidrian@podcastguestlaunch.com

# Google Drive
GDRIVE_CLIENT_ROOT_FOLDER_ID=your_google_drive_folder_id

# AstraDB Vector Database
ASTRA_DB_APPLICATION_TOKEN=your_astra_token
ASTRA_DB_API_ENDPOINT=your_astra_endpoint

# Slack Integration
SLACK_WEBHOOK_URL=your_slack_webhook_url
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# Attio CRM (Optional)
ATTIO_API_KEY=your_attio_api_key

# Production Mode
TESTING_MODE=false
```

### 3. Upload Service Account Key

1. Upload your `service-account-key.json` to the root directory
2. Make sure the filename matches `GMAIL_SERVICE_ACCOUNT_FILE`

### 4. Setup Database

In the Replit console, run:

```bash
python setup_neon_database.py
```

### 5. Test the Deployment

```bash
python test_neon_connection.py
```

### 6. Start the Service

Click the **"Run"** button in Replit. The unified app will start automatically.

## 🔗 Configure Slack App for Replit

### Update Slack App URLs

1. Go to your [Slack App settings](https://api.slack.com/apps)
2. Update **Interactive Components** Request URL:
   ```
   https://your-repl-name.replit.app/slack/interactions
   ```
3. Update **Event Subscriptions** Request URL:
   ```
   https://your-repl-name.replit.app/slack/events
   ```

### Get Your Replit URL

Your Replit URL format is:
```
https://your-repl-name--your-username.repl.co
```

## 📊 Access Your Services

Once deployed, access different services at:

- **📊 Dashboard**: `https://your-repl-name.replit.app/`
- **📧 Email Processing**: `POST https://your-repl-name.replit.app/start_agent_v2`
- **🔗 Slack Interactions**: `https://your-repl-name.replit.app/slack/interactions`
- **📈 Analytics API**: `https://your-repl-name.replit.app/api/overview`
- **🔄 Health Check**: `https://your-repl-name.replit.app/health`
- **📚 API Docs**: `https://your-repl-name.replit.app/docs`

## 🎯 Testing Email Processing

### API Test
```bash
curl -X POST "https://your-repl-name.replit.app/start_agent_v2" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "Hi, interested in having our CEO on your podcast.",
    "subject": "Podcast Guest Request",
    "sender_name": "John Doe",
    "sender_email": "john@example.com"
  }'
```

### Webhook Integration
Set your email webhook to:
```
https://your-repl-name.replit.app/start_agent_v2
```

## 🔧 Replit-Specific Features

### Always-On Service
- **Free Tier**: Service sleeps after inactivity
- **Hacker Plan**: Always-on available for $7/month
- **Recommended**: Use always-on for production

### Auto-Scaling
- Replit handles scaling automatically
- Database connections are pooled
- No manual server management needed

### Monitoring
The unified app includes comprehensive monitoring:
- **Health endpoint**: `/health`
- **Service status**: Database, Slack, and API status
- **Real-time metrics**: Built into dashboard

## 🐛 Troubleshooting

### Common Issues

**1. Service Won't Start**
```bash
# Check logs in Replit console
# Verify all environment variables are set
# Check database connection
```

**2. Slack Interactions Not Working**
- Verify Slack app URLs point to your Replit domain
- Check SLACK_WEBHOOK_URL in secrets
- Test with `/health` endpoint first

**3. Database Connection Failed**
```bash
# Test in Replit console
python -c "import os; print('DB Host:', os.getenv('PGHOST'))"
python test_neon_connection.py
```

**4. Email Processing Errors**
- Check OpenAI API key
- Verify AstraDB credentials
- Test with simple email via `/docs` interface

### Performance Optimization

**Database Connection Pooling**
- Configured automatically
- 1-20 connections per service
- Handles concurrent requests

**Memory Management**
- Services share memory efficiently
- Vector operations optimized
- Minimal resource usage

## 🔐 Security Considerations

### Environment Variables
- Use Replit Secrets (never hardcode)
- Rotate API keys regularly
- Limit database access

### API Security
- All endpoints have error handling
- Input validation on all routes
- Rate limiting available via FastAPI

### Database Security
- SSL connections to Neon
- Connection pooling with timeouts
- Prepared statements prevent injection

## 🚀 Production Checklist

- [ ] All environment variables configured in Replit Secrets
- [ ] Database schema created with `setup_neon_database.py`
- [ ] Slack app URLs updated to Replit domain
- [ ] Service account key uploaded
- [ ] Health check returning healthy status
- [ ] Test email processing working
- [ ] Dashboard displaying data
- [ ] Always-on enabled (recommended)

## 🎉 Deployment Complete

Your BookingAssistant is now running on Replit with:
- ✅ Single-port unified architecture
- ✅ Real-time dashboard and analytics
- ✅ Interactive Slack integration
- ✅ Comprehensive email processing
- ✅ Production-ready monitoring
- ✅ Automatic scaling and reliability

Access your dashboard at: `https://your-repl-name.replit.app/`