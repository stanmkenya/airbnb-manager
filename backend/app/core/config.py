import os
import json
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Airbnb Property Manager API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Firebase settings
    FIREBASE_SERVICE_ACCOUNT_JSON: str
    FIREBASE_DATABASE_URL: str

    # CORS settings
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def firebase_credentials(self) -> dict:
        """Parse Firebase service account JSON"""
        try:
            return json.loads(self.FIREBASE_SERVICE_ACCOUNT_JSON)
        except json.JSONDecodeError:
            raise ValueError("Invalid Firebase service account JSON")

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',')]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
