#!/usr/bin/env python3
"""
Script to fix user filters on production server
Run this on the production server to make all listings visible
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import User, UserSettings, CarListing
from sqlalchemy import or_

def fix_production_filters():
    """Fix user filters on production to show all listings"""
    with app.app_context():
        print("Fixing user filters on production server...")
        
        # Get all users
        users = User.query.all()
        print(f"Found {len(users)} users")
        
        for user in users:
            if user.settings:
                print(f"Updating filters for user: {user.email}")
                
                # Make filters very inclusive
                user.settings.min_price = 0
                user.settings.max_price = 100000
                user.settings.min_deal_score = 0
                
                # Set all Irish locations as approved
                all_locations = [
                    'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Wexford', 
                    'Kilkenny', 'Sligo', 'Donegal', 'Mayo', 'Kerry', 'Clare', 
                    'Tipperary', 'Laois', 'Offaly', 'Westmeath', 'Longford', 
                    'Leitrim', 'Cavan', 'Monaghan', 'Louth', 'Meath', 'Kildare', 
                    'Wicklow', 'Carlow', 'Leinster', 'Munster', 'Connacht', 'Ulster',
                    'Ireland', 'Irish', 'All', 'Any'
                ]
                
                user.settings.set_approved_locations(all_locations)
        
        db.session.commit()
        print("✅ User filters updated successfully!")
        
        # Check total listings
        total_listings = CarListing.query.count()
        print(f"Total listings in database: {total_listings}")
        
        # If no listings, add some sample ones
        if total_listings == 0:
            print("No listings found, adding sample data...")
            add_sample_listings()
        else:
            print("✅ Listings are available in the database")

def add_sample_listings():
    """Add sample listings if none exist"""
    import random
    from datetime import datetime
    
    makes = ['Toyota', 'Ford', 'Volkswagen', 'BMW', 'Mercedes', 'Audi', 'Nissan', 'Honda', 'Hyundai', 'Kia']
    models = ['Corolla', 'Focus', 'Golf', '3 Series', 'C-Class', 'A4', 'Qashqai', 'Civic', 'i30', 'Ceed']
    locations = ['Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Wexford', 'Kilkenny', 'Sligo', 'Donegal', 'Mayo']
    fuel_types = ['Petrol', 'Diesel', 'Hybrid', 'Electric']
    transmissions = ['Manual', 'Automatic']
    
    for i in range(20):
        make = random.choice(makes)
        model = random.choice(models)
        year = random.randint(2015, 2023)
        price = random.randint(5000, 25000)
        location = random.choice(locations)
        fuel_type = random.choice(fuel_types)
        transmission = random.choice(transmissions)
        mileage = random.randint(10000, 150000)
        
        listing = CarListing(
            title=f"{year} {make} {model} {fuel_type} {transmission}",
            price=price,
            location=location,
            url=f"https://example.com/car-{i+1}",
            image_url=f"https://via.placeholder.com/300x200?text={make}+{model}",
            image_hash=f"sample_hash_{i+1}",
            source_site='sample',
            make=make,
            model=model,
            year=year,
            mileage=mileage,
            fuel_type=fuel_type,
            transmission=transmission,
            deal_score=random.uniform(30, 95),
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            status='active'
        )
        
        db.session.add(listing)
    
    db.session.commit()
    print("✅ Added 20 sample listings")

if __name__ == "__main__":
    fix_production_filters()
