import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database settings
    database_url: str = Field(default="sqlite:///./app.db", env="DATABASE_URL")
    postgres_db: str = Field(default="property_db", env="POSTGRES_DB")
    postgres_user: str = Field(default="property_user", env="POSTGRES_USER")
    postgres_password: str = Field(default="property_pass", env="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")

    # Application settings
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8080, env="API_PORT")

    # Security settings
    secret_key: str = Field(default="dev-secret-key", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # JWT Configuration
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS settings
    allowed_origins: str = Field(default="*", env="ALLOWED_ORIGINS")

    # File upload settings
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    upload_path: str = Field(default="/tmp/uploads", env="UPLOAD_PATH")

    # Redis settings (optional)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")

    # Additional fields that might exist in .env but aren't used directly by the app
    database_url_local: Optional[str] = Field(default=None, env="DATABASE_URL_LOCAL")
    pgadmin_email: Optional[str] = Field(default=None, env="PGADMIN_EMAIL")
    pgadmin_password: Optional[str] = Field(default=None, env="PGADMIN_PASSWORD")
    pgadmin_port: Optional[int] = Field(default=None, env="PGADMIN_PORT")

    # Data extraction service settings
    data_extraction_url: Optional[str] = Field(default="http://data-extraction:8000", env="DATA_EXTRACTION_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Allow extra fields that might exist in .env but aren't defined in Settings
        extra = "ignore"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


# Create global settings instance
settings = Settings()