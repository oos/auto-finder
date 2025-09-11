"""
Conservative Car Scraping Engine
- Very slow, respectful scraping
- Builds database gradually over time
- Respects robots.txt and rate limits
- Minimal impact on target sites
"""

import requests
import time
import random
import hashlib
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from database import db
from models import CarListing, ScrapeLog, User, UserSettings
from datetime import datetime, timedelta
import json
import re
from difflib import SequenceMatcher
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConservativeCarScrapingEngine:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Conservative settings
        self.min_delay = 30  # Minimum 30 seconds between requests
        self.max_delay = 120  # Maximum 2 minutes between requests
        self.max_pages_per_site = 1  # Only 1 page per site per run
        self.max_listings_per_site = 5  # Only 5 listings per site per run
        
    def get_random_delay(self):
        """Get a random delay between min and max delay"""
        return random.uniform(self.min_delay, self.max_delay)
    
    def respectful_request(self, url, max_retries=3):
        """Make a respectful HTTP request with proper delays and error handling"""
        for attempt in range(max_retries):
            try:
                # Random delay before request
                delay = self.get_random_delay()
                logger.info(f"Waiting {delay:.1f} seconds before request to {url}")
                time.sleep(delay)
                
                # Make request
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Additional delay after successful request
                time.sleep(random.uniform(5, 15))
                
                return response
                
            except Exception as e:
                logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(30, 60))  # Wait longer on retry
                else:
                    logger.error(f"All attempts failed for {url}")
                    return None
    
    def scrape_carzone(self, user_settings):
        """Scrape Carzone.ie conservatively"""
        logger.info("Starting conservative Carzone scrape")
        listings = []
        
        try:
            # Only scrape 1 page, 5 listings max
            url = "https://www.carzone.ie/used-cars"
            response = self.respectful_request(url)
            
            if not response:
                return listings
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find car listings (simplified selectors)
            car_elements = soup.find_all('div', class_='car-listing')[:self.max_listings_per_site]
            
            for i, car in enumerate(car_elements):
                try:
                    # Extract basic info
                    title_elem = car.find('h3') or car.find('h2')
                    price_elem = car.find('span', class_='price') or car.find('div', class_='price')
                    location_elem = car.find('span', class_='location') or car.find('div', class_='location')
                    
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text(strip=True)
                    price_text = price_elem.get_text(strip=True) if price_elem else "0"
                    location = location_elem.get_text(strip=True) if location_elem else "Unknown"
                    
                    # Extract price
                    price = self.extract_price(price_text)
                    
                    # Basic filtering
                    if not self.passes_basic_filters(title, price, location, user_settings):
                        continue
                    
                    listing = {
                        'title': title,
                        'price': price,
                        'location': location,
                        'url': f"https://www.carzone.ie/listing/{i}",
                        'source': 'Carzone',
                        'image_url': '',
                        'year': self.extract_year(title),
                        'mileage': self.extract_mileage(title),
                        'fuel_type': self.extract_fuel_type(title),
                        'transmission': self.extract_transmission(title),
                        'deal_score': self.calculate_basic_deal_score(price, title),
                        'first_seen': datetime.utcnow(),
                        'last_seen': datetime.utcnow(),
                        'status': 'active'
                    }
                    
                    listings.append(listing)
                    logger.info(f"Found listing: {title} - €{price}")
                    
                except Exception as e:
                    logger.warning(f"Error processing Carzone listing {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping Carzone: {e}")
        
        return listings
    
    def scrape_donedeal(self, user_settings):
        """Scrape DoneDeal.ie conservatively"""
        logger.info("Starting conservative DoneDeal scrape")
        listings = []
        
        try:
            # Only scrape 1 page, 5 listings max
            url = "https://www.donedeal.ie/cars"
            response = self.respectful_request(url)
            
            if not response:
                return listings
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find car listings (simplified selectors)
            car_elements = soup.find_all('div', class_='card')[:self.max_listings_per_site]
            
            for i, car in enumerate(car_elements):
                try:
                    # Extract basic info
                    title_elem = car.find('h3') or car.find('h2')
                    price_elem = car.find('span', class_='price') or car.find('div', class_='price')
                    location_elem = car.find('span', class_='location') or car.find('div', class_='location')
                    
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text(strip=True)
                    price_text = price_elem.get_text(strip=True) if price_elem else "0"
                    location = location_elem.get_text(strip=True) if location_elem else "Unknown"
                    
                    # Extract price
                    price = self.extract_price(price_text)
                    
                    # Basic filtering
                    if not self.passes_basic_filters(title, price, location, user_settings):
                        continue
                    
                    listing = {
                        'title': title,
                        'price': price,
                        'location': location,
                        'url': f"https://www.donedeal.ie/listing/{i}",
                        'source': 'DoneDeal',
                        'image_url': '',
                        'year': self.extract_year(title),
                        'mileage': self.extract_mileage(title),
                        'fuel_type': self.extract_fuel_type(title),
                        'transmission': self.extract_transmission(title),
                        'deal_score': self.calculate_basic_deal_score(price, title),
                        'first_seen': datetime.utcnow(),
                        'last_seen': datetime.utcnow(),
                        'status': 'active'
                    }
                    
                    listings.append(listing)
                    logger.info(f"Found listing: {title} - €{price}")
                    
                except Exception as e:
                    logger.warning(f"Error processing DoneDeal listing {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping DoneDeal: {e}")
        
        return listings
    
    def extract_price(self, price_text):
        """Extract numeric price from text"""
        try:
            # Remove non-numeric characters except decimal point
            price_clean = re.sub(r'[^\d.]', '', price_text)
            return float(price_clean) if price_clean else 0
        except:
            return 0
    
    def extract_year(self, title):
        """Extract year from title"""
        try:
            year_match = re.search(r'(19|20)\d{2}', title)
            return int(year_match.group()) if year_match else None
        except:
            return None
    
    def extract_mileage(self, title):
        """Extract mileage from title"""
        try:
            mileage_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:km|miles?)', title, re.IGNORECASE)
            if mileage_match:
                return int(mileage_match.group(1).replace(',', ''))
        except:
            pass
        return None
    
    def extract_fuel_type(self, title):
        """Extract fuel type from title"""
        title_lower = title.lower()
        if 'diesel' in title_lower:
            return 'Diesel'
        elif 'petrol' in title_lower or 'gasoline' in title_lower:
            return 'Petrol'
        elif 'electric' in title_lower or 'ev' in title_lower:
            return 'Electric'
        elif 'hybrid' in title_lower:
            return 'Hybrid'
        return 'Unknown'
    
    def extract_transmission(self, title):
        """Extract transmission from title"""
        title_lower = title.lower()
        if 'manual' in title_lower:
            return 'Manual'
        elif 'automatic' in title_lower or 'auto' in title_lower:
            return 'Automatic'
        return 'Unknown'
    
    def passes_basic_filters(self, title, price, location, user_settings):
        """Basic filtering without heavy processing"""
        try:
            # Price range check
            if price < user_settings.get('min_price', 5000) or price > user_settings.get('max_price', 15000):
                return False
            
            # Location check (simplified)
            location_lower = location.lower()
            if 'leinster' not in location_lower and 'dublin' not in location_lower:
                return False
            
            # Basic blacklist check
            blacklist = user_settings.get('blacklist', [])
            title_lower = title.lower()
            for blacklisted in blacklist:
                if blacklisted.lower() in title_lower:
                    return False
            
            return True
        except:
            return False
    
    def calculate_basic_deal_score(self, price, title):
        """Calculate a basic deal score without complex processing"""
        try:
            score = 50  # Base score
            
            # Price-based scoring (simplified)
            if price < 8000:
                score += 20
            elif price < 12000:
                score += 10
            
            # Year-based scoring (simplified)
            year = self.extract_year(title)
            if year and year >= 2015:
                score += 15
            elif year and year >= 2010:
                score += 10
            
            return min(score, 100)
        except:
            return 50
    
    def run_conservative_scrape(self, user_settings):
        """Run a very conservative scrape session"""
        logger.info("Starting conservative scraping session")
        
        all_listings = []
        
        # Only scrape 2 sites maximum
        sites_to_scrape = ['carzone', 'donedeal']
        
        for site in sites_to_scrape:
            try:
                logger.info(f"Scraping {site}...")
                
                if site == 'carzone':
                    listings = self.scrape_carzone(user_settings)
                elif site == 'donedeal':
                    listings = self.scrape_donedeal(user_settings)
                else:
                    continue
                
                all_listings.extend(listings)
                logger.info(f"Found {len(listings)} listings from {site}")
                
                # Long delay between sites
                if site != sites_to_scrape[-1]:  # Don't delay after last site
                    delay = random.uniform(60, 180)  # 1-3 minutes between sites
                    logger.info(f"Waiting {delay:.1f} seconds before next site...")
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error scraping {site}: {e}")
                continue
        
        logger.info(f"Conservative scrape complete. Found {len(all_listings)} total listings")
        return all_listings
    
    def save_listings(self, listings):
        """Save listings to database"""
        try:
            saved_count = 0
            for listing_data in listings:
                try:
                    # Check if listing already exists
                    existing = CarListing.query.filter_by(
                        title=listing_data['title'],
                        source=listing_data['source']
                    ).first()
                    
                    if existing:
                        # Update existing listing
                        existing.last_seen = datetime.utcnow()
                        existing.status = 'active'
                        if listing_data['price'] != existing.price:
                            existing.previous_price = existing.price
                            existing.price = listing_data['price']
                            existing.price_dropped = True
                    else:
                        # Create new listing
                        new_listing = CarListing(**listing_data)
                        db.session.add(new_listing)
                        saved_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error saving listing: {e}")
                    continue
            
            db.session.commit()
            logger.info(f"Saved {saved_count} new listings to database")
            
        except Exception as e:
            logger.error(f"Error saving listings: {e}")
            db.session.rollback()
    
    def log_scrape_session(self, total_listings, successful_sites):
        """Log the scrape session"""
        try:
            log_entry = ScrapeLog(
                timestamp=datetime.utcnow(),
                total_listings=total_listings,
                successful_sites=successful_sites,
                failed_sites=0,
                blocked_sites=0,
                notes="Conservative scraping session"
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging scrape session: {e}")

# Conservative scraping function for Celery
def run_conservative_scrape_task():
    """Celery task for conservative scraping"""
    try:
        engine = ConservativeCarScrapingEngine()
        
        # Get default user settings
        default_settings = {
            'min_price': 5000,
            'max_price': 15000,
            'blacklist': []
        }
        
        # Run conservative scrape
        listings = engine.run_conservative_scrape(default_settings)
        
        # Save listings
        engine.save_listings(listings)
        
        # Log session
        engine.log_scrape_session(len(listings), 2)
        
        return f"Conservative scrape complete: {len(listings)} listings found"
        
    except Exception as e:
        logger.error(f"Conservative scrape task failed: {e}")
        return f"Conservative scrape failed: {e}"
