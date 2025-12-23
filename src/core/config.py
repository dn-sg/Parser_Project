"""
Configuration settings using environment variables
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration"""
    
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # PostgreSQL settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # Redis/Celery settings
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Database URLs
    DATABASE_URL: str = ""
    ASYNC_DATABASE_URL: str = ""

    # DockerHub
    DOCKERHUB_USERNAME: str = "dn_sg"
    DOCKERHUB_TOKEN: str = ""

    # API settings
    API_PORT: int = 8000
    FLOWER_PORT: int = 5555

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Build database URLs if not provided
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        if not self.ASYNC_DATABASE_URL:
            self.ASYNC_DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )


# Global config instance
config = Config()

