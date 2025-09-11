#!/bin/bash

# Start script optimized for Render free tier
echo "🚗 Starting Auto Finder on Render..."

# Get port from Render environment variable
PORT=${PORT:-5000}

# Start Redis in background (if available)
if command -v redis-server &> /dev/null; then
    redis-server --daemonize yes --port 6379
    echo "✅ Redis started"
else
    echo "⚠️  Redis not available, using in-memory storage"
fi

# Start Celery worker in background (if Redis is available)
if command -v redis-server &> /dev/null; then
    celery -A celery_app worker --loglevel=info --detach --concurrency=1
    celery -A celery_app beat --loglevel=info --detach
    echo "✅ Celery workers started"
else
    echo "⚠️  Celery not started (no Redis)"
fi

# Start Flask app with Gunicorn
echo "🚀 Starting Flask application on port $PORT..."
gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --worker-class sync app:app
