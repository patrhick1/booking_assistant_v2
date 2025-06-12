#!/usr/bin/env python3
"""
Secure Dashboard Application with Authentication and Prompt Management
"""

import sys
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Form, Query, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

load_dotenv()

# Import services
from src.dashboard_service import dashboard
from src.auth_service import auth_service, get_current_user, require_admin, require_dashboard_access, require_prompt_access
from src.prompt_manager import prompt_manager
from src.metrics_service import metrics

# Create secure FastAPI app
app = FastAPI(
    title="BookingAssistant - Secure Dashboard",
    description="Secure email processing dashboard with authentication and prompt management",
    version="3.1.0"
)

# Add CORS middleware
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
    pass

try:
    templates = Jinja2Templates(directory="templates")
except:
    templates = None

# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str

class PromptVersionRequest(BaseModel):
    content: str
    description: str

class ActivateVersionRequest(BaseModel):
    version_id: str

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.post("/auth/login")
async def login(login_data: LoginRequest):
    """Authenticate user and return JWT token"""
    user_data = auth_service.authenticate_user(login_data.username, login_data.password)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    access_token = auth_service.create_access_token(user_data)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }

@app.get("/auth/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.get("/auth/check")
async def check_auth_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Check if user is authenticated"""
    return {"authenticated": True, "user": current_user}

# ==========================================
# SECURE DASHBOARD ROUTES
# ==========================================

@app.get("/")
async def dashboard_home():
    """Redirect root to dashboard"""
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    login_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>BookingAssistant - Login</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
            .login-form { background: #f5f5f5; padding: 30px; border-radius: 10px; }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
            button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="login-form">
            <h2>🔐 BookingAssistant Login</h2>
            <div class="warning">
                <strong>Default Credentials:</strong><br>
                Username: admin<br>
                Password: BookingAssistant2024!<br>
                <em>Change these in production!</em>
            </div>
            <form id="loginForm">
                <input type="text" id="username" placeholder="Username" required>
                <input type="password" id="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
        
        <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username, password})
                });
                
                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('token', data.access_token);
                    window.location.href = '/dashboard';
                } else {
                    alert('Invalid credentials');
                }
            } catch (error) {
                alert('Login failed: ' + error.message);
            }
        });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(login_html)

@app.get("/prompts", response_class=HTMLResponse)
async def prompt_management_page(request: Request):
    """Prompt management page"""
    if not templates:
        return HTMLResponse("<h1>Templates not available</h1>")
    
    return templates.TemplateResponse("prompt_management.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_main(request: Request):
    """Main dashboard page (requires frontend authentication)"""
    if not templates:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BookingAssistant Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .auth-warning { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .dashboard-content { display: none; }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
                .stat-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }
                .stat-card h3 { margin: 0 0 10px 0; color: #333; }
                .stat-card .number { font-size: 2em; font-weight: bold; color: #007bff; }
            </style>
        </head>
        <body>
            <h1>📊 BookingAssistant Dashboard</h1>
            
            <div id="authWarning" class="auth-warning">
                <strong>⚠️ Authentication Required</strong><br>
                Please <a href="/login">login</a> to access the dashboard.
            </div>
            
            <div id="dashboardContent" class="dashboard-content">
                <h2>Welcome to the Dashboard!</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Sessions</h3>
                        <div class="number" id="totalSessions">Loading...</div>
                    </div>
                    <div class="stat-card">
                        <h3>Success Rate</h3>
                        <div class="number" id="successRate">Loading...</div>
                    </div>
                    <div class="stat-card">
                        <h3>Avg Response Time</h3>
                        <div class="number" id="avgResponseTime">Loading...</div>
                    </div>
                </div>
                
                <div style="margin-top: 30px;">
                    <h3>Quick Actions</h3>
                    <a href="/prompts" style="margin-right: 10px;">🎯 Manage Prompts</a>
                    <a href="/api/overview" style="margin-right: 10px;">📈 Overview Stats</a>
                    <a href="/api/timeline" style="margin-right: 10px;">⏰ Timeline</a>
                    <a href="/docs" style="margin-right: 10px;">📚 API Docs</a>
                    <button onclick="logout()" style="background: #dc3545; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">🚪 Logout</button>
                </div>
            </div>
            
            <script>
                function checkAuth() {
                    const token = localStorage.getItem('token');
                    if (!token) {
                        document.getElementById('authWarning').style.display = 'block';
                        document.getElementById('dashboardContent').style.display = 'none';
                        return false;
                    }
                    
                    fetch('/auth/check', {
                        headers: { 'Authorization': 'Bearer ' + token }
                    })
                    .then(response => {
                        if (response.ok) {
                            document.getElementById('authWarning').style.display = 'none';
                            document.getElementById('dashboardContent').style.display = 'block';
                            loadDashboardData();
                        } else {
                            localStorage.removeItem('token');
                            window.location.href = '/login';
                        }
                    })
                    .catch(() => {
                        localStorage.removeItem('token');
                        window.location.href = '/login';
                    });
                }
                
                function loadDashboardData() {
                    const token = localStorage.getItem('token');
                    fetch('/api/overview', {
                        headers: { 'Authorization': 'Bearer ' + token }
                    })
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('totalSessions').textContent = data.total_sessions || '0';
                        document.getElementById('successRate').textContent = (data.success_rate || 0) + '%';
                        document.getElementById('avgResponseTime').textContent = (data.avg_response_time || 0) + 's';
                    })
                    .catch(error => {
                        console.error('Error loading dashboard data:', error);
                    });
                }
                
                function logout() {
                    localStorage.removeItem('token');
                    window.location.href = '/login';
                }
                
                // Check authentication on page load
                checkAuth();
            </script>
        </body>
        </html>
        """)
    
    return templates.TemplateResponse("main_dashboard.html", {"request": request})

