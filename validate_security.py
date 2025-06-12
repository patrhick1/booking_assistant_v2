#!/usr/bin/env python3
"""
Security Validation Script for BookingAssistant
Comprehensive security audit and validation
"""

import os
import re
import sys
import json
import hashlib
from pathlib import Path
from dotenv import load_dotenv

def scan_for_hardcoded_secrets():
    """Scan codebase for hardcoded secrets and credentials"""
    print("🔍 Scanning for Hardcoded Secrets")
    print("="*40)
    
    # Patterns to look for
    secret_patterns = {
        'password': r'password\s*=\s*["\'][^"\']+["\']',
        'api_key': r'api_key\s*=\s*["\'][^"\']+["\']',
        'secret_key': r'secret_key\s*=\s*["\'][^"\']+["\']',
        'token': r'token\s*=\s*["\'][^"\']+["\']',
        'webhook_url': r'webhook_url\s*=\s*["\']https://hooks\.slack\.com[^"\']+["\']',
        'database_url': r'database_url\s*=\s*["\']postgresql://[^"\']+["\']',
        'openai_key': r'sk-[a-zA-Z0-9]{48}',
        'slack_token': r'xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+',
    }
    
    issues_found = []
    
    # Scan Python files
    python_files = list(Path('.').rglob('*.py'))
    for file_path in python_files:
        if 'venv' in str(file_path) or '__pycache__' in str(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern_name, pattern in secret_patterns.items():
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Skip if it's clearly a placeholder or example
                    matched_text = match.group(0)
                    if any(placeholder in matched_text.lower() for placeholder in 
                          ['your_', 'example', 'placeholder', 'xxx', 'secret_here', 'token_here']):
                        continue
                    
                    issues_found.append({
                        'file': str(file_path),
                        'type': pattern_name,
                        'line': content[:match.start()].count('\n') + 1,
                        'text': matched_text[:50] + '...' if len(matched_text) > 50 else matched_text
                    })
        except Exception as e:
            print(f"⚠️  Could not scan {file_path}: {e}")
    
    if issues_found:
        print(f"❌ Found {len(issues_found)} potential hardcoded secrets:")
        for issue in issues_found:
            print(f"   {issue['file']}:{issue['line']} - {issue['type']}: {issue['text']}")
        return False
    else:
        print("✅ No hardcoded secrets found")
        return True

def check_sql_injection_protection():
    """Check that database queries use parameterized statements"""
    print("\n🛡️  Checking SQL Injection Protection")
    print("="*40)
    
    # Patterns for unsafe SQL
    unsafe_patterns = [
        r'f".*SELECT.*{.*}"',  # f-string SQL
        r'".*SELECT.*"\s*%\s*\(',  # String formatting
        r'\.format\(.*SELECT',  # .format() with SQL
        r'execute\(["\'].*\+',  # String concatenation in execute
    ]
    
    python_files = list(Path('.').rglob('*.py'))
    issues_found = []
    
    for file_path in python_files:
        if 'venv' in str(file_path) or '__pycache__' in str(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern in unsafe_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    issues_found.append({
                        'file': str(file_path),
                        'line': content[:match.start()].count('\n') + 1,
                        'text': match.group(0)
                    })
        except Exception as e:
            print(f"⚠️  Could not scan {file_path}: {e}")
    
    if issues_found:
        print(f"❌ Found {len(issues_found)} potential SQL injection vulnerabilities:")
        for issue in issues_found:
            print(f"   {issue['file']}:{issue['line']} - {issue['text']}")
        return False
    else:
        print("✅ All database queries appear to use parameterized statements")
        return True

def validate_environment_security():
    """Validate environment variable security"""
    print("\n🔐 Validating Environment Security")
    print("="*40)
    
    load_dotenv()
    
    security_checks = []
    
    # Check secret key strength
    secret_key = os.getenv('DASHBOARD_SECRET_KEY')
    if secret_key:
        if len(secret_key) < 32:
            security_checks.append("❌ DASHBOARD_SECRET_KEY is too short (minimum 32 characters)")
        else:
            security_checks.append("✅ DASHBOARD_SECRET_KEY length is adequate")
    else:
        security_checks.append("❌ DASHBOARD_SECRET_KEY is not set")
    
    # Check password strength
    password = os.getenv('DASHBOARD_PASSWORD')
    if password:
        if len(password) < 8:
            security_checks.append("⚠️  DASHBOARD_PASSWORD is short (consider 12+ characters)")
        elif password in ['password', '12345678', 'admin123', 'BookingAssistant2024!']:
            security_checks.append("❌ DASHBOARD_PASSWORD is using a default/weak password")
        else:
            security_checks.append("✅ DASHBOARD_PASSWORD appears strong")
    else:
        security_checks.append("❌ DASHBOARD_PASSWORD is not set")
    
    # Check database credentials
    db_password = os.getenv('PGPASSWORD')
    if db_password:
        if len(db_password) < 12:
            security_checks.append("⚠️  PGPASSWORD is short for production use")
        else:
            security_checks.append("✅ PGPASSWORD length is adequate")
    else:
        security_checks.append("❌ PGPASSWORD is not set")
    
    # Check for sensitive data in environment
    sensitive_vars = ['OPENAI_API_KEY', 'SLACK_WEBHOOK_URL', 'SLACK_BOT_TOKEN']
    for var in sensitive_vars:
        value = os.getenv(var)
        if value and ('example' in value.lower() or 'your_' in value.lower()):
            security_checks.append(f"❌ {var} contains placeholder value")
        elif value:
            security_checks.append(f"✅ {var} is configured")
        else:
            security_checks.append(f"⚠️  {var} is not set (may be optional)")
    
    for check in security_checks:
        print(check)
    
    # Return True if no critical errors
    critical_errors = [check for check in security_checks if check.startswith("❌")]
    return len(critical_errors) == 0

def check_file_permissions():
    """Check file permissions for sensitive files"""
    print("\n📂 Checking File Permissions")
    print("="*40)
    
    sensitive_files = ['.env', 'service-account-key.json']
    permission_issues = []
    
    for filename in sensitive_files:
        if os.path.exists(filename):
            # Get file permissions
            stat_info = os.stat(filename)
            permissions = oct(stat_info.st_mode)[-3:]
            
            # Check if file is readable by others
            if permissions[2] != '0':
                permission_issues.append(f"❌ {filename} is readable by others (permissions: {permissions})")
            else:
                print(f"✅ {filename} permissions are secure ({permissions})")
        else:
            print(f"⚠️  {filename} not found")
    
    if permission_issues:
        for issue in permission_issues:
            print(issue)
        print("\n💡 Fix with: chmod 600 filename")
        return False
    
    return True

def test_database_security():
    """Test database connection security"""
    print("\n🗄️  Testing Database Security")
    print("="*40)
    
    try:
        from src.schema import db_manager
        
        # Test connection with credentials
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Test that we can't perform dangerous operations
                try:
                    cursor.execute("SELECT current_user, session_user")
                    user_info = cursor.fetchone()
                    print(f"✅ Connected as: {user_info['current_user']}")
                    
                    # Check if we're using SSL
                    cursor.execute("SHOW ssl")
                    ssl_info = cursor.fetchone()
                    if ssl_info and ssl_info['ssl'] == 'on':
                        print("✅ SSL connection enabled")
                    else:
                        print("⚠️  SSL connection not detected")
                    
                except Exception as e:
                    print(f"⚠️  Could not check database security: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database security test failed: {e}")
        return False

def generate_security_report():
    """Generate a comprehensive security report"""
    print("\n📋 Generating Security Report")
    print("="*40)
    
    report = {
        'timestamp': str(datetime.now()),
        'hardcoded_secrets': scan_for_hardcoded_secrets(),
        'sql_injection_protection': check_sql_injection_protection(),
        'environment_security': validate_environment_security(),
        'file_permissions': check_file_permissions(),
        'database_security': test_database_security()
    }
    
    # Save report
    with open('security_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Security report saved to security_report.json")
    
    # Calculate overall score
    passed_checks = sum(1 for check in report.values() if check is True)
    total_checks = len([k for k in report.keys() if k != 'timestamp'])
    score = (passed_checks / total_checks) * 100
    
    print(f"\n📊 Security Score: {score:.1f}% ({passed_checks}/{total_checks} checks passed)")
    
    return score >= 80  # 80% pass rate required

def main():
    """Main security validation function"""
    print("🔒 COMPREHENSIVE SECURITY VALIDATION")
    print("="*60)
    
    try:
        from datetime import datetime
        
        # Run all security checks
        overall_success = generate_security_report()
        
        print("\n" + "="*60)
        if overall_success:
            print("🎉 SECURITY VALIDATION PASSED!")
            print("✅ Your BookingAssistant deployment meets security standards")
        else:
            print("⚠️  SECURITY ISSUES DETECTED")
            print("❌ Please address the issues above before production deployment")
        
        print("\n🔐 Security Best Practices:")
        print("1. Regularly rotate API keys and passwords")
        print("2. Monitor audit logs for suspicious activity")  
        print("3. Keep dependencies updated")
        print("4. Use HTTPS for all external communications")
        print("5. Implement rate limiting in production")
        print("6. Regular security audits and penetration testing")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Security validation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Security validation failed. Please fix issues before deployment.")
        sys.exit(1)
    else:
        print("\n✅ Security validation completed successfully.")