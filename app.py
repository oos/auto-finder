from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
from database import db

# Load environment variables
load_dotenv()

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

# Serve React app for all non-API routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    print(f"DEBUG: Serving path: '{path}'")
    
    # Don't serve React app for API routes
    if path.startswith('api/'):
        print(f"DEBUG: API route detected, returning 404")
        return jsonify({'error': 'Not found'}), 404
    
    # Check if it's a static file (JS, CSS, images, etc.)
    if path and not path.startswith('api/'):
        static_file_path = os.path.join(app.static_folder, path)
        print(f"DEBUG: Checking static file: {static_file_path}")
        if os.path.exists(static_file_path):
            print(f"DEBUG: Serving static file: {path}")
            return send_from_directory(app.static_folder, path)
    
    # For all other routes (including /dashboard, /login, etc.), serve index.html
    # This allows React Router to handle client-side routing
    print(f"DEBUG: Serving index.html for path: {path}")
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
