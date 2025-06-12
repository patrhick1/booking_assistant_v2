#!/usr/bin/env python3
"""
Unified FastAPI application for Replit deployment
Combines dashboard, Slack interactions, and main API into single port
"""

import sys
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import parse_qs
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

load_dotenv()

# Import all services
from src.dashboard_service import dashboard
from src.slack_feedback_service import slack_feedback
from src.metrics_service import metrics
from src.main import graph

# Create unified FastAPI app
app = FastAPI(
    title="BookingAssistant - Unified Service",
    description="Email processing with dashboard, Slack integration, and analytics",
    version="3.0.0"
)

# Add CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass  # Directory might not exist in development

try:
    templates = Jinja2Templates(directory="templates")
except:
    templates = None

# ==========================================
# DASHBOARD ROUTES (Port 8001 equivalent)
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard homepage"""
    if not templates:
        return HTMLResponse("""
        <html><body>
        <h1>📊 BookingAssistant Dashboard</h1>
        <p>Dashboard template not found. API endpoints available at:</p>
        <ul>
            <li><a href="/docs">API Documentation</a></li>
            <li><a href="/api/overview">Overview API</a></li>
            <li><a href="/health">Health Check</a></li>
            <li><a href="/slack/interactions">Slack Interactions</a></li>
        </ul>
        </body></html>
        """)
    
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page (alias for root)"""
    return await dashboard_home(request)

