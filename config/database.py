"""
Database Configuration

This module contains database configuration and connection management.
"""

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging

from .settings import get_database_url, is_development, is_production

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    get_database_url(),
    echo=False,  # Set to True for SQL logging in development
    pool_pre_ping=True,
    poolclass=StaticPool if "sqlite" in get_database_url() else None,
    connect_args={"check_same_thread": False} if "sqlite" in get_database_url() else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Metadata
metadata = MetaData()


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


def drop_tables():
    """Drop all database tables"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {str(e)}")
        raise


def get_engine():
    """Get database engine"""
    return engine


def check_connection():
    """Check database connection"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


def init_database():
    """Initialize database"""
    try:
        # Check connection
        if not check_connection():
            raise Exception("Database connection failed")
        
        # Create tables
        create_tables()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


# Database utilities
def reset_database():
    """Reset database (drop and recreate)"""
    if not is_development():
        raise Exception("Database reset is only allowed in development environment")
    
    try:
        drop_tables()
        create_tables()
        logger.info("Database reset successfully")
    except Exception as e:
        logger.error(f"Database reset failed: {str(e)}")
        raise


def backup_database():
    """Create database backup"""
    if "sqlite" in get_database_url():
        import shutil
        from datetime import datetime
        
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_path = get_database_url().replace("sqlite:///", "")
        backup_path = os.path.join(backup_dir, f"scraper_backup_{timestamp}.db")
        
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            raise
    else:
        logger.warning("Database backup is only supported for SQLite")


def restore_database(backup_path: str):
    """Restore database from backup"""
    if "sqlite" in get_database_url():
        import shutil
        
        db_path = get_database_url().replace("sqlite:///", "")
        
        try:
            shutil.copy2(backup_path, db_path)
            logger.info(f"Database restored from: {backup_path}")
        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
            raise
    else:
        logger.warning("Database restore is only supported for SQLite")


# Database health check
def get_database_health():
    """Get database health status"""
    try:
        with engine.connect() as connection:
            # Test basic query
            result = connection.execute("SELECT 1").fetchone()
            
            # Get table info
            if "sqlite" in get_database_url():
                tables = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                table_count = len(tables)
            else:
                table_count = len(engine.table_names())
            
            return {
                "status": "healthy",
                "connection": "ok",
                "table_count": table_count,
                "database_type": "sqlite" if "sqlite" in get_database_url() else "postgresql"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connection": "failed",
            "error": str(e),
            "database_type": "sqlite" if "sqlite" in get_database_url() else "postgresql"
        }


# Migration utilities
def run_migrations():
    """Run database migrations"""
    try:
        # For now, just create tables
        # In production, you might want to use Alembic
        create_tables()
        logger.info("Database migrations completed")
    except Exception as e:
        logger.error(f"Database migrations failed: {str(e)}")
        raise


# Database statistics
def get_database_stats():
    """Get database statistics"""
    try:
        with engine.connect() as connection:
            stats = {}
            
            if "sqlite" in get_database_url():
                # SQLite stats
                stats["database_size"] = os.path.getsize(get_database_url().replace("sqlite:///", ""))
                stats["page_count"] = connection.execute("PRAGMA page_count").fetchone()[0]
                stats["page_size"] = connection.execute("PRAGMA page_size").fetchone()[0]
            else:
                # PostgreSQL stats
                stats["database_size"] = connection.execute(
                    "SELECT pg_database_size(current_database())"
                ).fetchone()[0]
                stats["connection_count"] = connection.execute(
                    "SELECT count(*) FROM pg_stat_activity"
                ).fetchone()[0]
            
            return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {str(e)}")
        return {}


# Database cleanup
def cleanup_old_data(days: int = 30):
    """Clean up old data"""
    try:
        with engine.connect() as connection:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Clean up old job logs
            connection.execute(
                "DELETE FROM job_logs WHERE created_at < :cutoff",
                {"cutoff": cutoff_date}
            )
            
            # Clean up old metrics
            connection.execute(
                "DELETE FROM job_metrics WHERE created_at < :cutoff",
                {"cutoff": cutoff_date}
            )
            
            connection.commit()
            logger.info(f"Cleaned up data older than {days} days")
    except Exception as e:
        logger.error(f"Database cleanup failed: {str(e)}")
        raise


# Initialize database on import
if __name__ != "__main__":
    try:
        init_database()
    except Exception as e:
        logger.warning(f"Database initialization failed: {str(e)}")
