#!/usr/bin/env python3
"""
Script to test login with different passwords
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import User
from werkzeug.security import check_password_hash

def test_login():
    """Test login with different passwords"""
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        if user:
            print(f"User found: {user.email}")
            print(f"Password hash: {user.password_hash[:50]}...")
            
            # Test different passwords
            passwords = ["testpass123", "password", "test", "123456", "admin"]
            
            for pwd in passwords:
                is_valid = check_password_hash(user.password_hash, pwd)
                print(f"Password '{pwd}': {'VALID' if is_valid else 'INVALID'}")
        else:
            print("User not found")

if __name__ == "__main__":
    test_login()
