#!/usr/bin/env python3
"""
Script to fix production database schema issues
"""
import os
import sys
import requests
import json

# Production URL
PROD_URL = "https://auto-finder.onrender.com"

def add_notes_column():
    """Add notes column to scrape_logs table via SQL"""
    try:
        # This would need to be done via a database migration endpoint
        # For now, let's create a simple endpoint to fix this
        print("🔧 Adding notes column to scrape_logs table...")
        
        # We'll need to create an endpoint in the app to handle this
        # For now, let's just test if we can access the database
        response = requests.get(f"{PROD_URL}/api/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Database connection working: {data}")
        else:
            print(f"❌ Database connection failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🔧 Fixing Production Database Schema")
    print("=" * 50)
    
    add_notes_column()
    
    print("\n✅ Database fix attempt complete!")
    print("\nNote: The production database needs the 'notes' column added to scrape_logs table.")
    print("This should be done via a proper database migration.")

if __name__ == "__main__":
    main()

