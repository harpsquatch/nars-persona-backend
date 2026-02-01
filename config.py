# filepath: /c:/ML_Projects/learning_datamodelling/app/config.py
import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from a .env file
load_dotenv()

class Config:
    # Load from Railway-provided `DATABASE_URL` or fallback to manual settings
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if DATABASE_URL:
        # Convert mysql:// → mysql+pymysql:// (required for SQLAlchemy)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("mysql://", "mysql+pymysql://")
    else:
        # Local fallback (for development)
        MYSQL_HOST = os.getenv('MYSQLHOST', 'localhost')
        MYSQL_USER = os.getenv('MYSQLUSER', 'root')
        MYSQL_PASSWORD = os.getenv('MYSQLPASSWORD', 'mysql')
        MYSQL_DB = os.getenv('MYSQLDATABASE', 'narsbeauty')
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    
    # Add connection pooling for stability
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'pool_recycle': 280,  # Recycle connections before MySQL's default timeout
        'pool_pre_ping': True,  # Verify connections before using them
        'max_overflow': 10
    }
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '8wkfDfzZdBLLfccIyBSgM7zcdUXokA8H3zNSho3zMNU=')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
    
    # Other Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    DEBUG = False  # Default to False for security
    PROPAGATE_EXCEPTIONS = True  # Ensure exceptions are properly handled
    
    # Add timeout settings for requests
    TIMEOUT = 30  # 30 second timeout for external requests
    
    # Add logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # In production, we should be more strict about security
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 280,
        'pool_pre_ping': True,
        'max_overflow': 20,
        'connect_args': {
            'connect_timeout': 10,
            'read_timeout': 30,
            'write_timeout': 30
        }
    }
    # Ensure we're using environment variables in production
    SQLALCHEMY_DATABASE_URI = os.getenv('MYSQL_URL')
    if not SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = f'mysql://{os.getenv("MYSQLUSER")}:{os.getenv("MYSQLPASSWORD")}@{os.getenv("MYSQLHOST")}/{os.getenv("MYSQLDATABASE")}'

# You can add more configurations for different environments

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}