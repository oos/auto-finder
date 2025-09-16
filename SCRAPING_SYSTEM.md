# Real Web Scraping System Documentation

## 🎯 Overview

This document describes the comprehensive real web scraping system implemented for the Auto Finder application. The system scrapes real car listings from Irish car websites and processes them for storage in the database.

## 🏗️ Architecture

### Phase 1: Research & Analysis ✅
- **Target Websites**: Carzone.ie, DoneDeal.ie, CarsIreland.ie, Adverts.ie
- **Analysis**: HTML structure analysis, anti-scraping measures, rate limiting
- **Compliance**: Respects robots.txt, implements proper delays, uses realistic user agents

### Phase 2: Robust Scraping Engine ✅
- **Base Engine**: `BaseScrapingEngine` with common functionality
- **Site-Specific Scrapers**: `CarzoneScraper`, `DoneDealScraper`
- **Main Coordinator**: `RealCarScrapingEngine`
- **Anti-Detection**: User agent rotation, random delays, session management

### Phase 3: Data Processing & Storage ✅
- **Data Processor**: `DataProcessor` class for cleaning and validation
- **Deduplication**: URL and title similarity checking
- **Database Integration**: Seamless integration with existing `CarListing` model
- **Quality Control**: Data validation, price/mileage range checking

### Phase 4: Testing & Monitoring ✅
- **Monitoring**: `ScrapingMonitor` for health checks and statistics
- **Testing**: Comprehensive test suite (`test_scraping_system.py`)
- **API Endpoints**: Health, stats, test suite, cleanup endpoints
- **Logging**: Detailed logging throughout the system

## 📁 File Structure

```
auto-finder/
├── scraping_engine_real.py      # Main scraping engine
├── data_processor.py            # Data processing and storage
├── scraping_monitor.py          # Monitoring and health checks
├── test_scraping_system.py      # Comprehensive test suite
├── routes/scraping.py           # API endpoints (updated)
└── SCRAPING_SYSTEM.md           # This documentation
```

## 🔧 Core Components

### 1. BaseScrapingEngine
```python
class BaseScrapingEngine:
    - setup_session()           # Configure HTTP session
    - get_page()               # Fetch page with retry logic
    - clean_text()             # Clean and normalize text
    - extract_price()          # Extract numeric price
    - extract_mileage()        # Extract numeric mileage
    - generate_image_hash()    # Generate image URL hash
```

### 2. Site-Specific Scrapers
```python
class CarzoneScraper(BaseScrapingEngine):
    - scrape_listings()        # Main scraping method
    - extract_car_data()       # Extract data from HTML
    - parse_car_title()        # Parse make, model, year
    - extract_additional_details() # Get mileage, fuel type, etc.

class DoneDealScraper(BaseScrapingEngine):
    - Similar structure to CarzoneScraper
    - Adapted for DoneDeal's HTML structure
```

### 3. DataProcessor
```python
class DataProcessor:
    - process_listings()       # Process and store listings
    - clean_listing_data()     # Clean and validate data
    - is_duplicate()          # Check for duplicates
    - store_listing()         # Store in database
    - calculate_deal_score()  # Calculate deal score
    - cleanup_old_listings()  # Remove old data
```

### 4. ScrapingMonitor
```python
class ScrapingMonitor:
    - test_scraping_health()   # Test site accessibility
    - get_scraping_stats()     # Get performance statistics
    - cleanup_old_data()       # Clean up old data
    - test_single_scraper()    # Test individual scrapers
    - run_full_test_suite()    # Run comprehensive tests
```

## 🚀 Usage

### Starting Real Scraping
```bash
# Via API
POST /api/scraping/start
Authorization: Bearer <jwt_token>

# Response
{
    "message": "Real car scraping completed",
    "scrape_log_id": 123,
    "engine_type": "real",
    "listings_found": 45,
    "new_listings": 32,
    "updated_listings": 8,
    "duplicates_skipped": 5
}
```

### Testing Individual Sites
```bash
# Test specific site
POST /api/scraping/test
{
    "site": "carzone"
}

# Run full test suite
POST /api/scraping/monitor/test-suite
```

### Monitoring
```bash
# Get health status
GET /api/scraping/monitor/health

# Get statistics
GET /api/scraping/monitor/stats?days=7

# Clean up old data
POST /api/scraping/monitor/cleanup
{
    "days_old": 30
}
```

## 🧪 Testing

### Run Comprehensive Test Suite
```bash
python test_scraping_system.py
```

### Test Components Individually
```python
from scraping_engine_real import RealCarScrapingEngine
from data_processor import DataProcessor
from scraping_monitor import ScrapingMonitor

# Test scraping
engine = RealCarScrapingEngine()
listings = engine.scrape_single_site('carzone', max_pages=1)

# Test data processing
processor = DataProcessor()
stats = processor.process_listings(listings, user_id=1)

# Test monitoring
monitor = ScrapingMonitor()
health = monitor.test_scraping_health()
```

