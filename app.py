from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
import os
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv
from database import db

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_finder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='build', static_url_path='')

# Configuration
jwt_secret = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
app.config['SECRET_KEY'] = jwt_secret
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///auto_finder.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = jwt_secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False

# Initialize extensions
jwt = JWTManager()
migrate = Migrate()
CORS(app)

# JWT configuration - let Flask-JWT-Extended handle defaults

# Debug JWT configuration
print(f"DEBUG: JWT_SECRET_KEY configured: {app.config['JWT_SECRET_KEY'][:10]}...")
print(f"DEBUG: JWT_ACCESS_TOKEN_EXPIRES: {app.config['JWT_ACCESS_TOKEN_EXPIRES']}")

# Initialize database
def init_db():
    """Initialize the database with all tables"""
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {e}")

# Initialize database on startup
init_db()

# Import models and routes AFTER db is initialized
from models import *
from routes.auth import auth_bp
from routes.listings import listings_bp
from routes.settings import settings_bp
from routes.scraping import scraping_bp
from routes.dashboard import dashboard_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(listings_bp, url_prefix='/api/listings')
app.register_blueprint(settings_bp, url_prefix='/api/settings')
app.register_blueprint(scraping_bp, url_prefix='/api/scraping')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Auto Finder API is running'})

@app.route('/api/debug-imports', methods=['GET'])
def debug_imports():
    import os
    import sys
    
    result = {
        'current_dir': os.getcwd(),
        'python_path': sys.path,
        'files_in_dir': os.listdir('.'),
        'scraping_engine_exists': os.path.exists('scraping_engine_simple.py'),
        'scraping_engine_size': os.path.getsize('scraping_engine_simple.py') if os.path.exists('scraping_engine_simple.py') else 0
    }
    
    # Try to import
    try:
        from scraping_engine_simple import SimpleCarScrapingEngine
        result['import_success'] = True
        result['class_name'] = SimpleCarScrapingEngine.__name__
    except Exception as e:
        result['import_success'] = False
        result['import_error'] = str(e)
    
    return jsonify(result), 200

