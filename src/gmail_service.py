from src.nylas_email_service import NylasEmailService

class GmailApiService(NylasEmailService):
    """Service for Gmail actions using Nylas API."""

    def create_draft(self, to: str, subject: str, body: str):
        """Creates a draft email in the user's Gmail account via Nylas."""
        # Extract sender name from email if available
        sender_name = to.split('@')[0] if '@' in to else ""
        
        # Use the parent class method from NylasEmailService
        return super().create_draft(to, subject, body, sender_name)