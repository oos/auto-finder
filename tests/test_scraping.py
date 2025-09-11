import pytest
from unittest.mock import Mock, patch
from scraping_engine import CarScrapingEngine

class TestCarScrapingEngine:
    """Test cases for the scraping engine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = CarScrapingEngine()
    
    def test_calculate_title_similarity(self):
        """Test title similarity calculation"""
        title1 = "2018 Toyota Corolla 1.6 Petrol"
        title2 = "2018 Toyota Corolla 1.6 Petrol Manual"
        title3 = "2019 Ford Focus 1.0 Petrol"
        
        similarity1 = self.engine.calculate_title_similarity(title1, title2)
        similarity2 = self.engine.calculate_title_similarity(title1, title3)
        
        assert similarity1 > 0.8  # Should be very similar
        assert similarity2 < 0.5  # Should be less similar
    
    def test_extract_car_details(self):
        """Test car details extraction from title and description"""
        title = "2019 Toyota Corolla 1.6 Petrol Manual 45000km"
        description = "One owner, full service history, NCT until 2025"
        
        details = self.engine.extract_car_details(title, description)
        
        assert details['year'] == 2019
        assert details['make'] == 'Toyota'
        assert details['model'] == 'Corolla'
        assert details['mileage'] == 45000
        assert details['fuel_type'] == 'Petrol'
        assert details['transmission'] == 'Manual'
    
    def test_extract_car_details_minimal(self):
        """Test car details extraction with minimal information"""
        title = "Car for sale"
        description = "Good condition"
        
        details = self.engine.extract_car_details(title, description)
        
        # Should not crash and return None for missing details
        assert details['year'] is None
        assert details['make'] is None
        assert details['model'] is None
    
    @patch('scraping_engine.requests.Session.get')
    def test_get_image_hash_success(self, mock_get):
        """Test successful image hash calculation"""
        # Mock successful image response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'fake_image_data'
        mock_get.return_value = mock_response
        
        # Mock PIL Image
        with patch('scraping_engine.Image.open') as mock_image:
            mock_image.return_value = Mock()
            with patch('scraping_engine.imagehash.average_hash') as mock_hash:
                mock_hash.return_value = 'fake_hash'
                
                result = self.engine.get_image_hash('http://example.com/image.jpg')
                assert result == 'fake_hash'
    
    @patch('scraping_engine.requests.Session.get')
    def test_get_image_hash_failure(self, mock_get):
        """Test image hash calculation with network error"""
        # Mock failed image response
        mock_get.side_effect = Exception('Network error')
        
        result = self.engine.get_image_hash('http://example.com/image.jpg')
        assert result is None
    
    def test_is_duplicate_exact_match(self):
        """Test duplicate detection with exact match"""
        new_listing = {
            'title': '2018 Toyota Corolla',
            'price': 15000,
            'image_hash': 'hash123'
        }
        
        existing_listing = Mock()
        existing_listing.title = '2018 Toyota Corolla'
        existing_listing.price = 15000
        existing_listing.image_hash = 'hash123'
        existing_listing.id = 1
        
        is_dup, dup_id = self.engine.is_duplicate(new_listing, [existing_listing])
        assert is_dup is True
        assert dup_id == 1
    
    def test_is_duplicate_similar_title_price(self):
        """Test duplicate detection with similar title and close price"""
        new_listing = {
            'title': '2018 Toyota Corolla 1.6 Petrol',
            'price': 15000,
            'image_hash': None
        }
        
        existing_listing = Mock()
        existing_listing.title = '2018 Toyota Corolla 1.6 Petrol Manual'
        existing_listing.price = 15050  # Within €50
        existing_listing.image_hash = None
        existing_listing.id = 1
        
        is_dup, dup_id = self.engine.is_duplicate(new_listing, [existing_listing])
        assert is_dup is True
        assert dup_id == 1
    
    def test_is_duplicate_different_cars(self):
        """Test duplicate detection with different cars"""
        new_listing = {
            'title': '2018 Toyota Corolla',
            'price': 15000,
            'image_hash': None
        }
        
        existing_listing = Mock()
        existing_listing.title = '2019 Ford Focus'
        existing_listing.price = 15000
        existing_listing.image_hash = None
        existing_listing.id = 1
        
        is_dup, dup_id = self.engine.is_duplicate(new_listing, [existing_listing])
        assert is_dup is False
        assert dup_id is None
    
    def test_calculate_deal_score(self):
        """Test deal score calculation"""
        from models import UserSettings
        
        # Create mock user settings
        settings = Mock(spec=UserSettings)
        settings.weight_price_vs_market = 25
        settings.weight_mileage_vs_year = 20
        settings.weight_co2_tax_band = 15
        settings.weight_popularity_rarity = 15
        settings.weight_price_dropped = 10
        settings.weight_location_match = 10
        settings.weight_listing_freshness = 5
        settings.get_approved_locations.return_value = ['Leinster']
        
        listing = {
            'price': 12000,
            'year': 2020,
            'mileage': 30000,
            'fuel_type': 'Petrol',
            'location': 'Dublin, Leinster',
            'price_dropped': False,
            'first_seen': None
        }
        
        score = self.engine.calculate_deal_score(listing, settings)
        
        # Score should be between 0 and 100
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    def test_calculate_deal_score_with_price_drop(self):
        """Test deal score calculation with price drop bonus"""
        from models import UserSettings
        
        settings = Mock(spec=UserSettings)
        settings.weight_price_vs_market = 25
        settings.weight_mileage_vs_year = 20
        settings.weight_co2_tax_band = 15
        settings.weight_popularity_rarity = 15
        settings.weight_price_dropped = 10
        settings.weight_location_match = 10
        settings.weight_listing_freshness = 5
        settings.get_approved_locations.return_value = ['Leinster']
        
        listing = {
            'price': 12000,
            'year': 2020,
            'mileage': 30000,
            'fuel_type': 'Petrol',
            'location': 'Dublin, Leinster',
            'price_dropped': True,  # Should get bonus
            'first_seen': None
        }
        
        score = self.engine.calculate_deal_score(listing, settings)
        
        # Score should be higher due to price drop bonus
        assert score > 0
        assert isinstance(score, float)
