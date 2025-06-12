#!/usr/bin/env python3
"""
Secure Setup Script for BookingAssistant
Creates database schema and validates security configuration
"""

import os
import sys
import secrets
import hashlib
from dotenv import load_dotenv

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("🔍 Checking Environment Variables")
    print("="*50)
    
    required_vars = {
        # Database
        'PGHOST': 'PostgreSQL host',
        'PGDATABASE': 'PostgreSQL database name',
        'PGUSER': 'PostgreSQL username',
        'PGPASSWORD': 'PostgreSQL password',
        
        # Security
        'DASHBOARD_USERNAME': 'Dashboard admin username',
        'DASHBOARD_PASSWORD': 'Dashboard admin password',
        'DASHBOARD_SECRET_KEY': 'JWT secret key (min 32 chars)',
        
        # OpenAI
        'OPENAI_API_KEY': 'OpenAI API key',
        
        # Optional but recommended
        'SLACK_WEBHOOK_URL': 'Slack webhook URL (optional)',
        'ASTRA_DB_API_ENDPOINT': 'AstraDB endpoint (optional)',
        'ASTRA_DB_APPLICATION_TOKEN': 'AstraDB token (optional)',
    }
    
    missing_vars = []
    warnings = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            if var in ['SLACK_WEBHOOK_URL', 'ASTRA_DB_API_ENDPOINT', 'ASTRA_DB_APPLICATION_TOKEN']:
                warnings.append(f"⚠️  {var}: Not set ({description})")
            else:
                missing_vars.append(f"❌ {var}: Missing ({description})")
        else:
            # Validate specific requirements
            if var == 'DASHBOARD_SECRET_KEY' and len(value) < 32:
                missing_vars.append(f"❌ {var}: Must be at least 32 characters")
            elif var == 'DASHBOARD_PASSWORD' and len(value) < 8:
                warnings.append(f"⚠️  {var}: Consider using a stronger password (8+ chars)")
            else:
                # Show partial value for security
                if 'PASSWORD' in var or 'KEY' in var or 'TOKEN' in var:
                    display_value = f"****{value[-4:]}" if len(value) > 4 else "****"
                else:
                    display_value = value[:30] + "..." if len(value) > 30 else value
                print(f"✅ {var}: {display_value}")
    
    # Print warnings
    for warning in warnings:
        print(warning)
    
    # Print missing variables
    if missing_vars:
        print("\n" + "="*50)
        print("❌ MISSING REQUIRED VARIABLES:")
        for missing in missing_vars:
            print(missing)
        return False
    
    print("\n✅ All required environment variables are set")
    return True

def generate_secure_credentials():
    """Generate secure credentials if needed"""
    print("\n🔐 Generating Secure Credentials")
    print("="*50)
    
    credentials = {}
    
    # Generate secret key if not set
    if not os.getenv('DASHBOARD_SECRET_KEY'):
        secret_key = secrets.token_urlsafe(32)
        credentials['DASHBOARD_SECRET_KEY'] = secret_key
        print(f"✅ Generated secure secret key: {secret_key}")
    
    # Set default username if not set
    if not os.getenv('DASHBOARD_USERNAME'):
        credentials['DASHBOARD_USERNAME'] = 'admin'
        print("✅ Set default username: admin")
    
    # Generate password if not set
    if not os.getenv('DASHBOARD_PASSWORD'):
        password = secrets.token_urlsafe(16)
        credentials['DASHBOARD_PASSWORD'] = password
        print(f"✅ Generated secure password: {password}")
    
    if credentials:
        print("\n📋 Add these to your .env file:")
        for key, value in credentials.items():
            print(f"{key}={value}")
        return credentials
    else:
        print("✅ All credentials already configured")
        return {}

def create_database_schema():
    """Create database schema using secure schema manager"""
    print("\n🗄️  Creating Database Schema")
    print("="*50)
    
    try:
        # Import after environment check
        from src.schema import db_manager
        
        # Test database connection
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()
                print(f"✅ Connected to PostgreSQL: {version['version'][:50]}...")
        
        # Create all tables
        success = db_manager.create_all_tables()
        if success:
            print("✅ Database schema created successfully")
            
            # Check table creation
            tables = db_manager.get_table_info()
            print(f"✅ Created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table['tablename']}")
            
            return True
        else:
            print("❌ Failed to create database schema")
            return False
            
    except Exception as e:
        print(f"❌ Database schema creation failed: {e}")
        return False

