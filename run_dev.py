#!/usr/bin/env python3
"""
Development server runner for Auto Finder
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def run_command(command, description, background=False):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        if background:
            process = subprocess.Popen(command, shell=True)
            return process
        else:
            result = subprocess.run(command, shell=True, check=True)
            print(f"✅ {description} completed successfully")
            return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please run setup.py first")
        return False
    
    # Check if virtual environment exists
    if not os.path.exists('venv'):
        print("❌ Virtual environment not found. Please run setup.py first")
        return False
    
    # Check if node_modules exists
    if not os.path.exists('node_modules'):
        print("❌ Node modules not found. Please run setup.py first")
        return False
    
    print("✅ All requirements met")
    return True

def start_services():
    """Start all development services"""
    processes = []
    
    try:
        # Determine commands based on OS
        if os.name == 'nt':  # Windows
            python_command = 'venv\\Scripts\\python'
            celery_command = 'venv\\Scripts\\celery'
        else:  # Unix/Linux/macOS
            python_command = 'venv/bin/python'
            celery_command = 'venv/bin/celery'
        
        # Start Flask backend
        print("\n🚀 Starting Flask backend...")
        flask_process = run_command(
            f'{python_command} app.py',
            'Starting Flask backend',
            background=True
        )
        processes.append(('Flask', flask_process))
        
        # Wait a moment for Flask to start
        time.sleep(3)
        
        # Start Celery worker
        print("\n🔄 Starting Celery worker...")
        celery_worker_process = run_command(
            f'{celery_command} -A celery_app worker --loglevel=info',
            'Starting Celery worker',
            background=True
        )
        processes.append(('Celery Worker', celery_worker_process))
        
        # Start Celery beat
        print("\n⏰ Starting Celery beat...")
        celery_beat_process = run_command(
            f'{celery_command} -A celery_app beat --loglevel=info',
            'Starting Celery beat',
            background=True
        )
        processes.append(('Celery Beat', celery_beat_process))
        
        # Start React frontend
        print("\n⚛️  Starting React frontend...")
        react_process = run_command(
            'npm start',
            'Starting React frontend',
            background=True
        )
        processes.append(('React', react_process))
        
        print("\n🎉 All services started!")
        print("\nServices running:")
        print("- Flask backend: http://localhost:5000")
        print("- React frontend: http://localhost:3000")
        print("- Celery worker: Background task processing")
        print("- Celery beat: Scheduled task processing")
        print("\nPress Ctrl+C to stop all services")
        
        # Wait for interrupt
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping all services...")
            
    except Exception as e:
        print(f"❌ Error starting services: {e}")
    
    finally:
        # Clean up processes
        for name, process in processes:
            if process and process.poll() is None:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        print("✅ All services stopped")

def main():
    """Main function"""
    print("🚗 Auto Finder Development Server")
    print("=" * 50)
    
    if not check_requirements():
        sys.exit(1)
    
    start_services()

if __name__ == '__main__':
    main()
