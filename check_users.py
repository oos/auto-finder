#!/usr/bin/env python3
"""
Script to check users in database
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import User

def check_users():
    """Check users in database"""
    with app.app_context():
        users = User.query.all()
        print(f"Total users: {len(users)}")
        
        for user in users:
            print(f"User ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Active: {user.is_active}")
            print(f"Created: {user.created_at}")
            print("---")

if __name__ == "__main__":
    check_users()
