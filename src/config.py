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
    API_RELOAD: bool = True
    
    # Cache
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
