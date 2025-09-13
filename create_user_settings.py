#!/usr/bin/env python3
"""
Script to create user settings
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import User, UserSettings

def create_user_settings():
    """Create settings for the test user"""
    with app.app_context():
        # Get the first user
        user = User.query.first()
        if not user:
            print("No users found.")
            return
        
        print(f"Creating settings for user: {user.email}")
        
        # Check if user already has settings
        if user.settings:
            print("User already has settings")
            return
        
        # Create settings
        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        db.session.commit()
        
        print("User settings created successfully")

if __name__ == "__main__":
    create_user_settings()
