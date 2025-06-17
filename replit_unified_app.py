#!/usr/bin/env python3
"""
Unified FastAPI application for Replit deployment
Combines dashboard, Slack interactions, and main API into single port
"""

import sys
import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Form, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import parse_qs
from dotenv import load_dotenv
import threading
import time

# Add src to path
sys.path.append('src')

load_dotenv()

# Import all services with error handling
try:
    from src.dashboard_service import dashboard
    from src.slack_feedback_service import slack_feedback
    from src.metrics_service import metrics
    print("Basic services loaded")
    
    # Auto-setup database if needed
    from src.auto_db_setup import ensure_database_ready
    try:
        if ensure_database_ready(metrics.db_pool):
            print("✅ Database schema verified/created")
        else:
            print("⚠️  WARNING: Database schema setup had issues")
    except Exception as setup_error:
        print(f"❌ ERROR: Auto database setup failed: {setup_error}")
        print("WARNING: Database schema setup had issues")
        
except Exception as e:
    print(f"ERROR: Error loading basic services: {e}")
    raise

# Import main graph with better error handling
try:
    from src.main import graph
    print("Main processing graph loaded")
except Exception as e:
    print(f"ERROR: Error loading main graph: {e}")
    print("    This might be due to missing environment variables.")
    print("    Please check your Secrets configuration.")
    # Don't raise here - we'll handle this gracefully
    graph = None

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
# EMAIL PROCESSING ENDPOINTS
# ==========================================

# Import email services
from src.email_service import EmailService

# Initialize email service
email_service = EmailService()

# Global flag for email processing
email_processing_active = False
email_processing_thread = None

@app.post("/process_emails")
async def process_emails():
    """Process unread emails from Gmail and IMAP sources (manual trigger)"""
    try:
        if graph is None:
            raise HTTPException(
                status_code=503, 
                detail="Email processing service unavailable. Please check environment configuration."
            )
        
        print("🔍 Manual email processing triggered...")
        results = process_emails_internal()
        
        if not results:
            return {
                "status": "success",
                "message": "No new emails to process",
                "processed_count": 0,
                "results": []
            }
        
        successful_count = len([r for r in results if r.get("status") == "success"])
        
        return {
            "status": "success",
            "message": f"Processed {successful_count} emails successfully",
            "processed_count": successful_count,
            "total_found": len(results),
            "results": results,
            "dashboard_url": f"/dashboard"
        }
        
    except Exception as e:
        print(f"Error processing emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start_agent_v2")
async def start_agent_v2(request: Request):
    """Legacy webhook endpoint - consider using /process_emails instead"""
    try:
        data = await request.json()
        
        # Extract email details
        email_text = data.get("email", "")
        subject = data.get("subject", "")
        sender_name = data.get("sender_name", "")
        sender_email = data.get("sender_email", "")
        
        if not email_text or not sender_email:
            raise HTTPException(status_code=400, detail="Email and sender_email are required")
        
        # Apply spam filtering using existing EmailService logic
        if not email_service._should_process_email(subject, email_text, sender_email):
            return {
                "status": "filtered", 
                "reason": "Email filtered by spam detection",
                "sender_email": sender_email
            }
        
        # Clean text using existing logic
        cleaned_email = email_service._clean_text(f"Subject: {subject}\n\nContent: {email_text}")
        
        # Start metrics session
        email_details = {
            'sender_email': sender_email,
            'sender_name': sender_name,
            'subject': subject,
            'email_text': cleaned_email
        }
        session_id = metrics.start_email_session(email_details)
        
        # Create initial state
        state = {
            "email_text": cleaned_email,
            "subject": subject,
            "sender_name": sender_name,
            "sender_email": sender_email
        }
        
        # Check if graph is available
        if graph is None:
            raise HTTPException(
                status_code=503, 
                detail="Email processing service unavailable. Please check environment configuration."
            )
        
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

