"""Application configuration."""
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/kasparro"
    )
    
    # API Configuration
    API_KEY: str = os.getenv("API_KEY", "")
    API_TIMEOUT_SECONDS: int = int(os.getenv("API_TIMEOUT_SECONDS", "30"))
    
    # ETL Configuration
    ETL_BATCH_SIZE: int = int(os.getenv("ETL_BATCH_SIZE", "100"))
    ETL_CHECKPOINT_INTERVAL: int = int(os.getenv("ETL_CHECKPOINT_INTERVAL", "100"))
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
