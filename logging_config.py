import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging():
    """Set up comprehensive logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'auto_finder.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'errors.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Scraping specific logger
    scraping_logger = logging.getLogger('scraping')
    scraping_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'scraping.log'),
        maxBytes=20*1024*1024,  # 20MB
        backupCount=10
    )
    scraping_handler.setLevel(logging.INFO)
    scraping_handler.setFormatter(detailed_formatter)
    scraping_logger.addHandler(scraping_handler)
    scraping_logger.setLevel(logging.INFO)
    
    # Email specific logger
    email_logger = logging.getLogger('email')
    email_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'email.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )
    email_handler.setLevel(logging.INFO)
    email_handler.setFormatter(detailed_formatter)
    email_logger.addHandler(email_handler)
    email_logger.setLevel(logging.INFO)
    
    # Database specific logger
    db_logger = logging.getLogger('sqlalchemy.engine')
    db_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'database.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3
    )
    db_handler.setLevel(logging.WARNING)
    db_handler.setFormatter(detailed_formatter)
    db_logger.addHandler(db_handler)
    db_logger.setLevel(logging.WARNING)
    
    # Celery specific logger
    celery_logger = logging.getLogger('celery')
    celery_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'celery.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    celery_handler.setLevel(logging.INFO)
    celery_handler.setFormatter(detailed_formatter)
    celery_logger.addHandler(celery_handler)
    celery_logger.setLevel(logging.INFO)
    
    # Suppress some noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name):
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

# Custom logging functions
def log_scraping_start(site_name, user_id=None):
    """Log the start of a scraping operation"""
    logger = get_logger('scraping')
    logger.info(f"Starting scraping for {site_name}" + (f" (User: {user_id})" if user_id else ""))

def log_scraping_end(site_name, listings_found, errors=None, user_id=None):
    """Log the end of a scraping operation"""
    logger = get_logger('scraping')
    message = f"Completed scraping for {site_name}. Found {listings_found} listings"
    if user_id:
        message += f" (User: {user_id})"
    if errors:
        message += f". Errors: {errors}"
    logger.info(message)

def log_scraping_error(site_name, error, user_id=None):
    """Log a scraping error"""
    logger = get_logger('scraping')
    logger.error(f"Scraping error for {site_name}: {str(error)}" + (f" (User: {user_id})" if user_id else ""))

def log_email_sent(user_id, subject, listings_count):
    """Log email sending"""
    logger = get_logger('email')
    logger.info(f"Email sent to user {user_id}: {subject} ({listings_count} listings)")

def log_email_error(user_id, error):
    """Log email sending error"""
    logger = get_logger('email')
    logger.error(f"Email error for user {user_id}: {str(error)}")

def log_database_error(operation, error):
    """Log database operation error"""
    logger = get_logger('database')
    logger.error(f"Database error during {operation}: {str(error)}")

def log_celery_task(task_name, status, message=""):
    """Log Celery task execution"""
    logger = get_logger('celery')
    logger.info(f"Celery task {task_name}: {status}" + (f" - {message}" if message else ""))

# Initialize logging when module is imported
setup_logging()
