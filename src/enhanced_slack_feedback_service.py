"""
Enhanced Slack Feedback Service with Database Integration
Handles all Slack interactions and triggers proper database updates
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import requests
from src.database_service import database_service, SlackInteraction, QualityFeedback
from src.metrics_service import metrics
from dotenv import load_dotenv

load_dotenv()

class EnhancedSlackFeedbackService:
    """Enhanced service for handling Slack interactions with full database integration"""
    
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.feedback_cache = {}  # Temporary cache for session data
    
    def create_enhanced_interactive_message(self, message: str, draft: str, 
                                          sender_email: str, subject: str,
                                          session_id: str, attio_url: str = "", 
                                          gdrive_url: str = "") -> int:
        """Create enhanced interactive Slack message with feedback options"""
        
        if not self.webhook_url:
            print("❌ SLACK_WEBHOOK_URL not configured")
            return 400
        
        # Store session data for feedback processing
        self.feedback_cache[session_id] = {
            "sender_email": sender_email,
            "subject": subject,
            "draft": draft,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Create rich interactive message with all action buttons
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
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*From:* {sender_email}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Subject:* {subject}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Session:* `{session_id[:8]}...`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Classification:* {message.split('Classification: ')[-1].split('\\n')[0] if 'Classification:' in message else 'N/A'}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*AI Analysis:*\\n{message[:200]}..." if len(message) > 200 else message
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Generated Draft:*\\n```{draft[:300]}...```" if len(draft) > 300 else f"*Generated Draft:*\\n```{draft}```"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*⭐ Rate the quality of this draft:*"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select rating"
                    },
                    "action_id": f"rate_quality_{session_id}",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "⭐ 1 - Poor"
                            },
                            "value": f"rate_1_{session_id}"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "⭐⭐ 2 - Below Average"
                            },
                            "value": f"rate_2_{session_id}"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "⭐⭐⭐ 3 - Average"
                            },
                            "value": f"rate_3_{session_id}"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "⭐⭐⭐⭐ 4 - Good"
                            },
                            "value": f"rate_4_{session_id}"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "⭐⭐⭐⭐⭐ 5 - Excellent"
                            },
                            "value": f"rate_5_{session_id}"
                        }
                    ]
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Approve & Send"
                        },
                        "style": "primary",
                        "action_id": f"approve_{session_id}",
                        "value": f"approve_{session_id}"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✏️ Edit Draft"
                        },
                        "action_id": f"edit_{session_id}",
                        "value": f"edit_{session_id}"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ Reject"
                        },
                        "style": "danger",
                        "action_id": f"reject_{session_id}",
                        "value": f"reject_{session_id}"
                    }
                ]
            }
        ]
        
        # Add external links if available
        if attio_url or gdrive_url:
            link_elements = []
            if attio_url:
                link_elements.append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Attio Campaign"
                    },
                    "url": attio_url,
                    "action_id": f"attio_link_{session_id}"
                })
            if gdrive_url:
                link_elements.append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📁 Client Drive"
                    },
                    "url": gdrive_url,
                    "action_id": f"gdrive_link_{session_id}"
                })
            
            blocks.append({
                "type": "actions",
                "elements": link_elements
            })
        
        # Add feedback button
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "💬 Add Feedback"
                    },
                    "action_id": f"feedback_{session_id}",
                    "value": f"feedback_{session_id}"
                }
            ]
        })
        
        payload = {
            "text": f"📧 New email response ready for review - {sender_email}",
            "blocks": blocks
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code == 200:
                print(f"✅ Enhanced Slack notification sent for session {session_id}")
            else:
                print(f"❌ Slack notification failed: {response.status_code}")
            return response.status_code
        except Exception as e:
            print(f"❌ Error sending Slack notification: {e}")
            return 500
    
    def handle_slack_interaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack interactive component interactions with database updates"""
        
        interaction_start = time.time()
        
        try:
            # Extract interaction data
            interaction_type = payload.get("type", "")
            user = payload.get("user", {})
            channel = payload.get("channel", {})
            message = payload.get("message", {})
            actions = payload.get("actions", [])
            
            if not actions:
                return {"response_type": "ephemeral", "text": "No action found"}
            
            action = actions[0]
            action_id = action.get("action_id", "")
            action_value = action.get("value", action.get("selected_option", {}).get("value", ""))
            
            # Extract session ID from action
            session_id = self._extract_session_id(action_id, action_value)
            if not session_id:
                return {"response_type": "ephemeral", "text": "Invalid session ID"}
            
            # Record the Slack interaction
            slack_interaction = SlackInteraction(
                session_id=session_id,
                interaction_type="button_click" if action.get("type") == "button" else "selection",
                action_value=action_value.split("_")[0] if "_" in action_value else action_value,
                user_id=user.get("id", ""),
                user_name=user.get("name", ""),
                channel_id=channel.get("id", ""),
                message_ts=message.get("ts", ""),
                trigger_id=payload.get("trigger_id", ""),
                response_time_ms=int((time.time() - interaction_start) * 1000),
                payload=payload
            )
            
            database_service.record_slack_interaction(slack_interaction)
            
            # Handle different action types
            if action_value.startswith("approve_"):
                return self._handle_approve_action(session_id, user, payload)
            elif action_value.startswith("reject_"):
                return self._handle_reject_action(session_id, user, payload)
            elif action_value.startswith("edit_"):
                return self._handle_edit_action(session_id, user, payload)
            elif action_value.startswith("rate_"):
                return self._handle_rating_action(session_id, action_value, user, payload)
            elif action_value.startswith("feedback_"):
                return self._handle_feedback_action(session_id, user, payload)
            else:
                return {"response_type": "ephemeral", "text": f"Unknown action: {action_value}"}
                
        except Exception as e:
            print(f"❌ Error handling Slack interaction: {e}")
            return {"response_type": "ephemeral", "text": "An error occurred processing your request"}
    
    def _extract_session_id(self, action_id: str, action_value: str) -> Optional[str]:
        """Extract session ID from action ID or value"""
        # Try to extract from action_id first
        if "_" in action_id:
            parts = action_id.split("_")
            if len(parts) >= 2:
                potential_session = parts[-1]
                if len(potential_session) >= 8:  # Minimum UUID length
                    return potential_session
        
        # Try to extract from action_value
        if "_" in action_value:
            parts = action_value.split("_")
            for part in parts:
                if len(part) >= 8:  # Could be a session ID
                    return part
        
        return None
    
    def _handle_approve_action(self, session_id: str, user: Dict, payload: Dict) -> Dict[str, Any]:
        """Handle approve action - create Gmail draft and update database"""
        
        # Record quality feedback
        feedback = QualityFeedback(
            session_id=session_id,
            human_action="approved",
            slack_user_id=user.get("id"),
            slack_user_name=user.get("name"),
            slack_channel_id=payload.get("channel", {}).get("id"),
            slack_message_id=payload.get("message", {}).get("ts")
        )
        
        database_service.record_quality_feedback(feedback)
        
        # Update workflow state
        database_service.update_workflow_state(
            session_id=session_id,
            new_state="approved",
            current_step="creating_gmail_draft",
            next_actions={"available_actions": ["create_draft", "send_email"]}
        )
        
        # TODO: Trigger Gmail draft creation
        # This would call the Gmail service to create the actual draft
        
        return {
            "response_type": "in_channel",
            "text": f"✅ Draft approved by {user.get('name')}! Creating Gmail draft...",
            "replace_original": False
        }
    
    def _handle_reject_action(self, session_id: str, user: Dict, payload: Dict) -> Dict[str, Any]:
        """Handle reject action - mark as rejected in database"""
        
        # Record quality feedback
        feedback = QualityFeedback(
            session_id=session_id,
            human_action="rejected",
            slack_user_id=user.get("id"),
            slack_user_name=user.get("name"),
            slack_channel_id=payload.get("channel", {}).get("id"),
            slack_message_id=payload.get("message", {}).get("ts")
        )
        
        database_service.record_quality_feedback(feedback)
        
        # Update workflow state
        database_service.update_workflow_state(
            session_id=session_id,
            new_state="rejected",
            current_step="rejected_by_human",
            next_actions={"available_actions": ["reprocess", "archive"]}
        )
        
        return {
            "response_type": "in_channel",
            "text": f"❌ Draft rejected by {user.get('name')}. No email will be sent.",
            "replace_original": False
        }
    
    def _handle_edit_action(self, session_id: str, user: Dict, payload: Dict) -> Dict[str, Any]:
        """Handle edit action - open modal for editing"""
        
        # Get current draft content
        session_data = database_service.get_session_data(session_id)
        if not session_data:
            return {"response_type": "ephemeral", "text": "Session not found"}
        
        current_draft = session_data.get('final_draft_content') or session_data.get('draft_content', '')
        
        # Create modal for editing
        modal = {
            "type": "modal",
            "callback_id": f"edit_draft_{session_id}",
            "title": {
                "type": "plain_text",
                "text": "Edit Draft"
            },
            "submit": {
                "type": "plain_text",
                "text": "Save Changes"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Editing draft for:* {session_data.get('sender_email')}"
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "multiline": True,
                        "initial_value": current_draft,
                        "action_id": "draft_content"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Draft Content"
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Optional: Explain your changes..."
                        },
                        "action_id": "edit_notes"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Edit Notes (Optional)"
                    },
                    "optional": True
                }
            ]
        }
        
        # Record the edit initiation
        feedback = QualityFeedback(
            session_id=session_id,
            human_action="editing_initiated",
            slack_user_id=user.get("id"),
            slack_user_name=user.get("name"),
            slack_channel_id=payload.get("channel", {}).get("id"),
            slack_message_id=payload.get("message", {}).get("ts")
        )
        
        database_service.record_quality_feedback(feedback)
        
        return {
            "response_type": "ephemeral",
            "text": "Opening edit modal...",
            "view": modal
        }
    
    def _handle_rating_action(self, session_id: str, action_value: str, user: Dict, payload: Dict) -> Dict[str, Any]:
        """Handle quality rating action"""
        
        # Extract rating from action_value (e.g., "rate_5_session_id" -> 5)
        rating = int(action_value.split("_")[1])
        
        # Record quality feedback with rating
        feedback = QualityFeedback(
            session_id=session_id,
            human_action="rated",
            human_rating=rating,
            slack_user_id=user.get("id"),
            slack_user_name=user.get("name"),
            slack_channel_id=payload.get("channel", {}).get("id"),
            slack_message_id=payload.get("message", {}).get("ts")
        )
        
        database_service.record_quality_feedback(feedback)
        
        # Update workflow state
        database_service.update_workflow_state(
            session_id=session_id,
            new_state="rated",
            current_step="awaiting_action",
            next_actions={"available_actions": ["approve", "edit", "reject"]}
        )
        
        star_display = "⭐" * rating
        
        return {
            "response_type": "ephemeral",
            "text": f"Thank you! You rated this draft: {star_display} ({rating}/5)"
        }
    
    def _handle_feedback_action(self, session_id: str, user: Dict, payload: Dict) -> Dict[str, Any]:
        """Handle feedback action - open modal for additional feedback"""
        
        modal = {
            "type": "modal",
            "callback_id": f"additional_feedback_{session_id}",
            "title": {
                "type": "plain_text",
                "text": "Additional Feedback"
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit Feedback"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Provide additional feedback about this draft:*"
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "What could be improved? Any specific suggestions?"
                        },
                        "action_id": "feedback_content"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Your Feedback"
                    }
                }
            ]
        }
        
        return {
            "response_type": "ephemeral",
            "text": "Opening feedback form...",
            "view": modal
        }

# Global enhanced slack feedback service instance
enhanced_slack_feedback = EnhancedSlackFeedbackService()