#!/usr/bin/env python3
"""
Slack Interaction Endpoint for BookingAssistant
Handles button clicks and user interactions from enhanced Slack messages
"""

import os
import json
import sys
from urllib.parse import parse_qs
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from src.slack_feedback_service import slack_feedback
from src.metrics_service import metrics

load_dotenv()

app = FastAPI(title="BookingAssistant Slack Interactions", version="1.0.0")

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
        
        # Verify the request is from Slack (optional but recommended)
        # You can add signature verification here for production
        
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "slack-interaction-endpoint",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "BookingAssistant Slack Interaction Endpoint",
        "version": "1.0.0",
        "endpoints": {
            "interactions": "/slack/interactions",
            "events": "/slack/events",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Slack Interaction Endpoint...")
    print("📋 Endpoints:")
    print("   - Interactions: http://localhost:8002/slack/interactions")
    print("   - Events: http://localhost:8002/slack/events") 
    print("   - Health: http://localhost:8002/health")
    print("   - Docs: http://localhost:8002/docs")
    
    uvicorn.run(
        "slack_interaction_endpoint:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )