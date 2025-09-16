"""
Scraping Monitor and Testing System
Provides monitoring, testing, and maintenance for the scraping system
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import db
from models import ScrapeLog, CarListing
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ScrapingMonitor:
    """Monitors scraping performance and health"""
    
    def __init__(self):
        self.test_urls = {
            'carzone': 'https://www.carzone.ie/used-cars',
            'donedeal': 'https://www.donedeal.ie/cars'
        }
    
    def test_scraping_health(self) -> Dict:
        """Test if scraping targets are accessible and responsive"""
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'sites': {},
            'overall_status': 'healthy'
        }
        
        for site_name, url in self.test_urls.items():
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # Check if we can find car listing elements
                    car_elements = soup.find_all(['div', 'article'], class_=lambda x: x and 'car' in x.lower() if x else False)
                    
                    health_status['sites'][site_name] = {
                        'status': 'healthy',
                        'response_time': response.elapsed.total_seconds(),
                        'car_elements_found': len(car_elements),
                        'accessible': True
                    }
                else:
                    health_status['sites'][site_name] = {
                        'status': 'unhealthy',
                        'response_code': response.status_code,
                        'accessible': False
                    }
                    health_status['overall_status'] = 'degraded'
                    
            except Exception as e:
                health_status['sites'][site_name] = {
                    'status': 'error',
                    'error': str(e),
                    'accessible': False
                }
                health_status['overall_status'] = 'unhealthy'
        
        return health_status
    
    def get_scraping_stats(self, days: int = 7) -> Dict:
        """Get scraping statistics for the last N days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get scrape logs
            scrape_logs = ScrapeLog.query.filter(
                ScrapeLog.started_at >= cutoff_date
            ).all()
            
            # Get listing counts
            total_listings = CarListing.query.count()
            recent_listings = CarListing.query.filter(
                CarListing.first_seen >= cutoff_date
            ).count()
            
            # Calculate success rate
            successful_scrapes = len([log for log in scrape_logs if log.status == 'completed'])
            total_scrapes = len(scrape_logs)
            success_rate = (successful_scrapes / total_scrapes * 100) if total_scrapes > 0 else 0
            
            # Get listings by source
            source_stats = db.session.query(
                CarListing.source_site,
                db.func.count(CarListing.id).label('count')
            ).group_by(CarListing.source_site).all()
            
            return {
                'period_days': days,
                'total_scrapes': total_scrapes,
                'successful_scrapes': successful_scrapes,
                'success_rate': round(success_rate, 2),
                'total_listings': total_listings,
                'recent_listings': recent_listings,
                'by_source': {stat.source_site: stat.count for stat in source_stats},
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting scraping stats: {e}")
            return {'error': str(e)}
    
    def cleanup_old_data(self, days_old: int = 30) -> Dict:
        """Clean up old scraping logs and listings"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Clean up old scrape logs
            old_logs = ScrapeLog.query.filter(
                ScrapeLog.started_at < cutoff_date
            ).all()
            
            logs_deleted = len(old_logs)
            for log in old_logs:
                db.session.delete(log)
            
            # Clean up old listings that haven't been seen recently
            old_listings = CarListing.query.filter(
                CarListing.last_seen < cutoff_date
            ).all()
            
            listings_deleted = len(old_listings)
            for listing in old_listings:
                db.session.delete(listing)
            
            db.session.commit()
            
            return {
                'logs_deleted': logs_deleted,
                'listings_deleted': listings_deleted,
                'total_cleaned': logs_deleted + listings_deleted,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            db.session.rollback()
            return {'error': str(e)}
    
    def test_single_scraper(self, site_name: str) -> Dict:
        """Test a single scraper"""
        try:
            from scraping_engine_real import RealCarScrapingEngine
            
            engine = RealCarScrapingEngine()
            start_time = datetime.utcnow()
            
            # Test with just 1 page
            listings = engine.scrape_single_site(site_name, max_pages=1)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'site': site_name,
                'status': 'success',
                'listings_found': len(listings),
                'duration_seconds': round(duration, 2),
                'test_time': start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error testing scraper {site_name}: {e}")
            return {
                'site': site_name,
                'status': 'error',
                'error': str(e),
                'test_time': datetime.utcnow().isoformat()
            }
    
    def run_full_test_suite(self) -> Dict:
        """Run comprehensive test suite"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'health_check': self.test_scraping_health(),
            'scraper_tests': {},
            'stats': self.get_scraping_stats(7)
        }
        
        # Test each scraper
        for site_name in ['carzone', 'donedeal']:
            results['scraper_tests'][site_name] = self.test_single_scraper(site_name)
        
        return results
