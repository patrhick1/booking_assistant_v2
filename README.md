# BookingAssistant - AI-Powered Email Response System

🤖 **Intelligent podcast booking assistant with real-time performance tracking and human feedback integration**

## 📚 Table of Contents

- [🚀 Replit Deployment (Recommended)](#-replit-deployment) - One-click deployment
- [🎯 Overview](#-overview) - System features and capabilities  
- [🏗️ Architecture](#-architecture) - Technical design
- [🚀 Quick Start](#-quick-start) - Local development setup
- [🔧 Slack App Setup](#-slack-app-setup) - Integration configuration
- [📊 Performance Dashboard](#-performance-dashboard) - Analytics and monitoring
- [💬 Slack Integration Features](#-slack-integration-features) - Interactive workflows
- [🧪 Testing & Development](#-testing--development) - Test suites and validation

## 🎯 Overview

BookingAssistant is an advanced AI-powered email processing system that automatically classifies incoming emails, extracts relevant client documents, generates contextual draft replies, and provides comprehensive performance analytics. The system features interactive Slack integration for human oversight and real-time quality tracking.

### Key Features

🔍 **Smart Email Classification** - Automatically categorizes emails into response types  
📁 **Document Intelligence** - Extracts relevant client documents from Google Drive  
✍️ **Contextual Draft Generation** - Creates personalized responses using RAG  
🎯 **Strategic Rejection Handling** - Special pipeline for challenging rejections  
💬 **Interactive Slack Integration** - Rich feedback interface with quality ratings  
📊 **Real-Time Analytics** - Comprehensive performance monitoring dashboard  
📧 **Gmail Integration** - Automated draft creation with service account auth  

---

## 🏗️ Architecture

### Core Pipeline (LangGraph-Based)

```
Email Input → Classify → Continue Check → Pipeline Routing
                                            ↓
                                    ┌───────────────────┐
                                    │ Standard Pipeline │ 
                                    └───────────────────┘
                                            ↓
Query Generation → Vector Retrieval → Document Extraction
                                            ↓
              Draft Generation → Draft Editing → Slack Notification
                                            ↓
                                    Gmail Draft Creation
```

### Three-Phase Performance System

**Phase 1: Core Metrics Collection**
- Session tracking and node performance monitoring
- Classification accuracy and document extraction stats
- Draft quality metrics with template adherence scoring

**Phase 2: Real-Time Dashboard**
- Live analytics and visualization with Plotly
- Performance trends and quality insights
- System health monitoring and error tracking

**Phase 3: Human Feedback Integration**
- Interactive Slack messages with quality rating (1-5 stars)
- Approve/Edit/Reject workflow with feedback collection
- Edit distance calculation and quality improvement tracking

---

## 🚀 Quick Start

> **⚡ REPLIT DEPLOYMENT (Recommended)**: For the fastest deployment, jump to the [Replit Deployment Section](#-replit-deployment) below.

### 1. Environment Setup

Create your `.env` file with the following variables:

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
GMAIL_SERVICE_ACCOUNT_FILE=path/to/service-account-key.json
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

# Testing Mode
TESTING_MODE=false
```

### 2. Database Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Setup Neon PostgreSQL database
python setup_neon_database.py

# Test database connection
python test_neon_connection.py
```

### 3. Start Services

```bash
# Terminal 1 - Performance Dashboard (Port 8001)
python secure_dashboard_app.py

# Terminal 2 - Slack Interaction Endpoint (Port 8002)
python start_slack_endpoint.py

# Terminal 3 - Main Email Assistant
python run_assistant.py
```

### 4. Access Interfaces

- **📊 Performance Dashboard**: http://localhost:8001
- **🔗 Slack Interactions**: http://localhost:8002
- **📚 API Documentation**: http://localhost:8001/docs

---

## 🔧 Slack App Setup

### Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Choose your workspace and app name (e.g., "BookingAssistant")

### Step 2: Configure Interactive Components

1. In your app settings, go to **"Interactive Components"**
2. Turn on **"Interactivity"**
3. Set **Request URL** to: `https://your-domain.com:8002/slack/interactions`
   - For local testing: `https://your-ngrok-url.ngrok.io/slack/interactions`
4. Click **"Save Changes"**

### Step 3: Set Up Incoming Webhooks

1. Go to **"Incoming Webhooks"**
2. Turn on **"Activate Incoming Webhooks"**
3. Click **"Add New Webhook to Workspace"**
4. Choose the channel where you want notifications
5. Copy the **Webhook URL** to your `.env` file as `SLACK_WEBHOOK_URL`

### Step 4: Configure Event Subscriptions (Optional)

1. Go to **"Event Subscriptions"**
2. Turn on **"Enable Events"**
3. Set **Request URL** to: `https://your-domain.com:8002/slack/events`
4. Subscribe to workspace events:
   - `message.channels` (for future message editing features)

### Step 5: Set OAuth Scopes

1. Go to **"OAuth & Permissions"**
2. Add the following **Bot Token Scopes**:
   - `incoming-webhook`
   - `chat:write`
   - `chat:write.public`
   - `commands` (if using slash commands)

### Step 6: Install App to Workspace

1. Go to **"Install App"**
2. Click **"Install to Workspace"**
3. Copy the **Bot User OAuth Token** to your `.env` file as `SLACK_BOT_TOKEN`

### Step 7: Test Integration

```bash
# Test the complete feedback system
python test_phase3_feedback.py
```

### Ngrok Setup for Local Testing

If testing locally, use ngrok to expose your endpoints:

```bash
# Install ngrok and expose port 8002
ngrok http 8002

# Use the https URL in your Slack app configuration
# Example: https://abc123.ngrok.io/slack/interactions
```

---

## 📊 Performance Dashboard

### Overview Metrics
- **Total Sessions**: Number of emails processed
- **Success Rate**: Percentage of successful processing
- **Average Processing Time**: Time per email analysis
- **Error Rate**: Recent processing failures

### Analytics Features
- **Processing Timeline**: Visual email processing history
- **Classification Distribution**: Email type breakdown with confidence scores
- **Document Extraction Stats**: Client matching and retrieval success rates
- **Draft Quality Metrics**: Template adherence and context usage analysis
- **Node Performance**: Individual component execution times and reliability

### Real-Time Features
- **Auto-refresh**: Updates every 30 seconds
- **Interactive Charts**: Hover details and time range selection
- **Session Monitoring**: Detailed view of individual processing sessions
- **Quality Trends**: Performance improvement tracking over time

---

## 💬 Slack Integration Features

### Enhanced Interactive Messages

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

### Feedback Collection
- **Quality Ratings**: 1-5 star rating system for draft quality
- **Action Tracking**: Approve/Edit/Reject decision logging
- **Edit Distance**: Measures modifications made to drafts
- **User Attribution**: Tracks who provided feedback and when
- **Session Linking**: Connects feedback to specific processing sessions

---

## 🗃️ Database Schema

### Core Tables

**email_sessions** - Main processing session tracking
- Session ID, email hash, sender info, processing times, status

**node_executions** - Individual component performance
- Node name, execution time, success/failure, input/output data

**classification_results** - Email classification metrics
- Predicted label, confidence score, processing time

**document_extractions** - Google Drive integration stats
- Client matching, documents found, extraction success

**draft_generations** - Draft creation metrics
- Draft length, context usage, template adherence scores

**quality_feedback** - Human feedback integration
- Quality ratings, actions taken, edit tracking, user attribution

---

## 🧪 Testing & Development

### Comprehensive Test Suite

```bash
# Test complete functionality (no Slack/Gmail)
python test_complete_functionality.py

# Test Phase 3 feedback integration
python test_phase3_feedback.py

# Test Neon database connectivity
python test_neon_connection.py

# Test specific scenarios
python "src/Test Case/test_multiple_scenarios.py"
```

### Development Mode

Set `TESTING_MODE=true` in your `.env` file to:
- Skip Slack notifications during development
- Skip Gmail draft creation
- Enable detailed logging
- Use test database sessions

--

## 📋 Response Classifications

### Standard Types
- **A. Rejected** - "We do not allow guests"
- **B. Pay-to-Play** - "Paid slots only"
- **C. Accepted** - "We'd love to have you!"
- **D. Conditional** - "Interested - more info?"
- **E. Other/Unknown** - Unclassified responses

### Special Rejection Handling
- **Identity-based rejection** - Guest credentials questioned
- **Topic-based rejection** - Subject matter mismatch
- **Qualification-based rejection** - Experience requirements not met

Each type triggers specialized response strategies with strategic angles.

---

## 🏗️ File Structure

```
BookingAssistant/
├── src/
│   ├── main.py                      # Core LangGraph pipeline
│   ├── prompts.py                   # LLM prompt templates
│   ├── email_service.py             # Email fetching (Gmail/Maildoso)
│   ├── gmail_service.py             # Gmail-specific operations
│   ├── google_docs_service.py       # Google Drive integration
│   ├── astradb_services.py          # Vector database operations
│   ├── metrics_service.py           # Performance tracking service
│   ├── dashboard_service.py         # Analytics backend
│   ├── slack_feedback_service.py    # Enhanced Slack integration
│   ├── utils.py                     # Utility functions
│   └── Test Case/                   # Automated testing suite
├── dashboard_app.py                 # FastAPI dashboard application
├── slack_interaction_endpoint.py    # Slack button interaction handler
├── secure_dashboard_app.py          # Secure dashboard with authentication
├── start_slack_endpoint.py          # Slack endpoint startup script
├── setup_neon_database.py           # Database schema setup
├── test_neon_connection.py          # Database connectivity test
├── test_phase3_feedback.py          # Feedback integration test
├── run_assistant.py                 # Main email processing script
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
└── README.md                        # This file
```

---

## 🎯 Quality Metrics

### Draft Quality Scoring
- **Template Adherence**: Measures compliance with response templates
- **Context Usage**: Tracks utilization of retrieved documents and email threads
- **Length Analysis**: Optimal response length for different email types
- **Placeholder Count**: Ensures complete information filling

### Performance Analytics
- **Processing Speed**: Node execution times and bottleneck identification
- **Success Rates**: Component reliability and error tracking
- **Classification Accuracy**: Model performance on email categorization
- **Document Matching**: Client folder identification and document retrieval rates

### Human Feedback Integration
- **Quality Trends**: Improvement patterns over time
- **User Satisfaction**: Approval vs rejection rates
- **Edit Frequency**: How often drafts require modification
- **Feedback Velocity**: Time from generation to human review

---

## 🔮 Advanced Features

### Document Intelligence
- **Smart Client Matching**: AI-powered client folder identification
- **Contextual Document Selection**: Prioritizes Final Briefs and latest versions
- **Content Integration**: Seamlessly incorporates client context into responses
- **Multi-format Support**: Handles various document types and structures

### Strategic Rejection Handling
- **Rejection Analysis**: Identifies specific rejection reasons and patterns
- **Challenge Angle Generation**: Creates persuasive counter-arguments
- **Client Expertise Leveraging**: Uses stored client information for credibility
- **Follow-up Strategy**: Generates strategic multi-touch sequences

### Real-Time Monitoring
- **Live Dashboard**: Real-time performance visualization
- **Alert System**: Configurable notifications for performance thresholds
- **Error Tracking**: Comprehensive logging and error analysis
- **Quality Assurance**: Automated quality checks and validation

---

## 🚀 Replit Deployment

### 🎯 One-Click Deployment

BookingAssistant is **production-ready for Replit** with a unified single-port architecture that combines all services.

#### Step 1: Fork to Replit

1. Go to [replit.com](https://replit.com)
2. Click **"Create Repl"** → **"Import from GitHub"**
3. Enter your repository URL: `https://github.com/your-username/BookingAssistant`
4. Name your Repl: `BookingAssistant`

#### Step 2: Configure Environment Variables

In your Replit **Secrets** tab (🔒), add these variables:

```bash
# Required: Database
PGDATABASE=neondb
PGUSER=neondb_owner  
PGPASSWORD=your_neon_password
PGHOST=your-neon-host.aws.neon.tech
PGPORT=5432

# Required: AI Processing
OPENAI_API_KEY=your_openai_api_key
ASTRA_DB_APPLICATION_TOKEN=your_astra_token
ASTRA_DB_API_ENDPOINT=your_astra_endpoint

# Required: Gmail Integration
GMAIL_SERVICE_ACCOUNT_FILE=service-account-key.json
GMAIL_TARGET_EMAIL=aidrian@podcastguestlaunch.com

# Required: Google Drive
GDRIVE_CLIENT_ROOT_FOLDER_ID=your_google_drive_folder_id

# Optional: Slack Integration
SLACK_WEBHOOK_URL=your_slack_webhook_url
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# Optional: CRM Integration
ATTIO_API_KEY=your_attio_api_key

# Production Settings
TESTING_MODE=false
```

#### Step 3: Upload Service Account Key

1. Upload your `service-account-key.json` file to the Replit root directory
2. Ensure the filename matches your `GMAIL_SERVICE_ACCOUNT_FILE` secret

#### Step 4: Start the System (Auto-Setup Included!)

Click **"Run"** in Replit! The system will automatically:
- ✅ Detect missing database tables
- ✅ Create complete schema using `psycopg2`
- ✅ Load essential prompt templates
- ✅ Start all services

**Expected startup output**:
```
✅ Basic services loaded
🔧 Auto-creating 9 missing database tables...
✅ Database auto-setup complete!
   Created tables: 12
   Loaded prompts: 3
✅ Database schema verified/created
✅ Main processing graph loaded
```

**Manual Setup Option**: If you prefer manual control, run `python replit_db_setup.py` first.

#### Step 5: Access Your System

The system automatically starts at:
- **Dashboard**: `https://your-repl-name--your-username.repl.co/`
- **API Docs**: `https://your-repl-name--your-username.repl.co/docs`

### 🔗 Configure Slack Integration

Update your Slack App settings with your Replit URLs:

1. **Interactive Components**: `https://your-repl-name--your-username.repl.co/slack/interactions`
2. **Event Subscriptions**: `https://your-repl-name--your-username.repl.co/slack/events`
3. **Webhook URL**: Use your Slack webhook URL in secrets

### 📊 Replit Service Architecture

```
https://your-repl-name--your-username.repl.co/
├── /                          # Dashboard homepage  
├── /dashboard                 # Analytics dashboard
├── /api/*                     # Analytics APIs
├── /slack/interactions        # Slack button handling
├── /start_agent_v2           # Email processing endpoint
├── /health                   # System health check
└── /docs                     # API documentation
```

### ⚡ Production Features

- **Always-On**: Upgrade to Hacker plan ($7/month) for 24/7 operation
- **Auto-Scaling**: Handles traffic spikes automatically  
- **Monitoring**: Built-in health checks and performance tracking
- **Security**: Environment-based secrets management

### 🧪 Test Your Deployment

Once your Replit is running, test the system:

#### 1. Health Check
Visit: `https://your-repl-name--your-username.repl.co/health`

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "dashboard": true,
    "metrics": true,
    "slack_feedback": true
  },
  "database": {
    "connected": true
  }
}
```

#### 2. Process Test Email

Send a test email via the API:
```bash
curl -X POST "https://your-repl-name--your-username.repl.co/start_agent_v2" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "Hi! We are interested in having our CEO as a guest on your podcast. Could you send us more info about the process?",
    "subject": "Podcast Guest Request",
    "sender_name": "Jane Smith",
    "sender_email": "jane.smith@techstartup.com"
  }'
```

#### 3. View Dashboard

Access the analytics dashboard:
`https://your-repl-name--your-username.repl.co/dashboard`

### 🔧 Replit-Specific Tips

- **Keep Alive**: Visit your URL periodically or upgrade to Hacker plan
- **Logs**: Check console output in Replit for debugging
- **Updates**: Push to GitHub and Replit will auto-sync
- **Backup**: Export your environment variables regularly

### 🚨 Replit Troubleshooting

#### Common Issues & Solutions

**❌ "Service won't start"**
```bash
# Check if all required secrets are set
python -c "import os; required=['PGHOST', 'OPENAI_API_KEY', 'ASTRA_DB_APPLICATION_TOKEN', 'ASTRA_DB_API_ENDPOINT']; missing=[v for v in required if not os.getenv(v)]; print('Missing vars:', missing if missing else 'None - all set!')"

# Test database connection
python test_neon_connection.py

# Run complete database setup
python setup_complete_database.py
```

**❌ "Database connection failed"**
- Verify your Neon PostgreSQL credentials in Secrets
- Check that your Neon database is not paused/sleeping
- Run database setup: `python setup_complete_database.py`

**❌ "Slack interactions not working"**
- Update Slack app URLs to your Replit domain
- Verify `SLACK_WEBHOOK_URL` in Secrets
- Test with: `curl https://your-repl.repl.co/health`

**❌ "Gmail integration failing"**
- Ensure `service-account-key.json` is uploaded to root directory
- Verify the filename matches `GMAIL_SERVICE_ACCOUNT_FILE` secret
- Check Google API credentials are enabled

**💡 Performance Optimization**
- Enable "Always On" for production use
- Monitor memory usage in Replit console
- Use connection pooling (automatically enabled)

### 📋 Environment Variables Quick Reference

For a complete environment template, see [`.env.replit.example`](.env.replit.example)

| Variable | Required | Description |
|----------|----------|-------------|
| `PGHOST` | ✅ | Neon PostgreSQL host |
| `PGDATABASE` | ✅ | Database name (usually "neondb") |
| `PGUSER` | ✅ | Database username |
| `PGPASSWORD` | ✅ | Database password |
| `OPENAI_API_KEY` | ✅ | OpenAI API key for LLM processing |
| `ASTRA_DB_APPLICATION_TOKEN` | ✅ | AstraDB token for vector search |
| `ASTRA_DB_API_ENDPOINT` | ✅ | AstraDB endpoint URL |
| `ASTRA_DB_KEYSPACE` | ⚪ | AstraDB keyspace (default: "default_keyspace") |
| `ASTRA_DB_COLLECTION` | ⚪ | AstraDB collection (default: "email_threads") |
| `GMAIL_SERVICE_ACCOUNT_FILE` | ✅ | Path to Gmail service account JSON |
| `GMAIL_TARGET_EMAIL` | ✅ | Target Gmail address |
| `GDRIVE_CLIENT_ROOT_FOLDER_ID` | ✅ | Google Drive root folder ID |
| `SLACK_WEBHOOK_URL` | ⚪ | Slack webhook for notifications |
| `SLACK_BOT_TOKEN` | ⚪ | Slack bot token |
| `ATTIO_API_KEY` | ⚪ | Attio CRM integration |
| `TESTING_MODE` | ⚪ | Set to "false" for production |

---

## 🚀 Alternative Deployment

### Local Development

For local development or custom hosting:

---

## 📞 Support & Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Test connection
python test_neon_connection.py

# Check environment variables
python -c "import os; print('DB Host:', os.getenv('PGHOST'))"
```

**Slack Interactions Not Working**
- Verify ngrok URL in Slack app settings
- Check SLACK_WEBHOOK_URL environment variable
- Ensure Interactive Components are enabled

**No Data in Dashboard**
- Process some emails first with the main assistant
- Verify database schema with `setup_neon_database.py`
- Check metrics service connection in startup logs

### Health Checks

- **Dashboard**: http://localhost:8001/health
- **Slack Endpoint**: http://localhost:8002/health
- **API Documentation**: http://localhost:8001/docs

---

## 🎉 Development Status

### ✅ Completed Features

- **Core Pipeline**: LangGraph workflow with conditional routing
- **Email Processing**: Gmail/Maildoso integration with service account auth
- **Document Intelligence**: Google Drive integration with smart client matching
- **Vector Search**: AstraDB integration for email thread similarity
- **Draft Generation**: Contextual responses with template adherence
- **Slack Integration**: Interactive messages with quality feedback
- **Performance Tracking**: Three-phase monitoring system
- **Real-Time Dashboard**: Comprehensive analytics and visualization
- **Human Feedback**: Quality rating and approval workflow
- **Database Integration**: Neon PostgreSQL with complete schema
- **Testing Framework**: Comprehensive test suite and validation

### 🔮 Future Enhancements

- **A/B Testing Framework**: Compare prompt variations and model performance
- **Advanced Analytics**: Predictive insights and quality recommendations
- **Multi-language Support**: International email processing capabilities
- **Custom Workflows**: Configurable processing pipelines for different use cases
- **API Rate Limiting**: Enhanced production-ready features
- **Automated Learning**: Feedback-driven prompt optimization

---

**🚀 Ready for production deployment with full monitoring, analytics, and human oversight capabilities.**