def continuous_email_processing():
    """Continuous email processing function that runs in a separate thread"""
    global email_processing_active
    
    print("🚀 Starting continuous email processing...")
    email_processing_active = True
    
    while email_processing_active:
        try:
            if graph is None:
                print("⚠️  Email processing service unavailable - waiting...")
                time.sleep(60)
                continue
            
            # Get emails from all sources
            gmail_emails = email_service.fetch_unread_gmail_emails()
            maildoso_emails = email_service.fetch_unread_maildoso_emails()
            all_emails = gmail_emails + maildoso_emails
            
            if all_emails:
                print(f"📧 Found {len(all_emails)} unread emails to process")
                
                for email_details in all_emails:
                    try:
                        print(f"🔄 Processing email from {email_details['sender_email']}: {email_details['subject'][:50]}...")
                        
                        # Start metrics session
                        session_id = metrics.start_email_session(email_details)
                        
                        # Create initial state for LangGraph
                        state = {
                            "email_text": email_details["body"],
                            "subject": email_details["subject"],
                            "sender_name": email_details["sender_name"],
                            "sender_email": email_details["sender_email"]
                        }
                        
                        # Process with LangGraph
                        thread = {"configurable": {"thread_id": session_id}}
                        result = graph.invoke(state, thread)
                        
                        # Complete metrics session
                        metrics.end_email_session('completed')
                        
                        print(f"✅ Successfully processed email from {email_details['sender_email']}")
                        
                    except Exception as e:
                        if 'session_id' in locals():
                            metrics.end_email_session('failed', str(e))
                        print(f"❌ Error processing email from {email_details.get('sender_email', 'unknown')}: {e}")
            else:
                # No emails found - this is normal, just a quick check
                pass
            
            # Wait 60 seconds before next check
            print(f"⏰ Next email check in 60 seconds... (Time: {datetime.now().strftime('%H:%M:%S')})")
            time.sleep(60)
            
        except Exception as e:
            print(f"❌ Critical error in email processing loop: {e}")
            print("⏳ Waiting 60 seconds before retry...")
            time.sleep(60)
    
    print("🛑 Email processing stopped")

@app.post("/start_email_polling")
async def start_email_polling():
    """Start continuous email polling in background thread"""
    global email_processing_thread, email_processing_active
    
    if email_processing_active:
        return {
            "status": "already_running",
            "message": "Email polling is already active"
        }
    
    # Start email processing in a separate thread
    email_processing_thread = threading.Thread(target=continuous_email_processing, daemon=True)
    email_processing_thread.start()
    
    return {
        "status": "success",
        "message": "Continuous email polling started",
        "note": "Emails will be checked every 60 seconds automatically"
    }

@app.post("/stop_email_polling")
async def stop_email_polling():
    """Stop continuous email polling"""
    global email_processing_active
    
    if not email_processing_active:
        return {
            "status": "not_running",
            "message": "Email polling is not currently active"
        }
    
    email_processing_active = False
    return {
        "status": "success",
        "message": "Email polling stop signal sent"
    }

@app.get("/email_polling_status")
async def email_polling_status():
    """Check email polling status"""
    return {
        "status": "active" if email_processing_active else "inactive",
        "active": email_processing_active,
        "thread_alive": email_processing_thread.is_alive() if email_processing_thread else False
    }

@app.post("/reload_prompts")
async def reload_prompts():
    """Manually reload essential prompts into database"""
    try:
        from src.auto_db_setup import load_essential_prompts
        
        conn = metrics.db_pool.getconn()
        cursor = conn.cursor()
        
        # Load prompts
        prompt_count = load_essential_prompts(cursor)
        conn.commit()
        
        metrics.db_pool.putconn(conn)
        
        return {
            "status": "success",
            "message": f"Reloaded {prompt_count} essential prompts",
            "prompts_loaded": prompt_count
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to reload prompts: {str(e)}"
        }

