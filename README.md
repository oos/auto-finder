# Auto Finder - Used Car Deal Tracker

A comprehensive web application that automatically tracks, filters, scores, and alerts users about the best used car deals from multiple Irish websites.

## 🚀 Features

- **Multi-site Scraping**: Automatically scrapes Carzone.ie, DoneDeal.ie, Adverts.ie, CarsIreland.ie, and LewisMotors.ie
- **Smart Filtering**: Price range, location, and blacklist filtering
- **Duplicate Detection**: Uses title similarity and image hashing to detect duplicate listings
- **Deal Scoring**: Configurable scoring algorithm based on price, mileage, year, CO2 emissions, and more
- **Email Notifications**: Daily email summaries with top deals
- **Real-time Dashboard**: Charts, statistics, and alerts
- **User Management**: Multi-tenant with individual settings and preferences
- **Anti-blocking**: Undetected Chrome driver with user-agent rotation and retry logic

## 🛠️ Tech Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Primary database
- **Redis**: Caching and task queue
- **Celery**: Background task processing
- **SendGrid**: Email notifications
- **Selenium**: Web scraping with undetected-chromedriver

### Frontend
- **React**: User interface
- **Styled Components**: CSS-in-JS styling
- **React Query**: Data fetching and caching
- **Recharts**: Data visualization
- **React Router**: Client-side routing

## 📋 Prerequisites

- Python 3.8+
- Node.js 18+
- PostgreSQL 12+
- Redis 6+
- Chrome/Chromium browser

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd auto-finder
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your configuration

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run the application
python app.py
```

### 3. Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm start
```

### 4. Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost/auto_finder
SQLALCHEMY_DATABASE_URI=postgresql://username:password@localhost/auto_finder

# JWT
JWT_SECRET_KEY=your-secret-key-here

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Email (SendGrid)
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@autofinder.com

# Scraping
CHROME_DRIVER_PATH=/usr/local/bin/chromedriver
MAX_PAGES_PER_SITE=10
SCRAPE_DELAY_MIN=2
SCRAPE_DELAY_MAX=5

# App
FLASK_ENV=development
FLASK_DEBUG=True
```

## 🏗️ Project Structure

```
auto-finder/
├── app.py                 # Flask application entry point
├── models.py              # Database models
├── scraping_engine.py     # Web scraping logic
├── email_service.py       # Email notification service
├── routes/                # API routes
│   ├── auth.py           # Authentication endpoints
│   ├── listings.py       # Listings management
│   ├── settings.py       # User settings
│   ├── scraping.py       # Scraping management
│   └── dashboard.py      # Dashboard data
├── src/                   # React frontend
│   ├── components/       # Reusable components
│   ├── pages/           # Page components
│   ├── contexts/        # React contexts
│   └── App.js           # Main app component
├── requirements.txt      # Python dependencies
├── package.json         # Node.js dependencies
└── README.md           # This file
```

## 🔧 Configuration

### Deal Scoring Weights

The application uses a configurable scoring system with weights that must total 100:

- **Price vs Market Value** (25%): Lower price = higher score
- **Mileage vs Year** (20%): Newer + lower mileage = higher score
- **CO2/Tax Band** (15%): Lower tax = higher score
- **Popularity/Rarity** (15%): Less common model = higher score
- **Price Dropped** (10%): Bonus for recent price drops
- **Location Match** (10%): Bonus for preferred locations
- **Listing Freshness** (5%): Newer listings score higher

### Scraping Configuration

- **Max Pages per Site**: Limit pages scraped per site (default: 10)
- **Scrape Delays**: Random delays between requests (2-5 seconds)
- **Retry Logic**: Exponential backoff for failed requests
- **User Agent Rotation**: Prevents detection and blocking

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile
- `POST /api/auth/change-password` - Change password

### Listings
- `GET /api/listings` - Get filtered listings with pagination
- `GET /api/listings/stats` - Get listing statistics
- `GET /api/listings/top-deals` - Get top deals
- `GET /api/listings/search` - Search listings

### Settings
- `GET /api/settings` - Get user settings
- `PUT /api/settings` - Update user settings
- `POST /api/settings/blacklist` - Add blacklist keyword
- `DELETE /api/settings/blacklist/:id` - Remove blacklist keyword

### Scraping
- `GET /api/scraping/status` - Get scraping status
- `POST /api/scraping/start` - Start scraping
- `POST /api/scraping/stop` - Stop scraping
- `GET /api/scraping/logs` - Get scraping logs

### Dashboard
- `GET /api/dashboard/overview` - Get dashboard overview
- `GET /api/dashboard/charts/trends` - Get trend charts
- `GET /api/dashboard/charts/distribution` - Get distribution charts
- `GET /api/dashboard/alerts` - Get recent alerts

## 🚀 Deployment

### Netlify (Frontend)

1. Connect your repository to Netlify
2. Set build command: `npm run build`
3. Set publish directory: `build`
4. Deploy

### Heroku (Backend)

1. Create a new Heroku app
2. Add PostgreSQL and Redis add-ons
3. Set environment variables
4. Deploy using Git

```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create auto-finder-api

# Add add-ons
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set JWT_SECRET_KEY=your-secret-key
heroku config:set SENDGRID_API_KEY=your-sendgrid-key
# ... other variables

# Deploy
git push heroku main
```

## 🔄 Scheduled Tasks

The application includes scheduled tasks for:

- **Daily Scraping**: Runs every day to collect new listings
- **Email Notifications**: Sends daily summaries to users
- **Data Cleanup**: Removes old logs and inactive listings

Set up using Celery Beat or your preferred task scheduler.

## 🛡️ Security Features

- JWT-based authentication
- Password hashing with Werkzeug
- CORS protection
- Input validation and sanitization
- SQL injection prevention with SQLAlchemy ORM

## 🧪 Testing

```bash
# Backend tests
python -m pytest tests/

# Frontend tests
npm test
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For support, email support@autofinder.com or create an issue in the repository.

## 🔮 Future Enhancements

- WhatsApp notifications
- Mobile app
- API for third-party integrations
- Advanced analytics and reporting
- Machine learning for better deal scoring
- Integration with more car websites
- Price prediction models
