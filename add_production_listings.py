#!/usr/bin/env python3
"""
Script to add sample listings to production database
Run this on the production server to populate listings
"""

import os
import sys
import random
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import User, UserSettings, CarListing

def add_production_listings():
    """Add sample listings to production database"""
    with app.app_context():
        print("Adding sample listings to production database...")
        
        # Check if listings already exist
        existing_count = CarListing.query.count()
        print(f"Existing listings: {existing_count}")
        
        if existing_count > 0:
            print("Listings already exist, skipping...")
            return
        
        # Create sample listings
        makes = ['Toyota', 'Ford', 'Volkswagen', 'BMW', 'Mercedes', 'Audi', 'Nissan', 'Honda', 'Hyundai', 'Kia']
        models = ['Corolla', 'Focus', 'Golf', '3 Series', 'C-Class', 'A4', 'Qashqai', 'Civic', 'i30', 'Ceed']
        locations = ['Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Wexford', 'Kilkenny', 'Sligo', 'Donegal', 'Mayo']
        fuel_types = ['Petrol', 'Diesel', 'Hybrid', 'Electric']
        transmissions = ['Manual', 'Automatic']
        
        listings_added = 0
        
        for i in range(25):
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
            listings_added += 1
        
        # Fix user settings to be more inclusive
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
            else:
                print(f"Creating settings for user: {user.email}")
                settings = UserSettings(user_id=user.id)
                settings.min_price = 0
                settings.max_price = 100000
                settings.min_deal_score = 0
                settings.set_approved_locations([
                    'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Wexford', 
                    'Kilkenny', 'Sligo', 'Donegal', 'Mayo', 'Kerry', 'Clare', 
                    'Tipperary', 'Laois', 'Offaly', 'Westmeath', 'Longford', 
                    'Leitrim', 'Cavan', 'Monaghan', 'Louth', 'Meath', 'Kildare', 
                    'Wicklow', 'Carlow', 'Leinster', 'Munster', 'Connacht', 'Ulster',
                    'Ireland', 'Irish', 'All', 'Any'
                ])
                db.session.add(settings)
        
        # Commit all changes
        db.session.commit()
        
        print(f"✅ Added {listings_added} sample listings")
        print(f"✅ Updated {len(users)} user settings")
        
        # Verify the fix
        total_listings = CarListing.query.count()
        print(f"Total listings in database: {total_listings}")
        
        # Test the listings query
        from sqlalchemy import or_
        if users:
            user = users[0]
            if user.settings:
                approved_locations = user.settings.get_approved_locations()
                location_filters = [CarListing.location.ilike(f'%{loc}%') for loc in approved_locations]
                
                visible_listings = CarListing.query.filter(
                    CarListing.price >= user.settings.min_price,
                    CarListing.price <= user.settings.max_price,
                    CarListing.deal_score >= user.settings.min_deal_score,
                    or_(*location_filters)
                ).count()
                
                print(f"Listings visible to user: {visible_listings}")

if __name__ == "__main__":
    add_production_listings()
