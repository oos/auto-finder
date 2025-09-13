#!/usr/bin/env python3
"""
Script to fix user settings
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import User, UserSettings, CarListing

def fix_user_settings():
    """Fix user settings to include all Irish locations"""
    with app.app_context():
        # Get the first user
        user = User.query.first()
        if not user:
            print("No users found.")
            return
        
        print(f"Fixing settings for user: {user.email}")
        
        if user.settings:
            # Update approved locations to include all Irish counties
            all_locations = [
                'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Wexford', 
                'Kilkenny', 'Sligo', 'Donegal', 'Mayo', 'Kerry', 'Clare', 
                'Tipperary', 'Laois', 'Offaly', 'Westmeath', 'Longford', 
                'Leitrim', 'Cavan', 'Monaghan', 'Louth', 'Meath', 'Kildare', 
                'Wicklow', 'Carlow', 'Leinster', 'Munster', 'Connacht', 'Ulster'
            ]
            
            user.settings.set_approved_locations(all_locations)
            db.session.commit()
            
            print(f"Updated approved locations to include all Irish counties")
            print(f"New approved locations: {user.settings.get_approved_locations()}")
        
        # Check listings again
        total_listings = CarListing.query.count()
        print(f"Total listings in database: {total_listings}")

if __name__ == "__main__":
    fix_user_settings()
