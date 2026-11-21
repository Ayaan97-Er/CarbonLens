import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "CarbonLens"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    # Default to sqlite for instant local setup, supports postgresql via DATABASE_URL
    DATABASE_URL: str = "sqlite:///./carbonlens.db"
    
    # JWT Security
    SECRET_KEY: str = "carbonlens-super-secret-key-change-in-production-2026-sustainability"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["*"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Demo User Details for Quick Seeding / Testing
    DEMO_USER_EMAIL: str = "demo@carbonlens.dev"
    DEMO_USER_PASSWORD: str = "CarbonLens2026!"
    DEMO_USER_NAME: str = "Alex Morgan"
    
    ADMIN_USER_EMAIL: str = "admin@carbonlens.dev"
    ADMIN_USER_PASSWORD: str = "AdminCarbonLens2026!"
    ADMIN_USER_NAME: str = "System Admin"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
