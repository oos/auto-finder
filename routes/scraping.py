from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import User, ScrapeLog, CarListing
from datetime import datetime
import json

scraping_bp = Blueprint('scraping', __name__)

def scrape_log_to_dict(log):
    """Convert scrape log query result to dict"""
    return {
        'id': log.id,
        'site_name': log.site_name,
        'started_at': log.started_at.isoformat(),
        'completed_at': log.completed_at.isoformat() if log.completed_at else None,
        'status': log.status,
        'listings_found': log.listings_found,
        'listings_new': log.listings_new,
        'listings_updated': log.listings_updated,
        'listings_removed': log.listings_removed,
        'pages_scraped': log.pages_scraped,
        'errors': json.loads(log.errors) if log.errors else [],
        'notes': None,  # Handle missing notes column
        'is_blocked': log.is_blocked
    }

@scraping_bp.route('/status', methods=['GET'])
def get_scraping_status():
    try:
        # Get recent scrape logs (exclude notes column for production compatibility)
        recent_logs = db.session.query(
            ScrapeLog.id,
            ScrapeLog.site_name,
            ScrapeLog.started_at,
            ScrapeLog.completed_at,
            ScrapeLog.status,
            ScrapeLog.listings_found,
            ScrapeLog.listings_new,
            ScrapeLog.listings_updated,
            ScrapeLog.listings_removed,
            ScrapeLog.pages_scraped,
            ScrapeLog.errors,
            ScrapeLog.is_blocked
        ).order_by(ScrapeLog.started_at.desc()).limit(10).all()
        
        # Check if any scrape is currently running
        running_scrapes = db.session.query(
            ScrapeLog.id,
            ScrapeLog.site_name,
            ScrapeLog.started_at,
            ScrapeLog.completed_at,
            ScrapeLog.status,
            ScrapeLog.listings_found,
            ScrapeLog.listings_new,
            ScrapeLog.listings_updated,
            ScrapeLog.listings_removed,
            ScrapeLog.pages_scraped,
            ScrapeLog.errors,
            ScrapeLog.is_blocked
        ).filter_by(status='running').all()
        
        return jsonify({
            'recent_logs': [scrape_log_to_dict(log) for log in recent_logs],
            'is_running': len(running_scrapes) > 0,
            'running_scrapes': [scrape_log_to_dict(log) for log in running_scrapes]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/start', methods=['POST'])
@jwt_required()
def start_scraping():
    try:
        user_id = get_jwt_identity()
        # Convert string user_id to int for database query
        user_id = int(user_id) if user_id else None
        user = User.query.get(user_id)
        
        if not user or not user.settings:
            return jsonify({'error': 'User or settings not found'}), 404
        
        # Check if scraping is already running
        running_scrapes = db.session.query(ScrapeLog.id).filter_by(status='running').count()
        if running_scrapes > 0:
            return jsonify({'error': 'Scraping is already in progress'}), 409
        
        # Create a scrape log entry
        scrape_log = ScrapeLog(
            site_name='manual_scrape',
            status='running',
            started_at=datetime.utcnow()
        )
        db.session.add(scrape_log)
        db.session.commit()
        
        # Import and run the scraping engine
        try:
            # Try to import the full scraping engine first
            try:
                from scraping_engine import CarScrapingEngine
                engine_class = CarScrapingEngine
                engine_type = "full"
            except ImportError:
                # Fallback to simple scraping engine
                from scraping_engine_simple import SimpleCarScrapingEngine
                engine_class = SimpleCarScrapingEngine
                engine_type = "simple"
            
            # Run scraping in a separate thread to avoid blocking the API
            import threading
            
            def run_scraping():
                from app import app
                with app.app_context():
                    try:
                        engine = engine_class()
                        listings = engine.run_full_scrape(user_id, app.app_context())
                        
                        # Update scrape log
                        scrape_log.status = 'completed'
                        scrape_log.completed_at = datetime.utcnow()
                        scrape_log.listings_found = len(listings) if listings else 0
                        scrape_log.notes = f'Scraping completed successfully using {engine_type} engine. Found {len(listings) if listings else 0} listings.'
                        
                    except Exception as e:
                        # Update scrape log with error
                        scrape_log.status = 'failed'
                        scrape_log.completed_at = datetime.utcnow()
                        scrape_log.errors = str(e)
                        scrape_log.notes = f'Scraping failed using {engine_type} engine: {str(e)}'
                    
                    finally:
                        db.session.commit()
            
            # Start scraping in background thread
            scraping_thread = threading.Thread(target=run_scraping)
            scraping_thread.daemon = True
            scraping_thread.start()
            
            return jsonify({
                'message': f'Scraping started successfully using {engine_type} engine',
                'scrape_log_id': scrape_log.id,
                'engine_type': engine_type
            }), 200
            
        except ImportError as e:
            # Fallback if no scraping engine is available
            scrape_log.status = 'failed'
            scrape_log.completed_at = datetime.utcnow()
            scrape_log.errors = f'No scraping engine available: {str(e)}'
            db.session.commit()
            
            return jsonify({
                'error': 'No scraping engine available',
                'details': str(e)
            }), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/stop', methods=['POST'])
@jwt_required()
def stop_scraping():
    try:
        user_id = get_jwt_identity()
        # Convert string user_id to int for database query
        user_id = int(user_id) if user_id else None
        
        # Mark all running scrapes as stopped
        running_scrapes = db.session.query(ScrapeLog).filter_by(status='running').all()
        
        for scrape in running_scrapes:
            scrape.status = 'stopped'
            scrape.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': f'Stopped {len(running_scrapes)} running scrape(s)'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/logs', methods=['GET'])
def get_scrape_logs():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Get logs with pagination (exclude notes column for production compatibility)
        pagination = db.session.query(
            ScrapeLog.id,
            ScrapeLog.site_name,
            ScrapeLog.started_at,
            ScrapeLog.completed_at,
            ScrapeLog.status,
            ScrapeLog.listings_found,
            ScrapeLog.listings_new,
            ScrapeLog.listings_updated,
            ScrapeLog.listings_removed,
            ScrapeLog.pages_scraped,
            ScrapeLog.errors,
            ScrapeLog.is_blocked
        ).order_by(ScrapeLog.started_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs = pagination.items
        
        return jsonify({
            'logs': [scrape_log_to_dict(log) for log in logs],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/logs/<int:log_id>', methods=['GET'])
@jwt_required()
def get_scrape_log(log_id):
    try:
        user_id = get_jwt_identity()
        # Convert string user_id to int for database query
        user_id = int(user_id) if user_id else None
        
        log = ScrapeLog.query.get(log_id)
        
        if not log:
            return jsonify({'error': 'Scrape log not found'}), 404
        
        return jsonify({'log': log.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
