import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_TITLE: str = "Agentic Honeypot API"
    API_VERSION: str = "1.0.0"
    API_KEY: str = os.getenv("API_KEY", "your-secret-api-key-change-in-production")
    
    # GUVI Evaluation Endpoint
    GUVI_ENDPOINT: str = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    GUVI_CALLBACK_TIMEOUT: int = 10
    
    # Scam Detection Settings
    SCAM_SCORE_THRESHOLD: int = 4  # Minimum score to trigger scam detection
    MIN_MESSAGES_BEFORE_CALLBACK: int = 3  # Minimum messages before sending final result
    MAX_MESSAGES_PER_SESSION: int = 20  # Max messages to prevent infinite loops
    
    # Session Settings
    SESSION_TIMEOUT_MINUTES: int = 30
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
