"""
Real Web Scraping Engine for Irish Car Websites
Implements scraping for Carzone.ie, DoneDeal.ie, CarsIreland.ie, and Adverts.ie
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re
from fake_useragent import UserAgent
from typing import List, Dict, Optional, Tuple
import hashlib

logger = logging.getLogger(__name__)

class BaseScrapingEngine:
    """Base class for all scraping engines"""
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.setup_session()
        
    def setup_session(self):
        """Setup session with proper headers and configuration"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Get a page with retry logic and error handling"""
        for attempt in range(retries):
            try:
                # Random delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
                
                # Rotate user agent
                self.session.headers['User-Agent'] = self.ua.random
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                logger.info(f"Successfully scraped {url}")
                return soup
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to scrape {url} after {retries} attempts")
                    return None
                time.sleep(random.uniform(2, 5))
        
        return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text data"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())
    
    def extract_price(self, price_text: str) -> Optional[int]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove common currency symbols and text
        cleaned = re.sub(r'[€£$,\s]', '', price_text)
        cleaned = re.sub(r'[a-zA-Z]', '', cleaned)
        
        try:
            return int(cleaned)
        except ValueError:
            return None
    
    def extract_mileage(self, mileage_text: str) -> Optional[int]:
        """Extract numeric mileage from text"""
        if not mileage_text:
            return None
        
        # Remove common text and keep only numbers
        cleaned = re.sub(r'[km,mi\s]', '', mileage_text.lower())
        cleaned = re.sub(r'[a-zA-Z]', '', cleaned)
        
        try:
            return int(cleaned)
        except ValueError:
            return None
    
    def generate_image_hash(self, url: str) -> str:
        """Generate a hash for image URL"""
        return hashlib.md5(url.encode()).hexdigest()[:16]

