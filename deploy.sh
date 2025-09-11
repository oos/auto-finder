#!/bin/bash

# Auto Finder Deployment Script
echo "🚗 Auto Finder Deployment Script"
echo "================================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Please run this script from the auto-finder directory"
    exit 1
fi

# Build frontend
echo "🔄 Building React frontend..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed"
    exit 1
fi

echo "✅ Frontend built successfully"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ Created .env file. Please edit it with your configuration."
    else
        echo "❌ env.example file not found"
        exit 1
    fi
fi

echo "✅ Deployment preparation completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your production configuration"
echo "2. Deploy frontend to Netlify/Vercel"
echo "3. Deploy backend to Heroku/DigitalOcean"
echo "4. Set up your database and Redis"
echo "5. Configure your domain and SSL certificates"
