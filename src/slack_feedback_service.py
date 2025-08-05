"""
Slack Feedback Service using Bot Token (instead of webhook)
Handles interactive Slack components and quality rating collection with proper bot features.
"""

import os
import json
import time
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
from urllib.parse import parse_qs
from src.metrics_service import metrics
from src.dashboard_service import dashboard
from dotenv import load_dotenv

# Import Slack SDK
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

class SlackFeedbackService:
    """Service for handling Slack interactions and feedback collection using Bot Token"""
    
    def __init__(self):
        # Bot token instead of webhook
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        self.channel_id = os.getenv("SLACK_CHANNEL_ID", "#booking-assistant")  # Default channel
        
        # Initialize Slack client
        if self.bot_token:
            self.slack_client = WebClient(token=self.bot_token)
        else:
            self.slack_client = None
            print("⚠️ SLACK_BOT_TOKEN not configured - Slack features disabled")
        
        self.feedback_cache = {}  # Cache session data for feedback
    
    def verify_slack_request(self, request_body: bytes, timestamp: str, signature: str) -> bool:
        """Verify that the request comes from Slack"""
        if not self.signing_secret:
            print("⚠️ SLACK_SIGNING_SECRET not configured - skipping verification")
            return True
        
        # Create the base string
        base_string = f"v0:{timestamp}:{request_body.decode('utf-8')}"
        
        # Create a new HMAC object
        my_signature = 'v0=' + hmac.new(
            self.signing_secret.encode(),
            base_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(my_signature, signature)
    
    def create_enhanced_interactive_message(self, message: str, draft: str, 
                                          sender_email: str, subject: str,
                                          session_id: str, attio_url: str = "", 
                                          gdrive_url: str = "") -> int:
        """Create enhanced interactive Slack message with feedback options using Bot Token"""
        
        if not self.slack_client:
            print("❌ Slack client not initialized")
            return 500
        
        # Store session data for feedback processing
        self.feedback_cache[session_id] = {
            "sender_email": sender_email,
            "subject": subject,
            "draft": draft,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Create rich interactive message blocks
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
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🤖 Generated by BookingAssistant • Session: {session_id[:8]}... • <http://localhost:8080|View Dashboard>"
                    }
                ]
            }
        ])
        
        try:
            # Send message using bot token
            response = self.slack_client.chat_postMessage(
                channel=self.channel_id,
                blocks=blocks,
                text=f"New email response ready for {sender_email}"  # Fallback text
            )
            
            # Store the message timestamp for threading
            if response["ok"]:
                self.feedback_cache[session_id]["message_ts"] = response["ts"]
                self.feedback_cache[session_id]["channel"] = response["channel"]
            
            return 200 if response["ok"] else 500
            
        except SlackApiError as e:
            print(f"Error sending Slack message: {e.response['error']}")
            return 500
    
    def handle_slack_interaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack button interactions and feedback"""
        print("\n📨 Processing Slack interaction in feedback service")
        try:
            user = payload.get("user", {})
            actions = payload.get("actions", [])
            
            if not actions:
                print("❌ No actions in payload")
                return {"text": "No action specified"}
            
            action = actions[0]
            action_id = action.get("action_id")
            action_value = json.loads(action.get("value", "{}"))
            
            print(f"📋 Action ID: {action_id}")
            print(f"📋 Action value: {action_value}")
            
            session_id = action_value.get("session_id")
            if not session_id:
                print("❌ No session_id in action value")
                return {"text": "Invalid session ID"}
            
            print(f"🔑 Session ID: {session_id}")
            
            # Get the original message info for threading
            channel = payload.get("channel", {}).get("id")
            message_ts = payload.get("message", {}).get("ts")
            
            # Debug channel info
            print(f"📍 Channel from payload: {channel}")
            print(f"⏰ Message timestamp: {message_ts}")
            
            # If no channel from payload, use default
            if not channel:
                channel = self.channel_id
                print(f"⚠️  No channel in payload, using default: {channel}")
            
            # Handle different action types
            if action_id.startswith("rate_"):
                print(f"⭐ Handling rating action: {action_id}")
                return self._handle_rating(session_id, action_value, user, channel, message_ts)
            elif action_id == "approve_draft":
                print("✅ Handling approval action")
                return self._handle_approval(session_id, user, channel, message_ts)
            elif action_id == "edit_draft":
                print("✏️ Handling edit action")
                return self._handle_edit_request(session_id, user, channel, message_ts)
            elif action_id == "reject_draft":
                print("❌ Handling rejection action")
                return self._handle_rejection(session_id, user, channel, message_ts)
            else:
                print(f"❓ Unknown action: {action_id}")
                return {"text": "Unknown action"}
                
        except Exception as e:
            print(f"Error handling Slack interaction: {e}")
            return {"text": "Error processing your request"}
    
    def _handle_rating(self, session_id: str, action_value: Dict, user: Dict, 
                      channel: str, message_ts: str) -> Dict[str, Any]:
        """Handle quality rating feedback"""
        rating = action_value.get("rating")
        print(f"📊 Recording rating: {rating} stars for session: {session_id}")
        
        # Log feedback to metrics
        try:
            success = metrics.log_feedback_for_session(
                session_id=session_id,
                action="rated",
                rating=rating,
                slack_message_id=session_id[:8]
            )
            
            if success and self.slack_client:
                rating_text = "⭐" * rating
                # Send ephemeral message to the user
                self.slack_client.chat_postEphemeral(
                    channel=channel,
                    user=user.get("id"),
                    text=f"✅ Your rating of {rating_text} ({rating}/5) has been recorded!",
                    thread_ts=message_ts
                )
                
                # Update the original message to show rating was given
                self.slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=message_ts,
                    text=f"📊 Rated {rating_text} by {user.get('name', 'user')}"
                )
            
            # Return empty response to acknowledge the interaction
            return {}
            
        except Exception as e:
            print(f"❌ Exception during rating save: {e}")
            return {"text": f"❌ Error recording rating: {str(e)}"}
    
    def _handle_approval(self, session_id: str, user: Dict, channel: str, 
                        message_ts: str) -> Dict[str, Any]:
        """Handle draft approval"""
        # Log approval to metrics
        success = metrics.log_feedback_for_session(
            session_id=session_id,
            action="approved",
            rating=5,  # Approval implies highest rating
            slack_message_id=session_id[:8]
        )
        
        if success and self.slack_client:
            # Send confirmation in thread
            self.slack_client.chat_postMessage(
                channel=channel,
                thread_ts=message_ts,
                text=f"✅ Draft approved by {user.get('name', 'user')} - Ready to send!"
            )
        
        return {}
    
    def _handle_edit_request(self, session_id: str, user: Dict, channel: str, 
                           message_ts: str) -> Dict[str, Any]:
        """Handle edit request - provide instructions for editing"""
        print(f"✏️ Edit draft requested for session: {session_id}")
        
        # Log the edit intent
        metrics.log_feedback_for_session(
            session_id=session_id,
            action="edited",
            slack_message_id=session_id[:8]
        )
        
        # Get the draft content from database
        session_data = dashboard.get_session_summary(session_id)
        
        if session_data:
            draft_content = (session_data.get('final_draft_content') or 
                           session_data.get('draft_content') or 
                           "No draft content available")
        else:
            draft_content = "Draft not found"
        
        if self.slack_client:
            try:
                # Send ephemeral message with edit instructions
                print(f"👻 Sending ephemeral to channel: {channel}, user: {user.get('id')}")
                self.slack_client.chat_postEphemeral(
                    channel=channel,
                    user=user.get("id"),
                    blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "📝 *Edit Draft Mode*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Current Draft:*\n```{draft_content[:1500]}{'...' if len(draft_content) > 1500 else ''}```"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*How to edit:*\n1. Copy the draft above\n2. Make your edits\n3. Reply in this thread with your edited version\n4. Click 'Approve' when satisfied"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [{
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Full Draft Online"},
                            "url": f"http://localhost:8080/session/{session_id}",
                            "action_id": "view_online"
                        }]
                    }
                ],
                text="Edit draft instructions"  # Fallback text
                )
                print("✅ Ephemeral message sent successfully")
            except SlackApiError as e:
                error = e.response['error']
                print(f"❌ Ephemeral message failed: {error}")
                
                if error == 'channel_not_found':
                    print("   Bot cannot find the channel. Trying with default channel...")
                    # Try with default channel
                    try:
                        self.slack_client.chat_postEphemeral(
                            channel=self.channel_id,
                            user=user.get("id"),
                            text=f"\ud83d\udcdd Edit Draft Mode\n\nDraft:\n```{draft_content[:1000]}```\n\nCopy and edit, then reply in the thread.",
                        )
                        print(f"✅ Sent to default channel: {self.channel_id}")
                    except Exception as e2:
                        print(f"❌ Default channel also failed: {e2}")
                elif error == 'user_not_found':
                    print(f"   User ID not found: {user.get('id')}")
            
            # Post a message in the thread for context
            try:
                self.slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=message_ts,
                    text=f"✏️ {user.get('name', 'user')} is editing the draft. Reply with your edited version."
                )
            except Exception as e:
                print(f"❌ Error posting thread message: {e}")
        
        return {}
    
    def _handle_rejection(self, session_id: str, user: Dict, channel: str, 
                         message_ts: str) -> Dict[str, Any]:
        """Handle draft rejection"""
        metrics.log_feedback_for_session(
            session_id=session_id,
            action="rejected",
            rating=1,  # Rejection implies lowest rating
            slack_message_id=session_id[:8]
        )
        
        if self.slack_client:
            self.slack_client.chat_postMessage(
                channel=channel,
                thread_ts=message_ts,
                text=f"❌ Draft rejected by {user.get('name', 'user')} - Needs revision"
            )
        
        return {}
    
    def send_message(self, text: str, blocks: List[Dict] = None) -> bool:
        """Send a simple message to the default channel"""
        if not self.slack_client:
            print("❌ Slack client not initialized")
            return False
        
        try:
            response = self.slack_client.chat_postMessage(
                channel=self.channel_id,
                text=text,
                blocks=blocks
            )
            return response["ok"]
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")
            return False
    
    def calculate_edit_distance(self, original: str, edited: str) -> int:
        """Calculate simple edit distance between original and edited text"""
        # Simple character difference count
        return abs(len(original) - len(edited)) + sum(
            c1 != c2 for c1, c2 in zip(original, edited)
        )

# Global feedback service instance
slack_feedback = SlackFeedbackService()