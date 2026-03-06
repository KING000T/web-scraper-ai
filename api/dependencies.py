"""
API Dependencies Module

This module provides dependency injection for FastAPI endpoints,
including database sessions, authentication, and other shared dependencies.
"""

from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Database configuration
DATABASE_URL = "sqlite:///./scraper.db"  # Default to SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
security = HTTPBearer()
logger = logging.getLogger(__name__)


def get_database() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database)
):
    """Get current authenticated user"""
    token = credentials.credentials
    
    # For now, we'll implement a simple token validation
    # In production, you'd use JWT or another secure method
    if not validate_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = get_user_by_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_admin_user(current_user = Depends(get_current_active_user)):
    """Get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_database)
):
    """Get current user (optional - allows anonymous access)"""
    if not credentials:
        return None
    
    token = credentials.credentials
    if not validate_token(token):
        return None
    
    return get_user_by_token(token, db)


# Authentication functions
def validate_token(token: str) -> bool:
    """Validate authentication token"""
    # Simple token validation for demo
    # In production, use JWT or other secure method
    if not token:
        return False
    
    # For demo purposes, accept any non-empty token
    # In production, validate against database or JWT
    return len(token) > 10


def get_user_by_token(token: str, db: Session):
    """Get user by authentication token"""
    # For demo purposes, return a mock user
    # In production, query database for user with this token
    
    class MockUser:
        def __init__(self):
            self.id = 1
            self.username = "demo_user"
            self.email = "demo@example.com"
            self.full_name = "Demo User"
            self.is_active = True
            self.is_admin = True
    
    return MockUser()


def get_job_manager():
    """Get job manager instance"""
    from jobs.manager import JobManager
    from jobs.queue import TaskQueue
    
    # Create task queue
    queue = TaskQueue()
    
    # Create job manager
    return JobManager(queue, SessionLocal())


def get_scraper_engine():
    """Get scraper engine instance"""
    from scrapers.factory import ScraperFactory
    
    # Return factory for creating scrapers
    return ScraperFactory


def get_data_processor():
    """Get data processor instance"""
    from processors.pipeline import DataProcessingPipeline
    
    # Create default processing pipeline
    from processors.cleaner import DataCleaner
    from processors.validator import DataValidator
    from processors.transformer import DataTransformer
    
    pipeline = DataProcessingPipeline()
    pipeline.add_processor(DataCleaner())
    pipeline.add_processor(DataValidator([]))
    pipeline.add_processor(DataTransformer([]))
    
    return pipeline


def get_export_engine():
    """Get export engine instance"""
    from exporters.factory import ExporterFactory
    
    return ExporterFactory


def get_logger():
    """Get logger instance"""
    return logging.getLogger(__name__)


# Rate limiting dependencies
def rate_limit_check(request_limit: int = 100):
    """Rate limiting check"""
    # Simple rate limiting implementation
    # In production, use Redis or other distributed cache
    def rate_limiter():
        # For demo, always allow
        return True
    
    return rate_limiter


# Pagination dependency
def get_pagination_params(
    page: int = 1,
    per_page: int = 50
):
    """Get pagination parameters"""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than 0"
        )
    
    if per_page < 1 or per_page > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Per page must be between 1 and 100"
        )
    
    offset = (page - 1) * per_page
    
    return {
        "page": page,
        "per_page": per_page,
        "offset": offset,
        "limit": per_page
    }


# Validation dependencies
def validate_job_id(job_id: int):
    """Validate job ID"""
    if job_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job ID must be positive"
        )
    return job_id


def validate_export_format(format: str):
    """Validate export format"""
    valid_formats = ["csv", "json", "xlsx", "google_sheets"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
        )
    return format


# File handling dependencies
def validate_file_size(file_size: int, max_size: int = 16 * 1024 * 1024):  # 16MB
    """Validate file size"""
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_size} bytes"
        )
    return file_size


def validate_file_type(file_type: str, allowed_types: list):
    """Validate file type"""
    if file_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )
    return file_type


# Configuration dependencies
def get_settings():
    """Get application settings"""
    from config.settings import Settings
    return Settings()


def get_database_config():
    """Get database configuration"""
    return {
        "url": DATABASE_URL,
        "engine": engine,
        "session": SessionLocal
    }


# Monitoring dependencies
def get_system_metrics():
    """Get system metrics"""
    import psutil
    
    return {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "network_io": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
    }


def get_health_status():
    """Get health status"""
    try:
        # Check database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    try:
        # Check task queue
        queue = TaskQueue()
        queue_status = "healthy" if queue.is_healthy() else "unhealthy"
    except Exception as e:
        logger.error(f"Queue health check failed: {str(e)}")
        queue_status = "unhealthy"
    
    return {
        "database": db_status,
        "queue": queue_status,
        "overall": "healthy" if db_status == "healthy" and queue_status == "healthy" else "unhealthy"
    }


# Security dependencies
def check_permissions(required_permissions: list):
    """Check user permissions"""
    def permission_checker(current_user = Depends(get_current_user)):
        # For demo, admin has all permissions
        if current_user.is_admin:
            return current_user
        
        # Check if user has required permissions
        user_permissions = []  # Get from database
        missing_permissions = set(required_permissions) - set(user_permissions)
        
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return permission_checker


# Cache dependencies
def get_cache():
    """Get cache instance"""
    # For demo, return None
    # In production, return Redis or other cache
    return None


def get_cached_data(cache_key: str):
    """Get cached data"""
    cache = get_cache()
    if cache:
        return cache.get(cache_key)
    return None


def set_cached_data(cache_key: str, data: any, ttl: int = 3600):
    """Set cached data"""
    cache = get_cache()
    if cache:
        return cache.set(cache_key, data, ttl)
    return False


# Logging dependencies
def log_request(request_id: str):
    """Log request"""
    def logger_middleware():
        logger.info(f"Request {request_id} started")
        return request_id
    
    return logger_middleware


def log_response(request_id: str, status_code: int):
    """Log response"""
    logger.info(f"Request {request_id} completed with status {status_code}")


# Utility dependencies
def get_client_ip(request):
    """Get client IP address"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host


def get_user_agent(request):
    """Get user agent"""
    return request.headers.get("User-Agent", "Unknown")


# Background task dependencies
def get_background_tasks():
    """Get background tasks"""
    from fastapi import BackgroundTasks
    return BackgroundTasks()


# WebSocket dependencies
def get_websocket_manager():
    """Get WebSocket manager"""
    # Return WebSocket manager instance
    return None


# Example usage patterns
def example_usage():
    """Example usage patterns for dependencies"""
    
    # Basic usage with database
    def example_endpoint(db: Session = Depends(get_database)):
        users = db.query(User).all()
        return {"users": len(users)}
    
    # Usage with authentication
    def protected_endpoint(
        current_user = Depends(get_current_user)
    ):
        return {"user": current_user.username}
    
    # Usage with pagination
    def paginated_endpoint(
        pagination = Depends(get_pagination_params)
    ):
        return {"page": pagination["page"], "per_page": pagination["per_page"]}
    
    # Usage with validation
    def job_endpoint(
        job_id: int = Depends(validate_job_id)
    ):
        return {"job_id": job_id}
    
    print("Dependencies example completed")


if __name__ == "__main__":
    # Test dependencies
    example_usage()
