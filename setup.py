#!/usr/bin/env python3
"""
Setup script for Auto Finder
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def check_node_version():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()} detected")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Node.js is not installed. Please install Node.js 18 or higher")
    return False

def setup_backend():
    """Set up Python backend"""
    print("\n🐍 Setting up Python backend...")
    
    # Check if virtual environment exists
    if not os.path.exists('venv'):
        if not run_command('python -m venv venv', 'Creating virtual environment'):
            return False
    
    # Determine activation script based on OS
    if os.name == 'nt':  # Windows
        activate_script = 'venv\\Scripts\\activate'
        pip_command = 'venv\\Scripts\\pip'
        python_command = 'venv\\Scripts\\python'
    else:  # Unix/Linux/macOS
        activate_script = 'source venv/bin/activate'
        pip_command = 'venv/bin/pip'
        python_command = 'venv/bin/python'
    
    # Install Python dependencies
    if not run_command(f'{pip_command} install --upgrade pip', 'Upgrading pip'):
        return False
    
    if not run_command(f'{pip_command} install -r requirements.txt', 'Installing Python dependencies'):
        return False
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        if os.path.exists('env.example'):
            run_command('cp env.example .env', 'Creating .env file from template')
            print("⚠️  Please edit .env file with your configuration")
        else:
            print("⚠️  Please create .env file with your configuration")
    
    print("✅ Backend setup completed")
    return True

def setup_frontend():
    """Set up React frontend"""
    print("\n⚛️  Setting up React frontend...")
    
    # Install Node.js dependencies
    if not run_command('npm install', 'Installing Node.js dependencies'):
        return False
    
    print("✅ Frontend setup completed")
    return True

def setup_database():
    """Set up database"""
    print("\n🗄️  Setting up database...")
    
    # Determine Python command based on OS
    if os.name == 'nt':  # Windows
        python_command = 'venv\\Scripts\\python'
    else:  # Unix/Linux/macOS
        python_command = 'venv/bin/python'
    
    # Initialize database
    if not run_command(f'{python_command} -c "from app import app, db; app.app_context().push(); db.create_all()"', 'Creating database tables'):
        return False
    
    print("✅ Database setup completed")
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ['logs', 'migrations', 'tests']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def main():
    """Main setup function"""
    print("🚗 Auto Finder Setup")
    print("=" * 50)
    
    # Check system requirements
    check_python_version()
    if not check_node_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup backend
    if not setup_backend():
        print("❌ Backend setup failed")
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        print("❌ Frontend setup failed")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("❌ Database setup failed")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Start the backend: python app.py")
    print("3. Start the frontend: npm start")
    print("4. Start Celery worker: celery -A celery_app worker --loglevel=info")
    print("5. Start Celery beat: celery -A celery_app beat --loglevel=info")

if __name__ == '__main__':
    main()
