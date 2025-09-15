from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import User, UserSettings, Blacklist
from datetime import datetime

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/', methods=['GET'])
def get_settings():
    try:
        user_id = 2  # Temporarily use test user
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
        # Convert string user_id to int for database query
        user_id = int(user_id) if user_id else None
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
        
        # Update port settings
        if 'frontend_port' in data:
            port = int(data['frontend_port'])
            if port < 1024 or port > 65535:
                return jsonify({'error': 'Frontend port must be between 1024 and 65535'}), 400
            settings.frontend_port = port
        if 'backend_port' in data:
            port = int(data['backend_port'])
            if port < 1024 or port > 65535:
                return jsonify({'error': 'Backend port must be between 1024 and 65535'}), 400
            settings.backend_port = port
        
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
        
        # Convert string user_id to int for database query
        user_id = int(user_id) if user_id else None
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
        
        # Convert string user_id to int for database query
        user_id = int(user_id) if user_id else None
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
        # Convert string user_id to int for database query
        user_id = int(user_id) if user_id else None
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

@settings_bp.route('/fix-filters', methods=['POST'])
def fix_filters():
    """Fix user filters to show all listings - temporary endpoint for debugging"""
    try:
        from sqlalchemy import or_
        
        # Get all users
        users = User.query.all()
        updated_count = 0
        
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
                updated_count += 1
        
        db.session.commit()
        
        # Check total listings
        total_listings = CarListing.query.count()
        
        return jsonify({
            'message': 'Filters updated successfully',
            'users_updated': updated_count,
            'total_listings': total_listings
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
