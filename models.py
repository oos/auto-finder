from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
from database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    settings = db.relationship('UserSettings', backref='user', uselist=False, cascade='all, delete-orphan')
    blacklists = db.relationship('Blacklist', backref='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_token(self):
        return create_access_token(identity=self.id)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Price range
    min_price = db.Column(db.Integer, default=5000)
    max_price = db.Column(db.Integer, default=15000)
    
    # Location settings
    approved_locations = db.Column(db.Text, default='["Leinster"]')  # JSON array
    
    # Scraping settings
    max_pages_per_site = db.Column(db.Integer, default=10)
    min_deal_score = db.Column(db.Integer, default=50)
    
    # Site toggles
    scrape_carzone = db.Column(db.Boolean, default=True)
    scrape_donedeal = db.Column(db.Boolean, default=True)
    scrape_adverts = db.Column(db.Boolean, default=True)
    scrape_carsireland = db.Column(db.Boolean, default=True)
    scrape_lewismotors = db.Column(db.Boolean, default=True)
    
    # Deal scoring weights (must total 100)
    weight_price_vs_market = db.Column(db.Integer, default=25)
    weight_mileage_vs_year = db.Column(db.Integer, default=20)
    weight_co2_tax_band = db.Column(db.Integer, default=15)
    weight_popularity_rarity = db.Column(db.Integer, default=15)
    weight_price_dropped = db.Column(db.Integer, default=10)
    weight_location_match = db.Column(db.Integer, default=10)
    weight_listing_freshness = db.Column(db.Integer, default=5)
    
    # Email settings
    email_notifications = db.Column(db.Boolean, default=True)
    daily_email_time = db.Column(db.String(5), default='09:00')  # HH:MM format
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_approved_locations(self):
        return json.loads(self.approved_locations)
    
    def set_approved_locations(self, locations):
        self.approved_locations = json.dumps(locations)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'min_price': self.min_price,
            'max_price': self.max_price,
            'approved_locations': self.get_approved_locations(),
            'max_pages_per_site': self.max_pages_per_site,
            'min_deal_score': self.min_deal_score,
            'scrape_carzone': self.scrape_carzone,
            'scrape_donedeal': self.scrape_donedeal,
            'scrape_adverts': self.scrape_adverts,
            'scrape_carsireland': self.scrape_carsireland,
            'scrape_lewismotors': self.scrape_lewismotors,
            'weight_price_vs_market': self.weight_price_vs_market,
            'weight_mileage_vs_year': self.weight_mileage_vs_year,
            'weight_co2_tax_band': self.weight_co2_tax_band,
            'weight_popularity_rarity': self.weight_popularity_rarity,
            'weight_price_dropped': self.weight_price_dropped,
            'weight_location_match': self.weight_location_match,
            'weight_listing_freshness': self.weight_listing_freshness,
            'email_notifications': self.email_notifications,
            'daily_email_time': self.daily_email_time,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Blacklist(db.Model):
    __tablename__ = 'blacklists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    keyword = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'keyword': self.keyword,
            'created_at': self.created_at.isoformat()
        }

class CarListing(db.Model):
    __tablename__ = 'car_listings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic listing info
    title = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(1000), nullable=False, unique=True)
    image_url = db.Column(db.String(1000))
    image_hash = db.Column(db.String(64))  # For duplicate detection
    source_site = db.Column(db.String(50), nullable=False)
    
    # Car details
    make = db.Column(db.String(50))
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)
    fuel_type = db.Column(db.String(20))
    transmission = db.Column(db.String(20))
    co2_emissions = db.Column(db.Integer)
    tax_band = db.Column(db.String(10))
    nct_expiry = db.Column(db.Date)
    
    # Status and tracking
    status = db.Column(db.String(20), default='active')  # active, removed, blocked
    is_duplicate = db.Column(db.Boolean, default=False)
    duplicate_group_id = db.Column(db.Integer)  # Groups duplicates together
    
    # Deal scoring
    deal_score = db.Column(db.Float, default=0.0)
    price_vs_market_score = db.Column(db.Float, default=0.0)
    mileage_vs_year_score = db.Column(db.Float, default=0.0)
    co2_tax_score = db.Column(db.Float, default=0.0)
    popularity_rarity_score = db.Column(db.Float, default=0.0)
    price_dropped_score = db.Column(db.Float, default=0.0)
    location_match_score = db.Column(db.Float, default=0.0)
    listing_freshness_score = db.Column(db.Float, default=0.0)
    
    # Price tracking
    previous_price = db.Column(db.Integer)
    price_dropped = db.Column(db.Boolean, default=False)
    price_drop_amount = db.Column(db.Integer, default=0)
    
    # Timestamps
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'location': self.location,
            'url': self.url,
            'image_url': self.image_url,
            'source_site': self.source_site,
            'make': self.make,
            'model': self.model,
            'year': self.year,
            'mileage': self.mileage,
            'fuel_type': self.fuel_type,
            'transmission': self.transmission,
            'co2_emissions': self.co2_emissions,
            'tax_band': self.tax_band,
            'nct_expiry': self.nct_expiry.isoformat() if self.nct_expiry else None,
            'status': self.status,
            'is_duplicate': self.is_duplicate,
            'duplicate_group_id': self.duplicate_group_id,
            'deal_score': self.deal_score,
            'price_dropped': self.price_dropped,
            'price_drop_amount': self.price_drop_amount,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ScrapeLog(db.Model):
    __tablename__ = 'scrape_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(50), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='running')  # running, completed, failed, blocked
    listings_found = db.Column(db.Integer, default=0)
    listings_new = db.Column(db.Integer, default=0)
    listings_updated = db.Column(db.Integer, default=0)
    listings_removed = db.Column(db.Integer, default=0)
    pages_scraped = db.Column(db.Integer, default=0)
    errors = db.Column(db.Text)  # JSON array of errors
    is_blocked = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'site_name': self.site_name,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'listings_found': self.listings_found,
            'listings_new': self.listings_new,
            'listings_updated': self.listings_updated,
            'listings_removed': self.listings_removed,
            'pages_scraped': self.pages_scraped,
            'errors': json.loads(self.errors) if self.errors else [],
            'is_blocked': self.is_blocked
        }

class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    subject = db.Column(db.String(200), nullable=False)
    listings_included = db.Column(db.Integer, default=0)
    total_listings_scraped = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='sent')  # sent, failed
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sent_at': self.sent_at.isoformat(),
            'subject': self.subject,
            'listings_included': self.listings_included,
            'total_listings_scraped': self.total_listings_scraped,
            'status': self.status
        }
