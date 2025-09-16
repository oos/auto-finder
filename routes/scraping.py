from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import User, ScrapeLog, CarListing
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
import json

scraping_bp = Blueprint('scraping', __name__)

def _safe_json_parse(json_str):
    """Safely parse JSON string, return empty list if invalid"""
    try:
        if json_str and json_str.strip():
            return json.loads(json_str)
        return []
    except (json.JSONDecodeError, TypeError):
        return []

def scrape_log_to_dict(log):
    """Convert scrape log query result to dict"""
    try:
        return {
            'id': getattr(log, 'id', None),
            'site_name': getattr(log, 'site_name', 'unknown'),
            'started_at': getattr(log, 'started_at', datetime.utcnow()).isoformat() if getattr(log, 'started_at', None) else None,
            'completed_at': getattr(log, 'completed_at', None).isoformat() if getattr(log, 'completed_at', None) else None,
            'status': getattr(log, 'status', 'unknown'),
            'listings_found': getattr(log, 'listings_found', 0),
            'listings_new': getattr(log, 'listings_new', 0),
            'listings_updated': getattr(log, 'listings_updated', 0),
            'listings_removed': getattr(log, 'listings_removed', 0),
            'pages_scraped': getattr(log, 'pages_scraped', 0),
            'errors': _safe_json_parse(getattr(log, 'errors', '[]')),
            'notes': getattr(log, 'notes', None),
            'is_blocked': getattr(log, 'is_blocked', False)
        }
    except Exception as e:
        # Fallback for any parsing errors
        return {
            'id': getattr(log, 'id', None),
            'site_name': 'unknown',
            'started_at': None,
            'completed_at': None,
            'status': 'error',
            'listings_found': 0,
            'listings_new': 0,
            'listings_updated': 0,
            'listings_removed': 0,
            'pages_scraped': 0,
            'errors': [str(e)],
            'notes': None,
            'is_blocked': False
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
    """Starts the real car scraping process."""
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id) if user_id else None
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        user = User.query.get(user_id)
        if not user or not user.settings:
            return jsonify({'error': 'User or settings not found'}), 404
        
        # Check if scraping is already running
        running_scrapes = db.session.query(ScrapeLog.id).filter_by(status='running').count()
        if running_scrapes > 0:
            return jsonify({'error': 'Scraping is already in progress'}), 409
        
        # Get scraping preferences from user settings
        settings = user.settings
        max_pages = settings.max_pages_per_site or 3

        # Create a new scrape log entry
        scrape_log = ScrapeLog(
            user_id=user_id,
            site_name='real_scraping',
            status='running',
            started_at=datetime.utcnow()
        )
        db.session.add(scrape_log)
        db.session.commit()

        try:
            # Import real scraping engine
            from scraping_engine_real import RealCarScrapingEngine
            from data_processor import DataProcessor

            # Initialize scrapers
            scraping_engine = RealCarScrapingEngine()
            data_processor = DataProcessor()

            # Scrape all enabled sites
            all_listings = []
            
            if settings.scrape_carzone:
                logger.info("Scraping Carzone.ie")
                carzone_listings = scraping_engine.scrape_single_site('carzone', max_pages)
                all_listings.extend(carzone_listings)
            
            if settings.scrape_donedeal:
                logger.info("Scraping DoneDeal.ie")
                donedeal_listings = scraping_engine.scrape_single_site('donedeal', max_pages)
                all_listings.extend(donedeal_listings)

            # Process and store listings
            logger.info(f"Processing {len(all_listings)} scraped listings")
            processing_stats = data_processor.process_listings(all_listings, user_id)

            # Update scrape log with results
            scrape_log.status = 'completed'
            scrape_log.completed_at = datetime.utcnow()
            scrape_log.listings_found = processing_stats['total_processed']
            scrape_log.listings_new = processing_stats['new_listings']
            scrape_log.listings_updated = processing_stats['updated_listings']
            scrape_log.notes = f'Real scraping completed. New: {processing_stats["new_listings"]}, Updated: {processing_stats["updated_listings"]}, Duplicates: {processing_stats["duplicates_skipped"]}'

        except Exception as e:
            # Handle any errors
            logger.error(f"Scraping failed: {e}")
            scrape_log.status = 'failed'
            scrape_log.completed_at = datetime.utcnow()
            scrape_log.errors = str(e)
            scrape_log.notes = f'Real scraping failed: {str(e)}'

        db.session.commit()

        return jsonify({
            'message': 'Real car scraping completed',
            'scrape_log_id': scrape_log.id,
            'engine_type': 'real',
            'listings_found': scrape_log.listings_found,
            'new_listings': processing_stats.get('new_listings', 0),
            'updated_listings': processing_stats.get('updated_listings', 0),
            'duplicates_skipped': processing_stats.get('duplicates_skipped', 0)
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Scraping route error: {e}")
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

@scraping_bp.route('/clear-all', methods=['POST'])
@jwt_required()
def clear_all_data():
    """Clear all scraping logs and dummy listings for a fresh start"""
    try:
        user_id = get_jwt_identity()
        # Convert string user_id to int for database query
        user_id = int(user_id) if user_id else None
        
        # Clear all scraping logs
        logs_deleted = db.session.query(ScrapeLog).delete()
        
        # Clear all dummy/sample listings
        from models import CarListing
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

@scraping_bp.route('/delete-failed', methods=['POST'])
@jwt_required()
def delete_failed_scrapes():
    """Delete only failed scraping attempts"""
    try:
        user_id = get_jwt_identity()
        # Convert string user_id to int for database query
        user_id = int(user_id) if user_id else None
        
        # Delete only failed scraping logs
        failed_logs_deleted = db.session.query(ScrapeLog).filter(
            ScrapeLog.status.in_(['failed', 'error'])
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Failed scrapes deleted successfully',
            'failed_logs_deleted': failed_logs_deleted
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/bulk-delete', methods=['POST'])
@jwt_required()
def bulk_delete_scrapes():
    """Delete selected scraping attempts by IDs"""
    try:
        user_id = get_jwt_identity()
        # Convert string user_id to int for database query
        user_id = int(user_id) if user_id else None
        
        data = request.get_json()
        if not data or 'ids' not in data:
            return jsonify({'error': 'No IDs provided'}), 400
        
        ids = data['ids']
        if not isinstance(ids, list) or len(ids) == 0:
            return jsonify({'error': 'Invalid IDs provided'}), 400
        
        # Delete selected scraping logs
        deleted_count = db.session.query(ScrapeLog).filter(
            ScrapeLog.id.in_(ids)
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Selected scrapes deleted successfully',
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/monitor/health', methods=['GET'])
@jwt_required()
def get_scraping_health():
    """Get scraping system health status"""
    try:
        # Try to import scraping monitor
        try:
            from scraping_monitor import ScrapingMonitor
            monitor = ScrapingMonitor()
            health_status = monitor.test_scraping_health()
            return jsonify(health_status), 200
        except ImportError as import_error:
            logger.warning(f"Scraping monitor not available, using fallback: {import_error}")
            # Use fallback monitoring
            from scraping_fallback import FallbackScrapingMonitor
            fallback_monitor = FallbackScrapingMonitor()
            health_status = fallback_monitor.test_scraping_health()
            return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'error',
            'error': str(e),
            'sites': {}
        }), 500

@scraping_bp.route('/monitor/stats', methods=['GET'])
@jwt_required()
def get_scraping_stats():
    """Get scraping statistics"""
    try:
        # Try to import scraping monitor
        try:
            from scraping_monitor import ScrapingMonitor
            days = request.args.get('days', 7, type=int)
            monitor = ScrapingMonitor()
            stats = monitor.get_scraping_stats(days)
            return jsonify(stats), 200
        except ImportError as import_error:
            logger.warning(f"Scraping monitor not available, using fallback: {import_error}")
            # Use fallback monitoring
            from scraping_fallback import FallbackScrapingMonitor
            fallback_monitor = FallbackScrapingMonitor()
            stats = fallback_monitor.get_scraping_stats(request.args.get('days', 7, type=int))
            return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/monitor/test-suite', methods=['POST'])
@jwt_required()
def run_test_suite():
    """Run comprehensive scraping test suite"""
    try:
        from scraping_monitor import ScrapingMonitor
        
        monitor = ScrapingMonitor()
        test_results = monitor.run_full_test_suite()
        
        return jsonify(test_results), 200
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/monitor/cleanup', methods=['POST'])
@jwt_required()
def cleanup_old_data():
    """Clean up old scraping data"""
    try:
        from scraping_monitor import ScrapingMonitor
        
        data = request.get_json() or {}
        days_old = data.get('days_old', 30)
        
        monitor = ScrapingMonitor()
        cleanup_results = monitor.cleanup_old_data(days_old)
        
        return jsonify(cleanup_results), 200
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/test-public', methods=['POST'])
def test_scraping_public():
    """Public test endpoint for scraping (no authentication required)"""
    try:
        # Get site from request
        data = request.get_json() or {}
        site_name = data.get('site', 'carzone')
        
        # Try to import scraping modules, fallback to simple version
        try:
            from scraping_engine_real import RealCarScrapingEngine
            from data_processor import DataProcessor
            
            # Initialize scrapers
            scraping_engine = RealCarScrapingEngine()
            data_processor = DataProcessor()
            
            # Test scrape single site with 1 page
            logger.info(f"Public test scraping for {site_name}")
            test_listings = scraping_engine.scrape_single_site(site_name, max_pages=1)
            
            return jsonify({
                'message': f'Public test completed for {site_name}',
                'site_tested': site_name,
                'listings_found': len(test_listings),
                'listings': test_listings[:3] if test_listings else []  # Show first 3 listings
            }), 200
            
        except ImportError as import_error:
            logger.warning(f"Scraping modules not available, using fallback: {import_error}")
            # Use fallback system
            from scraping_fallback import FallbackScrapingEngine
            fallback_engine = FallbackScrapingEngine()
            test_listings = fallback_engine.scrape_single_site(site_name, max_pages=1)
            
            return jsonify({
                'message': f'Fallback test completed for {site_name}',
                'site_tested': site_name,
                'listings_found': len(test_listings),
                'listings': test_listings[:3] if test_listings else [],
                'note': 'Using fallback system - sample data only'
            }), 200
        
    except Exception as e:
        logger.error(f"Public test scraping failed: {e}")
        return jsonify({
            'error': str(e),
            'message': 'Test failed due to server error',
            'site_tested': site_name,
            'listings_found': 0
        }), 500
