# src/nylas_email_service.py

import os
import hashlib
from typing import List, Dict, Any, Set
from dotenv import load_dotenv
from nylas import Client
from nylas.models.errors import NylasApiError

load_dotenv()

class NylasEmailService:
    """A service to fetch emails using Nylas API."""

    def __init__(self):
        self.nylas_client = self._get_nylas_client()
        self.grant_id = os.getenv('NYLAS_GRANT_ID')
        
        # Track processed emails in this session to avoid re-processing
        self.processed_message_ids: Set[str] = set()
        
        # Load spam filter keywords from environment or use defaults
        default_spam_keywords = [
            "delivery status notification", "drink-mouth", "uncle-quite", 
            "sheep-dress", "shown-shown", "meant-funny", "state-forth",
            "whale-floor", "saved-blood", "maybe-least"
        ]
        spam_keywords_env = os.getenv('SPAM_KEYWORDS', '')
        if spam_keywords_env:
            self.spam_keywords = [k.strip() for k in spam_keywords_env.split(',') if k.strip()]
        else:
            self.spam_keywords = default_spam_keywords
        
        # Load list of senders to ignore from environment or use defaults
        default_ignore_senders = [
            "aidrian@podcastguestlaunch.com",
            "workspace-noreply@google.com",
            "payments-noreply@google.com"
        ]
        ignore_senders_env = os.getenv('IGNORE_SENDERS', '')
        if ignore_senders_env:
            self.ignore_senders = [s.strip() for s in ignore_senders_env.split(',') if s.strip()]
        else:
            self.ignore_senders = default_ignore_senders
        
        # Log the current configuration
        print(f"📧 Email filtering configured:")
        print(f"   • Ignoring emails from: {', '.join(self.ignore_senders)}")
        print(f"   • Spam keywords: {len(self.spam_keywords)} configured")

    def _get_nylas_client(self):
        """Initialize Nylas client."""
        api_key = os.getenv('NYLAS_API_KEY')
        api_uri = os.getenv('NYLAS_API_URI', 'https://api.us.nylas.com')
        
        if not api_key:
            if os.getenv('TESTING_MODE') == 'true':
                print("⚠️  Nylas service unavailable in testing mode")
                return None
            else:
                raise ValueError("NYLAS_API_KEY environment variable is required")
        
        if not os.getenv('NYLAS_GRANT_ID'):
            if os.getenv('TESTING_MODE') == 'true':
                print("⚠️  Nylas grant ID not set in testing mode")
                return None
            else:
                raise ValueError("NYLAS_GRANT_ID environment variable is required")
        
        try:
            return Client(api_key=api_key, api_uri=api_uri)
        except Exception as e:
            print(f"⚠️  Nylas client initialization failed: {e}")
            return None

    def _should_process_email(self, subject, body, sender_email):
        """Replicates the 'Alive Blockers' filter from Make.com."""
        if not sender_email:
            return False
        
        # Check if sender is in the ignore list
        if sender_email.lower() in [s.lower() for s in self.ignore_senders]:
            print(f"Skipping email from ignored sender: {sender_email}")
            return False

        lower_subject = (subject or "").lower()
        lower_body = (body or "").lower()
        
        for keyword in self.spam_keywords:
            if keyword in lower_subject or keyword in lower_body:
                print(f"Skipping email due to spam keyword: '{keyword}'")
                return False
        
        return True

    def _clean_text(self, text):
        """Replicates the text cleaning from the Make.com scenario."""
        if not text:
            return ""
        return text.replace(' ', ' ').replace('\t', ' ').replace('\r', '\n')

    def _extract_email_body(self, message) -> str:
        """Extract the plain text body from a Nylas message."""
        # Nylas SDK v6 provides body as a string directly
        body = ""
        
        # Check for body attribute
        if hasattr(message, 'body') and message.body:
            body = message.body
        
        # If body is still empty, try snippet
        if not body and hasattr(message, 'snippet') and message.snippet:
            body = message.snippet
            
        return body

    def fetch_unread_emails(self) -> List[Dict[str, Any]]:
        """Fetches unread emails from Gmail via Nylas."""
        if not self.nylas_client or not self.grant_id:
            print("⚠️  Nylas service not available - skipping email fetch")
            return []
            
        print("Fetching unread emails from Gmail via Nylas...")
        
        try:
            # Fetch unread messages from inbox
            # Using folder_id for inbox as "in" parameter might not work with all Nylas versions
            messages = self.nylas_client.messages.list(
                self.grant_id,
                query_params={
                    "limit": 50,  # Adjust as needed
                    "unread": True
                }
            )
            
            email_data = []
            
            if not messages.data:
                print("No new unread messages found.")
                return []
            
            for msg in messages.data:
                # Skip if already processed in this session
                if msg.id in self.processed_message_ids:
                    print(f"Skipping already processed email: {msg.id}")
                    continue
                
                # Extract sender information
                sender_email = "unknown@email.com"
                sender_name = "Unknown"
                
                if msg.from_ and len(msg.from_) > 0:
                    sender = msg.from_[0]
                    if isinstance(sender, dict):
                        sender_email = sender.get('email', sender_email)
                        sender_name = sender.get('name', sender_email.split('@')[0])
                    else:
                        sender_email = getattr(sender, 'email', sender_email)
                        sender_name = getattr(sender, 'name', sender_email.split('@')[0])
                
                # Extract subject
                subject = msg.subject or "(No Subject)"
                
                # Extract body
                body = self._extract_email_body(msg)
                
                # Apply spam filtering
                if self._should_process_email(subject, body, sender_email):
                    # Combine subject and body as per Make.com logic
                    combined_content = f"Subject: {subject}\n\nContent: {body}"
                    
                    email_data.append({
                        "message_id": msg.id,  # Store for marking as read later
                        "subject": subject,
                        "sender_name": sender_name or sender_email.split('@')[0],
                        "sender_email": sender_email,
                        "body": self._clean_text(combined_content),
                        "date": msg.date
                    })
                    
                    # Mark as processed in this session
                    self.processed_message_ids.add(msg.id)
                
                # NOTE: We intentionally do NOT mark emails as read here
                # This preserves the unread status for human review in Gmail
                # The database tracking prevents duplicate processing instead
            
            print(f"Fetched and filtered {len(email_data)} new emails from Gmail via Nylas.")
            return email_data
            
        except NylasApiError as e:
            print(f"Nylas API Error while fetching emails: {e}")
            if hasattr(e, 'error_type'):
                print(f"Error Type: {e.error_type}")
            return []
        except Exception as e:
            print(f"An error occurred while fetching emails: {e}")
            import traceback
            traceback.print_exc()
            return []

    def create_draft(self, to: str, subject: str, body: str, sender_name: str = "") -> str:
        """Creates a draft email using Nylas."""
        if not self.nylas_client or not self.grant_id:
            print("⚠️  Nylas service not available - draft creation skipped")
            return "Nylas service unavailable - draft not created"
            
        try:
            # Create the draft
            draft = self.nylas_client.drafts.create(
                self.grant_id,
                request_body={
                    "to": [{"email": to, "name": sender_name}] if sender_name else [{"email": to}],
                    "subject": subject,
                    "body": body
                }
            )
            
            print(f"Draft created successfully via Nylas. Draft ID: {draft.data.id}")
            return f"Draft created with ID: {draft.data.id}"
            
        except NylasApiError as e:
            print(f"Nylas API Error while creating draft: {e}")
            if hasattr(e, 'error_type'):
                print(f"Error Type: {e.error_type}")
            return f"Error creating draft: {e}"
        except Exception as e:
            print(f"An error occurred while creating draft: {e}")
            return f"Error creating draft: {e}"

    def send_draft(self, draft_id: str) -> str:
        """Send a draft email using Nylas."""
        if not self.nylas_client or not self.grant_id:
            print("⚠️  Nylas service not available - cannot send draft")
            return "Nylas service unavailable - draft not sent"
            
        try:
            # Send the draft
            message = self.nylas_client.drafts.send(
                self.grant_id,
                draft_id
            )
            
            print(f"Draft sent successfully via Nylas. Message ID: {message.data.id}")
            return f"Message sent with ID: {message.data.id}"
            
        except NylasApiError as e:
            print(f"Nylas API Error while sending draft: {e}")
            return f"Error sending draft: {e}"
        except Exception as e:
            print(f"An error occurred while sending draft: {e}")
            return f"Error sending draft: {e}"
    
    def mark_email_as_read(self, message_id: str) -> bool:
        """Mark a specific email as read"""
        if not self.nylas_client or not self.grant_id or not message_id:
            return False
            
        try:
            self.nylas_client.messages.update(
                self.grant_id,
                message_id,
                request_body={
                    "unread": False
                }
            )
            print(f"✅ Marked message {message_id} as read")
            return True
        except Exception as e:
            print(f"⚠️  Could not mark message {message_id} as read: {e}")
            return False
    
    def clear_processed_cache(self):
        """Clear the processed message IDs cache. 
        Useful for long-running deployments to prevent memory growth."""
        cleared_count = len(self.processed_message_ids)
        self.processed_message_ids.clear()
        print(f"Cleared {cleared_count} processed message IDs from cache")
        return cleared_count