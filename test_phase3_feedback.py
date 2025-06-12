#!/usr/bin/env python3
"""
Test script for Phase 3: Human Feedback Integration
Tests the complete feedback loop from Slack interactions to metrics database
"""

import sys
import os
import json
import uuid
import time
from datetime import datetime, timezone

# Add src to path
sys.path.append('src')

from src.slack_feedback_service import slack_feedback
from src.metrics_service import metrics

def test_metrics_session_creation():
    """Test creating a metrics session"""
    print("🧪 Testing metrics session creation...")
    
    email_details = {
        'sender_email': 'test@example.com',
        'sender_name': 'Test User',
        'subject': 'Test Email for Phase 3',
        'email_text': 'This is a test email for Phase 3 feedback integration.'
    }
    
    session_id = metrics.start_email_session(email_details)
    print(f"✅ Created session: {session_id}")
    
    return session_id

def test_enhanced_slack_message(session_id):
    """Test creating enhanced Slack message"""
    print("🧪 Testing enhanced Slack message creation...")
    
    if not os.getenv("SLACK_WEBHOOK_URL"):
        print("⚠️  SLACK_WEBHOOK_URL not set - skipping actual Slack message")
        return True
    
    try:
        status_code = slack_feedback.create_enhanced_interactive_message(
            message="Test notification for Phase 3 integration",
            draft="This is a test draft response for quality feedback.",
            sender_email="test@example.com",
            subject="Test Email for Phase 3",
            session_id=session_id,
            attio_url="https://example.com/attio",
            gdrive_url="https://example.com/gdrive"
        )
        
        print(f"✅ Slack message sent with status: {status_code}")
        return status_code == 200
        
    except Exception as e:
        print(f"❌ Error sending Slack message: {e}")
        return False

def test_slack_interactions():
    """Test Slack interaction handling"""
    print("🧪 Testing Slack interaction handling...")
    
    session_id = str(uuid.uuid4())
    test_user = {"id": "U12345", "name": "test_user"}
    
    # Test rating interaction
    rating_payload = {
        "user": test_user,
        "actions": [{
            "action_id": "rate_4",
            "value": json.dumps({"session_id": session_id, "rating": 4, "action": "rate"})
        }]
    }
    
    response = slack_feedback.handle_slack_interaction(rating_payload)
    print(f"✅ Rating response: {response}")
    
    # Test approval interaction
    approval_payload = {
        "user": test_user,
        "actions": [{
            "action_id": "approve_draft",
            "value": json.dumps({"session_id": session_id, "action": "approve"})
        }]
    }
    
    response = slack_feedback.handle_slack_interaction(approval_payload)
    print(f"✅ Approval response: {response}")
    
    return True

def test_feedback_logging():
    """Test human feedback logging to metrics"""
    print("🧪 Testing feedback logging...")
    
    try:
        # Test logging various feedback types
        metrics.log_human_feedback(
            action="rated",
            rating=5,
            slack_message_id="test-msg-123"
        )
        print("✅ Rating feedback logged")
        
        metrics.log_human_feedback(
            action="approved",
            slack_message_id="test-msg-124"
        )
        print("✅ Approval feedback logged")
        
        metrics.log_human_feedback(
            action="rejected",
            slack_message_id="test-msg-125",
            feedback_text="Draft needs improvement"
        )
        print("✅ Rejection feedback logged")
        
        return True
        
    except Exception as e:
        print(f"❌ Error logging feedback: {e}")
        return False

def test_edit_distance_calculation():
    """Test edit distance calculation"""
    print("🧪 Testing edit distance calculation...")
    
    original = "This is the original draft text."
    edited = "This is the edited draft text with changes."
    
    distance = slack_feedback.calculate_edit_distance(original, edited)
    print(f"✅ Edit distance calculated: {distance}")
    
    return distance > 0

def test_session_completion():
    """Test completing a metrics session"""
    print("🧪 Testing session completion...")
    
    try:
        metrics.end_email_session('completed')
        print("✅ Session completed successfully")
        return True
    except Exception as e:
        print(f"❌ Error completing session: {e}")
        return False

def main():
    """Run all Phase 3 tests"""
    print("🚀 Starting Phase 3: Human Feedback Integration Tests")
    print("="*60)
    
    test_results = []
    
    # Test 1: Metrics session creation
    try:
        session_id = test_metrics_session_creation()
        test_results.append(("Metrics Session Creation", True))
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        test_results.append(("Metrics Session Creation", False))
        session_id = str(uuid.uuid4())  # Fallback for other tests
    
    # Test 2: Enhanced Slack message
    try:
        result = test_enhanced_slack_message(session_id)
        test_results.append(("Enhanced Slack Message", result))
    except Exception as e:
        print(f"❌ Slack message test failed: {e}")
        test_results.append(("Enhanced Slack Message", False))
    
    # Test 3: Slack interactions
    try:
        result = test_slack_interactions()
        test_results.append(("Slack Interactions", result))
    except Exception as e:
        print(f"❌ Slack interactions test failed: {e}")
        test_results.append(("Slack Interactions", False))
    
    # Test 4: Feedback logging
    try:
        result = test_feedback_logging()
        test_results.append(("Feedback Logging", result))
    except Exception as e:
        print(f"❌ Feedback logging test failed: {e}")
        test_results.append(("Feedback Logging", False))
    
    # Test 5: Edit distance calculation
    try:
        result = test_edit_distance_calculation()
        test_results.append(("Edit Distance Calculation", result))
    except Exception as e:
        print(f"❌ Edit distance test failed: {e}")
        test_results.append(("Edit Distance Calculation", False))
    
    # Test 6: Session completion
    try:
        result = test_session_completion()
        test_results.append(("Session Completion", result))
    except Exception as e:
        print(f"❌ Session completion test failed: {e}")
        test_results.append(("Session Completion", False))
    
    # Print test summary
    print("\n" + "="*60)
    print("📊 PHASE 3 TEST RESULTS")
    print("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print("="*60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 3 tests passed! Human feedback integration is ready.")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    print("\n🔗 Next Steps:")
    print("1. Start the Slack interaction endpoint: python start_slack_endpoint.py")
    print("2. Configure Slack app to use http://your-domain:8002/slack/interactions")
    print("3. Test with real Slack messages and button interactions")
    print("4. Monitor feedback data in the dashboard at http://localhost:8001")

if __name__ == "__main__":
    main()