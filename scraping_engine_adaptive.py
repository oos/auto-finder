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

class AdaptiveCarScrapingEngine:
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
        
    def scrape_any_car_site(self, url, max_pages=2):
        """Adaptive scraper that can handle any car listing website"""
        logger.info(f"Starting adaptive scraping for: {url}")
        listings = []
        
        try:
            for page in range(1, max_pages + 1):
                try:
                    page_url = f"{url}?page={page}" if '?' not in url else f"{url}&page={page}"
                    logger.info(f"Scraping page {page}: {page_url}")
                    
                    response = self.session.get(page_url, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple strategies to find car listings
                    car_containers = self._find_car_containers(soup)
                    logger.info(f"Found {len(car_containers)} potential car containers on page {page}")
                    
                    for container in car_containers:
                        try:
                            listing = self._extract_adaptive_listing(container, url)
                            if listing:
                                listings.append(listing)
                        except Exception as e:
                            logger.warning(f"Error extracting listing: {e}")
                            continue
                    
                    # Be respectful - delay between requests
                    time.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    logger.error(f"Error scraping page {page}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in adaptive scraping: {e}")
            
        logger.info(f"Adaptive scraping completed: {len(listings)} listings found")
        return listings
    
    def _find_car_containers(self, soup):
        """Find car listing containers using multiple strategies"""
        containers = []
        
        # Strategy 1: Look for common car listing class patterns
        patterns = [
            r'listing', r'car', r'vehicle', r'card', r'ad', r'item', r'product',
            r'result', r'search-result', r'listing-item', r'car-item'
        ]
        
        for pattern in patterns:
            containers.extend(soup.find_all(['div', 'article', 'section'], class_=re.compile(pattern, re.I)))
        
        # Strategy 2: Look for data attributes
        containers.extend(soup.find_all(['div', 'article'], {'data-testid': re.compile(r'listing|car|ad|item', re.I)}))
        
        # Strategy 3: Look for links that might be car listings
        car_links = soup.find_all('a', href=re.compile(r'/(car|vehicle|listing|ad)/', re.I))
        for link in car_links:
            parent = link.find_parent(['div', 'article', 'section'])
            if parent and parent not in containers:
                containers.append(parent)
        
        # Strategy 4: Look for elements containing price patterns
        price_elements = soup.find_all(text=re.compile(r'€\s*\d+'))
        for price_elem in price_elements:
            parent = price_elem.find_parent(['div', 'article', 'section'])
            if parent and parent not in containers:
                containers.append(parent)
        
        # Remove duplicates and return
        seen = set()
        unique_containers = []
        for container in containers:
            container_id = id(container)
            if container_id not in seen:
                seen.add(container_id)
                unique_containers.append(container)
        
        return unique_containers
    
    def _extract_adaptive_listing(self, container, base_url):
        """Extract listing data using adaptive strategies"""
        try:
            listing = {}
            
            # Extract title using multiple strategies
            title = self._extract_text_by_patterns(container, [
                ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
                ['a', {'class': re.compile(r'title|name|heading', re.I)}],
                ['span', {'class': re.compile(r'title|name|heading', re.I)}],
                ['div', {'class': re.compile(r'title|name|heading', re.I)}]
            ])
            if title:
                listing['title'] = title.strip()
            
            # Extract price using multiple strategies
            price = self._extract_price(container)
            if price:
                listing['price'] = price
            
            # Extract location using multiple strategies
            location = self._extract_text_by_patterns(container, [
                ['span', {'class': re.compile(r'location|area|county|address', re.I)}],
                ['div', {'class': re.compile(r'location|area|county|address', re.I)}],
                ['p', {'class': re.compile(r'location|area|county|address', re.I)}]
            ])
            
            # If no location found by class, search for Irish counties in text
            if not location:
                location_text = container.get_text()
                irish_counties = ['Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Kilkenny', 'Wexford', 
                                'Kerry', 'Donegal', 'Mayo', 'Sligo', 'Leitrim', 'Cavan', 'Monaghan', 'Louth', 
                                'Meath', 'Westmeath', 'Longford', 'Offaly', 'Laois', 'Kildare', 'Wicklow', 
                                'Carlow', 'Tipperary', 'Clare']
                for county in irish_counties:
                    if county in location_text:
                        location = county
                        break
            
            if location:
                listing['location'] = location.strip()
            
            # Extract URL
            link = container.find('a', href=True)
            if link:
                href = link['href']
                if href.startswith('/'):
                    href = f"{base_url.rstrip('/')}{href}"
                elif not href.startswith('http'):
                    href = f"{base_url.rstrip('/')}/{href}"
                listing['url'] = href
            
            # Extract image
            img = container.find('img')
            if img and img.get('src'):
                src = img['src']
                if src.startswith('/'):
                    src = f"{base_url.rstrip('/')}{src}"
                elif not src.startswith('http'):
                    src = f"{base_url.rstrip('/')}/{src}"
                listing['image_url'] = src
            
            # Extract year, make, model from title
            if 'title' in listing:
                self._extract_car_details(listing)
            
            # Only return if we have essential data
            if listing.get('title') and listing.get('price'):
                listing['first_seen'] = datetime.utcnow()
                listing['image_hash'] = hashlib.md5(listing.get('image_url', '').encode()).hexdigest()[:16]
                return listing
                
        except Exception as e:
            logger.warning(f"Error extracting adaptive listing: {e}")
            
        return None
    
    def _extract_text_by_patterns(self, container, patterns):
        """Extract text using multiple element patterns"""
        for pattern in patterns:
            if isinstance(pattern, list):
                tag = pattern[0]
                attrs = pattern[1] if len(pattern) > 1 else {}
                elem = container.find(tag, attrs)
                if elem:
                    text = elem.get_text(strip=True)
                    if text:
                        return text
        return None
    
    def _extract_price(self, container):
        """Extract price from container using multiple strategies"""
        # Look for price in text content
        text = container.get_text()
        price_patterns = [
            r'€\s*([\d,]+)',
            r'(\d{1,3}(?:,\d{3})*)\s*€',
            r'Price:\s*€?\s*([\d,]+)',
            r'€\s*(\d+)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    price = int(price_str)
                    if 1000 <= price <= 200000:  # Reasonable car price range
                        return price
                except ValueError:
                    continue
        
        # Look for price in specific elements
        price_elem = container.find(['span', 'div', 'p'], class_=re.compile(r'price|cost|amount', re.I))
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            for pattern in price_patterns:
                match = re.search(pattern, price_text)
                if match:
                    try:
                        price_str = match.group(1).replace(',', '')
                        price = int(price_str)
                        if 1000 <= price <= 200000:
                            return price
                    except ValueError:
                        continue
        
        return None
    
    def _extract_car_details(self, listing):
        """Extract year, make, model from title"""
        title = listing['title']
        
        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', title)
        if year_match:
            listing['year'] = int(year_match.group())
        
        # Common Irish car makes
        makes = ['Toyota', 'Ford', 'Volkswagen', 'Hyundai', 'Nissan', 'Honda', 'BMW', 'Audi', 
                'Mercedes', 'Kia', 'Mazda', 'Skoda', 'Peugeot', 'Renault', 'Opel', 'Fiat', 
                'Seat', 'Citroen', 'Dacia', 'Suzuki', 'Volvo', 'Jaguar', 'Land Rover', 'Mini']
        
        for make in makes:
            if make.lower() in title.lower():
                listing['make'] = make
                # Extract model (text after make)
                model_start = title.lower().find(make.lower()) + len(make)
                model_text = title[model_start:].strip()
                if model_text:
                    # Take first word as model
                    model = model_text.split()[0] if model_text.split() else model_text
                    listing['model'] = model
                break
    
    def run_full_scrape(self, user_id=None, app_context=None):
        """Run full scraping process for multiple Irish car sites"""
        logger.info("Starting adaptive car scraping process")
        
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
            logger.error(f"Error in adaptive car scraping process: {e}")
            return []
    
    def _do_scrape(self, user_id=None):
        """Internal method to do the actual scraping within app context"""
        try:
            users = User.query.filter_by(id=user_id).all() if user_id else User.query.filter_by(is_active=True).all()
            if not users:
                logger.warning("No active users found for adaptive car scraping")
                return []
            
            all_listings = []
            
            # List of Irish car websites to scrape
            car_sites = [
                "https://www.carzone.ie/used-cars",
                "https://www.donedeal.ie/cars",
                "https://www.carsireland.ie/used-cars",
                "https://www.autotrader.ie/used-cars"
            ]
            
            for site_url in car_sites:
                try:
                    logger.info(f"Scraping {site_url}")
                    site_listings = self.scrape_any_car_site(site_url, max_pages=1)
                    
                    # Determine source site from URL
                    if 'carzone' in site_url:
                        source_site = 'carzone'
                    elif 'donedeal' in site_url:
                        source_site = 'donedeal'
                    elif 'carsireland' in site_url:
                        source_site = 'carsireland'
                    elif 'autotrader' in site_url:
                        source_site = 'autotrader'
                    else:
                        source_site = 'unknown'
                    
                    for listing in site_listings:
                        listing['source_site'] = source_site
                        self.process_listing(listing, users[0])
                    
                    all_listings.extend(site_listings)
                    logger.info(f"Scraped {len(site_listings)} listings from {site_url}")
                    
                except Exception as e:
                    logger.error(f"Error scraping {site_url}: {e}")
                    continue
            
            logger.info(f"Adaptive car scraping process completed: {len(all_listings)} total listings")
            return all_listings
            
        except Exception as e:
            logger.error(f"Error in adaptive _do_scrape: {e}")
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