# Dashboard API endpoints
@app.get("/api/overview")
async def get_overview(days: int = Query(7, description="Number of days to analyze")):
    """Get overview statistics"""
    try:
        stats = dashboard.get_overview_stats(days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/timeline")
async def get_timeline(hours: int = Query(24, description="Number of hours to analyze")):
    """Get processing timeline"""
    try:
        timeline = dashboard.get_processing_timeline(hours)
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/classifications")
async def get_classifications(days: int = Query(30, description="Number of days to analyze")):
    """Get classification analytics"""
    try:
        analytics = dashboard.get_classification_analytics(days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def get_documents(days: int = Query(30, description="Number of days to analyze")):
    """Get document extraction statistics"""
    try:
        stats = dashboard.get_document_extraction_stats(days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quality")
async def get_quality(days: int = Query(30, description="Number of days to analyze")):
    """Get draft quality metrics"""
    try:
        quality = dashboard.get_draft_quality_metrics(days)
        return quality
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance")
async def get_performance(days: int = Query(7, description="Number of days to analyze")):
    """Get node performance metrics"""
    try:
        performance = dashboard.get_node_performance(days)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def get_sessions(limit: int = Query(50, description="Number of recent sessions to return")):
    """Get recent processing sessions"""
    try:
        sessions = dashboard.get_recent_sessions(limit)
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}")
async def get_session_details(session_id: str):
    """Get detailed session information"""
    try:
        session = dashboard.get_session_summary(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def get_system_health():
    """Get system health indicators"""
    try:
        health = dashboard.get_system_health()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# SLACK INTERACTION ROUTES (Port 8002 equivalent)
# ==========================================

@app.post("/slack/interactions")
async def handle_slack_interactions(request: Request):
    """Handle Slack interactive component interactions"""
    try:
        # Parse the form data from Slack
        form_data = await request.form()
        payload_str = form_data.get("payload")
        
        if not payload_str:
            raise HTTPException(status_code=400, detail="No payload found")
        
        # Parse the JSON payload
        payload = json.loads(payload_str)
        
        # Handle the interaction
        response = slack_feedback.handle_slack_interaction(payload)
        
        return JSONResponse(content=response)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        print(f"Error handling Slack interaction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/slack/events")
async def handle_slack_events(request: Request):
    """Handle Slack Events API (for future features like message editing)"""
    try:
        data = await request.json()
        
        # Handle URL verification challenge
        if data.get("type") == "url_verification":
            return {"challenge": data.get("challenge")}
        
        # Handle actual events
        event = data.get("event", {})
        event_type = event.get("type")
        
        if event_type == "message":
            # Future: Handle message edits for edit distance calculation
            pass
        
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Error handling Slack event: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ==========================================
# MAIN EMAIL PROCESSING API
# ==========================================

@app.post("/start_agent_v2")
async def start_agent_v2(request: Request):
    """Main email processing endpoint (webhook compatible)"""
    try:
        data = await request.json()
        
        # Extract email details
        email_text = data.get("email", "")
        subject = data.get("subject", "")
        sender_name = data.get("sender_name", "")
        sender_email = data.get("sender_email", "")
        
        if not email_text or not sender_email:
            raise HTTPException(status_code=400, detail="Email and sender_email are required")
        
        # Start metrics session
        email_details = {
            'sender_email': sender_email,
            'sender_name': sender_name,
            'subject': subject,
            'email_text': email_text
        }
        session_id = metrics.start_email_session(email_details)
        
        # Create initial state
        state = {
            "email_text": email_text,
            "subject": subject,
            "sender_name": sender_name,
            "sender_email": sender_email
        }
        
        # Process with LangGraph
        thread = {"configurable": {"thread_id": session_id}}
        result = graph.invoke(state, thread)
        
        # Complete metrics session
        metrics.end_email_session('completed')
        
        return {
            "status": "success",
            "session_id": session_id,
            "result": result,
            "dashboard_url": f"{request.url.scheme}://{request.url.netloc}/dashboard"
        }
        
    except Exception as e:
        # Log error and complete session
        if 'session_id' in locals():
            metrics.end_email_session('failed', str(e))
        
        print(f"Error processing email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# HEALTH AND STATUS ENDPOINTS
# ==========================================

@app.get("/health")
async def health_check():
    """Comprehensive health check for all services"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "dashboard": bool(dashboard.db_pool),
            "metrics": bool(metrics.db_pool),
            "slack_feedback": bool(slack_feedback.webhook_url),
        },
        "database": {
            "connected": bool(dashboard.db_pool),
            "host": os.getenv('PGHOST', 'not_set')[:20] + "..." if os.getenv('PGHOST') else 'not_set'
        }
    }
    
    # Overall health status
    all_services_healthy = all(health_status["services"].values())
    health_status["status"] = "healthy" if all_services_healthy else "degraded"
    
    return health_status

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# ==========================================
# REPLIT-SPECIFIC ROUTES
# ==========================================

@app.get("/replit")
async def replit_info():
    """Replit deployment information"""
    return {
        "deployment": "replit",
        "unified_port": True,
        "services": {
            "dashboard": "/ and /dashboard",
            "api": "/docs",
            "slack_interactions": "/slack/interactions",
            "email_processing": "/start_agent_v2",
            "health": "/health"
        },
        "environment": {
            "database": "connected" if dashboard.db_pool else "disconnected",
            "slack_configured": bool(os.getenv('SLACK_WEBHOOK_URL')),
            "testing_mode": os.getenv('TESTING_MODE', 'false') == 'true'
        }
    }

# ==========================================
# STARTUP INFORMATION
# ==========================================

def print_startup_info():
    """Print startup information for Replit"""
    print("\n" + "="*60)
    print("🚀 BOOKING ASSISTANT - UNIFIED REPLIT DEPLOYMENT")
    print("="*60)
    print("🏠 Main Dashboard: https://your-repl-name.replit.app/")
    print("📊 Analytics API: https://your-repl-name.replit.app/api/overview")
    print("🔗 Slack Interactions: https://your-repl-name.replit.app/slack/interactions")
    print("📧 Email Processing: POST https://your-repl-name.replit.app/start_agent_v2")
    print("🔄 Health Check: https://your-repl-name.replit.app/health")
    print("📚 API Docs: https://your-repl-name.replit.app/docs")
    print("="*60)
    print("✅ All services running on single port for Replit")
    print("✅ Database:", "Connected" if dashboard.db_pool else "Disconnected")
    print("✅ Slack:", "Configured" if os.getenv('SLACK_WEBHOOK_URL') else "Not configured")
    print("="*60)

if __name__ == "__main__":
    print_startup_info()
    
    # Get port from environment (Replit sets PORT automatically)
    port = int(os.getenv("PORT", 8080))
    
    uvicorn.run(
        "replit_unified_app:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload for production
        log_level="info"
    )