@app.get("/debug_prompts")
async def debug_prompts():
    """Debug prompt storage issues"""
    try:
        conn = metrics.db_pool.getconn()
        cursor = conn.cursor()
        
        # Check prompt_versions for classification_fewshot
        cursor.execute("""
            SELECT id, prompt_name, version, is_active, created_at 
            FROM prompt_versions 
            WHERE prompt_name = 'classification_fewshot'
            ORDER BY version DESC
        """)
        versions = cursor.fetchall()
        
        # Check if there's any active version
        cursor.execute("""
            SELECT id, prompt_name, version, is_active, content
            FROM prompt_versions 
            WHERE prompt_name = 'classification_fewshot' AND is_active = TRUE
        """)
        active_version = cursor.fetchone()
        
        # Also try to get the content directly
        cursor.execute("""
            SELECT content FROM prompt_versions 
            WHERE prompt_name = 'classification_fewshot' AND is_active = TRUE
            ORDER BY version DESC LIMIT 1
        """)
        content_result = cursor.fetchone()
        
        metrics.db_pool.putconn(conn)
        
        # Handle RealDictRow format
        versions_data = []
        for row in versions:
            if hasattr(row, 'items'):  # RealDictRow
                versions_data.append(dict(row))
            else:
                versions_data.append({
                    'id': str(row[0]), 
                    'prompt_name': str(row[1]), 
                    'version': int(row[2]), 
                    'is_active': bool(row[3]), 
                    'created_at': str(row[4])
                })
        
        active_data = None
        if active_version:
            if hasattr(active_version, 'items'):  # RealDictRow
                active_data = dict(active_version)
            else:
                active_data = {
                    'id': str(active_version[0]), 
                    'prompt_name': str(active_version[1]), 
                    'version': int(active_version[2]), 
                    'is_active': bool(active_version[3]),
                    'content_length': len(str(active_version[4])) if active_version[4] else 0
                }
        
        content_info = None
        if content_result:
            if hasattr(content_result, 'items'):  # RealDictRow
                content_info = {"content_length": len(content_result['content']) if content_result['content'] else 0}
            else:
                content_info = {"content_length": len(str(content_result[0])) if content_result[0] else 0}
        
        return {
            "status": "success",
            "prompt_versions": versions_data,
            "active_version": active_data,
            "content_info": content_info,
            "versions_count": len(versions)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Debug failed: {str(e)}",
            "error_type": type(e).__name__
        }

