# 🐳 Docker Deployment Guide for BookingAssistant

This guide covers deploying BookingAssistant using Docker, both locally and on Render.com.

## 📋 Prerequisites

- Docker installed locally (for testing)
- Render.com account
- All API keys and credentials ready

## 🏗️ Docker Setup

### Files Created

1. **`Dockerfile`** - Basic Docker image for the application
2. **`Dockerfile.production`** - Optimized multi-stage build for production
3. **`docker-compose.yml`** - Local development with PostgreSQL
4. **`render.yaml`** - Render.com deployment configuration
5. **`.dockerignore`** - Excludes unnecessary files from the image

## 🚀 Local Docker Testing

### 1. Build and Run with Docker Compose

```bash
# Create .env file with your credentials
cp .env.example .env
# Edit .env with your actual values

# Build and start services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

This starts:
- BookingAssistant app on http://localhost:8000
- PostgreSQL database on port 5432
- Adminer (database UI) on http://localhost:8080

### 2. Build and Run Standalone

```bash
# Build the image
docker build -t bookingassistant:latest .

# Run with environment variables
docker run -p 8000:8000 \
  -e NYLAS_API_KEY="your-key" \
  -e NYLAS_GRANT_ID="your-grant-id" \
  -e OPENAI_API_KEY="your-key" \
  # ... other env vars ... \
  bookingassistant:latest
```

## 📦 Deploying to Render.com

### Option 1: Using render.yaml (Recommended)

1. **Fork/Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Docker configuration"
   git push origin main
   ```

2. **Create New Web Service on Render**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Render will detect the `render.yaml` file

3. **Configure Environment Variables**
   
   In Render dashboard, add these environment variables:
   
   ```bash
   # Required
   NYLAS_API_KEY=your-nylas-api-key
   NYLAS_GRANT_ID=your-nylas-grant-id
   NYLAS_API_URI=https://api.us.nylas.com
   OPENAI_API_KEY=your-openai-key
   ASTRA_DB_APPLICATION_TOKEN=your-astra-token
   ASTRA_DB_API_ENDPOINT=your-astra-endpoint
   SLACK_WEBHOOK_URL=your-slack-webhook
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   GDRIVE_CLIENT_ROOT_FOLDER_ID=your-folder-id
   
   # Dashboard Auth
   DASHBOARD_USERNAME=admin
   DASHBOARD_PASSWORD=your-secure-password
   DASHBOARD_SECRET_KEY=your-32-char-secret-key
   
   # Google Service Account (as base64)
   GOOGLE_SERVICE_ACCOUNT_BASE64=base64-encoded-json
   
   # Optional
   ATTIO_API_KEY=your-attio-key
   TESTING_MODE=false
   MARK_EMAILS_AS_READ=false
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy automatically

### Option 2: Manual Docker Deployment

1. **Create Web Service**
   - Choose "Deploy an existing image"
   - Build and push to Docker Hub:
   
   ```bash
   # Build production image
   docker build -f Dockerfile.production -t yourusername/bookingassistant:latest .
   
   # Push to Docker Hub
   docker push yourusername/bookingassistant:latest
   ```

2. **Configure in Render**
   - Image URL: `docker.io/yourusername/bookingassistant:latest`
   - Port: 8000
   - Health Check Path: `/health`

## 🔧 Environment Variables for Render

### Database Configuration

If using Render's PostgreSQL:
- Render automatically sets `DATABASE_URL`
- The app will parse this and set individual PG variables

If using external database (like Neon):
```bash
PGHOST=your-host.neon.tech
PGPORT=5432
PGDATABASE=neondb
PGUSER=your-user
PGPASSWORD=your-password
```

### Google Service Account

For Google Drive access, encode your service account JSON:

```bash
# On Linux/Mac
base64 -i service-account-key.json | tr -d '\n' > service-account-base64.txt

# On Windows PowerShell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("service-account-key.json")) | Out-File service-account-base64.txt
```

Then add as `GOOGLE_SERVICE_ACCOUNT_BASE64` environment variable.

## 🔍 Health Checks and Monitoring

### Endpoints

- `/` - Main dashboard
- `/health` - Health check endpoint
- `/docs` - API documentation
- `/email_polling_status` - Check if email processing is active

### Logs

Check Render logs for:
```
✅ Database schema ready
✅ Starting automatic email processing...
📧 Found X unread emails to process
```

## 🚨 Troubleshooting

### "Database connection failed"
- Check PostgreSQL credentials
- Ensure database is not sleeping (Neon free tier)
- Verify firewall/IP allowlist settings

### "Email processing not starting"
- Check Nylas credentials
- Verify `TESTING_MODE=false`
- Look for error messages in logs

### "Slack notifications not working"
- Verify `SLACK_WEBHOOK_URL`
- Update Slack app with your Render URL
- Check for network restrictions

### "Google Drive not working"
- Ensure `GOOGLE_SERVICE_ACCOUNT_BASE64` is set correctly
- Verify service account has access to the Drive folder
- Check logs for authentication errors

## 🎯 Production Best Practices

1. **Use Production Dockerfile**
   ```dockerfile
   # In render.yaml or Dockerfile selection
   dockerfilePath: ./Dockerfile.production
   ```

2. **Set Resource Limits**
   - Upgrade from free tier for production
   - Monitor memory usage
   - Set up alerts

3. **Security**
   - Use strong passwords
   - Rotate API keys regularly
   - Enable Render's DDoS protection

4. **Scaling**
   - Use Render's autoscaling features
   - Consider separate workers for email processing
   - Implement rate limiting

## 📊 Monitoring

Once deployed, monitor your app:

1. **Render Dashboard**
   - CPU and memory usage
   - Request metrics
   - Error rates

2. **Application Dashboard**
   - Visit `https://your-app.onrender.com/`
   - Check email processing stats
   - Review performance metrics

3. **Slack Notifications**
   - Verify emails are being processed
   - Check quality ratings
   - Monitor response times

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# Make changes locally
git add .
git commit -m "Update: description"
git push origin main

# Render auto-deploys from GitHub
```

### Database Migrations

The app automatically runs database setup on startup. For manual migrations:

```bash
# SSH into Render instance (if available on your plan)
# Or run via Render shell
python setup_complete_database.py
```

## 🎉 Success Checklist

- [ ] Docker image builds successfully
- [ ] Local Docker Compose works
- [ ] All environment variables set in Render
- [ ] Health check passes (`/health` returns 200)
- [ ] Database connects successfully
- [ ] Email processing starts (check logs)
- [ ] Slack notifications working
- [ ] Dashboard accessible
- [ ] Metrics being recorded

## 📚 Additional Resources

- [Render Docker Docs](https://render.com/docs/docker)
- [Render Environment Variables](https://render.com/docs/environment-variables)
- [Render PostgreSQL](https://render.com/docs/databases)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Need Help?** Check the logs first, then refer to the troubleshooting section above.