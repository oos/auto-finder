from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, CarListing, Blacklist
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta
import json

listings_bp = Blueprint('listings', __name__)

@listings_bp.route('/', methods=['GET'])
@jwt_required()
def get_listings():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.settings:
            return jsonify({'error': 'User or settings not found'}), 404
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Filters
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        min_score = request.args.get('min_score', type=float)
        max_score = request.args.get('max_score', type=float)
        make = request.args.get('make')
        model = request.args.get('model')
        location = request.args.get('location')
        status = request.args.get('status', 'active')
        fuel_type = request.args.get('fuel_type')
        transmission = request.args.get('transmission')
        year_min = request.args.get('year_min', type=int)
        year_max = request.args.get('year_max', type=int)
        mileage_max = request.args.get('mileage_max', type=int)
        price_dropped = request.args.get('price_dropped', type=bool)
        is_duplicate = request.args.get('is_duplicate', type=bool)
        
        # Sorting
        sort_by = request.args.get('sort_by', 'deal_score')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = CarListing.query
        
        # Apply filters
        if min_price is not None:
            query = query.filter(CarListing.price >= min_price)
        if max_price is not None:
            query = query.filter(CarListing.price <= max_price)
        if min_score is not None:
            query = query.filter(CarListing.deal_score >= min_score)
        if max_score is not None:
            query = query.filter(CarListing.deal_score <= max_score)
        if make:
            query = query.filter(CarListing.make.ilike(f'%{make}%'))
        if model:
            query = query.filter(CarListing.model.ilike(f'%{model}%'))
        if location:
            query = query.filter(CarListing.location.ilike(f'%{location}%'))
        if status:
            query = query.filter(CarListing.status == status)
        if fuel_type:
            query = query.filter(CarListing.fuel_type == fuel_type)
        if transmission:
            query = query.filter(CarListing.transmission == transmission)
        if year_min is not None:
            query = query.filter(CarListing.year >= year_min)
        if year_max is not None:
            query = query.filter(CarListing.year <= year_max)
        if mileage_max is not None:
            query = query.filter(CarListing.mileage <= mileage_max)
        if price_dropped is not None:
            query = query.filter(CarListing.price_dropped == price_dropped)
        if is_duplicate is not None:
            query = query.filter(CarListing.is_duplicate == is_duplicate)
        
        # Apply user's blacklist
        blacklist_keywords = [item.keyword for item in user.blacklists]
        for keyword in blacklist_keywords:
            query = query.filter(~CarListing.title.ilike(f'%{keyword}%'))
        
        # Apply user's price range if not overridden
        if min_price is None:
            query = query.filter(CarListing.price >= user.settings.min_price)
        if max_price is None:
            query = query.filter(CarListing.price <= user.settings.max_price)
        
        # Apply user's location filter if not overridden
        if not location:
            approved_locations = user.settings.get_approved_locations()
            if approved_locations:
                location_filters = [CarListing.location.ilike(f'%{loc}%') for loc in approved_locations]
                query = query.filter(or_(*location_filters))
        
        # Apply minimum deal score if not overridden
        if min_score is None:
            query = query.filter(CarListing.deal_score >= user.settings.min_deal_score)
        
        # Apply sorting
        if sort_by in ['deal_score', 'price', 'year', 'mileage', 'created_at', 'last_seen']:
            if sort_order == 'desc':
                query = query.order_by(desc(getattr(CarListing, sort_by)))
            else:
                query = query.order_by(asc(getattr(CarListing, sort_by)))
        else:
            query = query.order_by(desc(CarListing.deal_score))
        
        # Pagination
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        listings = pagination.items
        
        return jsonify({
            'listings': [listing.to_dict() for listing in listings],
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

@listings_bp.route('/<int:listing_id>', methods=['GET'])
@jwt_required()
def get_listing(listing_id):
    try:
        listing = CarListing.query.get(listing_id)
        
        if not listing:
            return jsonify({'error': 'Listing not found'}), 404
        
        return jsonify({'listing': listing.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@listings_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_listing_stats():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.settings:
            return jsonify({'error': 'User or settings not found'}), 404
        
        # Get base query with user filters
        query = CarListing.query
        
        # Apply user's blacklist
        blacklist_keywords = [item.keyword for item in user.blacklists]
        for keyword in blacklist_keywords:
            query = query.filter(~CarListing.title.ilike(f'%{keyword}%'))
        
        # Apply user's price range
        query = query.filter(
            and_(
                CarListing.price >= user.settings.min_price,
                CarListing.price <= user.settings.max_price
            )
        )
        
        # Apply user's location filter
        approved_locations = user.settings.get_approved_locations()
        if approved_locations:
            location_filters = [CarListing.location.ilike(f'%{loc}%') for loc in approved_locations]
            query = query.filter(or_(*location_filters))
        
        # Apply minimum deal score
        query = query.filter(CarListing.deal_score >= user.settings.min_deal_score)
        
        # Calculate stats
        total_listings = query.count()
        active_listings = query.filter(CarListing.status == 'active').count()
        removed_listings = query.filter(CarListing.status == 'removed').count()
        blocked_listings = query.filter(CarListing.status == 'blocked').count()
        
        # Price stats
        price_stats = query.with_entities(
            func.avg(CarListing.price).label('avg_price'),
            func.min(CarListing.price).label('min_price'),
            func.max(CarListing.price).label('max_price')
        ).first()
        
        # Deal score stats
        score_stats = query.with_entities(
            func.avg(CarListing.deal_score).label('avg_score'),
            func.min(CarListing.deal_score).label('min_score'),
            func.max(CarListing.deal_score).label('max_score')
        ).first()
        
        # Price drops
        price_drops = query.filter(CarListing.price_dropped == True).count()
        
        # Duplicates
        duplicates = query.filter(CarListing.is_duplicate == True).count()
        
        # Recent listings (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_listings = query.filter(CarListing.first_seen >= week_ago).count()
        
        # By source site
        by_site = query.with_entities(
            CarListing.source_site,
            func.count(CarListing.id).label('count')
        ).group_by(CarListing.source_site).all()
        
        # By make
        by_make = query.filter(CarListing.make.isnot(None)).with_entities(
            CarListing.make,
            func.count(CarListing.id).label('count')
        ).group_by(CarListing.make).order_by(desc('count')).limit(10).all()
        
        # By fuel type
        by_fuel = query.filter(CarListing.fuel_type.isnot(None)).with_entities(
            CarListing.fuel_type,
            func.count(CarListing.id).label('count')
        ).group_by(CarListing.fuel_type).all()
        
        return jsonify({
            'overview': {
                'total_listings': total_listings,
                'active_listings': active_listings,
                'removed_listings': removed_listings,
                'blocked_listings': blocked_listings,
                'price_drops': price_drops,
                'duplicates': duplicates,
                'recent_listings': recent_listings
            },
            'price_stats': {
                'avg_price': float(price_stats.avg_price) if price_stats.avg_price else 0,
                'min_price': int(price_stats.min_price) if price_stats.min_price else 0,
                'max_price': int(price_stats.max_price) if price_stats.max_price else 0
            },
            'score_stats': {
                'avg_score': float(score_stats.avg_score) if score_stats.avg_score else 0,
                'min_score': float(score_stats.min_score) if score_stats.min_score else 0,
                'max_score': float(score_stats.max_score) if score_stats.max_score else 0
            },
            'by_site': [{'site': item.source_site, 'count': item.count} for item in by_site],
            'by_make': [{'make': item.make, 'count': item.count} for item in by_make],
            'by_fuel': [{'fuel_type': item.fuel_type, 'count': item.count} for item in by_fuel]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@listings_bp.route('/top-deals', methods=['GET'])
@jwt_required()
def get_top_deals():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.settings:
            return jsonify({'error': 'User or settings not found'}), 404
        
        limit = min(request.args.get('limit', 20, type=int), 100)
        
        # Get base query with user filters
        query = CarListing.query.filter(CarListing.status == 'active')
        
        # Apply user's blacklist
        blacklist_keywords = [item.keyword for item in user.blacklists]
        for keyword in blacklist_keywords:
            query = query.filter(~CarListing.title.ilike(f'%{keyword}%'))
        
        # Apply user's price range
        query = query.filter(
            and_(
                CarListing.price >= user.settings.min_price,
                CarListing.price <= user.settings.max_price
            )
        )
        
        # Apply user's location filter
        approved_locations = user.settings.get_approved_locations()
        if approved_locations:
            location_filters = [CarListing.location.ilike(f'%{loc}%') for loc in approved_locations]
            query = query.filter(or_(*location_filters))
        
        # Apply minimum deal score
        query = query.filter(CarListing.deal_score >= user.settings.min_deal_score)
        
        # Get top deals
        top_deals = query.order_by(desc(CarListing.deal_score)).limit(limit).all()
        
        return jsonify({
            'top_deals': [listing.to_dict() for listing in top_deals]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@listings_bp.route('/search', methods=['GET'])
@jwt_required()
def search_listings():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.settings:
            return jsonify({'error': 'User or settings not found'}), 404
        
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return jsonify({'error': 'Search term is required'}), 400
        
        # Build search query
        query = CarListing.query.filter(
            or_(
                CarListing.title.ilike(f'%{search_term}%'),
                CarListing.make.ilike(f'%{search_term}%'),
                CarListing.model.ilike(f'%{search_term}%'),
                CarListing.location.ilike(f'%{search_term}%')
            )
        )
        
        # Apply user's blacklist
        blacklist_keywords = [item.keyword for item in user.blacklists]
        for keyword in blacklist_keywords:
            query = query.filter(~CarListing.title.ilike(f'%{keyword}%'))
        
        # Apply user's price range
        query = query.filter(
            and_(
                CarListing.price >= user.settings.min_price,
                CarListing.price <= user.settings.max_price
            )
        )
        
        # Apply user's location filter
        approved_locations = user.settings.get_approved_locations()
        if approved_locations:
            location_filters = [CarListing.location.ilike(f'%{loc}%') for loc in approved_locations]
            query = query.filter(or_(*location_filters))
        
        # Apply minimum deal score
        query = query.filter(CarListing.deal_score >= user.settings.min_deal_score)
        
        # Order by deal score
        query = query.order_by(desc(CarListing.deal_score))
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        listings = pagination.items
        
        return jsonify({
            'listings': [listing.to_dict() for listing in listings],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'search_term': search_term
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
