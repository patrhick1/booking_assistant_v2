"""
Simple script to test the Slack Events API endpoint
"""

import requests
import json

# Your Replit URL
BASE_URL = "https://booking-assistant-paschal3.replit.app"

def test_url_verification():
    """Test the URL verification challenge that Slack sends"""

    url = f"{BASE_URL}/slack/events"

    # This is the exact payload Slack sends for URL verification
    challenge_payload = {
        "token": "verification_token_from_slack",
        "challenge": "test_challenge_12345",
        "type": "url_verification"
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("🔍 Testing Slack Events URL Verification...")
    print(f"📡 Sending POST to: {url}")
    print(f"📄 Payload: {json.dumps(challenge_payload, indent=2)}")
    print("-" * 50)

    try:
        response = requests.post(url, json=challenge_payload, headers=headers, timeout=10)

        print(f"✅ Status Code: {response.status_code}")
        print(f"📨 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Body: {response.text}")

        if response.status_code == 200:
            try:
                response_json = response.json()
                if response_json.get("challenge") == challenge_payload["challenge"]:
                    print("🎉 SUCCESS: Challenge echoed back correctly!")
                    print("✅ Your Slack Events endpoint is working!")
                else:
                    print("❌ FAIL: Challenge not echoed back correctly")
                    print(f"   Expected: {challenge_payload['challenge']}")
                    print(f"   Got: {response_json.get('challenge')}")
            except json.JSONDecodeError:
                print("❌ FAIL: Response is not valid JSON")
        else:
            print("❌ FAIL: Non-200 status code")

    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Request took too long")
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Could not connect to the endpoint")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_health_endpoint():
    """Test if the app is running by checking health"""

    url = f"{BASE_URL}/health"

    print("\n🔍 Testing Health Endpoint...")
    print(f"📡 Sending GET to: {url}")

    try:
        response = requests.get(url, timeout=5)
        print(f"✅ Status Code: {response.status_code}")

        if response.status_code == 200:
            health_data = response.json()
            print("📊 Health Status:")
            print(f"   Overall: {health_data.get('status')}")
            print(f"   Email Processing: {health_data.get('email_processing', {}).get('automatic_active')}")
            print(f"   Services: {health_data.get('services')}")
        else:
            print(f"❌ Health check failed with status: {response.status_code}")

    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_basic_connectivity():
    """Test basic connectivity to your app"""

    print("\n🔍 Testing Basic Connectivity...")

    # Test different endpoints
    endpoints = [
        "/",
        "/health",
        "/ping",
        "/docs"
    ]

    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            status = "✅" if response.status_code in [200, 404] else "❌"
            print(f"   {status} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: {e}")

if __name__ == "__main__":
    print("🚀 Slack Events Endpoint Tester")
    print("=" * 50)

    # Run all tests
    test_health_endpoint()
    test_basic_connectivity()
    test_url_verification()

    print("\n" + "=" * 50)
    print("🏁 Testing Complete!")
    print("\nIf the URL verification test passes, you can use this URL in Slack:")
    print(f"   {BASE_URL}/slack/events")