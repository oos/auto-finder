from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Celery instance
celery_app = Celery('auto_finder')

# Configure Celery
celery_app.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        # Daily scraping at 6 AM UTC
        'daily-scraping': {
            'task': 'celery_app.run_daily_scraping',
            'schedule': crontab(hour=6, minute=0),
        },
        # Send daily emails at 9 AM UTC
        'daily-email-notifications': {
            'task': 'celery_app.send_daily_emails',
            'schedule': crontab(hour=9, minute=0),
        },
        # Clean up old data weekly
        'weekly-cleanup': {
            'task': 'celery_app.cleanup_old_data',
            'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Monday at 2 AM
        },
    }
)

@celery_app.task(bind=True)
def run_daily_scraping(self):
    """Run daily scraping for all active users"""
    try:
        from scraping_engine import CarScrapingEngine
        from models import db, User, ScrapeLog
        from app import app
        
        with app.app_context():
            # Get all active users
            users = User.query.filter_by(is_active=True).all()
            
            if not users:
                return "No active users found"
            
            # Initialize scraping engine
            engine = CarScrapingEngine()
            
            # Run scraping for each user
            total_listings = 0
            for user in users:
                if not user.settings:
                    continue
                
                # Create scrape log
                scrape_log = ScrapeLog(
                    site_name='all_sites',
                    status='running'
                )
                db.session.add(scrape_log)
                db.session.commit()
                
                try:
                    # Run scraping
                    listings = engine.run_full_scrape(user.id)
                    total_listings += len(listings) if listings else 0
                    
                    # Update log
                    scrape_log.status = 'completed'
                    scrape_log.completed_at = db.func.now()
                    scrape_log.listings_found = len(listings) if listings else 0
                    
                except Exception as e:
                    # Update log with error
                    scrape_log.status = 'failed'
                    scrape_log.completed_at = db.func.now()
                    scrape_log.errors = str(e)
                    
                finally:
                    db.session.commit()
            
            return f"Daily scraping completed. Found {total_listings} listings across {len(users)} users"
            
    except Exception as e:
        return f"Daily scraping failed: {str(e)}"

@celery_app.task(bind=True)
def send_daily_emails(self):
    """Send daily email notifications to all users"""
    try:
        from email_service import EmailService
        from models import User, UserSettings
        from app import app
        
        with app.app_context():
            email_service = EmailService()
            success_count = email_service.send_all_daily_summaries()
            
            return f"Daily emails sent to {success_count} users"
            
    except Exception as e:
        return f"Daily email sending failed: {str(e)}"

@celery_app.task(bind=True)
def cleanup_old_data(self):
    """Clean up old data to keep database size manageable"""
    try:
        from models import db, ScrapeLog, EmailLog, CarListing
        from datetime import datetime, timedelta
        from app import app
        
        with app.app_context():
            # Keep only last 30 days of scrape logs
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            old_logs = ScrapeLog.query.filter(ScrapeLog.started_at < cutoff_date).all()
            for log in old_logs:
                db.session.delete(log)
            
            # Keep only last 90 days of email logs
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            old_emails = EmailLog.query.filter(EmailLog.sent_at < cutoff_date).all()
            for email in old_emails:
                db.session.delete(email)
            
            # Mark old removed listings for deletion (older than 7 days)
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            old_removed = CarListing.query.filter(
                CarListing.status == 'removed',
                CarListing.updated_at < cutoff_date
            ).all()
            for listing in old_removed:
                db.session.delete(listing)
            
            db.session.commit()
            
            return f"Cleanup completed. Removed {len(old_logs)} logs, {len(old_emails)} emails, {len(old_removed)} old listings"
            
    except Exception as e:
        return f"Cleanup failed: {str(e)}"

@celery_app.task(bind=True)
def run_manual_scraping(self, user_id=None):
    """Run manual scraping for a specific user or all users"""
    try:
        from scraping_engine import CarScrapingEngine
        from models import db, User
        from app import app
        
        with app.app_context():
            engine = CarScrapingEngine()
            
            if user_id:
                # Scrape for specific user
                user = User.query.get(user_id)
                if not user:
                    return f"User {user_id} not found"
                
                listings = engine.run_full_scrape(user_id)
                return f"Manual scraping completed for user {user_id}. Found {len(listings) if listings else 0} listings"
            else:
                # Scrape for all users
                return run_daily_scraping.delay()
                
    except Exception as e:
        return f"Manual scraping failed: {str(e)}"

@celery_app.task(bind=True)
def send_test_email(self, user_id):
    """Send a test email to a specific user"""
    try:
        from email_service import EmailService
        from models import User
        from app import app
        
        with app.app_context():
            user = User.query.get(user_id)
            if not user:
                return f"User {user_id} not found"
            
            email_service = EmailService()
            success = email_service.send_daily_summary(user_id)
            
            return f"Test email {'sent' if success else 'failed'} to user {user_id}"
            
    except Exception as e:
        return f"Test email failed: {str(e)}"

# Health check task
@celery_app.task
def health_check():
    """Simple health check task"""
    return "Celery worker is healthy"

if __name__ == '__main__':
    celery_app.start()
