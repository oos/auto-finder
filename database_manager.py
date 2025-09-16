"""
Database Management System for Auto Finder
Handles schema migrations, data integrity, and database health checks
"""

from database import db
from sqlalchemy import text, inspect
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database schema and data integrity"""
    
    def __init__(self, app):
        self.app = app
        
    def check_database_health(self):
        """Check if database is accessible and tables exist"""
        try:
            with self.app.app_context():
                # Test basic connection
                db.session.execute(text("SELECT 1"))
                
                # Check if main tables exist
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                
                required_tables = ['users', 'user_settings', 'car_listings', 'scrape_logs']
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    return {
                        'status': 'unhealthy',
                        'message': f'Missing tables: {missing_tables}',
                        'tables': tables
                    }
                
                return {
                    'status': 'healthy',
                    'message': 'Database is accessible and all tables exist',
                    'tables': tables
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}',
                'tables': []
            }
    
    def run_migrations(self):
        """Run all pending database migrations"""
        migrations = [
            self._add_notes_column,
            self._add_port_columns,
            self._add_missing_indexes,
            self._update_data_types
        ]
        
        results = []
        for migration in migrations:
            try:
                result = migration()
                results.append(result)
                logger.info(f"Migration {migration.__name__}: {result['status']}")
            except Exception as e:
                logger.error(f"Migration {migration.__name__} failed: {e}")
                results.append({
                    'migration': migration.__name__,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results
    
    def _add_notes_column(self):
        """Add notes column to scrape_logs table"""
        try:
            with self.app.app_context():
                # Check if column exists
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('scrape_logs')]
                
                if 'notes' not in columns:
                    db.session.execute(text("ALTER TABLE scrape_logs ADD COLUMN notes TEXT"))
                    db.session.commit()
                    return {
                        'migration': 'add_notes_column',
                        'status': 'success',
                        'message': 'Added notes column to scrape_logs'
                    }
                else:
                    return {
                        'migration': 'add_notes_column',
                        'status': 'skipped',
                        'message': 'Notes column already exists'
                    }
        except Exception as e:
            return {
                'migration': 'add_notes_column',
                'status': 'failed',
                'error': str(e)
            }
    
    def _add_port_columns(self):
        """Add port configuration columns to user_settings table"""
        try:
            with self.app.app_context():
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('user_settings')]
                
                results = []
                
                # Add frontend_port column
                if 'frontend_port' not in columns:
                    db.session.execute(text("ALTER TABLE user_settings ADD COLUMN frontend_port INTEGER DEFAULT 3000"))
                    db.session.execute(text("UPDATE user_settings SET frontend_port = 3000 WHERE frontend_port IS NULL"))
                    results.append('Added frontend_port column')
                
                # Add backend_port column
                if 'backend_port' not in columns:
                    db.session.execute(text("ALTER TABLE user_settings ADD COLUMN backend_port INTEGER DEFAULT 5003"))
                    db.session.execute(text("UPDATE user_settings SET backend_port = 5003 WHERE backend_port IS NULL"))
                    results.append('Added backend_port column')
                
                db.session.commit()
                
                return {
                    'migration': 'add_port_columns',
                    'status': 'success',
                    'message': '; '.join(results) if results else 'Port columns already exist'
                }
        except Exception as e:
            return {
                'migration': 'add_port_columns',
                'status': 'failed',
                'error': str(e)
            }
    
    def _add_missing_indexes(self):
        """Add missing database indexes for performance"""
        try:
            with self.app.app_context():
                indexes_added = []
                
                # Add indexes for common queries
                index_queries = [
                    "CREATE INDEX IF NOT EXISTS idx_car_listings_source_site ON car_listings(source_site)",
                    "CREATE INDEX IF NOT EXISTS idx_car_listings_make_model ON car_listings(make, model)",
                    "CREATE INDEX IF NOT EXISTS idx_car_listings_price ON car_listings(price)",
                    "CREATE INDEX IF NOT EXISTS idx_scrape_logs_user_id ON scrape_logs(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_scrape_logs_status ON scrape_logs(status)",
                    "CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id)"
                ]
                
                for query in index_queries:
                    try:
                        db.session.execute(text(query))
                        indexes_added.append(query.split('idx_')[1].split(' ON')[0])
                    except Exception as e:
                        logger.warning(f"Index creation failed (may already exist): {e}")
                
                db.session.commit()
                
                return {
                    'migration': 'add_missing_indexes',
                    'status': 'success',
                    'message': f'Added {len(indexes_added)} indexes: {", ".join(indexes_added)}'
                }
        except Exception as e:
            return {
                'migration': 'add_missing_indexes',
                'status': 'failed',
                'error': str(e)
            }
    
    def _update_data_types(self):
        """Update data types for better consistency"""
        try:
            with self.app.app_context():
                updates = []
                
                # Ensure price is INTEGER
                try:
                    db.session.execute(text("ALTER TABLE car_listings ALTER COLUMN price TYPE INTEGER"))
                    updates.append('Updated price to INTEGER')
                except Exception as e:
                    logger.warning(f"Price type update failed: {e}")
                
                # Ensure year is INTEGER
                try:
                    db.session.execute(text("ALTER TABLE car_listings ALTER COLUMN year TYPE INTEGER"))
                    updates.append('Updated year to INTEGER')
                except Exception as e:
                    logger.warning(f"Year type update failed: {e}")
                
                db.session.commit()
                
                return {
                    'migration': 'update_data_types',
                    'status': 'success',
                    'message': '; '.join(updates) if updates else 'Data types already correct'
                }
        except Exception as e:
            return {
                'migration': 'update_data_types',
                'status': 'failed',
                'error': str(e)
            }
    
    def get_database_stats(self):
        """Get database statistics and health metrics"""
        try:
            with self.app.app_context():
                stats = {}
                
                # Table row counts
                tables = ['users', 'user_settings', 'car_listings', 'scrape_logs']
                for table in tables:
                    try:
                        result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        stats[f'{table}_count'] = result.scalar()
                    except Exception as e:
                        stats[f'{table}_count'] = f'Error: {str(e)}'
                
                # Database size
                try:
                    result = db.session.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
                    stats['database_size'] = result.scalar()
                except Exception as e:
                    stats['database_size'] = f'Error: {str(e)}'
                
                # Recent activity
                try:
                    result = db.session.execute(text("""
                        SELECT COUNT(*) FROM scrape_logs 
                        WHERE started_at > NOW() - INTERVAL '24 hours'
                    """))
                    stats['scrapes_last_24h'] = result.scalar()
                except Exception as e:
                    stats['scrapes_last_24h'] = f'Error: {str(e)}'
                
                return {
                    'status': 'success',
                    'stats': stats,
                    'timestamp': datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
