"""
Data Processing and Storage System for Scraped Car Listings
Handles data cleaning, validation, deduplication, and database storage
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from database import db
from models import CarListing
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processes and stores scraped car listing data"""
    
    def __init__(self):
        self.processed_urls: Set[str] = set()
        self.processed_titles: Set[str] = set()
    
    def process_listings(self, raw_listings: List[Dict], user_id: int) -> Dict:
        """Process raw scraped listings and store in database"""
        if not raw_listings:
            return {
                'total_processed': 0,
                'new_listings': 0,
                'updated_listings': 0,
                'duplicates_skipped': 0,
                'errors': 0
            }
        
        stats = {
            'total_processed': len(raw_listings),
            'new_listings': 0,
            'updated_listings': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }
        
        for listing_data in raw_listings:
            try:
                # Clean and validate data
                cleaned_data = self.clean_listing_data(listing_data)
                if not cleaned_data:
                    stats['errors'] += 1
                    continue
                
                # Check for duplicates
                if self.is_duplicate(cleaned_data):
                    stats['duplicates_skipped'] += 1
                    continue
                
                # Store or update listing
                result = self.store_listing(cleaned_data, user_id)
                if result == 'new':
                    stats['new_listings'] += 1
                elif result == 'updated':
                    stats['updated_listings'] += 1
                
            except Exception as e:
                logger.error(f"Error processing listing: {e}")
                stats['errors'] += 1
                continue
        
        logger.info(f"Processing complete: {stats}")
        return stats
    
    def clean_listing_data(self, listing_data: Dict) -> Optional[Dict]:
        """Clean and validate listing data"""
        try:
            # Required fields validation
            if not listing_data.get('title') or not listing_data.get('url'):
                logger.warning("Skipping listing with missing required fields")
                return None
            
            # Clean title
            title = self.clean_text(listing_data['title'])
            if len(title) < 10:  # Too short to be meaningful
                return None
            
            # Validate price
            price = listing_data.get('price')
            if price and (price < 500 or price > 200000):  # Reasonable price range
                logger.warning(f"Suspicious price {price} for {title}")
                price = None
            
            # Clean location
            location = self.clean_text(listing_data.get('location', ''))
            if not location:
                location = 'Ireland'  # Default location
            
            # Validate year
            year = listing_data.get('year')
            if year and (year < 1990 or year > 2025):
                logger.warning(f"Suspicious year {year} for {title}")
                year = None
            
            # Validate mileage
            mileage = listing_data.get('mileage')
            if mileage and (mileage < 0 or mileage > 500000):
                logger.warning(f"Suspicious mileage {mileage} for {title}")
                mileage = None
            
            # Clean and validate URL
            url = listing_data['url']
            if not url.startswith('http'):
                logger.warning(f"Invalid URL: {url}")
                return None
            
            # Clean image URL
            image_url = listing_data.get('image_url', '')
            if image_url and not image_url.startswith('http'):
                image_url = ''
            
            return {
                'title': title,
                'price': price,
                'location': location,
                'url': url,
                'image_url': image_url,
                'image_hash': listing_data.get('image_hash', ''),
                'source_site': listing_data.get('source_site', 'unknown'),
                'first_seen': datetime.utcnow(),
                'make': self.clean_text(listing_data.get('make', '')),
                'model': self.clean_text(listing_data.get('model', '')),
                'year': year,
                'mileage': mileage,
                'fuel_type': self.clean_text(listing_data.get('fuel_type', '')),
                'transmission': self.clean_text(listing_data.get('transmission', '')),
                'deal_score': self.calculate_deal_score(listing_data),
                'is_duplicate': False
            }
            
        except Exception as e:
            logger.error(f"Error cleaning listing data: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', str(text).strip())
        
        # Remove special characters that might cause issues
        cleaned = re.sub(r'[^\w\s\-\.]', '', cleaned)
        
        return cleaned
    
    def is_duplicate(self, listing_data: Dict) -> bool:
        """Check if listing is a duplicate"""
        url = listing_data['url']
        title = listing_data['title']
        
        # Check URL duplicates
        if url in self.processed_urls:
            return True
        
        # Check title similarity
        for existing_title in self.processed_titles:
            similarity = SequenceMatcher(None, title.lower(), existing_title.lower()).ratio()
            if similarity > 0.9:  # 90% similarity threshold
                return True
        
        # Check database for existing URL
        existing = CarListing.query.filter_by(url=url).first()
        if existing:
            return True
        
        # Add to processed sets
        self.processed_urls.add(url)
        self.processed_titles.add(title)
        
        return False
    
    def store_listing(self, listing_data: Dict, user_id: int) -> str:
        """Store or update listing in database"""
        try:
            # Check if listing already exists by URL
            existing = CarListing.query.filter_by(url=listing_data['url']).first()
            
            if existing:
                # Update existing listing
                existing.title = listing_data['title']
                existing.price = listing_data['price']
                existing.location = listing_data['location']
                existing.image_url = listing_data['image_url']
                existing.image_hash = listing_data['image_hash']
                existing.make = listing_data['make']
                existing.model = listing_data['model']
                existing.year = listing_data['year']
                existing.mileage = listing_data['mileage']
                existing.fuel_type = listing_data['fuel_type']
                existing.transmission = listing_data['transmission']
                existing.deal_score = listing_data['deal_score']
                existing.last_seen = datetime.utcnow()
                
                db.session.commit()
                logger.info(f"Updated existing listing: {listing_data['title']}")
                return 'updated'
            else:
                # Create new listing
                new_listing = CarListing(
                    title=listing_data['title'],
                    price=listing_data['price'],
                    location=listing_data['location'],
                    url=listing_data['url'],
                    image_url=listing_data['image_url'],
                    image_hash=listing_data['image_hash'],
                    source_site=listing_data['source_site'],
                    first_seen=listing_data['first_seen'],
                    make=listing_data['make'],
                    model=listing_data['model'],
                    year=listing_data['year'],
                    mileage=listing_data['mileage'],
                    fuel_type=listing_data['fuel_type'],
                    transmission=listing_data['transmission'],
                    deal_score=listing_data['deal_score'],
                    is_duplicate=listing_data['is_duplicate']
                )
                
                db.session.add(new_listing)
                db.session.commit()
                logger.info(f"Created new listing: {listing_data['title']}")
                return 'new'
                
        except Exception as e:
            logger.error(f"Error storing listing: {e}")
            db.session.rollback()
            raise e
    
    def calculate_deal_score(self, listing_data: Dict) -> int:
        """Calculate deal score based on various factors"""
        try:
            score = 50  # Base score
            
            # Price factor
            price = listing_data.get('price')
            if price:
                if price < 10000:
                    score += 20
                elif price < 20000:
                    score += 15
                elif price < 30000:
                    score += 10
                else:
                    score += 5
            
            # Year factor
            year = listing_data.get('year')
            if year:
                current_year = datetime.now().year
                age = current_year - year
                if age <= 2:
                    score += 20
                elif age <= 5:
                    score += 15
                elif age <= 10:
                    score += 10
                else:
                    score += 5
            
            # Mileage factor
            mileage = listing_data.get('mileage')
            if mileage and year:
                current_year = datetime.now().year
                age = current_year - year
                if age > 0:
                    avg_mileage = age * 15000  # Average 15k per year
                    if mileage < avg_mileage * 0.5:
                        score += 15
                    elif mileage < avg_mileage:
                        score += 10
                    elif mileage < avg_mileage * 1.5:
                        score += 5
            
            # Fuel type factor
            fuel_type = listing_data.get('fuel_type', '').lower()
            if 'electric' in fuel_type:
                score += 10
            elif 'hybrid' in fuel_type:
                score += 8
            elif 'diesel' in fuel_type:
                score += 5
            
            # Ensure score is within bounds
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating deal score: {e}")
            return 50  # Default score
    
    def cleanup_old_listings(self, days_old: int = 30) -> int:
        """Remove listings that haven't been seen in X days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find old listings
            old_listings = CarListing.query.filter(
                CarListing.last_seen < cutoff_date
            ).all()
            
            count = len(old_listings)
            
            # Delete old listings
            for listing in old_listings:
                db.session.delete(listing)
            
            db.session.commit()
            logger.info(f"Cleaned up {count} old listings")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up old listings: {e}")
            db.session.rollback()
            return 0
    
    def get_scraping_stats(self, user_id: int) -> Dict:
        """Get statistics about scraped data"""
        try:
            total_listings = CarListing.query.count()
            
            # Group by source site
            source_stats = db.session.query(
                CarListing.source_site,
                db.func.count(CarListing.id).label('count')
            ).group_by(CarListing.source_site).all()
            
            # Recent activity
            recent_listings = CarListing.query.filter(
                CarListing.first_seen >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            return {
                'total_listings': total_listings,
                'recent_listings': recent_listings,
                'by_source': {stat.source_site: stat.count for stat in source_stats},
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting scraping stats: {e}")
            return {'error': str(e)}