## ⚙️ Configuration

### User Settings Integration
The scraping system respects user settings:
- `scrape_carzone`: Enable/disable Carzone scraping
- `scrape_donedeal`: Enable/disable DoneDeal scraping
- `max_pages_per_site`: Maximum pages to scrape per site
- `min_deal_score`: Minimum deal score threshold

### Rate Limiting
- **Delay between requests**: 1-3 seconds random
- **Delay between sites**: 5-10 seconds random
- **User agent rotation**: Random realistic user agents
- **Session management**: Persistent sessions with proper headers

## 📊 Data Quality

### Validation Rules
- **Price range**: €500 - €200,000
- **Year range**: 1990 - 2025
- **Mileage range**: 0 - 500,000 km
- **Title length**: Minimum 10 characters
- **URL validation**: Must start with http/https

### Deduplication
- **URL matching**: Exact URL comparison
- **Title similarity**: 90% similarity threshold using SequenceMatcher
- **Database checking**: Check existing listings before storing

### Deal Score Calculation
- **Base score**: 50 points
- **Price factor**: +5 to +20 based on price range
- **Year factor**: +5 to +20 based on age
- **Mileage factor**: +5 to +15 based on age vs mileage
- **Fuel type factor**: +5 to +10 for electric/hybrid
- **Final range**: 0-100 points

## 🔍 Monitoring & Maintenance

### Health Checks
- **Site accessibility**: HTTP status and response time
- **Data extraction**: Verify car listing elements found
- **Error tracking**: Comprehensive error logging

### Statistics
- **Scraping success rate**: Percentage of successful scrapes
- **Listings by source**: Count by website
- **Recent activity**: Listings added in last 7 days
- **Performance metrics**: Response times, error rates

### Cleanup
- **Old scrape logs**: Remove logs older than 30 days
- **Stale listings**: Remove listings not seen recently
- **Database optimization**: Regular cleanup for performance

## 🚨 Error Handling

### Scraping Errors
- **Network timeouts**: Retry with exponential backoff
- **HTTP errors**: Log and continue with next page
- **Parsing errors**: Skip invalid listings, log errors
- **Rate limiting**: Implement longer delays

### Data Processing Errors
- **Invalid data**: Skip and log validation errors
- **Database errors**: Rollback transactions, log errors
- **Duplicate detection**: Handle gracefully, update existing

### Monitoring Errors
- **Health check failures**: Mark as unhealthy, alert
- **Statistics errors**: Return error response, log issue
- **Cleanup failures**: Rollback, log error details

## 🔒 Security & Compliance

### Ethical Scraping
- **Respect robots.txt**: Check before scraping
- **Rate limiting**: Don't overwhelm servers
- **User agent identification**: Identify as legitimate scraper
- **No personal data**: Only scrape public car listings

### Data Protection
- **No PII collection**: Only car listing data
- **Secure storage**: Use existing database security
- **Access control**: JWT authentication required
- **Audit logging**: Track all scraping activities

## 📈 Performance

### Optimization
- **Concurrent processing**: Process multiple listings
- **Database batching**: Batch database operations
- **Memory management**: Clean up processed data
- **Caching**: Cache user agents and sessions

### Scalability
- **Modular design**: Easy to add new scrapers
- **Configuration driven**: Enable/disable sites via settings
- **Resource monitoring**: Track CPU, memory, disk usage
- **Error recovery**: Graceful handling of failures

## 🛠️ Troubleshooting

### Common Issues
1. **No listings found**: Check site structure changes
2. **Rate limiting**: Increase delays between requests
3. **Database errors**: Check connection and schema
4. **Memory issues**: Reduce batch sizes

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('scraping_engine_real').setLevel(logging.DEBUG)
logging.getLogger('data_processor').setLevel(logging.DEBUG)
```

### Health Check
```bash
# Check system health
curl -H "Authorization: Bearer <token>" \
     http://localhost:5003/api/scraping/monitor/health
```

## 🚀 Future Enhancements

### Planned Features
- **More sites**: Add CarsIreland.ie, Adverts.ie scrapers
- **Machine learning**: Improve deal score calculation
- **Real-time monitoring**: WebSocket-based live updates
- **Advanced filtering**: More sophisticated duplicate detection
- **Proxy support**: Rotate IP addresses for large-scale scraping

### Performance Improvements
- **Async scraping**: Use asyncio for concurrent requests
- **Caching layer**: Redis for temporary data storage
- **Database optimization**: Indexing and query optimization
- **Load balancing**: Distribute scraping across multiple instances

---

## 📞 Support

For issues or questions about the scraping system:
1. Check the logs in `auto_finder.log`
2. Run the test suite: `python test_scraping_system.py`
3. Check health status via API endpoints
4. Review this documentation for configuration options

The scraping system is designed to be robust, maintainable, and respectful of target websites while providing high-quality car listing data for the Auto Finder application.
