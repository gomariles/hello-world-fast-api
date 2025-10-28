from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    redis_db: int = 0
    
    # Default key for GET endpoint when no key is provided
    default_key: str = "default"
    
    # Application Insights Configuration
    applicationinsights_connection_string: Optional[str] = None
    
    # App Configuration
    app_name: str = "FastAPI Redis Cache API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()