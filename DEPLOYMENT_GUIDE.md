# Auto Finder - Deployment Guide

## 🚀 Quick Fix for Empty Listings

### Step 1: Deploy Updated Code
Deploy the updated `app.py` file to your production server (Render.com).

### Step 2: Populate Database with Sample Data
Call this endpoint to add sample listings and fix user filters:

```bash
curl -X POST https://auto-finder.onrender.com/api/setup-sample-data
```

**Expected Response:**
```json
{
  "message": "Sample data setup completed successfully",
  "listings_added": 25,
  "users_updated": 1,
  "total_listings": 25
}
```

### Step 3: Verify Listings
Refresh your listings page at `https://auto-finder.onrender.com/listings` - you should now see 25 sample car listings!

## 🔄 Data Management

### When Ready for Real Scraping
Once your scraping process is working, clear the dummy data:

```bash
curl -X POST https://auto-finder.onrender.com/api/clear-dummy-data
```

**Expected Response:**
```json
{
  "message": "Dummy data cleared successfully",
  "cleared_listings": 25,
  "remaining_listings": 0
}
```

### Local Development
For local testing, run:
```bash
python add_production_listings.py  # Add sample data
python clear_dummy_data.py         # Clear sample data
```

## 🛠️ What the Fix Does

### Sample Data Setup (`/api/setup-sample-data`)
- ✅ Adds 25 sample car listings with realistic data
- ✅ Sets all user price ranges to €0 - €100,000 (inclusive)
- ✅ Sets minimum deal score to 0 (inclusive)
- ✅ Adds all Irish counties to approved locations
- ✅ Creates user settings for users who don't have them

### Sample Data Clear (`/api/clear-dummy-data`)
- ✅ Removes all listings with `source_site='sample'`
- ✅ Keeps any real scraped data
- ✅ Returns count of cleared vs remaining listings

## 📊 Sample Data Structure

The sample listings include:
- **Makes**: Toyota, Ford, Volkswagen, BMW, Mercedes, Audi, Nissan, Honda, Hyundai, Kia
- **Models**: Corolla, Focus, Golf, 3 Series, C-Class, A4, Qashqai, Civic, i30, Ceed
- **Locations**: Dublin, Cork, Galway, Limerick, Waterford, Wexford, Kilkenny, Sligo, Donegal, Mayo
- **Fuel Types**: Petrol, Diesel, Hybrid, Electric
- **Transmissions**: Manual, Automatic
- **Price Range**: €5,000 - €25,000
- **Years**: 2015 - 2023
- **Mileage**: 10,000 - 150,000 km
- **Deal Scores**: 30 - 95

## 🎯 Next Steps

1. **Deploy** the updated code
2. **Call** `/api/setup-sample-data` to populate the database
3. **Verify** listings appear on the frontend
4. **Test** the scraping functionality
5. **Clear** dummy data when ready for real scraping

## 🔍 Troubleshooting

### If listings still don't appear:
1. Check browser console for errors
2. Verify the API call returns data: `curl https://auto-finder.onrender.com/api/listings/`
3. Check user authentication is working
4. Ensure user has proper settings

### If API calls fail:
1. Check server logs on Render.com
2. Verify database connection
3. Check for any deployment errors
