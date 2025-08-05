# 📧 Email Processing Configuration Guide

This guide explains how BookingAssistant processes emails and the available configuration options.

## 🔄 Email Processing Behavior

### Default Behavior
- **Polls emails every 60 seconds** when deployed
- **Keeps emails unread** after processing (for human review)
- **Prevents duplicate processing** using session tracking
- **Creates draft responses** via Nylas API

### Why Emails Stay Unread by Default
The system keeps emails unread after processing so that:
1. **Human reviewers can see new emails** in their inbox
2. **Quality control** - humans can verify AI responses
3. **Backup safety** - nothing is missed if AI fails

## ⚙️ Configuration Options

### 1. Email Read Status
Control whether emails are marked as read after processing:

```bash
# In your .env file
MARK_EMAILS_AS_READ=false  # Default: keeps emails unread
# or
MARK_EMAILS_AS_READ=true   # Marks emails as read after processing
```

### 2. Polling Interval
Adjust how often the system checks for new emails:

```python
# In run_assistant.py
polling_interval = 60  # seconds (default)
# Change to:
polling_interval = 30  # Check every 30 seconds
```

⚠️ **Note**: Shorter intervals may hit API rate limits

### 3. Spam Filtering
The system filters out spam using keywords. To modify:

```python
# In src/nylas_email_service.py
self.spam_keywords = [
    "delivery status notification",
    "your-custom-spam-keyword",
    # Add more as needed
]
```

## 🚀 Real-Time Email Processing Options

### Option 1: Polling (Current Setup)
- **Pros**: Simple, reliable, works everywhere
- **Cons**: Not instant (up to 60-second delay)
- **Best for**: Most use cases

### Option 2: Nylas Webhooks (Advanced)
For instant email notifications, configure Nylas webhooks:

1. **Set up webhook endpoint** in your app:
```python
@app.post("/webhook/nylas")
async def nylas_webhook(request: Request):
    # Process incoming email notification
    pass
```

2. **Configure in Nylas Dashboard**:
   - Go to Webhooks section
   - Add webhook URL: `https://your-app.com/webhook/nylas`
   - Select "message.created" event

3. **Benefits**:
   - Instant processing (< 1 second)
   - More efficient (no polling)
   - Scales better

### Option 3: Hybrid Approach
Combine webhooks with polling as backup:
- Primary: Webhooks for instant processing
- Backup: Polling every 5 minutes for missed events

## 📊 Duplicate Prevention

The system prevents processing the same email multiple times through:

1. **Session Memory**: Tracks processed message IDs in current session
2. **Database Deduplication**: Uses email hash to prevent re-processing across sessions
3. **Unread Filter**: Only fetches unread emails

### How It Works
```
New Email Arrives → Check if Unread → Check Session Memory → Check Database → Process if New
```

## 🔍 Monitoring Email Processing

### Check Processing Status
Monitor which emails have been processed:

```sql
-- In your database
SELECT sender_email, subject, processing_started_at, status
FROM email_sessions
ORDER BY processing_started_at DESC
LIMIT 10;
```

### View Unprocessed Emails
See emails that were skipped:
- Check spam filter logs in console
- Review emails marked as read manually
- Check for processing errors in logs

## 🛠️ Troubleshooting

### "Email processed multiple times"
- Check if `MARK_EMAILS_AS_READ=false` is set
- Verify database deduplication is working
- Check for multiple instances running

### "Emails not being processed"
- Verify emails are unread in Gmail
- Check spam keyword filtering
- Ensure Nylas grant has proper permissions
- Check polling is active in logs

### "Humans don't see new emails"
- Confirm `MARK_EMAILS_AS_READ=false`
- Check if emails are in spam/other folders
- Verify email client sync settings

## 💡 Best Practices

1. **For Human-in-the-Loop Workflows**:
   ```bash
   MARK_EMAILS_AS_READ=false  # Keep unread for review
   polling_interval = 60       # Check every minute
   ```

2. **For Fully Automated Workflows**:
   ```bash
   MARK_EMAILS_AS_READ=true   # Mark as processed
   polling_interval = 300      # Check every 5 minutes
   ```

3. **For High-Volume Processing**:
   - Use Nylas webhooks
   - Implement rate limiting
   - Add queue system for processing

## 📈 Performance Considerations

- **API Rate Limits**: Nylas has rate limits - respect them
- **Processing Time**: Each email takes 5-10 seconds to process
- **Database Load**: High volume may need connection pooling
- **Memory Usage**: Session tracking grows with processed emails

## 🔐 Security Notes

- Unread emails are visible to all Gmail users
- Draft responses are saved but not sent automatically
- Human approval required via Slack before sending
- All processing is logged for audit trail