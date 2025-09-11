#!/bin/bash

# Start script for Auto Finder Docker container

echo "🚗 Starting Auto Finder..."

# Start Redis in background
redis-server --daemonize yes

# Start Celery worker in background
celery -A celery_app worker --loglevel=info --detach

# Start Celery beat in background
celery -A celery_app beat --loglevel=info --detach

# Start Flask app
echo "🚀 Starting Flask application..."
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
