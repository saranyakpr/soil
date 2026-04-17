"""
Configuration settings for Soil Vision 360
Supports development, testing, and production environments
"""

import os
from datetime import timedelta
from urllib.parse import quote_plus

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-secret-key-in-production'
    
    # Database
    MYSQL_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.environ.get("DB_PORT", 3306))
    MYSQL_USER = os.environ.get("DB_USER", "root")
    MYSQL_PASSWORD = os.environ.get("DB_PASSWORD", "")
    MYSQL_DB = os.environ.get("DB_NAME", "soil_vision_360")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        (
            f"mysql+pymysql://{quote_plus(MYSQL_USER)}:"
            f"{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        ),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'connect_args': {'charset': 'utf8mb4'}
    }
    
    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
    
    # JWT / Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt-secret-sv360')
    
    # Reports
    REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'reports')
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    
    # CORS
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
    
    # Rate limiting
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Weather/Climate API
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')

    # SoilBot AI provider - SambaNova Cloud
    SAMBANOVA_API_KEY = os.environ.get('SAMBANOVA_API_KEY', '')
    SAMBANOVA_BASE_URL = os.environ.get('SAMBANOVA_BASE_URL', 'https://api.sambanova.ai/v1')
    SAMBANOVA_MODEL = os.environ.get('SAMBANOVA_MODEL', 'Meta-Llama-3.3-70B-Instruct')
    SAMBANOVA_TIMEOUT = int(os.environ.get('SAMBANOVA_TIMEOUT', 30))
    
    # OAuth Settings
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', '')
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', '')
    
    # OAuth Redirect URIs
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', f'{BASE_URL}/auth/google/callback')
    GITHUB_REDIRECT_URI = os.environ.get('GITHUB_REDIRECT_URI', f'{BASE_URL}/auth/github/callback')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False  # Set True to see SQL queries


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Force HTTPS in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
