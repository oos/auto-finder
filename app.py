from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
import os
from datetime import datetime
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

# JWT configuration
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return identity

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
    
    # For all other routes, serve the React app
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except FileNotFoundError:
        return jsonify({'error': 'React app not built'}), 500

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
