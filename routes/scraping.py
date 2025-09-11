from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import User, ScrapeLog, CarListing
from datetime import datetime
import json

scraping_bp = Blueprint('scraping', __name__)

@scraping_bp.route('/status', methods=['GET'])
@jwt_required()
def get_scraping_status():
    try:
        # Get recent scrape logs
        recent_logs = ScrapeLog.query.order_by(ScrapeLog.started_at.desc()).limit(10).all()
        
        # Check if any scrape is currently running
        running_scrapes = ScrapeLog.query.filter_by(status='running').all()
        
        return jsonify({
            'recent_logs': [log.to_dict() for log in recent_logs],
            'is_running': len(running_scrapes) > 0,
            'running_scrapes': [log.to_dict() for log in running_scrapes]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/start', methods=['POST'])
@jwt_required()
def start_scraping():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.settings:
            return jsonify({'error': 'User or settings not found'}), 404
        
        # Check if scraping is already running
        running_scrapes = ScrapeLog.query.filter_by(status='running').count()
        if running_scrapes > 0:
            return jsonify({'error': 'Scraping is already in progress'}), 409
        
        # This would typically trigger a background task
        # For now, we'll just return a success message
        # In production, you'd use Celery or similar to run this in the background
        
        return jsonify({
            'message': 'Scraping started',
            'note': 'This is a placeholder - actual scraping would be implemented with Celery'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/stop', methods=['POST'])
@jwt_required()
def stop_scraping():
    try:
        # Mark all running scrapes as stopped
        running_scrapes = ScrapeLog.query.filter_by(status='running').all()
        
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
@jwt_required()
def get_scrape_logs():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Get logs with pagination
        pagination = ScrapeLog.query.order_by(ScrapeLog.started_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs = pagination.items
        
        return jsonify({
            'logs': [log.to_dict() for log in logs],
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
        log = ScrapeLog.query.get(log_id)
        
        if not log:
            return jsonify({'error': 'Scrape log not found'}), 404
        
        return jsonify({'log': log.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
