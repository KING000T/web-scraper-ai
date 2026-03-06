"""
Configuration Settings

This module contains all configuration settings for the Web Scraper AI system.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    app_name: str = "Web Scraper AI"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Database settings
    database_url: str = Field(default="sqlite:///./scraper.db", env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # Celery settings
    celery_broker_url: str = Field(default="redis://localhost:6379", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379", env="CELERY_RESULT_BACKEND")
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: List[str] = ["json"]
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True
    
    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    api_reload: bool = Field(default=True, env="API_RELOAD")
    
    # Security settings
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # CORS settings
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8080"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Trusted hosts
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "logs/app.log"
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # Scraping settings
    default_delay: float = Field(default=1.0, env="DEFAULT_DELAY")
    default_timeout: int = Field(default=30, env="DEFAULT_TIMEOUT")
    default_max_retries: int = Field(default=3, env="DEFAULT_MAX_RETRIES")
    default_user_agent: str = "WebScraper/1.0"
    
    # Browser settings
    chrome_driver_path: Optional[str] = Field(default=None, env="CHROME_DRIVER_PATH")
    headless_browser: bool = Field(default=True, env="HEADLESS_BROWSER")
    browser_window_size: str = "1920,1080"
    
    # File storage settings
    upload_dir: str = "uploads"
    export_dir: str = "exports"
    temp_dir: str = "temp"
    static_dir: str = "static"
    
    # File size limits
    max_file_size: int = Field(default=16 * 1024 * 1024, env="MAX_FILE_SIZE")  # 16MB
    max_records_per_export: int = Field(default=100000, env="MAX_RECORDS_PER_EXPORT")
    
    # Rate limiting settings
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=3600, env="RATE_LIMIT_PERIOD")  # 1 hour
    
    # Email settings
    smtp_server: str = Field(default="smtp.gmail.com", env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    
    # Google Sheets settings
    google_sheets_credentials: str = Field(default="", env="GOOGLE_SHEETS_CREDENTIALS")
    google_sheets_token: str = Field(default="", env="GOOGLE_SHEETS_TOKEN")
    
    # Monitoring settings
    monitoring_enabled: bool = Field(default=True, env="MONITORING_ENABLED")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # Performance settings
    max_concurrent_jobs: int = Field(default=10, env="MAX_CONCURRENT_JOBS")
    max_concurrent_scrapers: int = Field(default=5, env="MAX_CONCURRENT_SCRAPERS")
    worker_concurrency: int = Field(default=4, env="WORKER_CONCURRENCY")
    
    # Backup settings
    backup_enabled: bool = Field(default=True, env="BACKUP_ENABLED")
    backup_interval: int = Field(default=24, env="BACKUP_INTERVAL")  # hours
    backup_retention_days: int = Field(default=30, env="BACKUP_RETENTION_DAYS")
    backup_dir: str = "backups"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create global settings instance
settings = Settings()


# Database configuration
def get_database_url() -> str:
    """Get database URL"""
    return settings.database_url


def get_redis_url() -> str:
    """Get Redis URL"""
    return settings.redis_url


# Celery configuration
def get_celery_config() -> dict:
    """Get Celery configuration"""
    return {
        "broker_url": settings.celery_broker_url,
        "result_backend": settings.celery_result_backend,
        "task_serializer": settings.celery_task_serializer,
        "result_serializer": settings.celery_result_serializer,
        "accept_content": settings.celery_accept_content,
        "timezone": settings.celery_timezone,
        "enable_utc": settings.celery_enable_utc,
        "task_routes": {
            "scrapers.tasks.*": {"queue": "scraping"},
            "processors.tasks.*": {"queue": "processing"},
            "exporters.tasks.*": {"queue": "exporting"},
        },
        "task_annotations": {
            "*": {"rate_limit": "10/m"},
        },
    }


# Logging configuration
def get_logging_config() -> dict:
    """Get logging configuration"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.log_format,
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": settings.log_level,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": settings.log_file,
                "maxBytes": settings.log_max_size,
                "backupCount": settings.log_backup_count,
                "formatter": "detailed",
                "level": settings.log_level,
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": settings.log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            },
            "celery": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }


# Security configuration
def get_security_config() -> dict:
    """Get security configuration"""
    return {
        "secret_key": settings.secret_key,
        "algorithm": settings.algorithm,
        "access_token_expire_minutes": settings.access_token_expire_minutes,
        "refresh_token_expire_days": settings.refresh_token_expire_days,
    }


# CORS configuration
def get_cors_config() -> dict:
    """Get CORS configuration"""
    return {
        "allow_origins": settings.cors_origins,
        "allow_credentials": settings.cors_allow_credentials,
        "allow_methods": settings.cors_allow_methods,
        "allow_headers": settings.cors_allow_headers,
    }


# File configuration
def get_file_config() -> dict:
    """Get file configuration"""
    return {
        "upload_dir": settings.upload_dir,
        "export_dir": settings.export_dir,
        "temp_dir": settings.temp_dir,
        "static_dir": settings.static_dir,
        "max_file_size": settings.max_file_size,
        "max_records_per_export": settings.max_records_per_export,
    }


# Browser configuration
def get_browser_config() -> dict:
    """Get browser configuration"""
    return {
        "chrome_driver_path": settings.chrome_driver_path,
        "headless": settings.headless_browser,
        "window_size": settings.browser_window_size,
        "options": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
        ],
    }


# Rate limiting configuration
def get_rate_limit_config() -> dict:
    """Get rate limiting configuration"""
    return {
        "enabled": settings.rate_limit_enabled,
        "requests": settings.rate_limit_requests,
        "period": settings.rate_limit_period,
    }


# Email configuration
def get_email_config() -> dict:
    """Get email configuration"""
    return {
        "server": settings.smtp_server,
        "port": settings.smtp_port,
        "username": settings.smtp_username,
        "password": settings.smtp_password,
        "use_tls": settings.smtp_use_tls,
    }


# Google Sheets configuration
def get_google_sheets_config() -> dict:
    """Get Google Sheets configuration"""
    return {
        "credentials_file": settings.google_sheets_credentials,
        "token_file": settings.google_sheets_token,
    }


# Monitoring configuration
def get_monitoring_config() -> dict:
    """Get monitoring configuration"""
    return {
        "enabled": settings.monitoring_enabled,
        "metrics_port": settings.metrics_port,
        "health_check_interval": settings.health_check_interval,
    }


# Performance configuration
def get_performance_config() -> dict:
    """Get performance configuration"""
    return {
        "max_concurrent_jobs": settings.max_concurrent_jobs,
        "max_concurrent_scrapers": settings.max_concurrent_scrapers,
        "worker_concurrency": settings.worker_concurrency,
    }


# Backup configuration
def get_backup_config() -> dict:
    """Get backup configuration"""
    return {
        "enabled": settings.backup_enabled,
        "interval": settings.backup_interval,
        "retention_days": settings.backup_retention_days,
        "backup_dir": settings.backup_dir,
    }


# Environment-specific configuration
def is_development() -> bool:
    """Check if running in development environment"""
    return settings.environment.lower() == "development"


def is_production() -> bool:
    """Check if running in production environment"""
    return settings.environment.lower() == "production"


def is_testing() -> bool:
    """Check if running in testing environment"""
    return settings.environment.lower() == "testing"


# Utility functions
def create_directories():
    """Create necessary directories"""
    import os
    
    directories = [
        settings.upload_dir,
        settings.export_dir,
        settings.temp_dir,
        settings.static_dir,
        settings.backup_dir,
        "logs",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


# Initialize directories on import
create_directories()
