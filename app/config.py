from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    PORT: int = 8000
    CORS_ORIGINS: str = "*"

    JWT_SECRET: str = "change_me"
    JWT_EXPIRES_MIN: int = 43200

    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "changeme"

    DATABASE_URL: str = "sqlite:///./docqmint.db"

    PROVIDER: str = "openrouter"
    DEFAULT_MODEL: str = "gpt-4o-mini"
    TEMPERATURE: float = 0.2
    MAX_TOKENS: int = 1024

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_SITE_URL: str = "https://docqmint.proxy"
    OPENROUTER_SITE_NAME: str = "DocQmint Proxy"

    class Config:
        env_file = ".env"

settings = Settings()
