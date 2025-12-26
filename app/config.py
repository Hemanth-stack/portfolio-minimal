from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/portfolio"
    
    # Admin
    admin_username: str = "admin"
    admin_password: str = "changeme"
    
    # Security
    secret_key: str = "change-this-secret-key"
    
    # SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    
    # Site
    site_url: str = "https://iamhemanth.in"
    site_name: str = "Hemanth Irivichetty"
    site_tagline: str = "AI & MLOps Engineer"
    
    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
