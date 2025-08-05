# run_assistant.py

import time
import os
import sys
from dotenv import load_dotenv

# Add src to path and load environment variables
sys.path.append('src')
load_dotenv()

from src.email_service import EmailService
from src.main import graph
from src.metrics_service import metrics

def process_email(email_details: dict):
    """Invokes the LangGraph pipeline for a single email."""
    print("\n" + "="*70)
    print(f"📧 PROCESSING EMAIL FROM: {email_details['sender_email']}")
    print(f"📝 SUBJECT: {email_details['subject']}")
    print(f"👤 SENDER: {email_details['sender_name']}")
    print("="*70)

    # Start metrics session
    session_id = metrics.start_session(email_details)

    # The 'body' from the service already contains the combined subject and content
    state = {
        "email_text": email_details["body"],
        "subject": email_details["subject"],
        "sender_name": email_details["sender_name"],
        "sender_email": email_details["sender_email"]
    }

    import uuid
    thread_id = str(uuid.uuid4())
    thread = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph.invoke(state, thread)
        
        print("\n" + "="*70)
        print("📊 PROCESSING RESULTS")
        print("="*70)
        print(f"🏷️  Classification: {result.get('label', 'N/A')}")
        print(f"📁 Document Status: {result.get('document_extraction_status', 'N/A')}")
        print(f"📧 Draft Status: {result.get('draft_status', 'N/A')}")
        print(f"💬 Slack Status: {result.get('notification_status', 'N/A')}")
        print(f"📈 Session ID: {session_id}")
        
        if result.get('final_draft'):
            print(f"\n📝 FINAL DRAFT PREVIEW:")
            print("-" * 50)
            print(result['final_draft'][:300] + "..." if len(result['final_draft']) > 300 else result['final_draft'])
            print("-" * 50)
        
        # Complete metrics session
        metrics.complete_session(final_result=result)
        
        print(f"\n✅ COMPLETED processing email from: {email_details['sender_email']}")
        
    except Exception as e:
        print(f"\n❌ ERROR processing email from {email_details['sender_email']}: {e}")
        
        # Log error in metrics
        metrics.complete_session(error=str(e))
        
        import traceback
        traceback.print_exc()

def main_loop():
    """Main loop to poll for new emails and process them."""
    email_service = EmailService()
    polling_interval = 60  # seconds
    cache_clear_interval = 3600  # Clear cache every hour
    last_cache_clear = time.time()
    
    # Check email marking configuration
    mark_as_read = os.getenv('MARK_EMAILS_AS_READ', 'false').lower() == 'true'

    print("\n" + "="*70)
    print("🚀 STARTING BOOKING & REPLY ASSISTANT - PRODUCTION MODE")
    print("="*70)
    print("📧 Email Service: Nylas API")
    print("🔄 Polling Interval: 60 seconds")
    print(f"📖 Mark Emails as Read: {'Yes' if mark_as_read else 'No (keeps unread for human review)'}")
    print(f"💬 Slack Notifications: {'ENABLED' if os.getenv('TESTING_MODE') != 'true' else 'DISABLED (Testing Mode)'}")
    print("📝 Gmail Drafts: ENABLED via Nylas")
    print("="*70)
    
    while True:
        try:
            print(f"\n🔍 Checking for new emails... (Next check in {polling_interval}s)")
            
            # Clear cache periodically to prevent memory growth
            current_time = time.time()
            if current_time - last_cache_clear > cache_clear_interval:
                email_service.clear_processed_cache()
                last_cache_clear = current_time
            
            # Fetch emails (Nylas handles all email sources)
            all_new_emails = email_service.fetch_unread_gmail_emails()
            
            if not all_new_emails:
                print("No new emails found.")
            else:
                print(f"Found {len(all_new_emails)} new email(s) to process.")
                for email_details in all_new_emails:
                    process_email(email_details)
            
            time.sleep(polling_interval)
        
        except KeyboardInterrupt:
            print("\n👋 Shutting down assistant.")
            break
        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")
            print("Restarting loop in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()