def process_emails_internal():
    """Internal function to process emails (used by both endpoint and polling)"""
    if graph is None:
        print("⚠️  Email processing service unavailable")
        return []
    
    # Get emails from all sources
    gmail_emails = email_service.fetch_unread_gmail_emails()
    maildoso_emails = email_service.fetch_unread_maildoso_emails()
    all_emails = gmail_emails + maildoso_emails
    
    if not all_emails:
        return []
    
    results = []
    print(f"📧 Processing {len(all_emails)} unread emails...")
    
    for email_details in all_emails:
        try:
            # Start metrics session
            session_id = metrics.start_email_session(email_details)
            
            # Create initial state for LangGraph
            state = {
                "email_text": email_details["body"],
                "subject": email_details["subject"],
                "sender_name": email_details["sender_name"],
                "sender_email": email_details["sender_email"]
            }
            
            # Process with LangGraph
            thread = {"configurable": {"thread_id": session_id}}
            result = graph.invoke(state, thread)
            
            # Complete metrics session
            metrics.end_email_session('completed')
            
            results.append({
                "session_id": session_id,
                "sender_email": email_details["sender_email"],
                "subject": email_details["subject"],
                "status": "success",
                "result": result
            })
            
            print(f"✅ Processed email from {email_details['sender_email']}")
            
        except Exception as e:
            if 'session_id' in locals():
                metrics.end_email_session('failed', str(e))
            print(f"❌ Error processing email: {e}")
            results.append({
                "sender_email": email_details.get("sender_email", "unknown"),
                "subject": email_details.get("subject", "unknown"),
                "status": "error",
                "error": str(e)
            })
    
    return results

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
            "email_processing": graph is not None,
            "gmail_service": bool(email_service.gmail_service),
            "automatic_email_processing": email_processing_active,
        },
        "email_processing": {
            "automatic_active": email_processing_active,
            "thread_alive": email_processing_thread.is_alive() if email_processing_thread else False,
            "gmail_available": bool(email_service.gmail_service),
            "graph_available": graph is not None
        },
        "database": {
            "connected": bool(dashboard.db_pool),
            "host": os.getenv('PGHOST', 'not_set')[:20] + "..." if os.getenv('PGHOST') else 'not_set'
        },
        "environment": {
            "openai_configured": bool(os.getenv('OPENAI_API_KEY')),
            "astra_configured": bool(os.getenv('ASTRA_DB_APPLICATION_TOKEN')),
            "gmail_configured": bool(os.getenv('GMAIL_SERVICE_ACCOUNT_FILE')),
            "gdrive_configured": bool(os.getenv('GDRIVE_CLIENT_ROOT_FOLDER_ID')),
            "slack_configured": bool(os.getenv('SLACK_WEBHOOK_URL')),
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

def start_automatic_email_processing():
    """Start automatic email processing on app startup"""
    global email_processing_thread, email_processing_active
    
    # Only start if services are available
    if graph and (email_service.gmail_service or True):  # IMAP might work even if Gmail doesn't
        print("🚀 Starting automatic email processing...")
        
        # Start email processing in a separate thread
        email_processing_thread = threading.Thread(target=continuous_email_processing, daemon=True)
        email_processing_thread.start()
        
        print("✅ Automatic email processing started - checking every 60 seconds")
    else:
        print("⚠️  Automatic email processing not started - services unavailable")

def print_startup_info():
    """Print startup information for Replit"""
    print("\n" + "="*80)
    print("🚀 BOOKING ASSISTANT - FULLY AUTOMATED UNIFIED DEPLOYMENT")
    print("="*80)
    print("🏠 Main Dashboard: https://your-repl-name.replit.app/")
    print("📊 Analytics API: https://your-repl-name.replit.app/api/overview")
    print("🔗 Slack Interactions: https://your-repl-name.replit.app/slack/interactions")
    print("")
    print("📧 EMAIL PROCESSING (AUTOMATED):")
    print("   • ✅ Continuous Processing: AUTOMATICALLY ACTIVE")
    print("   • 📝 Manual Trigger: POST https://your-repl-name.replit.app/process_emails")
    print("   • 🔄 Status Check: GET https://your-repl-name.replit.app/email_polling_status")
    print("   • ⏸️  Stop Processing: POST https://your-repl-name.replit.app/stop_email_polling")
    print("")
    print("🔧 MANAGEMENT:")
    print("   • 🔄 Health Check: https://your-repl-name.replit.app/health")
    print("   • 📚 API Docs: https://your-repl-name.replit.app/docs")
    print("   • 🎛️  Prompt Management: Available via Dashboard")
    print("")
    print("="*80)
    print("✅ All services running on single port for Replit")
    print("✅ Database:", "Connected" if dashboard.db_pool else "Disconnected")
    print("✅ Slack:", "Configured" if os.getenv('SLACK_WEBHOOK_URL') else "Not configured")
    print("✅ Gmail Service:", "Available" if email_service.gmail_service else "Unavailable")
    print("✅ Email Processing:", "Ready" if graph else "Unavailable")
    print("✅ Auto Processing:", "Active" if email_processing_active else "Inactive")
    print("")
    print("🎯 FULLY AUTOMATED WORKFLOW:")
    print("   📧 Fetch Emails → 🤖 AI Processing → 📝 Draft Creation → ")
    print("   💬 Slack Notification → 👥 Human Review → 📊 Metrics Tracking")
    print("="*80)

if __name__ == "__main__":
    print_startup_info()
    
    # Start automatic email processing
    start_automatic_email_processing()
    
    # Get port from environment (Replit sets PORT automatically)
    port = int(os.getenv("PORT", 8080))
    
    uvicorn.run(
        "replit_unified_app:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload for production
        log_level="info"
    )