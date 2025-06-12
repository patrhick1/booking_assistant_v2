#!/usr/bin/env python3
"""
Setup script for security and prompt management features
Installs dependencies and generates secure credentials
"""

import os
import sys
import subprocess
import secrets
import hashlib

def install_dependencies():
    """Install new dependencies for security features"""
    print("📦 Installing security dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyJWT", "python-multipart"])
        print("✅ Security dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def generate_credentials():
    """Generate secure credentials for dashboard"""
    print("\n🔐 Generating secure credentials...")
    
    # Generate secret key
    secret_key = secrets.token_urlsafe(32)
    
    # Generate password hash for default password
    default_password = "BookingAssistant2024!"
    password_hash = hashlib.sha256(default_password.encode()).hexdigest()
    
    # Create .env additions
    env_additions = f"""
# Dashboard Security Credentials (CHANGE FOR PRODUCTION!)
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD_HASH={password_hash}
DASHBOARD_SECRET_KEY={secret_key}
"""
    
    print("✅ Credentials generated!")
    print("\n📋 Add these to your .env file:")
    print(env_additions)
    
    # Check if .env exists and offer to append
    if os.path.exists('.env'):
        response = input("\n❓ Would you like to append these to your existing .env file? (y/n): ")
        if response.lower() == 'y':
            with open('.env', 'a') as f:
                f.write(env_additions)
            print("✅ Credentials added to .env file")
    else:
        print("⚠️  No .env file found. Please create one and add the credentials above.")

def test_imports():
    """Test that all security imports work"""
    print("\n🧪 Testing security imports...")
    try:
        import jwt
        from fastapi.security import HTTPBearer
        print("✅ JWT import successful")
        
        from src.auth_service import auth_service
        print("✅ Auth service import successful")
        
        from src.prompt_manager import prompt_manager
        print("✅ Prompt manager import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Security and Prompt Management")
    print("="*50)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed. Please install dependencies manually:")
        print("pip install PyJWT python-multipart")
        return False
    
    # Generate credentials
    generate_credentials()
    
    # Test imports
    if not test_imports():
        print("\n⚠️  Some imports failed. This might be expected if database isn't set up yet.")
    
    print("\n" + "="*50)
    print("🎉 SECURITY SETUP COMPLETE!")
    print("="*50)
    print("🔑 Default Login: admin / BookingAssistant2024!")
    print("🚀 Start secure dashboard: python secure_dashboard_app.py")
    print("🔒 Login at: http://localhost:8001/login")
    print("⚠️  IMPORTANT: Change default credentials for production!")
    print("="*50)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)