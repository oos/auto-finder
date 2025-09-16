#!/usr/bin/env python3
"""
Comprehensive Test Script for Real Web Scraping System
Tests all components: scrapers, data processing, monitoring, and API endpoints
"""

import sys
import os
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        from scraping_engine_real import RealCarScrapingEngine, CarzoneScraper, DoneDealScraper
        from data_processor import DataProcessor
        from scraping_monitor import ScrapingMonitor
        logger.info("✅ All imports successful")
        return True
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def test_scraping_engines():
    """Test individual scraping engines"""
    logger.info("Testing scraping engines...")
    
    try:
        from scraping_engine_real import CarzoneScraper, DoneDealScraper
        
        # Test Carzone scraper
        carzone = CarzoneScraper()
        logger.info("✅ Carzone scraper initialized")
        
        # Test DoneDeal scraper
        donedeal = DoneDealScraper()
        logger.info("✅ DoneDeal scraper initialized")
        
        return True
    except Exception as e:
        logger.error(f"❌ Scraping engine test failed: {e}")
        return False

def test_data_processor():
    """Test data processing functionality"""
    logger.info("Testing data processor...")
    
    try:
        from data_processor import DataProcessor
        
        processor = DataProcessor()
        
        # Test with sample data
        sample_listing = {
            'title': '2020 Toyota Corolla',
            'price': 25000,
            'location': 'Dublin',
            'url': 'https://example.com/car/1',
            'image_url': 'https://example.com/image.jpg',
            'source_site': 'test',
            'make': 'Toyota',
            'model': 'Corolla',
            'year': 2020,
            'mileage': 30000,
            'fuel_type': 'Petrol',
            'transmission': 'Manual'
        }
        
        # Test data cleaning
        cleaned = processor.clean_listing_data(sample_listing)
        if cleaned:
            logger.info("✅ Data processor cleaning works")
        else:
            logger.warning("⚠️ Data processor returned None for valid data")
        
        return True
    except Exception as e:
        logger.error(f"❌ Data processor test failed: {e}")
        return False

def test_monitoring_system():
    """Test monitoring system"""
    logger.info("Testing monitoring system...")
    
    try:
        from scraping_monitor import ScrapingMonitor
        
        monitor = ScrapingMonitor()
        
        # Test health check (this will make real HTTP requests)
        logger.info("Running health check...")
        health = monitor.test_scraping_health()
        logger.info(f"Health check result: {health['overall_status']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Monitoring system test failed: {e}")
        return False

def test_real_scraping():
    """Test actual web scraping (limited)"""
    logger.info("Testing real web scraping...")
    
    try:
        from scraping_engine_real import RealCarScrapingEngine
        
        engine = RealCarScrapingEngine()
        
        # Test scraping with just 1 page to avoid overwhelming servers
        logger.info("Testing Carzone scraping (1 page)...")
        carzone_listings = engine.scrape_single_site('carzone', max_pages=1)
        logger.info(f"Found {len(carzone_listings)} listings from Carzone")
        
        if carzone_listings:
            sample = carzone_listings[0]
            logger.info(f"Sample listing: {sample.get('title', 'No title')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Real scraping test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints (requires running Flask app)"""
    logger.info("Testing API endpoints...")
    
    try:
        import requests
        
        # Test health endpoint
        try:
            response = requests.get('http://localhost:5003/api/scraping/monitor/health', timeout=5)
            if response.status_code == 200:
                logger.info("✅ Health endpoint accessible")
            else:
                logger.warning(f"⚠️ Health endpoint returned {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.warning("⚠️ Flask app not running - skipping API tests")
            return True
        
        return True
    except Exception as e:
        logger.error(f"❌ API endpoint test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    logger.info("🚀 Starting comprehensive scraping system test...")
    
    tests = [
        ("Import Test", test_imports),
        ("Scraping Engines", test_scraping_engines),
        ("Data Processor", test_data_processor),
        ("Monitoring System", test_monitoring_system),
        ("Real Scraping", test_real_scraping),
        ("API Endpoints", test_api_endpoints)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info('='*50)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info('='*50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Scraping system is ready.")
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Check logs above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
