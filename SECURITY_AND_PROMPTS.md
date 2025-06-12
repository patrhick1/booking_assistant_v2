# 🔐 Security & Prompt Management Guide

## Overview

BookingAssistant now includes comprehensive security features and dynamic prompt management capabilities for production deployment.

## 🛡️ Authentication & Security

### Password Protection

The dashboard is now protected with JWT-based authentication:

- **Login Required**: All dashboard and analytics endpoints require authentication
- **Role-Based Access**: Different permission levels for users
- **Secure Sessions**: JWT tokens with 8-hour expiration
- **Admin Controls**: User management and system administration

### Default Credentials

**⚠️ CHANGE THESE IN PRODUCTION!**

```
Username: admin
Password: BookingAssistant2024!
```

### Setting Custom Credentials

Add to your `.env` file:

```bash
# Dashboard Authentication
DASHBOARD_USERNAME=your_admin_username
DASHBOARD_PASSWORD_HASH=your_password_hash_here
DASHBOARD_SECRET_KEY=your_secret_key_here

# Generate password hash via API:
# GET /api/admin/generate-password-hash?password=YourPassword123
```

### Generating Secure Password Hash

1. Start the secure dashboard: `python secure_dashboard_app.py`
2. Login with default credentials
3. Visit: `http://localhost:8001/api/admin/generate-password-hash?password=YourNewPassword`
4. Copy the hash to your `.env` file as `DASHBOARD_PASSWORD_HASH`

## 🎯 Prompt Management System

### Dynamic Prompt Control

All prompts are now stored in PostgreSQL and can be managed through the dashboard:

- **Version Control**: Multiple versions of each prompt with rollback capability
- **A/B Testing**: Test different prompt variations simultaneously  
- **Performance Tracking**: Monitor which prompts perform better
- **Live Updates**: Change prompts without redeploying code
- **Usage Analytics**: Track prompt usage and effectiveness

### Managed Prompts

The following prompts are now dynamically managed:

1. **classification_fewshot** - Email classification examples
2. **draft_generation_prompt** - Main draft generation
3. **query_for_relevant_email_prompt** - Vector search queries
4. **rejection_strategy_prompt** - Rejection analysis
5. **soft_rejection_drafting_prompt** - Soft rejection responses
6. **draft_editing_prompt** - Draft refinement
7. **slack_notification_prompt** - Slack message generation
8. **continuation_decision_prompt** - Processing decisions
9. **client_gdrive_extract_prompt** - Document extraction

### Prompt Management APIs

#### Get All Prompts
```bash
GET /api/prompts
Authorization: Bearer your_jwt_token
```

#### Get Prompt Details
```bash
GET /api/prompts/{prompt_name}
Authorization: Bearer your_jwt_token
```

#### Create New Prompt Version
```bash
POST /api/prompts/{prompt_name}/versions
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "content": "Your new prompt content here...",
  "description": "Description of changes made"
}
```

#### Activate Prompt Version
```bash
POST /api/prompts/{prompt_name}/activate
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "version_id": "uuid-of-version-to-activate"
}
```

## 🚀 Deployment Options

### Option 1: Secure Dashboard (Recommended for Production)

```bash
python secure_dashboard_app.py
```

**Features:**
- ✅ Password protection
- ✅ Prompt management interface
- ✅ Role-based access control
- ✅ Audit logging
- ✅ Production-ready

**Access:**
- Dashboard: http://localhost:8001/ (requires login)
- Login Page: http://localhost:8001/login
- Prompt Management: http://localhost:8001/api/prompts

### Option 2: Replit Unified (Single Port with Security)

Update `replit_unified_app.py` to include security features:

```bash
python replit_unified_app.py
```

### Option 3: Original Simple (Development Only)

```bash
python start_dashboard.py  # Original dashboard (no auth)
```

## 📊 Prompt Performance Analytics

### Tracking Metrics

The system automatically tracks:

- **Usage Count**: How often each prompt version is used
- **Performance Score**: Quality metrics based on outcomes
- **Success Rate**: Successful vs failed executions
- **Response Time**: Processing speed for each prompt
- **Quality Ratings**: Human feedback from Slack interactions

### A/B Testing Framework

Create A/B tests to compare prompt variations:

1. **Create Two Versions**: Upload different prompt variations
2. **Configure Split**: Set traffic percentage (e.g., 50/50)
3. **Monitor Results**: Track performance metrics
4. **Activate Winner**: Deploy the better-performing version

### Performance Dashboard

View prompt analytics at:
- `/api/prompts/{prompt_name}/performance`
- Real-time usage statistics
- Version comparison charts
- Quality trend analysis

## 🔧 Database Schema

### New Tables for Security & Prompts

```sql
-- Authentication & User Management
users
user_sessions
user_permissions

-- Prompt Management
prompt_templates
prompt_versions
prompt_usage

-- A/B Testing
ab_test_configs
ab_test_results

-- Audit Logging
audit_logs
```

## 🛠️ Advanced Features

### Role-Based Permissions

**Admin Role:**
- Full dashboard access
- Prompt management
- User administration
- System settings
- Analytics viewing

**Manager Role:**
- Dashboard access
- Prompt management
- Analytics viewing
- No user administration

**User Role:**
- Dashboard access only
- Read-only analytics

### Audit Logging

All actions are logged:
- Prompt version changes
- User logins and actions
- System configuration changes
- API access attempts

### Security Best Practices

1. **Change Default Credentials**: Set strong custom passwords
2. **Use HTTPS**: Deploy with SSL certificates
3. **Regular Updates**: Keep dependencies updated
4. **Access Control**: Limit dashboard access by IP if needed
5. **Monitor Logs**: Review audit logs regularly

## 🔄 Migration from Original System

### Automatic Migration

When you first start the secure dashboard:

1. **Prompt Import**: All prompts from `prompts.py` are automatically imported
2. **Database Setup**: Required tables are created automatically
3. **Default User**: Admin user is created with default credentials
4. **Version 1**: Each prompt gets its first version marked as active

### Zero Downtime Migration

The system includes fallback mechanisms:
- If database is unavailable, falls back to `prompts.py`
- Gradual migration of prompts to database
- Backward compatibility maintained

## 📞 Support & Troubleshooting

### Common Issues

**Can't Access Dashboard**
- Check if you're using the secure version: `secure_dashboard_app.py`
- Verify credentials at `/login` page
- Check JWT token in browser developer tools

**Prompts Not Loading**
- Verify database connection
- Check prompt_manager initialization
- Review console logs for errors

**Permission Denied**
- Check user role and permissions
- Verify JWT token is valid
- Review audit logs for access attempts

### Health Checks

- **Authentication**: `/auth/check`
- **Database**: `/health`
- **Prompt System**: `/api/prompts`

---

🎉 **Your BookingAssistant now has enterprise-grade security and dynamic prompt management capabilities!**