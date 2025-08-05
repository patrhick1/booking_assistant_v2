#!/usr/bin/env python3
"""
Test script for Nylas integration with BookingAssistant
"""

import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

load_dotenv()

def test_nylas_connection():
    """Test basic Nylas connection"""
    print("\n" + "="*60)
    print("TESTING NYLAS CONNECTION")
    print("="*60)
    
    # Check environment variables
    required_vars = ['NYLAS_API_KEY', 'NYLAS_GRANT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following in your .env file:")
        for var in missing_vars:
            print(f"  {var}=your_value_here")
        return False
    
    print("✅ All required environment variables are set")
    
    # Test Nylas client initialization
    try:
        from src.nylas_email_service import NylasEmailService
        service = NylasEmailService()
        
        if service.nylas_client:
            print("✅ Nylas client initialized successfully")
            return True
        else:
            print("❌ Nylas client initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing Nylas service: {e}")
        return False

def test_email_fetching():
    """Test fetching emails via Nylas"""
    print("\n" + "="*60)
    print("TESTING EMAIL FETCHING")
    print("="*60)
    
    try:
        from src.email_service import EmailService
        email_service = EmailService()
        
        print("Fetching unread emails...")
        emails = email_service.fetch_unread_gmail_emails()
        
        if emails:
            print(f"✅ Found {len(emails)} unread email(s)")
            for i, email in enumerate(emails[:3]):  # Show first 3
                print(f"\nEmail {i+1}:")
                print(f"  From: {email['sender_email']} ({email['sender_name']})")
                print(f"  Subject: {email['subject']}")
                print(f"  Preview: {email['body'][:100]}...")
        else:
            print("ℹ️  No unread emails found (this is okay if inbox is empty)")
            
        return True
        
    except Exception as e:
        print(f"❌ Error fetching emails: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_draft_creation():
    """Test creating a draft via Nylas"""
    print("\n" + "="*60)
    print("TESTING DRAFT CREATION")
    print("="*60)
    
    try:
        from src.gmail_service import GmailApiService
        gmail_service = GmailApiService()
        
        # Test draft
        test_email = "test@example.com"
        test_subject = "Test Draft from BookingAssistant (Nylas)"
        test_body = "This is a test draft created via Nylas integration.\n\nPlease do not send."
        
        print(f"Creating test draft to: {test_email}")
        result = gmail_service.create_draft(test_email, test_subject, test_body)
        
        if "Draft created with ID:" in result:
            print(f"✅ {result}")
            print("ℹ️  Check your Gmail drafts folder to verify")
            return True
        else:
            print(f"❌ Draft creation failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating draft: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pipeline_integration():
    """Test the full pipeline with a sample email"""
    print("\n" + "="*60)
    print("TESTING PIPELINE INTEGRATION")
    print("="*60)
    
    # Set testing mode to avoid Slack/Gmail actions
    os.environ['TESTING_MODE'] = 'true'
    
    try:
        from src.main import graph
        import uuid
        
        test_email = {
            "email_text": """Subject: Re: Podcast Guest - Tom Elliot
            
            Hi Aidrian,
            Thanks for the email. Tom Elliot sounds interesting.
            Could you send over his bio and some potential talking points for our show?
            We focus on early-stage startup growth.
            Best,
            Jane Doe""",
            "subject": "Re: Podcast Guest - Tom Elliot",
            "sender_name": "Jane Doe",
            "sender_email": "jane.doe@example.com"
        }
        
        print("Running test email through the pipeline...")
        thread_id = str(uuid.uuid4())
        thread = {"configurable": {"thread_id": thread_id}}
        
        result = graph.invoke(test_email, thread)
        
        print("\n✅ Pipeline completed successfully!")
        print(f"Classification: {result.get('label', 'N/A')}")
        print(f"Document Status: {result.get('document_extraction_status', 'N/A')}")
        print(f"Draft Status: {result.get('draft_status', 'N/A')}")
        
        if result.get('final_draft'):
            print(f"\nGenerated Draft Preview:")
            print("-" * 40)
            print(result['final_draft'][:300] + "...")
            
        return True
        
    except Exception as e:
        print(f"❌ Error in pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Reset testing mode
        os.environ['TESTING_MODE'] = 'false'

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 NYLAS INTEGRATION TEST SUITE")
    print("="*80)
    
    tests = [
        ("Connection Test", test_nylas_connection),
        ("Email Fetching", test_email_fetching),
        ("Draft Creation", test_draft_creation),
        ("Pipeline Integration", test_pipeline_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Unexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {total_passed}/{len(tests)} tests passed")
    
    if total_passed == len(tests):
        print("\n🎉 All tests passed! Nylas integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the output above for details.")

if __name__ == "__main__":
    main()