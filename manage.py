"""
Database Management Commands

This module provides Django-style management commands for the Web Scraper AI system.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Optional

from config.database import engine, Base, create_tables, check_connection
from config.settings import settings
from jobs.models import Job as JobModel
from api.models import User as UserModel

logger = logging.getLogger(__name__)


def create_superuser(username: str, email: str, password: str):
    """Create a superuser account"""
    try:
        from config.database import SessionLocal
        
        with SessionLocal() as session:
            # Check if user already exists
            existing_user = session.query(UserModel).filter(UserModel.username == username).first()
            if existing_user:
                print(f"User '{username}' already exists")
                return False
            
            # Create new user
            user = UserModel(
                username=username,
                email=email,
                is_admin=True,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            # Set password (would need hashing in production)
            user.set_password(password)
            
            session.add(user)
            session.commit()
            
            print(f"Superuser '{username}' created successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error creating superuser: {str(e)}")
        return False


def create_sample_data():
    """Create sample data for testing"""
    try:
        from config.database import SessionLocal
        from scrapers.factory import ScraperFactory
        from scrapers.config import ScraperConfig, ScraperType
        from processors.pipeline import DataProcessingPipeline
        from exporters.factory import ExporterFactory
        
        with SessionLocal() as session:
            # Create sample job
            job = JobModel(
                name="Sample Product Scraper",
                description="Sample job for testing",
                url="https://example.com/products",
                selectors={"title": "h1", "price": ".price", "rating": ".rating"},
                config={
                    "scraper_type": "static",
                    "delay": 1.0,
                    "max_retries": 3,
                    "timeout": 30,
                    "user_agent": "WebScraper/1.0"
                },
                status="pending",
                priority=3,
                delay=1.0,
                max_retries=3,
                timeout=30,
                user_agent="WebScraper/1.0",
                headers={},
                cookies={},
                proxy=None,
                pagination=None,
                extract_links=False,
                extract_images=False,
                extract_metadata=True,
                continue_on_error=True,
                ignore_ssl_errors=False,
                output_format="csv",
                include_headers=True,
                encoding="utf-8",
                tags=["sample"],
                is_public=True,
                metadata={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(job)
            session.commit()
            
            print("Sample data created successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error creating sample data: {str(e)}")
        return False


def run_migrations():
    """Run database migrations"""
    try:
        print("Running database migrations...")
        create_tables()
        print("Database migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        return False


def seed_database():
    """Seed database with initial data"""
    try:
        print("Seeding database...")
        create_sample_data()
        print("Database seeded successfully")
        return True
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        return False


def check_system_health():
    """Check system health"""
    try:
        print("Checking system health...")
        
        # Check database connection
        db_healthy = check_connection()
        if db_healthy:
            print("✓ Database: Connected")
        else:
            print("✗ Database: Disconnected")
        
        # Check directories
        directories = ['logs', 'exports', 'uploads', 'temp', 'static']
        for directory in directories:
            if os.path.exists(directory):
                print(f"✓ {directory}: Exists")
            else:
                print(f"✗ {directory}: Missing")
        
        # Check configuration
        if os.path.exists('.env'):
            print("✓ Configuration: .env file exists")
        else:
            print("✗ Configuration: .env file missing")
        
        return db_healthy
        
    except Exception as e:
        logger.error(f"Error checking system health: {str(e)}")
        return False


def backup_database():
    """Create database backup"""
    try:
        from backups.backup_manager import backup_manager
        
        print("Creating database backup...")
        result = backup_manager.perform_backup()
        
        if result['success']:
            print(f"✓ Backup created: {result['backup_path']}")
        else:
            print(f"✗ Backup failed: {result.get('error', 'Unknown error')}")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return False


def restore_database(backup_path: str):
    """Restore database from backup"""
    try:
        from backups.backup_manager import backup_manager
        
        print(f"Restoring database from: {backup_path}")
        result = backup_manager.restore_backup(backup_path)
        
        if result['success']:
            print("✓ Database restored successfully")
        else:
            print(f"✗ Restore failed: {result.get('error', 'Unknown error')}")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"Error restoring database: {str(e)}")
        return False


def cleanup_old_data(days: int = 30):
    """Clean up old data"""
    try:
        from config.database import SessionLocal
        
        print(f"Cleaning up data older than {days} days...")
        
        with SessionLocal() as session:
            # Clean up old job logs
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Delete old job records
            deleted_jobs = session.query(JobModel).filter(
                JobModel.created_at < cutoff_date,
                JobModel.status.in_(['completed', 'failed', 'cancelled'])
            ).delete()
            
            session.commit()
            
            print(f"✓ Cleaned up {deleted_jobs} old job records")
            return deleted_jobs
            
    except Exception as e:
        logger.error(f"Error cleaning up old data: {str(e)}")
        return 0


def run_server(host: str = "0.0.0.0", port: int = 8000, workers: int = 1):
    """Run the development server"""
    try:
        print(f"Starting server on {host}:{port}")
        
        # Import here to avoid circular imports
        import uvicorn
        
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            workers=workers,
            reload=settings.debug,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)


def run_worker():
    """Run the Celery worker"""
    try:
        print("Starting Celery worker...")
        
        # Import here to avoid circular imports
        from config.celery import celery_app
        
        celery_app.start(['worker', '--loglevel=info'])
        
    except Exception as e:
        logger.error(f"Error starting worker: {str(e)}")
        sys.exit(1)


def run_beat():
    """Run the Celery beat scheduler"""
    try:
        print("Starting Celery beat scheduler...")
        
        # Import here to avoid circular imports
        from config.celery import celery_app
        
        celery_app.start(['beat', '--loglevel=info'])
        
    except Exception as e:
        logger.error(f"Error starting beat scheduler: {str(e)}")
        sys.exit(1)


def test_scraping():
    """Test the scraping functionality"""
    try:
        print("Testing scraping functionality...")
        
        # Import here to avoid circular imports
        from scrapers.factory import ScraperFactory
        from scrapers.config import ScraperConfig, ScraperType
        from processors.pipeline import DataProcessingPipeline
        from exporters.factory import ExporterFactory
        
        # Create test scraper
        config = ScraperConfig(
            url="https://httpbin.org/json",
            selectors={"title": "title", "slugs": "slugs"},
            scraper_type=ScraperType.STATIC,
            delay=1.0
        )
        
        scraper = ScraperFactory.create_scraper(config)
        
        # Scrape data
        import asyncio
        session = asyncio.run(scraper.scrape_page(config.url))
        
        if session.is_successful:
            print(f"✓ Test scraping successful: {len(session.data)} records")
            
            # Process data
            pipeline = DataProcessingPipeline()
            processed_data = asyncio.run(pipeline.process(session.data))
            print(f"✓ Data processing completed: {len(processed_data)} records")
            
            # Export data
            exporter = ExporterFactory.create_exporter('json')
            result = exporter.export_with_stats(processed_data)
            
            if result.success:
                print(f"✓ Export successful: {result.file_path}")
            else:
                print(f"✗ Export failed: {result.error_message}")
            
            return True
        else:
            print(f"✗ Test scraping failed: {session.error}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing scraping: {str(e)}")
        return False


def test_api():
    """Test the API endpoints"""
    try:
        print("Testing API endpoints...")
        
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test health check
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ Health check: OK")
        else:
            print(f"✗ Health check failed: {response.status_code}")
        
        # Test jobs endpoint
        response = requests.get(f"{base_url}/api/v1/jobs")
        if response.status_code == 200:
            jobs = response.json()
            print(f"✓ Jobs endpoint: {len(jobs)} jobs found")
        else:
            print(f"✗ Jobs endpoint failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing API: {str(e)}")
        return False


def generate_sample_config():
    """Generate sample configuration files"""
    try:
        print("Generating sample configuration files...")
        
        # Generate sample .env file
        sample_env = """# Web Scraper AI Configuration

