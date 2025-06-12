"""
Authentication service for BookingAssistant dashboard
Provides secure login and session management
"""

import os
import hashlib
import secrets
import jwt  # PyJWT library
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("DASHBOARD_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("DASHBOARD_SECRET_KEY environment variable is required")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Admin credentials from environment variables (REQUIRED)
ADMIN_USERNAME = os.getenv("DASHBOARD_USERNAME")
ADMIN_PASSWORD = os.getenv("DASHBOARD_PASSWORD")

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise ValueError("DASHBOARD_USERNAME and DASHBOARD_PASSWORD environment variables are required")

# Hash the password for secure storage
ADMIN_PASSWORD_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()

security = HTTPBearer()

class AuthService:
    """Service for handling authentication and authorization"""
    
    def __init__(self):
        self.users = {
            ADMIN_USERNAME: {
                "username": ADMIN_USERNAME,
                "password_hash": ADMIN_PASSWORD_HASH,
                "role": "admin",
                "permissions": ["dashboard", "prompts", "analytics", "settings"]
            }
        }
    
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return self.hash_password(password) == password_hash
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password"""
        user = self.users.get(username)
        if not user:
            return None
        
        if not self.verify_password(password, user["password_hash"]):
            return None
        
        return {
            "username": user["username"],
            "role": user["role"],
            "permissions": user["permissions"]
        }
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create a JWT access token"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": user_data["username"],
            "role": user_data["role"],
            "permissions": user_data["permissions"],
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                return None
            
            return {
                "username": username,
                "role": payload.get("role"),
                "permissions": payload.get("permissions", [])
            }
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Get the current authenticated user from JWT token"""
        user_data = self.verify_token(credentials.credentials)
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_data
    
    def require_permission(self, permission: str):
        """Decorator factory to require specific permissions"""
        def permission_checker(current_user: Dict[str, Any] = Depends(self.get_current_user)):
            if permission not in current_user.get("permissions", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            return current_user
        return permission_checker
    
    def add_user(self, username: str, password: str, role: str = "user", permissions: list = None):
        """Add a new user (admin only)"""
        if permissions is None:
            permissions = ["dashboard"]
        
        password_hash = self.hash_password(password)
        self.users[username] = {
            "username": username,
            "password_hash": password_hash,
            "role": role,
            "permissions": permissions
        }
        return True
    
    def generate_password_hash(self, password: str) -> str:
        """Generate a password hash for environment variable"""
        return self.hash_password(password)

# Global auth service instance
auth_service = AuthService()

# Dependency functions for FastAPI
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """FastAPI dependency to get current user"""
    return auth_service.get_current_user(credentials)

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """FastAPI dependency to require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user

def require_dashboard_access(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """FastAPI dependency to require dashboard access"""
    if "dashboard" not in current_user.get("permissions", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dashboard access required"
        )
    return current_user

def require_prompt_access(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """FastAPI dependency to require prompt management access"""
    if "prompts" not in current_user.get("permissions", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Prompt management access required"
        )
    return current_user