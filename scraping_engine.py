import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import requests
import time
import random
import hashlib
import imagehash
from PIL import Image
from io import BytesIO
from fake_useragent import UserAgent
from models import db, CarListing, ScrapeLog, User, UserSettings
from datetime import datetime, timedelta
import json
import re
from difflib import SequenceMatcher
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CarScrapingEngine:
    def __init__(self):
        self.ua = UserAgent()
        self.driver = None
        self.session = requests.Session()
        
    def setup_driver(self):
        """Initialize undetected Chrome driver"""
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument(f'--user-agent={self.ua.random}')
            
            self.driver = uc.Chrome(options=options)
            self.driver.implicitly_wait(10)
            return True
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            return False
    
    def close_driver(self):
        """Close the Chrome driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def get_image_hash(self, image_url):
        """Calculate perceptual hash of an image for duplicate detection"""
        try:
            response = self.session.get(image_url, timeout=10)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                return str(imagehash.average_hash(image))
        except Exception as e:
            logger.warning(f"Failed to hash image {image_url}: {e}")
        return None
    
    def calculate_title_similarity(self, title1, title2):
        """Calculate similarity between two titles using SequenceMatcher"""
        return SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
    
    def is_duplicate(self, new_listing, existing_listings):
        """Check if a new listing is a duplicate of existing ones"""
        for existing in existing_listings:
            # Check title similarity
            title_similarity = self.calculate_title_similarity(
                new_listing['title'], existing.title
            )
            
            # Check price difference (within €50)
            price_diff = abs(new_listing['price'] - existing.price)
            
            # Check image hash if both have images
            image_match = False
            if (new_listing.get('image_hash') and existing.image_hash and 
                new_listing['image_hash'] == existing.image_hash):
                image_match = True
            
            # Consider duplicate if:
            # - Title similarity > 0.8 AND price difference < €50
            # - OR image hash matches
            if (title_similarity > 0.8 and price_diff < 50) or image_match:
                return True, existing.id
        
        return False, None
    
    def extract_car_details(self, title, description=""):
        """Extract car details from title and description"""
        details = {
            'make': None,
            'model': None,
            'year': None,
            'mileage': None,
            'fuel_type': None,
            'transmission': None
        }
        
        text = f"{title} {description}".lower()
        
        # Extract year (4 digits between 1990-2024)
        year_match = re.search(r'\b(19[9]\d|20[0-2]\d)\b', text)
        if year_match:
            details['year'] = int(year_match.group(1))
        
        # Extract mileage
        mileage_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*miles?',
            r'(\d{1,3}(?:,\d{3})*)\s*km',
            r'(\d{1,3}(?:,\d{3})*)\s*k\s*miles?',
            r'(\d{1,3}(?:,\d{3})*)\s*k\s*km'
        ]
        
        for pattern in mileage_patterns:
            match = re.search(pattern, text)
            if match:
                mileage_str = match.group(1).replace(',', '')
                details['mileage'] = int(mileage_str)
                break
        
        # Extract fuel type
        fuel_types = ['petrol', 'diesel', 'electric', 'hybrid', 'lpg', 'cng']
        for fuel in fuel_types:
            if fuel in text:
                details['fuel_type'] = fuel.title()
                break
        
        # Extract transmission
        if 'manual' in text:
            details['transmission'] = 'Manual'
        elif 'automatic' in text or 'auto' in text:
            details['transmission'] = 'Automatic'
        
        # Extract make and model (basic implementation)
        common_makes = [
            'toyota', 'ford', 'volkswagen', 'bmw', 'mercedes', 'audi',
            'nissan', 'honda', 'hyundai', 'kia', 'skoda', 'seat',
            'peugeot', 'renault', 'citroen', 'opel', 'fiat', 'mazda',
            'subaru', 'mitsubishi', 'suzuki', 'dacia', 'volvo', 'saab'
        ]
        
        for make in common_makes:
            if make in text:
                details['make'] = make.title()
                # Try to extract model (next word after make)
                make_index = text.find(make)
                words_after = text[make_index:].split()[:3]
                if len(words_after) > 1:
                    details['model'] = words_after[1].title()
                break
        
        return details
    
    def calculate_deal_score(self, listing, user_settings):
        """Calculate deal score based on user-defined weights"""
        score = 0.0
        
        # Price vs Market Value (25% weight)
        # This is a simplified calculation - in production you'd use actual market data
        if listing.get('price') and listing.get('year'):
            # Rough market value estimation based on year
            current_year = datetime.now().year
            age = current_year - listing['year']
            estimated_market_value = max(1000, 20000 - (age * 1500))
            price_ratio = min(1.0, estimated_market_value / listing['price'])
            score += (price_ratio * user_settings.weight_price_vs_market)
        
        # Mileage vs Year (20% weight)
        if listing.get('mileage') and listing.get('year'):
            current_year = datetime.now().year
            age = current_year - listing['year']
            expected_mileage = age * 12000  # 12k miles per year average
            if listing['mileage'] < expected_mileage:
                mileage_ratio = min(1.0, expected_mileage / listing['mileage'])
                score += (mileage_ratio * user_settings.weight_mileage_vs_year)
        
        # CO2/Tax Band (15% weight) - simplified
        if listing.get('fuel_type'):
            if listing['fuel_type'].lower() in ['electric', 'hybrid']:
                score += user_settings.weight_co2_tax_band
            elif listing['fuel_type'].lower() == 'diesel':
                score += user_settings.weight_co2_tax_band * 0.7
            else:  # petrol
                score += user_settings.weight_co2_tax_band * 0.5
        
        # Popularity/Rarity (15% weight) - simplified
        # In production, you'd use actual market data
        score += user_settings.weight_popularity_rarity * 0.5
        
        # Price Dropped (10% weight)
        if listing.get('price_dropped'):
            score += user_settings.weight_price_dropped
        
        # Location Match (10% weight)
        if listing.get('location'):
            approved_locations = user_settings.get_approved_locations()
            location_match = any(loc.lower() in listing['location'].lower() 
                               for loc in approved_locations)
            if location_match:
                score += user_settings.weight_location_match
        
        # Listing Freshness (5% weight)
        if listing.get('first_seen'):
            days_old = (datetime.utcnow() - listing['first_seen']).days
            freshness_ratio = max(0, 1 - (days_old / 30))  # Fresh for 30 days
            score += (freshness_ratio * user_settings.weight_listing_freshness)
        
        return min(100.0, max(0.0, score))
    
    def scrape_carzone(self, max_pages=10):
        """Scrape Carzone.ie"""
        logger.info("Starting Carzone scraping")
        
        try:
            if not self.driver:
                if not self.setup_driver():
                    return []
            
            listings = []
            base_url = "https://www.carzone.ie/used-cars"
            
            for page in range(1, max_pages + 1):
                try:
                    url = f"{base_url}?page={page}"
                    logger.info(f"Scraping Carzone page {page}: {url}")
                    
                    self.driver.get(url)
                    time.sleep(random.uniform(2, 5))
                    
                    # Wait for listings to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "listing-item"))
                    )
                    
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    listing_items = soup.find_all('div', class_='listing-item')
                    
                    if not listing_items:
                        logger.info(f"No listings found on page {page}, stopping")
                        break
                    
                    for item in listing_items:
                        try:
                            listing = self.parse_carzone_listing(item)
                            if listing:
                                listings.append(listing)
                        except Exception as e:
                            logger.warning(f"Error parsing Carzone listing: {e}")
                            continue
                    
                    # Random delay between pages
                    time.sleep(random.uniform(3, 7))
                    
                except TimeoutException:
                    logger.warning(f"Timeout on Carzone page {page}")
                    break
                except Exception as e:
                    logger.error(f"Error scraping Carzone page {page}: {e}")
                    break
            
            logger.info(f"Carzone scraping completed: {len(listings)} listings found")
            return listings
            
        except Exception as e:
            logger.error(f"Error in Carzone scraping: {e}")
            return []
    
    def parse_carzone_listing(self, item):
        """Parse a single Carzone listing"""
        try:
            # Extract basic info
            title_elem = item.find('h3', class_='listing-title')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Extract price
            price_elem = item.find('span', class_='price')
            if not price_elem:
                return None
            
            price_text = price_elem.get_text(strip=True)
            price_match = re.search(r'€?([\d,]+)', price_text.replace(',', ''))
            if not price_match:
                return None
            
            price = int(price_match.group(1))
            
            # Extract location
            location_elem = item.find('span', class_='location')
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Extract URL
            link_elem = item.find('a', href=True)
            url = f"https://www.carzone.ie{link_elem['href']}" if link_elem else ""
            
            # Extract image
            img_elem = item.find('img', src=True)
            image_url = img_elem['src'] if img_elem else None
            
            # Calculate image hash
            image_hash = None
            if image_url:
                image_hash = self.get_image_hash(image_url)
            
            # Extract car details
            description = ""
            desc_elem = item.find('p', class_='description')
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            car_details = self.extract_car_details(title, description)
            
            return {
                'title': title,
                'price': price,
                'location': location,
                'url': url,
                'image_url': image_url,
                'image_hash': image_hash,
                'source_site': 'carzone',
                'first_seen': datetime.utcnow(),
                **car_details
            }
            
        except Exception as e:
            logger.warning(f"Error parsing Carzone listing: {e}")
            return None
    
    def scrape_donedeal(self, max_pages=10):
        """Scrape DoneDeal.ie"""
        logger.info("Starting DoneDeal scraping")
        
        try:
            if not self.driver:
                if not self.setup_driver():
                    return []
            
            listings = []
            base_url = "https://www.donedeal.ie/cars"
            
            for page in range(1, max_pages + 1):
                try:
                    url = f"{base_url}?page={page}"
                    logger.info(f"Scraping DoneDeal page {page}: {url}")
                    
                    self.driver.get(url)
                    time.sleep(random.uniform(2, 5))
                    
                    # Wait for listings to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "card"))
                    )
                    
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    listing_items = soup.find_all('div', class_='card')
                    
                    if not listing_items:
                        logger.info(f"No listings found on page {page}, stopping")
                        break
                    
                    for item in listing_items:
                        try:
                            listing = self.parse_donedeal_listing(item)
                            if listing:
                                listings.append(listing)
                        except Exception as e:
                            logger.warning(f"Error parsing DoneDeal listing: {e}")
                            continue
                    
                    # Random delay between pages
                    time.sleep(random.uniform(3, 7))
                    
                except TimeoutException:
                    logger.warning(f"Timeout on DoneDeal page {page}")
                    break
                except Exception as e:
                    logger.error(f"Error scraping DoneDeal page {page}: {e}")
                    break
            
            logger.info(f"DoneDeal scraping completed: {len(listings)} listings found")
            return listings
            
        except Exception as e:
            logger.error(f"Error in DoneDeal scraping: {e}")
            return []
    
    def parse_donedeal_listing(self, item):
        """Parse a single DoneDeal listing"""
        try:
            # Extract basic info
            title_elem = item.find('h3', class_='card__title')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Extract price
            price_elem = item.find('span', class_='card__price')
            if not price_elem:
                return None
            
            price_text = price_elem.get_text(strip=True)
            price_match = re.search(r'€?([\d,]+)', price_text.replace(',', ''))
            if not price_match:
                return None
            
            price = int(price_match.group(1))
            
            # Extract location
            location_elem = item.find('span', class_='card__location')
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Extract URL
            link_elem = item.find('a', href=True)
            url = f"https://www.donedeal.ie{link_elem['href']}" if link_elem else ""
            
            # Extract image
            img_elem = item.find('img', src=True)
            image_url = img_elem['src'] if img_elem else None
            
            # Calculate image hash
            image_hash = None
            if image_url:
                image_hash = self.get_image_hash(image_url)
            
            # Extract car details
            description = ""
            desc_elem = item.find('p', class_='card__description')
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            car_details = self.extract_car_details(title, description)
            
            return {
                'title': title,
                'price': price,
                'location': location,
                'url': url,
                'image_url': image_url,
                'image_hash': image_hash,
                'source_site': 'donedeal',
                'first_seen': datetime.utcnow(),
                **car_details
            }
            
        except Exception as e:
            logger.warning(f"Error parsing DoneDeal listing: {e}")
            return None
    
    def run_full_scrape(self, user_id=None):
        """Run full scraping process for all enabled sites"""
        logger.info("Starting full scraping process")
        
        try:
            # Get all users or specific user
            if user_id:
                users = User.query.filter_by(id=user_id).all()
            else:
                users = User.query.filter_by(is_active=True).all()
            
            if not users:
                logger.warning("No active users found")
                return
            
            for user in users:
                if not user.settings:
                    logger.warning(f"No settings found for user {user.id}")
                    continue
                
                logger.info(f"Processing user {user.id}")
                
                # Run scraping for each enabled site
                all_listings = []
                
                if user.settings.scrape_carzone:
                    listings = self.scrape_carzone(user.settings.max_pages_per_site)
                    all_listings.extend(listings)
                
                if user.settings.scrape_donedeal:
                    listings = self.scrape_donedeal(user.settings.max_pages_per_site)
                    all_listings.extend(listings)
                
                # Process and save listings
                self.process_listings(all_listings, user)
            
            logger.info("Full scraping process completed")
            
        except Exception as e:
            logger.error(f"Error in full scraping process: {e}")
        finally:
            self.close_driver()
    
    def process_listings(self, listings, user):
        """Process scraped listings and save to database"""
        logger.info(f"Processing {len(listings)} listings for user {user.id}")
        
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
                        
                        # Check for price drop
                        if existing.previous_price and listing_data['price'] < existing.previous_price:
                            existing.price_dropped = True
                            existing.price_drop_amount = existing.previous_price - listing_data['price']
                        
                        existing.previous_price = listing_data['price']
                        existing.updated_at = datetime.utcnow()
                        
                        updated_count += 1
                    else:
                        # Check for duplicates
                        is_dup, dup_id = self.is_duplicate(listing_data, existing_listings)
                        
                        if is_dup:
                            # Mark as duplicate
                            listing_data['is_duplicate'] = True
                            listing_data['duplicate_group_id'] = dup_id
                        else:
                            listing_data['is_duplicate'] = False
                        
                        # Calculate deal score
                        deal_score = self.calculate_deal_score(listing_data, user.settings)
                        listing_data['deal_score'] = deal_score
                        
                        # Create new listing
                        listing = CarListing(**listing_data)
                        db.session.add(listing)
                        
                        new_count += 1
                        existing_listings.append(listing)  # Add to list for future duplicate checks
                
                except Exception as e:
                    logger.warning(f"Error processing listing {listing_data.get('url', 'unknown')}: {e}")
                    continue
            
            db.session.commit()
            logger.info(f"Processed {new_count} new listings, {updated_count} updated listings")
            
        except Exception as e:
            logger.error(f"Error processing listings: {e}")
            db.session.rollback()

# Example usage
if __name__ == "__main__":
    engine = CarScrapingEngine()
    engine.run_full_scrape()