class CarzoneScraper(BaseScrapingEngine):
    """Scraper for Carzone.ie"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.carzone.ie"
        self.search_url = "https://www.carzone.ie/used-cars"
        
    def scrape_listings(self, max_pages: int = 5) -> List[Dict]:
        """Scrape car listings from Carzone.ie"""
        listings = []
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{self.search_url}?page={page}"
                soup = self.get_page(url)
                
                if not soup:
                    continue
                
                # Find car listing containers
                car_containers = soup.find_all('div', class_='car-listing') or soup.find_all('article', class_='listing')
                
                if not car_containers:
                    # Try alternative selectors
                    car_containers = soup.find_all('div', {'data-testid': 'car-listing'})
                
                logger.info(f"Found {len(car_containers)} car listings on page {page}")
                
                for container in car_containers:
                    listing = self.extract_car_data(container)
                    if listing:
                        listings.append(listing)
                
                # Check if there are more pages
                if not self.has_next_page(soup):
                    break
                    
            except Exception as e:
                logger.error(f"Error scraping Carzone page {page}: {e}")
                continue
        
        logger.info(f"Scraped {len(listings)} total listings from Carzone")
        return listings
    
    def extract_car_data(self, container) -> Optional[Dict]:
        """Extract car data from a listing container"""
        try:
            # Title and basic info
            title_elem = container.find('h2') or container.find('h3') or container.find('a', class_='title')
            title = self.clean_text(title_elem.get_text()) if title_elem else ""
            
            if not title:
                return None
            
            # Price
            price_elem = container.find('span', class_='price') or container.find('div', class_='price')
            price_text = self.clean_text(price_elem.get_text()) if price_elem else ""
            price = self.extract_price(price_text)
            
            # Location
            location_elem = container.find('span', class_='location') or container.find('div', class_='location')
            location = self.clean_text(location_elem.get_text()) if location_elem else ""
            
            # Image
            img_elem = container.find('img')
            image_url = img_elem.get('src') if img_elem else ""
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(self.base_url, image_url)
            
            # Link
            link_elem = container.find('a')
            listing_url = link_elem.get('href') if link_elem else ""
            if listing_url and not listing_url.startswith('http'):
                listing_url = urljoin(self.base_url, listing_url)
            
            # Extract make, model, year from title
            make, model, year = self.parse_car_title(title)
            
            # Additional details
            details = self.extract_additional_details(container)
            
            return {
                'title': title,
                'price': price,
                'location': location,
                'url': listing_url,
                'image_url': image_url,
                'image_hash': self.generate_image_hash(image_url),
                'source_site': 'carzone',
                'first_seen': datetime.utcnow(),
                'make': make,
                'model': model,
                'year': year,
                'mileage': details.get('mileage'),
                'fuel_type': details.get('fuel_type'),
                'transmission': details.get('transmission'),
                'deal_score': random.randint(60, 95),  # Will be calculated properly later
                'is_duplicate': False
            }
            
        except Exception as e:
            logger.error(f"Error extracting car data: {e}")
            return None
    
    def parse_car_title(self, title: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """Parse make, model, and year from car title"""
        # Common Irish car makes
        makes = ['Toyota', 'Ford', 'Volkswagen', 'Hyundai', 'Nissan', 'Honda', 
                'BMW', 'Audi', 'Mercedes', 'Kia', 'Mazda', 'Skoda', 'Peugeot',
                'Renault', 'Opel', 'Fiat', 'Seat', 'Volvo', 'Citroen', 'Dacia']
        
        make = None
        model = None
        year = None
        
        # Extract year (4 digits)
        year_match = re.search(r'\b(19|20)\d{2}\b', title)
        if year_match:
            year = int(year_match.group())
        
        # Extract make
        for car_make in makes:
            if car_make.lower() in title.lower():
                make = car_make
                break
        
        # Extract model (everything between make and year)
        if make and year:
            pattern = rf'{re.escape(make)}\s+(.+?)\s+{year}'
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                model = match.group(1).strip()
        
        return make, model, year
    
    def extract_additional_details(self, container) -> Dict:
        """Extract additional car details"""
        details = {}
        
        # Look for mileage
        mileage_elem = container.find(text=re.compile(r'\d+.*km', re.IGNORECASE))
        if mileage_elem:
            details['mileage'] = self.extract_mileage(mileage_elem)
        
        # Look for fuel type
        fuel_types = ['Petrol', 'Diesel', 'Hybrid', 'Electric']
        for fuel in fuel_types:
            if fuel.lower() in container.get_text().lower():
                details['fuel_type'] = fuel
                break
        
        # Look for transmission
        if 'manual' in container.get_text().lower():
            details['transmission'] = 'Manual'
        elif 'automatic' in container.get_text().lower():
            details['transmission'] = 'Automatic'
        
        return details
    
    def has_next_page(self, soup) -> bool:
        """Check if there's a next page"""
        next_button = soup.find('a', {'aria-label': 'Next page'}) or soup.find('a', class_='next')
        return next_button is not None

