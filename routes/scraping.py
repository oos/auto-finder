from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import User, ScrapeLog, CarListing
from datetime import datetime
import json

scraping_bp = Blueprint('scraping', __name__)

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
            'errors': json.loads(getattr(log, 'errors', '[]')) if getattr(log, 'errors', None) else [],
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
        
        # For now, just mark as completed since we're not doing real scraping yet
        # This will be replaced with actual scraping logic when ready
        scrape_log.status = 'completed'
        scrape_log.completed_at = datetime.utcnow()
        scrape_log.listings_found = 0
        scrape_log.notes = 'Scraping endpoint ready - no actual scraping implemented yet'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Scraping endpoint ready - no actual scraping implemented yet',
            'scrape_log_id': scrape_log.id,
            'engine_type': 'none'
        }), 200
        
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
