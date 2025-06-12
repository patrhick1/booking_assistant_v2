"""
Slack Feedback Service for capturing human feedback on draft quality.
Handles interactive Slack components and quality rating collection.
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
from urllib.parse import parse_qs
from src.metrics_service import metrics
from dotenv import load_dotenv

load_dotenv()

class SlackFeedbackService:
    """Service for handling Slack interactions and feedback collection"""
    
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")  # For future bot features
        self.feedback_cache = {}  # Cache session data for feedback
    
    def create_enhanced_interactive_message(self, message: str, draft: str, 
                                          sender_email: str, subject: str,
                                          session_id: str, attio_url: str = "", 
                                          gdrive_url: str = "") -> int:
        """Create enhanced interactive Slack message with feedback options"""
        
        # Store session data for feedback processing
        self.feedback_cache[session_id] = {
            "sender_email": sender_email,
            "subject": subject,
            "draft": draft,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Create rich interactive message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📧 New Email Response Ready"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*From:* {sender_email}\n*Subject:* {subject}\n*Session:* `{session_id[:8]}...`"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*AI Analysis:*\n{message}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Generated Draft:*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{draft[:1000]}{'...' if len(draft) > 1000 else ''}```"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Please review and rate the draft quality:*"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "⭐ Poor (1)",
                            "emoji": True
                        },
                        "value": json.dumps({"session_id": session_id, "rating": 1, "action": "rate"}),
                        "action_id": "rate_1",
                        "style": "danger"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "⭐⭐ Fair (2)",
                            "emoji": True
                        },
                        "value": json.dumps({"session_id": session_id, "rating": 2, "action": "rate"}),
                        "action_id": "rate_2"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "⭐⭐⭐ Good (3)",
                            "emoji": True
                        },
                        "value": json.dumps({"session_id": session_id, "rating": 3, "action": "rate"}),
                        "action_id": "rate_3"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "⭐⭐⭐⭐ Great (4)",
                            "emoji": True
                        },
                        "value": json.dumps({"session_id": session_id, "rating": 4, "action": "rate"}),
                        "action_id": "rate_4",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "⭐⭐⭐⭐⭐ Excellent (5)",
                            "emoji": True
                        },
                        "value": json.dumps({"session_id": session_id, "rating": 5, "action": "rate"}),
                        "action_id": "rate_5",
                        "style": "primary"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Approve & Send",
                            "emoji": True
                        },
                        "value": json.dumps({"session_id": session_id, "action": "approve"}),
                        "action_id": "approve_draft",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✏️ Edit Draft",
                            "emoji": True
                        },
                        "value": json.dumps({"session_id": session_id, "action": "edit"}),
                        "action_id": "edit_draft"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ Reject",
                            "emoji": True
                        },
                        "value": json.dumps({"session_id": session_id, "action": "reject"}),
                        "action_id": "reject_draft",
                        "style": "danger"
                    }
                ]
            }
        ]
        
        # Add external links if provided
        if attio_url or gdrive_url:
            link_elements = []
            if attio_url:
                link_elements.append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Attio Campaign",
                        "emoji": True
                    },
                    "url": attio_url,
                    "action_id": "attio_link"
                })
            if gdrive_url:
                link_elements.append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📁 Client Drive",
                        "emoji": True
                    },
                    "url": gdrive_url,
                    "action_id": "gdrive_link"
                })
            
            blocks.append({
                "type": "actions",
                "elements": link_elements
            })
        
        # Add feedback section
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Optional: Add feedback or notes*"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "💬 Add Feedback",
                        "emoji": True
                    },
                    "value": json.dumps({"session_id": session_id, "action": "feedback"}),
                    "action_id": "add_feedback"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🤖 Generated by BookingAssistant • Session: {session_id[:8]}... • <http://localhost:8001|View Dashboard>"
                    }
                ]
            }
        ])
        
        payload = {"blocks": blocks}
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code
        except Exception as e:
            print(f"Error sending enhanced Slack message: {e}")
            return 500
    
    def handle_slack_interaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack button interactions and feedback"""
        try:
            user = payload.get("user", {})
            actions = payload.get("actions", [])
            
            if not actions:
                return {"response_type": "ephemeral", "text": "No action specified"}
            
            action = actions[0]
            action_id = action.get("action_id")
            action_value = json.loads(action.get("value", "{}"))
            
            session_id = action_value.get("session_id")
            if not session_id:
                return {"response_type": "ephemeral", "text": "Invalid session ID"}
            
            # Handle different action types
            if action_id.startswith("rate_"):
                return self._handle_rating(session_id, action_value, user)
            elif action_id == "approve_draft":
                return self._handle_approval(session_id, user)
            elif action_id == "edit_draft":
                return self._handle_edit_request(session_id, user)
            elif action_id == "reject_draft":
                return self._handle_rejection(session_id, user)
            elif action_id == "add_feedback":
                return self._handle_feedback_request(session_id, user)
            else:
                return {"response_type": "ephemeral", "text": "Unknown action"}
                
        except Exception as e:
            print(f"Error handling Slack interaction: {e}")
            return {"response_type": "ephemeral", "text": "Error processing your request"}
    
    def _handle_rating(self, session_id: str, action_value: Dict, user: Dict) -> Dict[str, Any]:
        """Handle quality rating feedback"""
        rating = action_value.get("rating")
        
        # Log feedback to metrics
        metrics.log_human_feedback(
            action="rated",
            rating=rating,
            slack_message_id=session_id[:8]
        )
        
        # Update message to show rating received
        rating_text = "⭐" * rating
        return {
            "response_type": "in_channel",
            "replace_original": False,
            "text": f"✅ Quality rating recorded: {rating_text} ({rating}/5) by {user.get('name', 'user')}"
        }
    
    def _handle_approval(self, session_id: str, user: Dict) -> Dict[str, Any]:
        """Handle draft approval"""
        # Log approval to metrics
        metrics.log_human_feedback(
            action="approved",
            slack_message_id=session_id[:8]
        )
        
        return {
            "response_type": "in_channel",
            "replace_original": False,
            "text": f"✅ Draft approved by {user.get('name', 'user')} - Ready to send!"
        }
    
    def _handle_edit_request(self, session_id: str, user: Dict) -> Dict[str, Any]:
        """Handle edit request"""
        # For now, just log the edit intent
        # In a full implementation, this could open a modal for editing
        metrics.log_human_feedback(
            action="edit_requested",
            slack_message_id=session_id[:8]
        )
        
        return {
            "response_type": "ephemeral",
            "text": "📝 Edit mode requested. Please copy the draft and edit manually, then mark as approved when ready."
        }
    
    def _handle_rejection(self, session_id: str, user: Dict) -> Dict[str, Any]:
        """Handle draft rejection"""
        metrics.log_human_feedback(
            action="rejected",
            slack_message_id=session_id[:8]
        )
        
        return {
            "response_type": "in_channel",
            "replace_original": False,
            "text": f"❌ Draft rejected by {user.get('name', 'user')} - Needs revision"
        }
    
    def _handle_feedback_request(self, session_id: str, user: Dict) -> Dict[str, Any]:
        """Handle feedback addition request"""
        # In a full implementation, this would open a modal for detailed feedback
        return {
            "response_type": "ephemeral",
            "text": "💬 Feedback feature coming soon! For now, please use the rating buttons above."
        }
    
    def calculate_edit_distance(self, original: str, edited: str) -> int:
        """Calculate simple edit distance between original and edited text"""
        # Simple character difference count
        return abs(len(original) - len(edited)) + sum(
            c1 != c2 for c1, c2 in zip(original, edited)
        )

# Global feedback service instance
slack_feedback = SlackFeedbackService()