# Application Settings
APP_NAME=Web Scraper AI
DEBUG=True
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# Database Settings
DATABASE_URL=sqlite:///./scraper.db

# Redis Settings
REDIS_URL=redis://localhost:6379/0

# Scraping Settings
DEFAULT_DELAY=1.0
MAX_CONCURRENT_JOBS=5
USER_AGENT=WebScraper/1.0

# File Storage
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Monitoring Settings
MONITORING_ENABLED=True
LOG_LEVEL=INFO
"""
        
        with open('.env.example', 'w') as f:
            f.write(sample_env)
        
        print("✓ Sample .env.example file created")
        
        # Generate sample docker-compose override
        sample_override = """# Docker Compose Override for Development

version: '3.8'

services:
  web-scraper:
    build: .
    volumes:
      - ./logs:/app/logs
      - ./exports:/app/exports
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
"""
        
        with open('docker-compose.override.yml', 'w') as f:
            f.write(sample_override)
        
        print("✓ Sample docker-compose.override.yml file created")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating sample config: {str(e)}")
        return False


def main():
    """Main management command handler"""
    parser = argparse.ArgumentParser(description='Web Scraper AI Management Commands')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Database commands
    db_parser = subparsers.add_parser('db', help='Database operations')
    db_subparsers = db_parser.add_subparsers(dest='db_action', help='Database actions')
    db_subparsers.add_parser('migrate', help='Run database migrations')
    db_subparsers.add_parser('seed', help='Seed database with sample data')
    db_subparsers.add_parser('backup', help='Create database backup')
    db_subparsers.add_parser('restore', help='Restore database from backup')
    db_subparsers.add_parser('cleanup', help='Clean up old data', type=int, default=30)
    
    # User commands
    user_parser = subparsers.add_parser('user', help='User management')
    user_subparsers = user_parser.add_subparsers(dest='user_action', help='User actions')
    user_subparsers.add_parser('createsuperuser', help='Create superuser', nargs=3, metavar=('USERNAME', 'EMAIL', 'PASSWORD'))
    
    # Server commands
    server_parser = subparsers.add_parser('server', help='Server operations')
    server_subparsers = server_parser.add_subparsers(dest='server_action', help='Server actions')
    server_subparsers.add_parser('run', help='Run development server')
    server_subparsers.add_parser('start', help='Start server (alias for run)', nargs='?', const='run')
    server_subparsers.add_parser('worker', help='Run Celery worker')
    server_subparsers.add_parser('beat', help='Run Celery beat scheduler')
    
    # Testing commands
    test_parser = subparsers.add_parser('test', help='Testing operations')
    test_subparsers = test_parser.add_subparsers(dest='test_action', help='Test actions')
    test_subparsers.add_parser('scraping', help='Test scraping functionality')
    test_subparsers.add_parser('api', help='Test API endpoints')
    
    # Utility commands
    util_parser = subparsers.add_parser('util', help='Utility operations')
    util_subparsers = util_subparsers.add_subparsers(dest='util_action', help='Utility actions')
    util_subparsers.add_parser('health', help='Check system health')
    util_subparsers.add_parser('config', help='Generate sample configuration')
    
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'db':
        if args.db_action == 'migrate':
            run_migrations()
        elif args.db_action == 'seed':
            seed_database()
        elif args.db_action == 'backup':
            backup_database()
        elif args.db_action == 'restore':
            restore_database(args.backup_path) if hasattr(args, 'backup_path') else None
        elif args.db_action == 'cleanup':
            cleanup_old_data(args.cleanup)
        else:
            print(f"Unknown db action: {args.db_action}")
    
    elif args.command == 'user':
        if args.user_action == 'createsuperuser':
            username, email, password = args.createsuperuser
            create_superuser(username, email, password)
        else:
            print(f"Unknown user action: {args.user_action}")
    
    elif args.command == 'server':
        if args.server_action == 'run':
            run_server()
        elif args.server_action == 'start':
            run_server()
        elif args.server_action == 'worker':
            run_worker()
        elif args.server_action == 'beat':
            run_beat()
        else:
            print(f"Unknown server action: {args.server_action}")
    
    elif args.command == 'test':
        if args.test_action == 'scraping':
            test_scraping()
        elif args.test_action == 'api':
            test_api()
        else:
            print(f"Unknown test action: {args.test_action}")
    
    elif args.command == 'util':
        if args.util_action == 'health':
            check_system_health()
        elif args.util_action == 'config':
            generate_sample_config()
        else:
            print(f"Unknown utility action: {args.util_action}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
