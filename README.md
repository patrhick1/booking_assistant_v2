# BookingAssistant - AI-Powered Email Response System

🤖 **Intelligent podcast booking assistant with real-time performance tracking and human feedback integration**

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

---

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

## 🚀 Deployment

### Production Environment

The system is designed for deployment on cloud platforms with the following architecture:

- **Application**: Replit for main processing logic
- **Database**: Neon PostgreSQL for metrics and analytics
- **Vector Store**: DataStax Astra DB for email similarity search
- **Document Storage**: Google Drive with service account access
- **Monitoring**: Built-in dashboard and Slack integration

### Scaling Considerations

- **Database Connection Pooling**: Handles concurrent requests efficiently
- **Async Processing**: Non-blocking email processing pipeline
- **Modular Architecture**: Easy to scale individual components
- **Performance Monitoring**: Built-in metrics for optimization guidance

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