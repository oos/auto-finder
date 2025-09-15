#!/usr/bin/env python3
"""
Script to populate production database with sample data
"""
import os
import sys
import requests
import json

# Production URL
PROD_URL = "https://auto-finder.onrender.com"

def test_endpoint(endpoint):
    """Test an endpoint and return the response"""
    try:
        response = requests.get(f"{PROD_URL}{endpoint}", timeout=30)
        print(f"GET {endpoint}: {response.status_code}")
        if response.status_code != 200:
            print(f"  Error: {response.text}")
        return response
    except Exception as e:
        print(f"GET {endpoint}: ERROR - {e}")
        return None

def setup_sample_data():
    """Setup sample data on production"""
    try:
        response = requests.post(f"{PROD_URL}/api/setup-sample-data", timeout=60)
        print(f"POST /api/setup-sample-data: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {data}")
        else:
            print(f"  Error: {response.text}")
        return response
    except Exception as e:
        print(f"POST /api/setup-sample-data: ERROR - {e}")
        return None

def main():
    print("🚀 Testing Production Auto Finder API")
    print("=" * 50)
    
    # Test basic endpoints
    print("\n1. Testing basic endpoints:")
    test_endpoint("/api/health")
    test_endpoint("/api/listings/")
    
    # Test dashboard endpoints
    print("\n2. Testing dashboard endpoints:")
    test_endpoint("/api/dashboard/overview")
    test_endpoint("/api/dashboard/alerts")
    test_endpoint("/api/dashboard/charts/trends?days=30")
    test_endpoint("/api/dashboard/charts/distribution")
    
    # Test scraping endpoints
    print("\n3. Testing scraping endpoints:")
    test_endpoint("/api/scraping/status")
    test_endpoint("/api/scraping/logs?per_page=50")
    
    # Setup sample data
    print("\n4. Setting up sample data:")
    setup_sample_data()
    
    # Test again after setup
    print("\n5. Testing after sample data setup:")
    test_endpoint("/api/dashboard/overview")
    test_endpoint("/api/listings/")
    
    print("\n✅ Production testing complete!")

if __name__ == "__main__":
    main()

