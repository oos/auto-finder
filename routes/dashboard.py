from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import User, CarListing, ScrapeLog
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check without authentication"""
    try:
        from database import db
        from models import User, UserSettings, CarListing
        
        # Test database connection
        user_count = User.query.count()
        settings_count = UserSettings.query.count()
        listings_count = CarListing.query.count()
        
        return jsonify({
            'status': 'healthy',
            'database_connected': True,
            'user_count': user_count,
            'settings_count': settings_count,
            'listings_count': listings_count
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@dashboard_bp.route('/test', methods=['GET'])
@jwt_required()
def test_dashboard():
    """Test endpoint to debug user data"""
    try:
        user_id = get_jwt_identity()
        # Convert string user_id to int for database query
        user_id = int(user_id) if user_id else None
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user_id': user_id,
            'user_exists': user is not None,
            'has_settings': user.settings is not None,
            'settings_id': user.settings.id if user.settings else None,
            'user_email': user.email if user else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/overview', methods=['GET'])
def get_dashboard_overview():
    try:
        print(f"DEBUG: dashboard/overview called")
        # Temporarily use user ID 1 for testing
        user_id = 1
        print(f"DEBUG: using test user_id: {user_id}")
        user = User.query.get(user_id)
        print(f"DEBUG: user found: {user is not None}")
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Create settings if they don't exist
        if not user.settings:
            from models import UserSettings
            settings = UserSettings(user_id=user.id)
            db.session.add(settings)
            db.session.commit()
            user = User.query.get(user_id)  # Refresh user object
        
        # Debug: Check if settings exist and have required attributes
        if not user.settings:
            return jsonify({'error': 'Settings still not found after creation'}), 500
        
        # Check if settings have required attributes
        if not hasattr(user.settings, 'min_price'):
            return jsonify({'error': 'Settings missing required attributes'}), 500
        
        # Get base query with user filters
        query = CarListing.query
        
        # Apply user's blacklist
        try:
            blacklist_keywords = [item.keyword for item in user.blacklists]
            for keyword in blacklist_keywords:
                query = query.filter(~CarListing.title.ilike(f'%{keyword}%'))
        except Exception as e:
            print(f"Error accessing blacklists: {e}")
            blacklist_keywords = []
        
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
        
        # Calculate overview stats
        total_listings = query.count()
        active_listings = query.filter(CarListing.status == 'active').count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_listings = query.filter(CarListing.first_seen >= week_ago).count()
        
        # Price drops
        price_drops = query.filter(CarListing.price_dropped == True).count()
        
        # Top deals (score >= 80)
        top_deals = query.filter(
            and_(
                CarListing.status == 'active',
                CarListing.deal_score >= 80
            )
        ).count()
        
        # Average deal score
        avg_score = query.filter(CarListing.status == 'active').with_entities(
            func.avg(CarListing.deal_score)
        ).scalar() or 0
        
        # Recent scrape activity (exclude notes column for production compatibility)
        recent_scrapes = db.session.query(
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
        ).filter(
            ScrapeLog.started_at >= week_ago
        ).order_by(ScrapeLog.started_at.desc()).limit(5).all()
        
        return jsonify({
            'overview': {
                'total_listings': total_listings,
                'active_listings': active_listings,
                'recent_listings': recent_listings,
                'price_drops': price_drops,
                'top_deals': top_deals,
                'avg_deal_score': round(float(avg_score), 2)
            },
            'recent_scrapes': [log.to_dict() for log in recent_scrapes]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/charts/trends', methods=['GET'])
def get_trend_charts():
    try:
        user_id = 1  # Temporarily use test user
        user = User.query.get(user_id)
        
        if not user or not user.settings:
            return jsonify({'error': 'User or settings not found'}), 404
        
        # Get date range (default to last 30 days)
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get base query with user filters
        query = CarListing.query.filter(CarListing.first_seen >= start_date)
        
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
        
        # Daily listings trend
        daily_listings = query.with_entities(
            func.date(CarListing.first_seen).label('date'),
            func.count(CarListing.id).label('count')
        ).group_by(func.date(CarListing.first_seen)).order_by('date').all()
        
        # Daily average deal score
        daily_scores = query.filter(CarListing.status == 'active').with_entities(
            func.date(CarListing.first_seen).label('date'),
            func.avg(CarListing.deal_score).label('avg_score')
        ).group_by(func.date(CarListing.first_seen)).order_by('date').all()
        
        # Price drops by day
        daily_price_drops = query.filter(CarListing.price_dropped == True).with_entities(
            func.date(CarListing.updated_at).label('date'),
            func.count(CarListing.id).label('count')
        ).group_by(func.date(CarListing.updated_at)).order_by('date').all()
        
        return jsonify({
            'daily_listings': [
                {'date': str(item.date), 'count': item.count}
                for item in daily_listings
            ],
            'daily_scores': [
                {'date': str(item.date), 'avg_score': round(float(item.avg_score), 2)}
                for item in daily_scores
            ],
            'daily_price_drops': [
                {'date': str(item.date), 'count': item.count}
                for item in daily_price_drops
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/charts/distribution', methods=['GET'])
def get_distribution_charts():
    try:
        user_id = 1  # Temporarily use test user
        user = User.query.get(user_id)
        
        if not user or not user.settings:
            return jsonify({'error': 'User or settings not found'}), 404
        
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
        
        # By source site
        by_site = query.with_entities(
            CarListing.source_site,
            func.count(CarListing.id).label('count'),
            func.avg(CarListing.deal_score).label('avg_score')
        ).group_by(CarListing.source_site).all()
        
        # By make (top 10)
        by_make = query.filter(CarListing.make.isnot(None)).with_entities(
            CarListing.make,
            func.count(CarListing.id).label('count'),
            func.avg(CarListing.deal_score).label('avg_score')
        ).group_by(CarListing.make).order_by(func.count(CarListing.id).desc()).limit(10).all()
        
        # By fuel type
        by_fuel = query.filter(CarListing.fuel_type.isnot(None)).with_entities(
            CarListing.fuel_type,
            func.count(CarListing.id).label('count'),
            func.avg(CarListing.deal_score).label('avg_score')
        ).group_by(CarListing.fuel_type).all()
        
        # By transmission
        by_transmission = query.filter(CarListing.transmission.isnot(None)).with_entities(
            CarListing.transmission,
            func.count(CarListing.id).label('count'),
            func.avg(CarListing.deal_score).label('avg_score')
        ).group_by(CarListing.transmission).all()
        
        # By price range
        price_ranges = [
            (0, 5000, 'Under €5k'),
            (5000, 10000, '€5k - €10k'),
            (10000, 15000, '€10k - €15k'),
            (15000, 20000, '€15k - €20k'),
            (20000, 999999, 'Over €20k')
        ]
        
        by_price_range = []
        for min_price, max_price, label in price_ranges:
            count = query.filter(
                and_(
                    CarListing.price >= min_price,
                    CarListing.price < max_price
                )
            ).count()
            if count > 0:
                avg_score = query.filter(
                    and_(
                        CarListing.price >= min_price,
                        CarListing.price < max_price
                    )
                ).with_entities(func.avg(CarListing.deal_score)).scalar() or 0
                by_price_range.append({
                    'range': label,
                    'count': count,
                    'avg_score': round(float(avg_score), 2)
                })
        
        return jsonify({
            'by_site': [
                {
                    'site': item.source_site,
                    'count': item.count,
                    'avg_score': round(float(item.avg_score), 2)
                }
                for item in by_site
            ],
            'by_make': [
                {
                    'make': item.make,
                    'count': item.count,
                    'avg_score': round(float(item.avg_score), 2)
                }
                for item in by_make
            ],
            'by_fuel': [
                {
                    'fuel_type': item.fuel_type,
                    'count': item.count,
                    'avg_score': round(float(item.avg_score), 2)
                }
                for item in by_fuel
            ],
            'by_transmission': [
                {
                    'transmission': item.transmission,
                    'count': item.count,
                    'avg_score': round(float(item.avg_score), 2)
                }
                for item in by_transmission
            ],
            'by_price_range': by_price_range
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/alerts', methods=['GET'])
def get_alerts():
    try:
        user_id = 1  # Temporarily use test user
        user = User.query.get(user_id)
        
        if not user or not user.settings:
            return jsonify({'error': 'User or settings not found'}), 404
        
        alerts = []
        
        # Check for recent price drops
        recent_price_drops = CarListing.query.filter(
            and_(
                CarListing.price_dropped == True,
                CarListing.updated_at >= datetime.utcnow() - timedelta(hours=24)
            )
        ).count()
        
        if recent_price_drops > 0:
            alerts.append({
                'type': 'price_drop',
                'message': f'{recent_price_drops} cars had price drops in the last 24 hours',
                'count': recent_price_drops,
                'priority': 'high'
            })
        
        # Check for high-scoring deals
        high_score_deals = CarListing.query.filter(
            and_(
                CarListing.status == 'active',
                CarListing.deal_score >= 90,
                CarListing.first_seen >= datetime.utcnow() - timedelta(hours=24)
            )
        ).count()
        
        if high_score_deals > 0:
            alerts.append({
                'type': 'high_score',
                'message': f'{high_score_deals} high-scoring deals found in the last 24 hours',
                'count': high_score_deals,
                'priority': 'medium'
            })
        
        # Check for scraping issues (exclude notes column for production compatibility)
        recent_failed_scrapes = db.session.query(ScrapeLog.id).filter(
            and_(
                ScrapeLog.status == 'failed',
                ScrapeLog.started_at >= datetime.utcnow() - timedelta(hours=6)
            )
        ).count()
        
        if recent_failed_scrapes > 0:
            alerts.append({
                'type': 'scraping_error',
                'message': f'{recent_failed_scrapes} scraping jobs failed in the last 6 hours',
                'count': recent_failed_scrapes,
                'priority': 'high'
            })
        
        # Check for blocked scrapes (exclude notes column for production compatibility)
        recent_blocked_scrapes = db.session.query(ScrapeLog.id).filter(
            and_(
                ScrapeLog.is_blocked == True,
                ScrapeLog.started_at >= datetime.utcnow() - timedelta(hours=6)
            )
        ).count()
        
        if recent_blocked_scrapes > 0:
            alerts.append({
                'type': 'blocked_scrape',
                'message': f'{recent_blocked_scrapes} scraping jobs were blocked in the last 6 hours',
                'count': recent_blocked_scrapes,
                'priority': 'high'
            })
        
        return jsonify({
            'alerts': alerts,
            'total_alerts': len(alerts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
