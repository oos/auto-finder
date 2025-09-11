#!/bin/bash

# Simple start script for Render free tier
echo "🚗 Starting Auto Finder (Simple Mode)..."

# Get port from Render environment variable
PORT=${PORT:-5000}

# Start Flask app with Gunicorn
echo "🚀 Starting Flask application on port $PORT..."
gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --worker-class sync app:app