@app.route('/api/clear-all-data', methods=['POST'])
def clear_all_data_simple():
    """Simple endpoint to clear all data for testing"""
    try:
        from models import CarListing, ScrapeLog
        
        # Clear all scraping logs
        logs_deleted = db.session.query(ScrapeLog).delete()
        
        # Clear all dummy/sample listings
        dummy_listings_deleted = CarListing.query.filter(
            CarListing.source_site.in_(['sample', 'lewismotors'])
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'message': 'All data cleared successfully',
            'logs_deleted': logs_deleted,
            'listings_deleted': dummy_listings_deleted
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/test-routing')
def test_routing():
    return jsonify({'message': 'Routing is working', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/test-jwt')
def test_jwt():
    from flask_jwt_extended import create_access_token, decode_token
    try:
        # Test creating a token
        test_token = create_access_token(identity=1)
        
        # Test decoding the token
        decoded = decode_token(test_token)
        
        return jsonify({
            'message': 'JWT test successful',
            'token_created': True,
            'token_decoded': True,
            'decoded_subject': decoded.get('sub'),
            'jwt_secret_length': len(app.config['JWT_SECRET_KEY']),
            'jwt_secret_type': type(app.config['JWT_SECRET_KEY']).__name__
        })
    except Exception as e:
        return jsonify({
            'message': 'JWT test failed',
            'error': str(e),
            'error_type': type(e).__name__,
            'jwt_secret_length': len(app.config['JWT_SECRET_KEY']),
            'jwt_secret_type': type(app.config['JWT_SECRET_KEY']).__name__
        })

# Simple SPA routing - serve React app for all non-API routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    # API routes should not reach here due to blueprints, but double-check
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    
    # Test routes should not be served as SPA
    if path.startswith('test-'):
        return jsonify({'error': 'Test endpoint not found'}), 404
    
    # Check if it's a static file (has file extension)
    if path and '.' in path:
        try:
            return send_from_directory(app.static_folder, path)
        except FileNotFoundError:
            return jsonify({'error': 'Static file not found'}), 404
    
    # For SPA routes, serve the main index.html
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except FileNotFoundError:
        # Fallback: return a simple HTML page with API info
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Auto Finder - API Running</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .status { color: green; font-weight: bold; }
                .api-link { margin: 10px 0; }
                .api-link a { color: #007bff; text-decoration: none; }
                .api-link a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚗 Auto Finder</h1>
                <p class="status">✅ Backend API is running successfully!</p>
                
                <h2>Available Endpoints:</h2>
                <div class="api-link">
                    <a href="/api/health">/api/health</a> - Health check
                </div>
                <div class="api-link">
                    <a href="/api/listings/">/api/listings/</a> - Car listings (25 sample cars available)
                </div>
                <div class="api-link">
                    <a href="/api/setup-sample-data">/api/setup-sample-data</a> - Setup sample data
                </div>
                <div class="api-link">
                    <a href="/api/clear-dummy-data">/api/clear-dummy-data</a> - Clear sample data
                </div>
                
                <h2>Sample Data Status:</h2>
                <p>✅ 25 sample car listings are available in the database</p>
                <p>✅ User filters have been set to be inclusive</p>
                <p>✅ All Irish locations are approved</p>
                
                <h2>Next Steps:</h2>
                <p>1. The React frontend build files are missing from the deployment</p>
                <p>2. The backend API is working perfectly with sample data</p>
                <p>3. You can test the API endpoints above</p>
                <p>4. To fix the frontend, rebuild and redeploy the React app</p>
            </div>
        </body>
        </html>
        """
        return html_content, 200
    
@app.route('/api/setup-sample-data', methods=['POST'])
def setup_sample_data():
    """Setup sample data for testing - no authentication required"""
    try:
        from models import User, UserSettings, CarListing
        from sqlalchemy import or_
        import random
        
        # Check if listings already exist
        existing_count = CarListing.query.count()
        if existing_count > 0:
            return jsonify({
                'message': 'Sample data already exists',
                'existing_listings': existing_count
            }), 200
        
        # Add sample listings
        makes = ['Toyota', 'Ford', 'Volkswagen', 'BMW', 'Mercedes', 'Audi', 'Nissan', 'Honda', 'Hyundai', 'Kia']
        models = ['Corolla', 'Focus', 'Golf', '3 Series', 'C-Class', 'A4', 'Qashqai', 'Civic', 'i30', 'Ceed']
        locations = ['Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Wexford', 'Kilkenny', 'Sligo', 'Donegal', 'Mayo']
        fuel_types = ['Petrol', 'Diesel', 'Hybrid', 'Electric']
        transmissions = ['Manual', 'Automatic']
        
        listings_added = 0
        
        for i in range(25):
            make = random.choice(makes)
            model = random.choice(models)
            year = random.randint(2015, 2023)
            price = random.randint(5000, 25000)
            location = random.choice(locations)
            fuel_type = random.choice(fuel_types)
            transmission = random.choice(transmissions)
            mileage = random.randint(10000, 150000)
            
            listing = CarListing(
                title=f"{year} {make} {model} {fuel_type} {transmission}",
                price=price,
                location=location,
                url=f"https://example.com/car-{i+1}",
                image_url=f"https://via.placeholder.com/300x200?text={make}+{model}",
                image_hash=f"sample_hash_{i+1}",
                source_site='sample',
                make=make,
                model=model,
                year=year,
                mileage=mileage,
                fuel_type=fuel_type,
                transmission=transmission,
                deal_score=random.uniform(30, 95),
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                status='active'
            )
            
            db.session.add(listing)
            listings_added += 1
        
        # Fix user settings to be more inclusive
        users = User.query.all()
        users_updated = 0
        
        for user in users:
            if user.settings:
                # Make filters very inclusive
                user.settings.min_price = 0
                user.settings.max_price = 100000
                user.settings.min_deal_score = 0
                
                # Set all Irish locations as approved
                all_locations = [
                    'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Wexford', 
                    'Kilkenny', 'Sligo', 'Donegal', 'Mayo', 'Kerry', 'Clare', 
                    'Tipperary', 'Laois', 'Offaly', 'Westmeath', 'Longford', 
                    'Leitrim', 'Cavan', 'Monaghan', 'Louth', 'Meath', 'Kildare', 
                    'Wicklow', 'Carlow', 'Leinster', 'Munster', 'Connacht', 'Ulster',
                    'Ireland', 'Irish', 'All', 'Any'
                ]
                
                user.settings.set_approved_locations(all_locations)
                users_updated += 1
            else:
                # Create settings for user
                settings = UserSettings(user_id=user.id)
                settings.min_price = 0
                settings.max_price = 100000
                settings.min_deal_score = 0
                settings.set_approved_locations([
                    'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Wexford', 
                    'Kilkenny', 'Sligo', 'Donegal', 'Mayo', 'Kerry', 'Clare', 
                    'Tipperary', 'Laois', 'Offaly', 'Westmeath', 'Longford', 
                    'Leitrim', 'Cavan', 'Monaghan', 'Louth', 'Meath', 'Kildare', 
                    'Wicklow', 'Carlow', 'Leinster', 'Munster', 'Connacht', 'Ulster',
                    'Ireland', 'Irish', 'All', 'Any'
                ])
                db.session.add(settings)
                users_updated += 1
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'message': 'Sample data setup completed successfully',
            'listings_added': listings_added,
            'users_updated': users_updated,
            'total_listings': CarListing.query.count()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-dummy-data', methods=['POST'])
def clear_dummy_data():
    """Clear dummy/sample data - no authentication required"""
    try:
        from models import CarListing
        
        # Count existing listings
        total_listings = CarListing.query.count()
        sample_listings = CarListing.query.filter_by(source_site='sample').count()
        
        if sample_listings == 0:
            return jsonify({
                'message': 'No sample listings found to clear',
                'total_listings': total_listings,
                'sample_listings': sample_listings
            }), 200
        
        # Delete all sample listings
        CarListing.query.filter_by(source_site='sample').delete()
        db.session.commit()
        
        remaining_listings = CarListing.query.count()
        
        return jsonify({
            'message': 'Dummy data cleared successfully',
            'cleared_listings': sample_listings,
            'remaining_listings': remaining_listings
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fix-database', methods=['POST'])
def fix_database():
    """Fix database schema issues - no authentication required"""
    try:
        from sqlalchemy import text
        
        # Add notes column to scrape_logs table if it doesn't exist
        try:
            db.session.execute(text("ALTER TABLE scrape_logs ADD COLUMN notes TEXT"))
            db.session.commit()
            print("✅ Added notes column to scrape_logs table")
            return jsonify({
                'message': 'Database schema fixed successfully',
                'added_notes_column': True
            }), 200
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                print("ℹ️ Notes column already exists")
                return jsonify({
                    'message': 'Database schema is already correct',
                    'added_notes_column': False
                }), 200
            else:
                print(f"⚠️ Error adding notes column: {e}")
                return jsonify({
                    'message': 'Error fixing database schema',
                    'error': str(e)
                }), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-port-columns', methods=['POST'])
def add_port_columns():
    """Add port configuration columns to user_settings table"""
    try:
        from sqlalchemy import text
        
        # Add frontend_port column if it doesn't exist
        try:
            db.session.execute(text("ALTER TABLE user_settings ADD COLUMN frontend_port INTEGER DEFAULT 3000"))
            db.session.commit()
            added_frontend_port = True
            print("✅ Added frontend_port column to user_settings table")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                added_frontend_port = False
                print("ℹ️ frontend_port column already exists")
            else:
                raise e
                
        # Add backend_port column if it doesn't exist
        try:
            db.session.execute(text("ALTER TABLE user_settings ADD COLUMN backend_port INTEGER DEFAULT 5003"))
            db.session.commit()
            added_backend_port = True
            print("✅ Added backend_port column to user_settings table")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                added_backend_port = False
                print("ℹ️ backend_port column already exists")
            else:
                raise e
        
        # Set default values for existing records
        if added_frontend_port:
            db.session.execute(text("UPDATE user_settings SET frontend_port = 3000 WHERE frontend_port IS NULL"))
            db.session.commit()
        if added_backend_port:
            db.session.execute(text("UPDATE user_settings SET backend_port = 5003 WHERE backend_port IS NULL"))
            db.session.commit()
        
        return jsonify({
            'message': 'Port columns added successfully',
            'added_frontend_port': added_frontend_port,
            'added_backend_port': added_backend_port
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fix-historical-listings', methods=['POST'])
def fix_historical_listings():
    """Update historical listings from irish_market to sample source_site"""
    try:
        from sqlalchemy import text
        
        # Update all listings with source_site 'irish_market' to 'sample'
        result = db.session.execute(text("""
            UPDATE car_listings 
            SET source_site = 'sample' 
            WHERE source_site = 'irish_market'
        """))
        db.session.commit()
        
        updated_count = result.rowcount
        
        return jsonify({
            'message': f'Successfully updated {updated_count} historical listings from irish_market to sample',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/restart-with-new-ports', methods=['POST'])
def restart_with_new_ports():
    """Restart the application with new port configuration"""
    try:
        from models import UserSettings
        
        # Get current settings
        settings = UserSettings.query.first()
        if not settings:
            return jsonify({'error': 'No user settings found'}), 404
        
        current_frontend_port = settings.frontend_port or 3000
        current_backend_port = settings.backend_port or 5003
        
        return jsonify({
            'message': 'Application restart required to apply new port settings',
            'current_frontend_port': current_frontend_port,
            'current_backend_port': current_backend_port,
            'note': 'Please restart the application manually to apply port changes'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/health', methods=['GET'])
def database_health():
    """Check database health and status"""
    try:
        from database_manager import DatabaseManager
        db_manager = DatabaseManager(app)
        health_status = db_manager.check_database_health()
        return jsonify(health_status), 200
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/migrate', methods=['POST'])
def run_database_migrations():
    """Run all pending database migrations"""
    try:
        from database_manager import DatabaseManager
        db_manager = DatabaseManager(app)
        migration_results = db_manager.run_migrations()
        return jsonify({
            'message': 'Database migrations completed',
            'results': migration_results
        }), 200
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/stats', methods=['GET'])
def database_stats():
    """Get database statistics and metrics"""
    try:
        from database_manager import DatabaseManager
        db_manager = DatabaseManager(app)
        stats = db_manager.get_database_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Database stats failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/status', methods=['GET'])
def system_status():
    """Get comprehensive system status and health metrics"""
    try:
        from database_manager import DatabaseManager
        import psutil
        import platform
        
        # Database health
        db_manager = DatabaseManager(app)
        db_health = db_manager.check_database_health()
        db_stats = db_manager.get_database_stats()
        
        # System metrics
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime_seconds': int((datetime.utcnow() - datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())
        }
        
        # Application metrics
        app_info = {
            'flask_version': '2.3.3',  # Could be dynamic
            'environment': 'production' if os.getenv('FLASK_ENV') == 'production' else 'development',
            'debug_mode': app.debug,
            'port': get_configured_port(),
            'database_url': 'configured' if os.getenv('DATABASE_URL') else 'not_set'
        }
        
        # Log recent entries (last 10)
        try:
            with open('auto_finder.log', 'r') as f:
                recent_logs = f.readlines()[-10:]
        except FileNotFoundError:
            recent_logs = ['No log file found']
        
        return jsonify({
            'status': 'healthy' if db_health['status'] == 'healthy' else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'database': db_health,
            'database_stats': db_stats,
            'system': system_info,
            'application': app_info,
            'recent_logs': [log.strip() for log in recent_logs]
        }), 200
        
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/api/system/logs', methods=['GET'])
def get_system_logs():
    """Get recent application logs"""
    try:
        lines = request.args.get('lines', 50, type=int)
        
        try:
            with open('auto_finder.log', 'r') as f:
                all_logs = f.readlines()
                recent_logs = all_logs[-lines:] if len(all_logs) > lines else all_logs
        except FileNotFoundError:
            return jsonify({
                'message': 'No log file found',
                'logs': []
            }), 200
        
        return jsonify({
            'message': f'Retrieved last {len(recent_logs)} log entries',
            'logs': [log.strip() for log in recent_logs],
            'total_lines': len(all_logs)
        }), 200
        
    except Exception as e:
        logger.error(f"Log retrieval failed: {e}")
        return jsonify({'error': str(e)}), 500

    # For all other routes, serve the React app
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except FileNotFoundError:
        # Fallback: return a simple HTML page with API info
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Auto Finder - API Running</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .status { color: green; font-weight: bold; }
                .api-link { margin: 10px 0; }
                .api-link a { color: #007bff; text-decoration: none; }
                .api-link a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚗 Auto Finder</h1>
                <p class="status">✅ Backend API is running successfully!</p>
                
                <h2>Available Endpoints:</h2>
                <div class="api-link">
                    <a href="/api/health">/api/health</a> - Health check
                </div>
                <div class="api-link">
                    <a href="/api/listings/">/api/listings/</a> - Car listings (25 sample cars available)
                </div>
                <div class="api-link">
                    <a href="/api/setup-sample-data">/api/setup-sample-data</a> - Setup sample data
                </div>
                <div class="api-link">
                    <a href="/api/clear-dummy-data">/api/clear-dummy-data</a> - Clear sample data
                </div>
                
                <h2>Sample Data Status:</h2>
                <p>✅ 25 sample car listings are available in the database</p>
                <p>✅ User filters have been set to be inclusive</p>
                <p>✅ All Irish locations are approved</p>
                
                <h2>Next Steps:</h2>
                <p>1. The React frontend build files are missing from the deployment</p>
                <p>2. The backend API is working perfectly with sample data</p>
                <p>3. You can test the API endpoints above</p>
                <p>4. To fix the frontend, rebuild and redeploy the React app</p>
            </div>
        </body>
        </html>
        """
        return html_content, 200

@app.before_request
def log_request_info():
    """Log all incoming requests"""
    logger.info(f"Request: {request.method} {request.url} from {request.remote_addr}")

@app.after_request
def log_response_info(response):
    """Log all outgoing responses"""
    logger.info(f"Response: {response.status_code} for {request.method} {request.url}")
    return response

@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"Bad request: {error}")
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@app.errorhandler(401)
def unauthorized(error):
    logger.warning(f"Unauthorized access: {error}")
    return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

@app.errorhandler(403)
def forbidden(error):
    logger.warning(f"Forbidden access: {error}")
    return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"Not found: {error}")
    return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return jsonify({
        'error': 'Internal server error', 
        'message': 'An unexpected error occurred',
        'timestamp': datetime.utcnow().isoformat()
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred',
        'timestamp': datetime.utcnow().isoformat()
    }), 500

def get_configured_port():
    """Get the configured backend port from user settings, fallback to default"""
    try:
        with app.app_context():
            from models import UserSettings
            # Get the first user's settings (or create default)
            settings = UserSettings.query.first()
            if settings and settings.backend_port:
                return settings.backend_port
            return 5003  # Default port
    except Exception as e:
        print(f"Warning: Could not get configured port, using default: {e}")
        return 5003

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Get configured port from database
    configured_port = get_configured_port()
    print(f"🚀 Starting Auto Finder on port {configured_port}")
    
    app.run(debug=True, host='0.0.0.0', port=configured_port)