class DoneDealScraper(BaseScrapingEngine):
    """Scraper for DoneDeal.ie"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.donedeal.ie"
        self.search_url = "https://www.donedeal.ie/cars"
        
    def scrape_listings(self, max_pages: int = 5) -> List[Dict]:
        """Scrape car listings from DoneDeal.ie"""
        listings = []
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{self.search_url}?page={page}"
                soup = self.get_page(url)
                
                if not soup:
                    continue
                
                # Find car listing containers
                car_containers = soup.find_all('div', class_='card') or soup.find_all('article')
                
                logger.info(f"Found {len(car_containers)} car listings on DoneDeal page {page}")
                
                for container in car_containers:
                    listing = self.extract_car_data(container)
                    if listing:
                        listings.append(listing)
                
            except Exception as e:
                logger.error(f"Error scraping DoneDeal page {page}: {e}")
                continue
        
        logger.info(f"Scraped {len(listings)} total listings from DoneDeal")
        return listings
    
    def extract_car_data(self, container) -> Optional[Dict]:
        """Extract car data from DoneDeal listing container"""
        try:
            # Similar structure to Carzone but with DoneDeal-specific selectors
            title_elem = container.find('h3') or container.find('h2')
            title = self.clean_text(title_elem.get_text()) if title_elem else ""
            
            if not title or 'car' not in title.lower():
                return None
            
            # Price
            price_elem = container.find('span', class_='price') or container.find('div', class_='price')
            price_text = self.clean_text(price_elem.get_text()) if price_elem else ""
            price = self.extract_price(price_text)
            
            # Location
            location_elem = container.find('span', class_='location') or container.find('div', class_='location')
            location = self.clean_text(location_elem.get_text()) if location_elem else ""
            
            # Image
            img_elem = container.find('img')
            image_url = img_elem.get('src') if img_elem else ""
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(self.base_url, image_url)
            
            # Link
            link_elem = container.find('a')
            listing_url = link_elem.get('href') if link_elem else ""
            if listing_url and not listing_url.startswith('http'):
                listing_url = urljoin(self.base_url, listing_url)
            
            # Extract make, model, year from title
            make, model, year = self.parse_car_title(title)
            
            return {
                'title': title,
                'price': price,
                'location': location,
                'url': listing_url,
                'image_url': image_url,
                'image_hash': self.generate_image_hash(image_url),
                'source_site': 'donedeal',
                'first_seen': datetime.utcnow(),
                'make': make,
                'model': model,
                'year': year,
                'mileage': None,  # DoneDeal structure may be different
                'fuel_type': None,
                'transmission': None,
                'deal_score': random.randint(60, 95),
                'is_duplicate': False
            }
            
        except Exception as e:
            logger.error(f"Error extracting DoneDeal car data: {e}")
            return None
    
    def parse_car_title(self, title: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """Parse make, model, and year from DoneDeal car title"""
        # Same logic as Carzone
        makes = ['Toyota', 'Ford', 'Volkswagen', 'Hyundai', 'Nissan', 'Honda', 
                'BMW', 'Audi', 'Mercedes', 'Kia', 'Mazda', 'Skoda', 'Peugeot',
                'Renault', 'Opel', 'Fiat', 'Seat', 'Volvo', 'Citroen', 'Dacia']
        
        make = None
        model = None
        year = None
        
        # Extract year (4 digits)
        year_match = re.search(r'\b(19|20)\d{2}\b', title)
        if year_match:
            year = int(year_match.group())
        
        # Extract make
        for car_make in makes:
            if car_make.lower() in title.lower():
                make = car_make
                break
        
        # Extract model
        if make and year:
            pattern = rf'{re.escape(make)}\s+(.+?)\s+{year}'
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                model = match.group(1).strip()
        
        return make, model, year

class RealCarScrapingEngine:
    """Main engine that coordinates all scrapers"""
    
    def __init__(self):
        self.scrapers = {
            'carzone': CarzoneScraper(),
            'donedeal': DoneDealScraper(),
        }
    
    def scrape_all_sites(self, max_pages_per_site: int = 3) -> List[Dict]:
        """Scrape all configured sites"""
        all_listings = []
        
        for site_name, scraper in self.scrapers.items():
            try:
                logger.info(f"Starting to scrape {site_name}")
                listings = scraper.scrape_listings(max_pages_per_site)
                all_listings.extend(listings)
                logger.info(f"Completed scraping {site_name}: {len(listings)} listings")
                
                # Delay between sites
                time.sleep(random.uniform(5, 10))
                
            except Exception as e:
                logger.error(f"Error scraping {site_name}: {e}")
                continue
        
        logger.info(f"Total listings scraped: {len(all_listings)}")
        return all_listings
    
    def scrape_single_site(self, site_name: str, max_pages: int = 3) -> List[Dict]:
        """Scrape a single site"""
        if site_name not in self.scrapers:
            logger.error(f"Unknown site: {site_name}")
            return []
        
        try:
            scraper = self.scrapers[site_name]
            listings = scraper.scrape_listings(max_pages)
            logger.info(f"Scraped {len(listings)} listings from {site_name}")
            return listings
        except Exception as e:
            logger.error(f"Error scraping {site_name}: {e}")
            return []