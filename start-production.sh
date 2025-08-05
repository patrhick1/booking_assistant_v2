#!/bin/bash
set -e

# Decode Google service account if provided as base64
if [ ! -z "$GOOGLE_SERVICE_ACCOUNT_BASE64" ]; then
    echo "Decoding Google service account..."
    echo "$GOOGLE_SERVICE_ACCOUNT_BASE64" | base64 -d > /app/src/service-account-key.json
    export GOOGLE_APPLICATION_CREDENTIALS=/app/src/service-account-key.json
fi

# Run database setup
echo "Checking database..."
python -c "
import sys
sys.path.append('src')
from src.auto_db_setup import ensure_database_ready
from src.metrics_service import metrics
try:
    if ensure_database_ready(metrics.db_pool):
        print('✅ Database schema ready')
    else:
        print('⚠️ Database setup had issues but continuing...')
except Exception as e:
    print(f'⚠️ Database setup error: {e}')
    print('Continuing anyway...')
"

# Start the application
echo "Starting BookingAssistant..."
exec python replit_unified_app.py