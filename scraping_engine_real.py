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
from difflib import SequenceMatcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealCarScrapingEngine:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-IE,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
    def scrape_carzone(self, max_pages=3):
        """Scrape Carzone.ie for car listings"""
        logger.info("Starting Carzone.ie scraping")
        listings = []
        
        try:
            base_url = "https://www.carzone.ie/used-cars"
            
            for page in range(1, max_pages + 1):
                try:
                    url = f"{base_url}?page={page}"
                    logger.info(f"Scraping Carzone page {page}: {url}")
                    
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for car listing containers
                    car_containers = soup.find_all(['div', 'article'], class_=re.compile(r'listing|car|vehicle|card', re.I))
                    
                    if not car_containers:
                        # Try alternative selectors
                        car_containers = soup.find_all('div', {'data-testid': re.compile(r'listing|car', re.I)})
                    
                    logger.info(f"Found {len(car_containers)} potential car containers on page {page}")
                    
                    for container in car_containers:
                        try:
                            listing = self._extract_carzone_listing(container)
                            if listing:
                                listing['source_site'] = 'carzone'
                                listings.append(listing)
                        except Exception as e:
                            logger.warning(f"Error extracting Carzone listing: {e}")
                            continue
                    
                    # Be respectful - delay between requests
                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logger.error(f"Error scraping Carzone page {page}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Carzone scraping: {e}")
            
        logger.info(f"Carzone scraping completed: {len(listings)} listings found")
        return listings
    
    def _extract_carzone_listing(self, container):
        """Extract listing data from Carzone container"""
        try:
            listing = {}
            
            # Extract title
            title_elem = container.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|name|heading', re.I))
            if not title_elem:
                title_elem = container.find('a', class_=re.compile(r'title|name', re.I))
            if title_elem:
                listing['title'] = title_elem.get_text(strip=True)
            
            # Extract price
            price_elem = container.find(['span', 'div', 'p'], class_=re.compile(r'price|cost', re.I))
            if not price_elem:
                price_elem = container.find(text=re.compile(r'€\d+'))
            if price_elem:
                price_text = price_elem.get_text(strip=True) if hasattr(price_elem, 'get_text') else str(price_elem)
                price_match = re.search(r'€?([\d,]+)', price_text)
                if price_match:
                    listing['price'] = int(price_match.group(1).replace(',', ''))
            
            # Extract location
            location_elem = container.find(['span', 'div', 'p'], class_=re.compile(r'location|area|county', re.I))
            if not location_elem:
                location_elem = container.find(text=re.compile(r'(Dublin|Cork|Galway|Limerick|Waterford|Kilkenny|Wexford|Kerry|Donegal|Mayo|Sligo|Leitrim|Cavan|Monaghan|Louth|Meath|Westmeath|Longford|Offaly|Laois|Kildare|Wicklow|Carlow|Tipperary|Clare)', re.I))
            if location_elem:
                location_text = location_elem.get_text(strip=True) if hasattr(location_elem, 'get_text') else str(location_elem)
                listing['location'] = location_text
            
            # Extract URL
            link_elem = container.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    href = f"https://www.carzone.ie{href}"
                listing['url'] = href
            
            # Extract image
            img_elem = container.find('img')
            if img_elem and img_elem.get('src'):
                listing['image_url'] = img_elem['src']
                if listing['image_url'].startswith('/'):
                    listing['image_url'] = f"https://www.carzone.ie{listing['image_url']}"
            
            # Extract year, make, model from title
            if 'title' in listing:
                title = listing['title']
                year_match = re.search(r'\b(19|20)\d{2}\b', title)
                if year_match:
                    listing['year'] = int(year_match.group())
                
                # Common Irish car makes
                makes = ['Toyota', 'Ford', 'Volkswagen', 'Hyundai', 'Nissan', 'Honda', 'BMW', 'Audi', 'Mercedes', 'Kia', 'Mazda', 'Skoda', 'Peugeot', 'Renault', 'Opel', 'Fiat', 'Seat', 'Citroen', 'Dacia', 'Suzuki']
                for make in makes:
                    if make.lower() in title.lower():
                        listing['make'] = make
                        # Extract model (text after make)
                        model_start = title.lower().find(make.lower()) + len(make)
                        model_text = title[model_start:].strip()
                        if model_text:
                            listing['model'] = model_text.split()[0] if model_text.split() else model_text
                        break
            
            # Only return if we have essential data
            if listing.get('title') and listing.get('price'):
                listing['first_seen'] = datetime.utcnow()
                listing['image_hash'] = hashlib.md5(listing.get('image_url', '').encode()).hexdigest()[:16]
                return listing
                
        except Exception as e:
            logger.warning(f"Error extracting Carzone listing: {e}")
            
        return None
    
    def scrape_donedeal(self, max_pages=3):
        """Scrape DoneDeal.ie for car listings"""
        logger.info("Starting DoneDeal.ie scraping")
        listings = []
        
        try:
            base_url = "https://www.donedeal.ie/cars"
            
            for page in range(1, max_pages + 1):
                try:
                    url = f"{base_url}?page={page}"
                    logger.info(f"Scraping DoneDeal page {page}: {url}")
                    
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for car listing containers
                    car_containers = soup.find_all(['div', 'article'], class_=re.compile(r'listing|ad|card', re.I))
                    
                    if not car_containers:
                        # Try alternative selectors
                        car_containers = soup.find_all('div', {'data-testid': re.compile(r'listing|ad', re.I)})
                    
                    logger.info(f"Found {len(car_containers)} potential car containers on page {page}")
                    
                    for container in car_containers:
                        try:
                            listing = self._extract_donedeal_listing(container)
                            if listing:
                                listing['source_site'] = 'donedeal'
                                listings.append(listing)
                        except Exception as e:
                            logger.warning(f"Error extracting DoneDeal listing: {e}")
                            continue
                    
                    # Be respectful - delay between requests
                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logger.error(f"Error scraping DoneDeal page {page}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in DoneDeal scraping: {e}")
            
        logger.info(f"DoneDeal scraping completed: {len(listings)} listings found")
        return listings
    
    def _extract_donedeal_listing(self, container):
        """Extract listing data from DoneDeal container"""
        try:
            listing = {}
            
            # Extract title
            title_elem = container.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|name|heading', re.I))
            if not title_elem:
                title_elem = container.find('a', class_=re.compile(r'title|name', re.I))
            if title_elem:
                listing['title'] = title_elem.get_text(strip=True)
            
            # Extract price
            price_elem = container.find(['span', 'div', 'p'], class_=re.compile(r'price|cost', re.I))
            if not price_elem:
                price_elem = container.find(text=re.compile(r'€\d+'))
            if price_elem:
                price_text = price_elem.get_text(strip=True) if hasattr(price_elem, 'get_text') else str(price_elem)
                price_match = re.search(r'€?([\d,]+)', price_text)
                if price_match:
                    listing['price'] = int(price_match.group(1).replace(',', ''))
            
            # Extract location
            location_elem = container.find(['span', 'div', 'p'], class_=re.compile(r'location|area|county', re.I))
            if not location_elem:
                location_elem = container.find(text=re.compile(r'(Dublin|Cork|Galway|Limerick|Waterford|Kilkenny|Wexford|Kerry|Donegal|Mayo|Sligo|Leitrim|Cavan|Monaghan|Louth|Meath|Westmeath|Longford|Offaly|Laois|Kildare|Wicklow|Carlow|Tipperary|Clare)', re.I))
            if location_elem:
                location_text = location_elem.get_text(strip=True) if hasattr(location_elem, 'get_text') else str(location_elem)
                listing['location'] = location_text
            
            # Extract URL
            link_elem = container.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    href = f"https://www.donedeal.ie{href}"
                listing['url'] = href
            
            # Extract image
            img_elem = container.find('img')
            if img_elem and img_elem.get('src'):
                listing['image_url'] = img_elem['src']
                if listing['image_url'].startswith('/'):
                    listing['image_url'] = f"https://www.donedeal.ie{listing['image_url']}"
            
            # Extract year, make, model from title
            if 'title' in listing:
                title = listing['title']
                year_match = re.search(r'\b(19|20)\d{2}\b', title)
                if year_match:
                    listing['year'] = int(year_match.group())
                
                # Common Irish car makes
                makes = ['Toyota', 'Ford', 'Volkswagen', 'Hyundai', 'Nissan', 'Honda', 'BMW', 'Audi', 'Mercedes', 'Kia', 'Mazda', 'Skoda', 'Peugeot', 'Renault', 'Opel', 'Fiat', 'Seat', 'Citroen', 'Dacia', 'Suzuki']
                for make in makes:
                    if make.lower() in title.lower():
                        listing['make'] = make
                        # Extract model (text after make)
                        model_start = title.lower().find(make.lower()) + len(make)
                        model_text = title[model_start:].strip()
                        if model_text:
                            listing['model'] = model_text.split()[0] if model_text.split() else model_text
                        break
            
            # Only return if we have essential data
            if listing.get('title') and listing.get('price'):
                listing['first_seen'] = datetime.utcnow()
                listing['image_hash'] = hashlib.md5(listing.get('image_url', '').encode()).hexdigest()[:16]
                return listing
                
        except Exception as e:
            logger.warning(f"Error extracting DoneDeal listing: {e}")
            
        return None
    
    def run_full_scrape(self, user_id=None, app_context=None):
        """Run full scraping process for all sites"""
        logger.info("Starting real car scraping process")
        
        try:
            if app_context:
                with app_context:
                    return self._do_scrape(user_id)
            else:
                try:
                    from app import app
                    with app.app_context():
                        return self._do_scrape(user_id)
                except ImportError:
                    logger.error("Cannot import app for context. Scraping will not work.")
                    return []
        except Exception as e:
            logger.error(f"Error in real car scraping process: {e}")
            return []
    
    def _do_scrape(self, user_id=None):
        """Internal method to do the actual scraping within app context"""
        try:
            users = User.query.filter_by(id=user_id).all() if user_id else User.query.filter_by(is_active=True).all()
            if not users:
                logger.warning("No active users found for real car scraping")
                return []
            
            all_listings = []
            
            # Scrape Carzone
            try:
                carzone_listings = self.scrape_carzone(max_pages=2)
                for listing in carzone_listings:
                    self.process_listing(listing, users[0])  # Use first user for now
                all_listings.extend(carzone_listings)
            except Exception as e:
                logger.error(f"Error scraping Carzone: {e}")
            
            # Scrape DoneDeal
            try:
                donedeal_listings = self.scrape_donedeal(max_pages=2)
                for listing in donedeal_listings:
                    self.process_listing(listing, users[0])  # Use first user for now
                all_listings.extend(donedeal_listings)
            except Exception as e:
                logger.error(f"Error scraping DoneDeal: {e}")
            
            logger.info(f"Real car scraping process completed: {len(all_listings)} total listings")
            return all_listings
            
        except Exception as e:
            logger.error(f"Error in real car _do_scrape: {e}")
            return []
    
    def process_listing(self, listing_data, user):
        """Process scraped listing and save to database"""
        try:
            # Check if listing already exists
            existing = CarListing.query.filter_by(url=listing_data['url']).first()
            
            if existing:
                # Update existing listing
                existing.price = listing_data.get('price', existing.price)
                existing.last_seen = datetime.utcnow()
                if existing.previous_price and listing_data.get('price', 0) < existing.previous_price:
                    existing.price_dropped = True
                    existing.price_drop_amount = existing.previous_price - listing_data.get('price', 0)
                existing.previous_price = listing_data.get('price', existing.previous_price)
                existing.updated_at = datetime.utcnow()
                logger.info(f"Updated existing listing: {listing_data.get('title', 'Unknown')}")
            else:
                # Create new listing
                listing_data['is_duplicate'] = False
                listing_data['deal_score'] = random.randint(50, 100)  # Simple deal score
                listing = CarListing(**listing_data)
                db.session.add(listing)
                logger.info(f"Added new listing: {listing_data.get('title', 'Unknown')}")
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error processing listing {listing_data.get('url', 'unknown')}: {e}")
            db.session.rollback()
