# Simple Dockerfile for Render free tier - minimal setup
FROM node:18-alpine AS frontend-build

# Build React frontend
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY src/ ./src/
COPY public/ ./public/
RUN npm run build

# Python backend stage
FROM python:3.11-slim

# Install basic system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY app.py .
COPY models.py .
COPY database.py .
COPY scraping_engine.py .
COPY scraping_engine_conservative.py .
COPY email_service.py .
COPY celery_app.py .
COPY logging_config.py .
COPY routes/ ./routes/
COPY migrations/ ./migrations/

# Copy built frontend
COPY --from=frontend-build /app/build ./build

# Create logs directory
RUN mkdir -p logs

# Expose port (Render uses PORT environment variable)
EXPOSE $PORT

# Simple start script
COPY start-simple.sh .
RUN chmod +x start-simple.sh

CMD ["./start-simple.sh"]
