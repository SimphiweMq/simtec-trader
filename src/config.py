"""Configuration management for the trading signal engine."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    # Use SQLite for development (no Docker needed), PostgreSQL for production
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./simtek_trader.db"  # SQLite development db
    )
    # Production PostgreSQL URL: postgresql://user:password@localhost:5432/simtek_trader
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8001
    API_RELOAD: bool = True
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Frontend
    VITE_API_URL: str = "http://localhost:8001"
    
    # PostgreSQL (for Docker/Production)
    POSTGRES_USER: str = "simtek_user"
    POSTGRES_PASSWORD: str = "simtek_password_dev"
    POSTGRES_DB: str = "simtek_trader"
    
    # Cache
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()