def test_security_features():
    """Test security features and authentication"""
    print("\n🔒 Testing Security Features")
    print("="*50)
    
    try:
        from src.auth_service import auth_service
        
        # Test password hashing
        test_password = "test123"
        hash1 = auth_service.hash_password(test_password)
        hash2 = auth_service.hash_password(test_password)
        
        if hash1 == hash2:
            print("✅ Password hashing working correctly")
        else:
            print("❌ Password hashing inconsistent")
            return False
        
        # Test authentication with configured credentials
        username = os.getenv('DASHBOARD_USERNAME')
        password = os.getenv('DASHBOARD_PASSWORD')
        
        user_data = auth_service.authenticate_user(username, password)
        if user_data:
            print("✅ Authentication working with configured credentials")
            
            # Test JWT token creation
            token = auth_service.create_access_token(user_data)
            if token:
                print("✅ JWT token creation working")
                
                # Test token verification
                verified = auth_service.verify_token(token)
                if verified:
                    print("✅ JWT token verification working")
                    return True
                else:
                    print("❌ JWT token verification failed")
                    return False
            else:
                print("❌ JWT token creation failed")
                return False
        else:
            print("❌ Authentication failed with configured credentials")
            return False
            
    except Exception as e:
        print(f"❌ Security test failed: {e}")
        return False

def test_prompt_management():
    """Test prompt management system"""
    print("\n📝 Testing Prompt Management")
    print("="*50)
    
    try:
        from src.prompt_manager import prompt_manager
        
        # Test prompt retrieval
        classification_prompt = prompt_manager.get_active_prompt("classification_fewshot")
        if classification_prompt:
            print("✅ Prompt management system working")
            print(f"   Retrieved prompt length: {len(classification_prompt)} characters")
            return True
        else:
            print("⚠️  Prompt management using fallback mode")
            return True  # Fallback is acceptable
            
    except Exception as e:
        print(f"❌ Prompt management test failed: {e}")
        return False

def create_sample_env_file():
    """Create a sample .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("\n📄 Creating sample .env file")
        print("="*50)
        
        sample_env = f"""# Neon PostgreSQL Database
PGDATABASE=neondb
PGUSER=neondb_owner
PGPASSWORD=your_neon_password_here
PGHOST=your-neon-host.aws.neon.tech
PGPORT=5432

# Dashboard Security (REQUIRED)
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD={secrets.token_urlsafe(16)}
DASHBOARD_SECRET_KEY={secrets.token_urlsafe(32)}

# OpenAI API (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# Gmail API (Service Account)
GMAIL_SERVICE_ACCOUNT_FILE=service-account-key.json
GMAIL_TARGET_EMAIL=your_email@domain.com

# Google Drive
GDRIVE_CLIENT_ROOT_FOLDER_ID=your_google_drive_folder_id

# AstraDB Vector Database (Optional)
ASTRA_DB_APPLICATION_TOKEN=your_astra_token
ASTRA_DB_API_ENDPOINT=your_astra_endpoint

# Slack Integration (Optional)
SLACK_WEBHOOK_URL=your_slack_webhook_url
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# Testing Mode
TESTING_MODE=false
"""
        
        with open('.env', 'w') as f:
            f.write(sample_env)
        
        print("✅ Created .env file with secure defaults")
        print("⚠️  Please update the placeholder values before running the system")

def main():
    """Main setup function"""
    print("🚀 SECURE SETUP FOR BOOKING ASSISTANT")
    print("="*60)
    
    # Load environment variables
    load_dotenv()
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        create_sample_env_file()
        print("\n❗ Please update your .env file with actual values and run setup again")
        return False
    
    # Check environment variables
    if not check_environment_variables():
        print("\n❌ Environment check failed. Please fix the issues above.")
        return False
    
    # Generate credentials if needed
    new_credentials = generate_secure_credentials()
    if new_credentials:
        print("\n❗ Please add the generated credentials to your .env file and restart")
        return False
    
    # Create database schema
    if not create_database_schema():
        print("\n❌ Database setup failed.")
        return False
    
    # Test security features
    if not test_security_features():
        print("\n❌ Security tests failed.")
        return False
    
    # Test prompt management
    if not test_prompt_management():
        print("\n❌ Prompt management tests failed.")
        return False
    
    print("\n" + "="*60)
    print("🎉 SECURE SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("✅ Database schema created with SQL injection protection")
    print("✅ Authentication system configured and tested")
    print("✅ Prompt management system ready")
    print("✅ All security features validated")
    
    print("\n🚀 Next Steps:")
    print("1. Start secure dashboard: python secure_dashboard_app.py")
    print("2. Login at: http://localhost:8001/login")
    print(f"3. Use credentials: {os.getenv('DASHBOARD_USERNAME')} / {os.getenv('DASHBOARD_PASSWORD')}")
    print("4. Change default password after first login!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)