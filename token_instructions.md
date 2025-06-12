# 🔑 How to Get Your API Authorization Token

## Quick Options:

### Option 1: Use the Token Generator Page 🌐
1. Start your server: `python secure_dashboard_app.py`
2. Open: `get_token.html` in your browser (double-click the file)
3. Login with your credentials
4. Copy the generated token

### Option 2: Use the Python Script 💻
```bash
python get_api_token.py
```
This will:
- Login automatically using your .env credentials
- Show your token
- Test the token
- Save it to `token.txt`

### Option 3: Browser Developer Tools 🔧
1. Go to `http://localhost:8001`
2. Login with `admin` / `BookingAssistant2024!`
3. Press `F12` to open Developer Tools
4. Go to `Application` tab → `Local Storage` → `http://localhost:8001`
5. Find the `token` key - that's your authorization token!

### Option 4: Manual curl Command 📡
```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "BookingAssistant2024!"}'
```

## How to Use Your Token:

### 🌐 In Browser (JavaScript):
```javascript
const token = "YOUR_TOKEN_HERE";
fetch('/api/overview', {
    headers: { 'Authorization': `Bearer ${token}` }
})
```

### 💻 In Python:
```python
import requests
token = "YOUR_TOKEN_HERE"
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8001/api/overview", headers=headers)
```

### 📡 In curl:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:8001/api/overview
```

### 🔧 In Postman/Insomnia:
- Header Name: `Authorization`
- Header Value: `Bearer YOUR_TOKEN_HERE`

## Available API Endpoints:

| Endpoint | Description | Auth Required |
|----------|-------------|---------------|
| `/api/overview` | Dashboard statistics | ✅ Yes |
| `/api/timeline` | Processing timeline | ✅ Yes |
| `/api/classifications` | Classification analytics | ✅ Yes |
| `/api/prompts` | List all prompts | ✅ Yes |
| `/api/prompts/{name}` | Specific prompt details | ✅ Yes |
| `/health` | System health check | ❌ No |
| `/ping` | Simple connectivity test | ❌ No |

## Token Details:
- **Expires**: 8 hours after generation
- **Format**: JWT (JSON Web Token)
- **Permissions**: Based on your user role
- **Storage**: Can be saved in localStorage, file, or environment variable

## Troubleshooting:

### 401 Unauthorized Error:
- Check that you're including the `Authorization` header
- Verify the token format: `Bearer YOUR_TOKEN`
- Make sure the token hasn't expired (8 hours)

### 403 Forbidden Error:
- Your user account may lack the required permissions
- Check that your role has access to the endpoint

### Connection Errors:
- Ensure the server is running on `http://localhost:8001`
- Check your firewall settings
- Verify the URL is correct