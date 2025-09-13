#!/usr/bin/env python3
"""
Script to clear dummy/sample data when ready to switch to real scraped data
Run this when you want to remove sample listings and start fresh with real data
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import CarListing

def clear_dummy_data():
    """Clear all sample/dummy listings from the database"""
    with app.app_context():
        print("Clearing dummy data from database...")
        
        # Count existing listings
        total_listings = CarListing.query.count()
        sample_listings = CarListing.query.filter_by(source_site='sample').count()
        
        print(f"Total listings: {total_listings}")
        print(f"Sample listings: {sample_listings}")
        
        if sample_listings == 0:
            print("No sample listings found to clear.")
            return
        
        # Delete all sample listings
        CarListing.query.filter_by(source_site='sample').delete()
        db.session.commit()
        
        remaining_listings = CarListing.query.count()
        print(f"✅ Cleared {sample_listings} sample listings")
        print(f"Remaining listings: {remaining_listings}")
        
        if remaining_listings > 0:
            print("Note: There are still some non-sample listings in the database")

if __name__ == "__main__":
    clear_dummy_data()
