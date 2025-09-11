from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, UserSettings, Blacklist
from datetime import datetime

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/', methods=['GET'])
@jwt_required()
def get_settings():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.settings:
            # Create default settings if they don't exist
            settings = UserSettings(user_id=user_id)
            db.session.add(settings)
            db.session.commit()
            user = User.query.get(user_id)  # Refresh user object
        
        # Get blacklist
        blacklist = Blacklist.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'settings': user.settings.to_dict(),
            'blacklist': [item.to_dict() for item in blacklist]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/', methods=['PUT'])
@jwt_required()
def update_settings():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.settings:
            settings = UserSettings(user_id=user_id)
            db.session.add(settings)
            db.session.commit()
            user = User.query.get(user_id)  # Refresh user object
        
        data = request.get_json()
        settings = user.settings
        
        # Update price range
        if 'min_price' in data:
            settings.min_price = max(0, int(data['min_price']))
        if 'max_price' in data:
            settings.max_price = max(settings.min_price, int(data['max_price']))
        
        # Update locations
        if 'approved_locations' in data:
            if isinstance(data['approved_locations'], list):
                settings.set_approved_locations(data['approved_locations'])
            else:
                return jsonify({'error': 'approved_locations must be an array'}), 400
        
        # Update scraping settings
        if 'max_pages_per_site' in data:
            settings.max_pages_per_site = max(1, int(data['max_pages_per_site']))
        if 'min_deal_score' in data:
            settings.min_deal_score = max(0, min(100, int(data['min_deal_score'])))
        
        # Update site toggles
        site_toggles = [
            'scrape_carzone', 'scrape_donedeal', 'scrape_adverts',
            'scrape_carsireland', 'scrape_lewismotors'
        ]
        for toggle in site_toggles:
            if toggle in data:
                setattr(settings, toggle, bool(data[toggle]))
        
        # Update deal scoring weights
        weight_fields = [
            'weight_price_vs_market', 'weight_mileage_vs_year', 'weight_co2_tax_band',
            'weight_popularity_rarity', 'weight_price_dropped', 'weight_location_match',
            'weight_listing_freshness'
        ]
        
        total_weight = 0
        for field in weight_fields:
            if field in data:
                weight = max(0, min(100, int(data[field])))
                setattr(settings, field, weight)
                total_weight += weight
        
        # Validate weights total 100
        if total_weight > 0 and total_weight != 100:
            return jsonify({'error': f'Deal scoring weights must total 100, currently totals {total_weight}'}), 400
        
        # Update email settings
        if 'email_notifications' in data:
            settings.email_notifications = bool(data['email_notifications'])
        if 'daily_email_time' in data:
            # Validate time format (HH:MM)
            time_str = data['daily_email_time']
            try:
                datetime.strptime(time_str, '%H:%M')
                settings.daily_email_time = time_str
            except ValueError:
                return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
        
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Settings updated successfully',
            'settings': settings.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/blacklist', methods=['POST'])
@jwt_required()
def add_blacklist_item():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('keyword'):
            return jsonify({'error': 'Keyword is required'}), 400
        
        keyword = data['keyword'].strip().lower()
        
        # Check if keyword already exists
        existing = Blacklist.query.filter_by(user_id=user_id, keyword=keyword).first()
        if existing:
            return jsonify({'error': 'Keyword already in blacklist'}), 409
        
        # Add to blacklist
        blacklist_item = Blacklist(
            user_id=user_id,
            keyword=keyword
        )
        
        db.session.add(blacklist_item)
        db.session.commit()
        
        return jsonify({
            'message': 'Keyword added to blacklist',
            'item': blacklist_item.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/blacklist/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_blacklist_item(item_id):
    try:
        user_id = get_jwt_identity()
        
        blacklist_item = Blacklist.query.filter_by(id=item_id, user_id=user_id).first()
        if not blacklist_item:
            return jsonify({'error': 'Blacklist item not found'}), 404
        
        db.session.delete(blacklist_item)
        db.session.commit()
        
        return jsonify({'message': 'Keyword removed from blacklist'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/blacklist', methods=['GET'])
@jwt_required()
def get_blacklist():
    try:
        user_id = get_jwt_identity()
        
        blacklist_items = Blacklist.query.filter_by(user_id=user_id).order_by(Blacklist.created_at.desc()).all()
        
        return jsonify({
            'blacklist': [item.to_dict() for item in blacklist_items]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/reset-weights', methods=['POST'])
@jwt_required()
def reset_weights():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.settings:
            return jsonify({'error': 'User or settings not found'}), 404
        
        settings = user.settings
        
        # Reset to default weights
        settings.weight_price_vs_market = 25
        settings.weight_mileage_vs_year = 20
        settings.weight_co2_tax_band = 15
        settings.weight_popularity_rarity = 15
        settings.weight_price_dropped = 10
        settings.weight_location_match = 10
        settings.weight_listing_freshness = 5
        
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Weights reset to default values',
            'settings': settings.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
