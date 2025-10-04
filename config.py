"""
Production Configuration for NBA Lineup Optimizer
"""

import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Base configuration class."""
    
    # Application settings
    APP_NAME = "NBA Lineup Optimizer"
    VERSION = "1.0.0"
    DEBUG = False
    
    # Database settings
    DATABASE_PATH = os.getenv("DATABASE_PATH", "src/nba_stats/db/nba_stats.db")
    MODEL_COEFFICIENTS_PATH = os.getenv("MODEL_COEFFICIENTS_PATH", "model_coefficients.csv")
    
    # Security settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    
    # Authentication settings
    ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    AUTH_USERS = {
        "admin": os.getenv("ADMIN_PASSWORD", "admin123"),
        "user": os.getenv("USER_PASSWORD", "user123")
    }
    
    # API settings
    API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "100"))  # requests per hour
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))  # seconds
    
    # Monitoring settings
    ENABLE_MONITORING = os.getenv("ENABLE_MONITORING", "true").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
    
    # Model settings
    MODEL_CACHE_SIZE = int(os.getenv("MODEL_CACHE_SIZE", "10"))
    MODEL_TIMEOUT = int(os.getenv("MODEL_TIMEOUT", "30"))  # seconds
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        # Check if database exists
        if not Path(cls.DATABASE_PATH).exists():
            raise FileNotFoundError(f"Database not found at {cls.DATABASE_PATH}")
        
        # Check if required directories exist
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        Path("models").mkdir(exist_ok=True)
        
        return True

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENABLE_AUTH = False
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENABLE_AUTH = True
    LOG_LEVEL = "INFO"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate production configuration."""
        if not super().validate():
            return False
        
        # Production-specific validations
        if cls.SECRET_KEY == "your-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be changed in production")
        
        if not cls.AUTH_USERS.get("admin") or cls.AUTH_USERS["admin"] == "admin123":
            raise ValueError("Admin password must be changed in production")
        
        return True

def get_config() -> Config:
    """Get configuration based on environment."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()
