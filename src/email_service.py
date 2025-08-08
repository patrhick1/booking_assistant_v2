# src/email_service.py

# This file now uses Nylas for all email operations
# The original Gmail service account and IMAP implementations have been replaced

from src.nylas_email_service import NylasEmailService

class EmailService(NylasEmailService):
    """
    Email service using Nylas API for all email operations.
    This replaces the previous Gmail service account and IMAP implementations.
    """
    
    def __init__(self):
        super().__init__()
    
    def fetch_unread_gmail_emails(self):
        """Fetch unread emails from Gmail using Nylas."""
        # Nylas handles all email sources through the same API
        return self.fetch_unread_emails()
    
    def fetch_unread_maildoso_emails(self):
        """Legacy method - Nylas handles all emails through unified API."""
        # Since we're using Nylas with Gmail, this returns empty
        # You can remove calls to this method from the codebase
        print("Note: Maildoso email fetching not needed with Nylas - all emails come through unified API")
        return []