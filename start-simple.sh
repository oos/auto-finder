#!/bin/bash

# Simple start script for Render free tier
echo "🚗 Starting Auto Finder (Simple Mode)..."

# Get port from Render environment variable
PORT=${PORT:-5000}

# Initialize database
echo "🗄️ Initializing database..."
python -c "
from app import app
from database import db
with app.app_context():
    db.create_all()
    print('✅ Database tables created successfully')
"

# Start Flask app with Gunicorn
echo "🚀 Starting Flask application on port $PORT..."
gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --worker-class sync app:app
