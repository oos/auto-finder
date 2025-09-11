import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from models import db, User, CarListing, EmailLog
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@autofinder.com')
    
    def send_daily_summary(self, user_id):
        """Send daily summary email to user"""
        try:
            user = User.query.get(user_id)
            if not user or not user.settings:
                logger.error(f"User {user_id} or settings not found")
                return False
            
            if not user.settings.email_notifications:
                logger.info(f"Email notifications disabled for user {user_id}")
                return True
            
            # Get top deals for user
            top_deals = self.get_top_deals_for_user(user)
            
            # Get scraping summary
            scrape_summary = self.get_scrape_summary()
            
            # Build email content
            subject = "New Matching Used Car Deals [Auto Tracker]"
            html_content = self.build_email_html(user, top_deals, scrape_summary)
            text_content = self.build_email_text(user, top_deals, scrape_summary)
            
            # Send email
            from_email = Email(self.from_email)
            to_email = To(user.email)
            
            mail = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=text_content,
                html_content=html_content
            )
            
            response = self.sg.send(mail)
            
            # Log email
            email_log = EmailLog(
                user_id=user_id,
                subject=subject,
                listings_included=len(top_deals),
                total_listings_scraped=scrape_summary.get('total_listings', 0),
                status='sent' if response.status_code == 202 else 'failed'
            )
            db.session.add(email_log)
            db.session.commit()
            
            logger.info(f"Daily summary email sent to user {user_id}")
            return response.status_code == 202
            
        except Exception as e:
            logger.error(f"Error sending daily summary to user {user_id}: {e}")
            
            # Log failed email
            try:
                email_log = EmailLog(
                    user_id=user_id,
                    subject="New Matching Used Car Deals [Auto Tracker]",
                    listings_included=0,
                    total_listings_scraped=0,
                    status='failed'
                )
                db.session.add(email_log)
                db.session.commit()
            except:
                pass
            
            return False
    
    def get_top_deals_for_user(self, user):
        """Get top 20 deals for user based on their settings"""
        try:
            # Build query with user filters
            query = CarListing.query.filter(CarListing.status == 'active')
            
            # Apply user's blacklist
            blacklist_keywords = [item.keyword for item in user.blacklists]
            for keyword in blacklist_keywords:
                query = query.filter(~CarListing.title.ilike(f'%{keyword}%'))
            
            # Apply user's price range
            query = query.filter(
                CarListing.price >= user.settings.min_price,
                CarListing.price <= user.settings.max_price
            )
            
            # Apply user's location filter
            approved_locations = user.settings.get_approved_locations()
            if approved_locations:
                location_filters = [CarListing.location.ilike(f'%{loc}%') for loc in approved_locations]
                query = query.filter(or_(*location_filters))
            
            # Apply minimum deal score
            query = query.filter(CarListing.deal_score >= user.settings.min_deal_score)
            
            # Get top 20 deals
            top_deals = query.order_by(CarListing.deal_score.desc()).limit(20).all()
            
            return top_deals
            
        except Exception as e:
            logger.error(f"Error getting top deals for user {user.id}: {e}")
            return []
    
    def get_scrape_summary(self):
        """Get summary of recent scraping activity"""
        try:
            # Get scraping stats for last 24 hours
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            recent_logs = ScrapeLog.query.filter(
                ScrapeLog.started_at >= yesterday
            ).all()
            
            total_listings = sum(log.listings_found for log in recent_logs)
            total_pages = sum(log.pages_scraped for log in recent_logs)
            blocked_sites = [log.site_name for log in recent_logs if log.is_blocked]
            
            return {
                'total_listings': total_listings,
                'total_pages': total_pages,
                'sites_scraped': len(recent_logs),
                'blocked_sites': blocked_sites
            }
            
        except Exception as e:
            logger.error(f"Error getting scrape summary: {e}")
            return {
                'total_listings': 0,
                'total_pages': 0,
                'sites_scraped': 0,
                'blocked_sites': []
            }
    
    def build_email_html(self, user, top_deals, scrape_summary):
        """Build HTML email content"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Auto Finder Daily Summary</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .summary {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .deal-item {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .deal-score {{ background-color: #27ae60; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
                .price {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
                .location {{ color: #7f8c8d; }}
                .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 Auto Finder Daily Summary</h1>
                    <p>Your personalized used car deals for {datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                
                <div class="summary">
                    <h2>📊 Scraping Summary</h2>
                    <p><strong>Total Listings Found:</strong> {scrape_summary['total_listings']:,}</p>
                    <p><strong>Pages Scraped:</strong> {scrape_summary['total_pages']:,}</p>
                    <p><strong>Sites Scraped:</strong> {scrape_summary['sites_scraped']}</p>
                    {f"<p><strong>⚠️ Blocked Sites:</strong> {', '.join(scrape_summary['blocked_sites'])}</p>" if scrape_summary['blocked_sites'] else ""}
                </div>
                
                <h2>🏆 Top {len(top_deals)} Deals</h2>
        """
        
        if top_deals:
            for i, deal in enumerate(top_deals, 1):
                html += f"""
                <div class="deal-item">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h3 style="margin: 0;">{i}. {deal.title}</h3>
                        <span class="deal-score">{deal.deal_score:.1f}</span>
                    </div>
                    <div class="price">€{deal.price:,}</div>
                    <div class="location">📍 {deal.location}</div>
                    <div style="margin-top: 10px;">
                        <a href="{deal.url}" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px;">View Listing</a>
                    </div>
                </div>
                """
        else:
            html += "<p>No matching deals found based on your current settings.</p>"
        
        html += f"""
                <div class="footer">
                    <p>This email was sent by Auto Finder</p>
                    <p>To update your preferences, visit your dashboard</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def build_email_text(self, user, top_deals, scrape_summary):
        """Build plain text email content"""
        text = f"""
Auto Finder Daily Summary - {datetime.now().strftime('%B %d, %Y')}

Scraping Summary:
- Total Listings Found: {scrape_summary['total_listings']:,}
- Pages Scraped: {scrape_summary['total_pages']:,}
- Sites Scraped: {scrape_summary['sites_scraped']}
"""
        
        if scrape_summary['blocked_sites']:
            text += f"- Blocked Sites: {', '.join(scrape_summary['blocked_sites'])}\n"
        
        text += f"\nTop {len(top_deals)} Deals:\n\n"
        
        if top_deals:
            for i, deal in enumerate(top_deals, 1):
                text += f"""
{i}. {deal.title}
   Price: €{deal.price:,}
   Location: {deal.location}
   Deal Score: {deal.deal_score:.1f}
   Link: {deal.url}
"""
        else:
            text += "No matching deals found based on your current settings.\n"
        
        text += "\n---\nThis email was sent by Auto Finder\nTo update your preferences, visit your dashboard"
        
        return text
    
    def send_all_daily_summaries(self):
        """Send daily summaries to all users with email notifications enabled"""
        try:
            users = User.query.filter(
                User.is_active == True,
                User.settings.has(UserSettings.email_notifications == True)
            ).all()
            
            success_count = 0
            for user in users:
                if self.send_daily_summary(user.id):
                    success_count += 1
            
            logger.info(f"Sent daily summaries to {success_count}/{len(users)} users")
            return success_count
            
        except Exception as e:
            logger.error(f"Error sending daily summaries: {e}")
            return 0

# Example usage
if __name__ == "__main__":
    email_service = EmailService()
    email_service.send_all_daily_summaries()
