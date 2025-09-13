#!/usr/bin/env python3
"""
Script to fix user filters to show more listings
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import User, UserSettings, CarListing

def fix_user_filters():
    """Fix user filters to show more listings"""
    with app.app_context():
        # Get the first user
        user = User.query.first()
        if not user:
            print("No users found.")
            return
        
        print(f"Fixing filters for user: {user.email}")
        
        if user.settings:
            # Make filters more inclusive
            user.settings.min_price = 0  # No minimum price
            user.settings.max_price = 100000  # Very high maximum price
            user.settings.min_deal_score = 0  # No minimum deal score
            
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
            
            print(f"Updated user settings:")
            print(f"  Min price: {user.settings.min_price}")
            print(f"  Max price: {user.settings.max_price}")
            print(f"  Min deal score: {user.settings.min_deal_score}")
            print(f"  Approved locations: {len(user.settings.get_approved_locations())} locations")
        
        # Check total listings
        total_listings = CarListing.query.count()
        print(f"Total listings in database: {total_listings}")
        
        # Check listings that would be shown with new filters
        from sqlalchemy import or_
        approved_locations = user.settings.get_approved_locations()
        location_filters = [CarListing.location.ilike(f'%{loc}%') for loc in approved_locations]
        
        filtered_listings = CarListing.query.filter(
            CarListing.price >= user.settings.min_price,
            CarListing.price <= user.settings.max_price,
            CarListing.deal_score >= user.settings.min_deal_score,
            or_(*location_filters)
        ).count()
        
        print(f"Listings that would be shown with new filters: {filtered_listings}")

if __name__ == "__main__":
    fix_user_filters()