# Protected dashboard API endpoints
@app.get("/api/overview")
async def get_overview(
    days: int = Query(7, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(require_dashboard_access)
):
    """Get overview statistics (authenticated)"""
    try:
        stats = dashboard.get_overview_stats(days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/timeline")
async def get_timeline(
    hours: int = Query(24, description="Number of hours to analyze"),
    current_user: Dict[str, Any] = Depends(require_dashboard_access)
):
    """Get processing timeline (authenticated)"""
    try:
        timeline = dashboard.get_processing_timeline(hours)
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/classifications")
async def get_classifications(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(require_dashboard_access)
):
    """Get classification analytics (authenticated)"""
    try:
        analytics = dashboard.get_classification_analytics(days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# PROMPT MANAGEMENT ROUTES
# ==========================================

@app.get("/api/prompts")
async def get_all_prompts(current_user: Dict[str, Any] = Depends(require_prompt_access)):
    """Get all prompt templates and their active versions"""
    try:
        prompts = prompt_manager.get_all_prompts()
        return {"prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/prompts/{prompt_name}")
async def get_prompt_details(
    prompt_name: str,
    current_user: Dict[str, Any] = Depends(require_prompt_access)
):
    """Get detailed information about a specific prompt"""
    try:
        # Get active prompt content
        active_content = prompt_manager.get_active_prompt(prompt_name)
        if not active_content:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        # Get all versions
        versions = prompt_manager.get_prompt_versions(prompt_name)
        
        # Get template info
        all_prompts = prompt_manager.get_all_prompts()
        template_info = next((p for p in all_prompts if p["prompt_name"] == prompt_name), {})
        
        return {
            "prompt_name": prompt_name,
            "description": template_info.get("description", ""),
            "category": template_info.get("category", ""),
            "active_content": active_content,
            "active_version": template_info.get("active_version", 1),
            "performance_score": template_info.get("performance_score", 0),
            "usage_count": template_info.get("usage_count", 0),
            "versions": versions
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/prompts/{prompt_name}/versions")
async def create_prompt_version(
    prompt_name: str,
    version_data: PromptVersionRequest,
    current_user: Dict[str, Any] = Depends(require_prompt_access)
):
    """Create a new version of a prompt"""
    try:
        version_id = prompt_manager.create_prompt_version(
            prompt_name=prompt_name,
            content=version_data.content,
            description=version_data.description,
            created_by=current_user["username"]
        )
        
        return {
            "version_id": version_id,
            "message": f"New version created for {prompt_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/prompts/{prompt_name}/activate")
async def activate_prompt_version(
    prompt_name: str,
    activation_data: ActivateVersionRequest,
    current_user: Dict[str, Any] = Depends(require_prompt_access)
):
    """Activate a specific version of a prompt"""
    try:
        success = prompt_manager.activate_prompt_version(prompt_name, activation_data.version_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to activate version")
        
        return {
            "message": f"Version activated for {prompt_name}",
            "activated_version_id": activation_data.version_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/prompts/{prompt_name}/activate/{version_number}")
async def activate_prompt_version_by_number(
    prompt_name: str,
    version_number: int,
    current_user: Dict[str, Any] = Depends(require_prompt_access)
):
    """Activate a specific version of a prompt by version number"""
    try:
        # Get the version ID from version number
        versions = prompt_manager.get_prompt_versions(prompt_name)
        target_version = next((v for v in versions if v["version"] == version_number), None)
        
        if not target_version:
            raise HTTPException(status_code=404, detail=f"Version {version_number} not found")
        
        success = prompt_manager.activate_prompt_version(prompt_name, target_version["id"])
        if not success:
            raise HTTPException(status_code=400, detail="Failed to activate version")
        
        return {
            "message": f"Version {version_number} activated for {prompt_name}",
            "activated_version_id": target_version["id"],
            "version_number": version_number
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/prompts/{prompt_name}/performance")
async def get_prompt_performance(
    prompt_name: str,
    days: int = Query(30, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(require_prompt_access)
):
    """Get performance analytics for a specific prompt"""
    try:
        # This would be implemented with detailed analytics
        # For now, return basic info
        versions = prompt_manager.get_prompt_versions(prompt_name)
        return {
            "prompt_name": prompt_name,
            "performance_data": versions,
            "analysis_period_days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ADMINISTRATION ROUTES
# ==========================================

@app.post("/api/admin/users")
async def create_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Create a new user (admin only)"""
    try:
        permissions = ["dashboard"]
        if role == "admin":
            permissions = ["dashboard", "prompts", "analytics", "settings"]
        elif role == "manager":
            permissions = ["dashboard", "prompts", "analytics"]
        
        success = auth_service.add_user(username, password, role, permissions)
        if success:
            return {"message": f"User {username} created successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/generate-password-hash")
async def generate_password_hash(
    password: str = Query(..., description="Password to hash"),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Generate a password hash for environment variables"""
    password_hash = auth_service.generate_password_hash(password)
    return {
        "password": password,
        "hash": password_hash,
        "env_var": f"DASHBOARD_PASSWORD_HASH={password_hash}"
    }

# ==========================================
# HEALTH AND STATUS
# ==========================================

@app.get("/health")
async def health_check():
    """Public health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "dashboard": bool(dashboard.db_pool),
            "metrics": bool(metrics.db_pool),
            "prompt_manager": bool(prompt_manager.db_pool),
            "authentication": True
        },
        "security": {
            "authentication_enabled": True,
            "prompt_management_protected": True
        }
    }
    
    all_services_healthy = all(health_status["services"].values())
    health_status["status"] = "healthy" if all_services_healthy else "degraded"
    
    return health_status

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# ==========================================
# EMAIL PROCESSING (Public API)
# ==========================================

@app.post("/start_agent_v2")
async def start_agent_v2(request: Request):
    """Email processing endpoint (public for webhooks)"""
    try:
        from src.main import graph
        
        data = await request.json()
        
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
        if 'session_id' in locals():
            metrics.end_email_session('failed', str(e))
        
        print(f"Error processing email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔐 BOOKING ASSISTANT - SECURE DASHBOARD")
    print("="*60)
    print("🏠 Login Page: http://localhost:8001/login")
    print("📊 Dashboard: http://localhost:8001/ (requires auth)")
    print("🔧 Prompt Management: http://localhost:8001/api/prompts (requires auth)")
    print("🔄 Health Check: http://localhost:8001/health")
    print("📚 API Docs: http://localhost:8001/docs")
    print("="*60)
    print("🔑 Default Login: admin / BookingAssistant2024!")
    print("⚠️  Change default credentials for production!")
    print("="*60)
    
    port = int(os.getenv("PORT", 8001))
    
    uvicorn.run(
        "secure_dashboard_app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )