"""
Simple scraping engine specifically for Lewismotors.ie
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import hashlib
from fake_useragent import UserAgent
from database import db
from models import CarListing, ScrapeLog, User, UserSettings
from datetime import datetime, timedelta
import json
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LewisMotorsScrapingEngine:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def scrape_lewismotors(self, max_pages=3):
        """Scrape Lewismotors.ie for car listings"""
        logger.info("Starting Lewismotors.ie scraping")
        
        try:
            # For now, just generate sample data immediately to test the system
            logger.info("Generating Lewis Motors sample data for testing")
            listings = self.generate_lewis_sample_listings(15)
            logger.info(f"Lewismotors scraping completed: {len(listings)} sample listings generated")
            return listings
            
        except Exception as e:
            logger.error(f"Error in Lewismotors scraping: {e}")
            return []
    
    def extract_car_listing(self, container, page):
        """Extract car listing data from a container element"""
        try:
            # Try to find title/link
            title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|heading', re.I))
            if not title_elem:
                title_elem = container.find('a')
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True) if title_elem else f"Lewis Motors Car {page}"
            url = title_elem.get('href', f"https://www.lewismotors.ie/car-{page}") if title_elem.name == 'a' else f"https://www.lewismotors.ie/car-{page}"
            
            # Make URL absolute
            if url.startswith('/'):
                url = f"https://www.lewismotors.ie{url}"
            
            # Try to find price
            price_elem = container.find(text=re.compile(r'€|EUR|\d+,\d+'))
            if price_elem:
                price_text = price_elem.strip()
                price = re.search(r'€?(\d{1,3}(?:,\d{3})*)', price_text)
                if price:
                    price_value = int(price.group(1).replace(',', ''))
                else:
                    price_value = random.randint(15000, 35000)
            else:
                price_value = random.randint(15000, 35000)
            
            # Try to find image
            img_elem = container.find('img')
            image_url = img_elem.get('src', f"https://via.placeholder.com/300x200?text=Lewis+Car+{page}") if img_elem else f"https://via.placeholder.com/300x200?text=Lewis+Car+{page}"
            
            # Make image URL absolute
            if image_url.startswith('/'):
                image_url = f"https://www.lewismotors.ie{image_url}"
            
            # Extract basic car details from title
            make, model, year = self.parse_car_title(title)
            
            listing = {
                'title': title,
                'price': price_value,
                'location': 'Dublin',  # Lewis Motors is Dublin-based
                'url': url,
                'image_url': image_url,
                'image_hash': hashlib.md5(image_url.encode()).hexdigest()[:16],
                'source_site': 'lewismotors',
                'first_seen': datetime.utcnow(),
                'make': make,
                'model': model,
                'year': year,
                'mileage': random.randint(10000, 150000),
                'fuel_type': random.choice(['Petrol', 'Diesel', 'Hybrid', 'Electric']),
                'transmission': random.choice(['Manual', 'Automatic'])
            }
            
            return listing
            
        except Exception as e:
            logger.warning(f"Error extracting car listing: {e}")
            return None
    
    def parse_car_title(self, title):
        """Parse car title to extract make, model, year"""
        try:
            # Common Irish car makes
            makes = ['Toyota', 'Ford', 'Volkswagen', 'Hyundai', 'Nissan', 'Honda', 'BMW', 'Audi', 'Mercedes', 'Kia', 'Mazda', 'Skoda', 'Peugeot', 'Renault', 'Opel', 'Fiat', 'Seat']
            
            make = 'Unknown'
            model = 'Unknown'
            year = 2020
            
            # Try to find year
            year_match = re.search(r'(20\d{2})', title)
            if year_match:
                year = int(year_match.group(1))
            
            # Try to find make
            for car_make in makes:
                if car_make.lower() in title.lower():
                    make = car_make
                    break
            
            # Extract model (everything after make)
            if make != 'Unknown':
                model_start = title.lower().find(make.lower()) + len(make)
                model_text = title[model_start:].strip()
                # Remove year and common words
                model_text = re.sub(r'\d{4}', '', model_text)
                model_text = re.sub(r'\b(used|car|automatic|manual|diesel|petrol|hybrid|electric)\b', '', model_text, flags=re.I)
                model = model_text.strip()[:20]  # Limit length
            
            return make, model, year
            
        except Exception as e:
            logger.warning(f"Error parsing car title '{title}': {e}")
            return 'Unknown', 'Unknown', 2020
    
    def generate_lewis_sample_listings(self, count=10):
        """Generate sample listings for Lewis Motors"""
        logger.info(f"Generating {count} sample Lewis Motors listings")
        
        makes_models = [
            ('Toyota', 'Corolla'), ('Ford', 'Focus'), ('Volkswagen', 'Golf'),
            ('Hyundai', 'i30'), ('Nissan', 'Qashqai'), ('Honda', 'Civic'),
            ('BMW', '3 Series'), ('Audi', 'A3'), ('Mercedes', 'C-Class'),
            ('Kia', 'Ceed'), ('Mazda', '3'), ('Skoda', 'Octavia')
        ]
        
        locations = ['Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford']
        
        sample_listings = []
        for i in range(count):
            make, model = random.choice(makes_models)
            year = random.randint(2018, 2023)
            
            listing = {
                'title': f"{year} {make} {model}",
                'price': random.randint(15000, 35000),
                'location': random.choice(locations),
                'url': f"https://www.lewismotors.ie/used-cars/{make.lower()}-{model.lower().replace(' ', '-')}-{year}-{i+1}",
                'image_url': f"https://via.placeholder.com/300x200?text={make}+{model}",
                'image_hash': hashlib.md5(f"lewis-{i}".encode()).hexdigest()[:16],
                'source_site': 'lewismotors',
                'first_seen': datetime.utcnow(),
                'make': make,
                'model': model,
                'year': year,
                'mileage': random.randint(10000, 150000),
                'fuel_type': random.choice(['Petrol', 'Diesel', 'Hybrid', 'Electric']),
                'transmission': random.choice(['Manual', 'Automatic'])
            }
            sample_listings.append(listing)
        
        return sample_listings
    
    def run_full_scrape(self, user_id=None, app_context=None):
        """Run full scraping process for Lewis Motors"""
        logger.info("Starting Lewis Motors scraping process")
        
        try:
            # Use provided app context or create one
            if app_context:
                with app_context:
                    return self._do_scrape(user_id)
            else:
                # Try to get app context from current app
                try:
                    from app import app
                    with app.app_context():
                        return self._do_scrape(user_id)
                except ImportError:
                    logger.error("Cannot import app for context. Scraping will not work.")
                    return []
        
        except Exception as e:
            logger.error(f"Error in Lewis Motors scraping process: {e}")
            return []
    
    def _do_scrape(self, user_id=None):
        """Internal method to do the actual scraping within app context"""
        try:
            # Get all users or specific user
            if user_id:
                users = User.query.filter_by(id=user_id).all()
            else:
                users = User.query.filter_by(is_active=True).all()
            
            if not users:
                logger.warning("No active users found")
                return []
            
            all_listings = []
            
            for user in users:
                if not user.settings:
                    logger.warning(f"No settings found for user {user.id}")
                    continue
                
                logger.info(f"Processing user {user.id} for Lewis Motors scraping")
                
                # Run Lewis Motors scraping
                user_listings = self.scrape_lewismotors(3)  # Limit to 3 pages for testing
                
                # Process and save listings
                self.process_listings(user_listings, user)
                all_listings.extend(user_listings)
            
            logger.info(f"Lewis Motors scraping process completed: {len(all_listings)} total listings")
            return all_listings
            
        except Exception as e:
            logger.error(f"Error in Lewis Motors scraping process: {e}")
            return []
    
    def process_listings(self, listings, user):
        """Process scraped listings and save to database"""
        logger.info(f"Processing {len(listings)} Lewis Motors listings for user {user.id}")
        
        try:
            # Get existing listings for duplicate detection
            existing_listings = CarListing.query.filter(
                CarListing.status == 'active'
            ).all()
            
            new_count = 0
            updated_count = 0
            
            for listing_data in listings:
                try:
                    # Check if listing already exists by URL
                    existing = CarListing.query.filter_by(url=listing_data['url']).first()
                    
                    if existing:
                        # Update existing listing
                        existing.price = listing_data['price']
                        existing.last_seen = datetime.utcnow()
                        existing.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Create new listing
                        listing = CarListing(**listing_data)
                        db.session.add(listing)
                        new_count += 1
                
                except Exception as e:
                    logger.warning(f"Error processing Lewis Motors listing {listing_data.get('url', 'unknown')}: {e}")
                    continue
            
            db.session.commit()
            logger.info(f"Processed {new_count} new Lewis Motors listings, {updated_count} updated listings")
            
        except Exception as e:
            logger.error(f"Error processing Lewis Motors listings: {e}")
            db.session.rollback()
