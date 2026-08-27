# ==================================================
# Application Configuration
# ==================================================
# Loads settings from environment variables (.env file)
# and provides config classes for different environments.
# ==================================================

import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


class Config:
    """Base configuration shared across all environments."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'ecommerce_db')

    # Session Security
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds
    SESSION_COOKIE_HTTPONLY = True    # Prevents JavaScript document.cookie access
    SESSION_COOKIE_SAMESITE = 'Lax'   # Prevents CSRF attacks
    SESSION_COOKIE_SECURE = False     # Set True in production when HTTPS is enabled


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False


# Config registry for easy lookup
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
