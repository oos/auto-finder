#!/usr/bin/env python3
"""
Script to check user settings
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import User, UserSettings, CarListing

def check_user_settings():
    """Check user settings and listings"""
    with app.app_context():
        # Get the first user
        user = User.query.first()
        if not user:
            print("No users found.")
            return
        
        print(f"User: {user.email}")
        print(f"Has settings: {user.settings is not None}")
        
        if user.settings:
            print(f"Min price: {user.settings.min_price}")
            print(f"Max price: {user.settings.max_price}")
            print(f"Approved locations: {user.settings.get_approved_locations()}")
            print(f"Min deal score: {user.settings.min_deal_score}")
        
        # Check total listings
        total_listings = CarListing.query.count()
        print(f"Total listings in database: {total_listings}")
        
        # Check listings with different filters
        all_listings = CarListing.query.all()
        print(f"All listings: {len(all_listings)}")
        
        if all_listings:
            print("Sample listing:")
            listing = all_listings[0]
            print(f"  Title: {listing.title}")
            print(f"  Price: {listing.price}")
            print(f"  Location: {listing.location}")
            print(f"  Status: {listing.status}")

if __name__ == "__main__":
    check_user_settings()
