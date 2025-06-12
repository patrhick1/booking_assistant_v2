#!/usr/bin/env python3
"""
Startup script for the Slack Interaction Endpoint
Handles button clicks and user interactions from enhanced Slack messages
"""

import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.append('src')

def check_environment():
    """Check required environment variables"""
    required_vars = [
        'SLACK_WEBHOOK_URL',
        'PGHOST',
        'PGDATABASE', 
        'PGUSER',
        'PGPASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please check your .env file")
        return False
    else:
        print("✅ Environment variables: OK")
        return True

def check_database_connection():
    """Check if database is accessible"""
    try:
        from src.metrics_service import metrics
        if metrics.db_pool:
            print("✅ Database connection: OK")
            return True
        else:
            print("❌ Database connection: FAILED")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def print_startup_info():
    """Print helpful startup information"""
    print("\n" + "="*60)
    print("🔗 SLACK INTERACTION ENDPOINT")
    print("="*60)
    print("🎯 Interactions URL: http://localhost:8002/slack/interactions")
    print("📡 Events URL: http://localhost:8002/slack/events")
    print("🔄 Health Check: http://localhost:8002/health")
    print("📚 API Documentation: http://localhost:8002/docs")
    print("💬 Handles Slack button clicks and feedback collection")
    print("="*60)

def main():
    """Main startup function"""
    print("🚀 Starting Slack Interaction Endpoint...")
    
    # Check prerequisites
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above and try again.")
        sys.exit(1)
    
    if not check_database_connection():
        print("\n⚠️  Warning: Database connection failed.")
        print("   The endpoint will start but feedback logging may not work.")
        print("   Please check your PostgreSQL setup and database credentials.")
        time.sleep(3)
    
    print_startup_info()
    
    # Import and start the endpoint
    try:
        import uvicorn
        from slack_interaction_endpoint import app
        
        uvicorn.run(
            "slack_interaction_endpoint:app",
            host="0.0.0.0",
            port=8002,
            reload=True,
            log_level="info"
        )
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Please install required dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Slack endpoint shutdown completed.")
    except Exception as e:
        print(f"❌ Failed to start Slack endpoint: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()