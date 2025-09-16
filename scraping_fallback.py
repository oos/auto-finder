"""
Fallback scraping system for production environments
Provides basic functionality without heavy dependencies
"""

import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

class FallbackScrapingEngine:
    """Fallback scraping engine for production environments"""
    
    def __init__(self):
        self.name = "fallback"
    
    def scrape_single_site(self, site_name: str, max_pages: int = 1) -> List[Dict]:
        """Fallback scraping that returns sample data"""
        logger.info(f"Using fallback scraping for {site_name}")
        
        # Return sample data instead of real scraping
        sample_listings = [
            {
                'title': f'2020 Toyota Corolla - Sample from {site_name}',
                'price': 25000,
                'location': 'Dublin',
                'url': f'https://example.com/{site_name}/car/1',
                'image_url': 'https://via.placeholder.com/300x200?text=Sample+Car',
                'image_hash': 'sample_hash_1',
                'source_site': site_name,
                'first_seen': datetime.utcnow(),
                'make': 'Toyota',
                'model': 'Corolla',
                'year': 2020,
                'mileage': 30000,
                'fuel_type': 'Petrol',
                'transmission': 'Manual',
                'deal_score': 75,
                'is_duplicate': False
            },
            {
                'title': f'2019 Ford Focus - Sample from {site_name}',
                'price': 22000,
                'location': 'Cork',
                'url': f'https://example.com/{site_name}/car/2',
                'image_url': 'https://via.placeholder.com/300x200?text=Sample+Car+2',
                'image_hash': 'sample_hash_2',
                'source_site': site_name,
                'first_seen': datetime.utcnow(),
                'make': 'Ford',
                'model': 'Focus',
                'year': 2019,
                'mileage': 45000,
                'fuel_type': 'Diesel',
                'transmission': 'Manual',
                'deal_score': 70,
                'is_duplicate': False
            }
        ]
        
        return sample_listings[:max_pages]  # Return limited results

class FallbackDataProcessor:
    """Fallback data processor for production environments"""
    
    def process_listings(self, raw_listings: List[Dict], user_id: int) -> Dict:
        """Process listings with fallback logic"""
        return {
            'total_processed': len(raw_listings),
            'new_listings': len(raw_listings),
            'updated_listings': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }

class FallbackScrapingMonitor:
    """Fallback monitoring for production environments"""
    
    def test_scraping_health(self) -> Dict:
        """Return basic health status"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'degraded',
            'message': 'Using fallback scraping system',
            'sites': {
                'carzone': {
                    'status': 'degraded',
                    'accessible': True,
                    'message': 'Fallback mode'
                },
                'donedeal': {
                    'status': 'degraded', 
                    'accessible': True,
                    'message': 'Fallback mode'
                }
            }
        }
    
    def get_scraping_stats(self, days: int = 7) -> Dict:
        """Return basic stats"""
        return {
            'period_days': days,
            'total_scrapes': 0,
            'successful_scrapes': 0,
            'success_rate': 0,
            'total_listings': 0,
            'recent_listings': 0,
            'by_source': {},
            'last_updated': datetime.utcnow().isoformat(),
            'message': 'Using fallback system - no real data available'
        }
