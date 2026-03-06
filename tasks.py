"""
Celery Tasks

This module defines Celery tasks for the Web Scraper AI system.
"""

from celery import Celery
from datetime import datetime, timedelta
import logging
import asyncio
from typing import Dict, Any, List

from config.celery import celery_app
from scrapers.factory import ScraperFactory
from scrapers.config import ScraperConfig, ScraperType
from processors.pipeline import DataProcessingPipeline
from exporters.factory import ExporterFactory
from jobs.models import Job as JobModel
from config.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='scrapers.tasks.scrape_job')
def scrape_job(self, job_id: int) -> Dict[str, Any]:
    """Scrape a job"""
    try:
        with SessionLocal() as session:
            # Get job from database
            job = session.query(JobModel).filter(JobModel.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Update job status
            job.status = "running"
            job.started_at = datetime.utcnow()
            session.commit()
            
            # Create scraper configuration
            config = ScraperConfig(
                url=job.url,
                selectors=job.selectors,
                scraper_type=ScraperType(job.config.get("scraper_type", "static")),
                delay=job.delay,
                max_retries=job.max_retries,
                timeout=job.timeout,
                user_agent=job.user_agent,
                headers=job.headers,
                cookies=job.cookies,
                proxy=job.proxy,
                pagination=job.pagination,
                extract_links=job.extract_links,
                extract_images=job.extract_images,
                extract_metadata=job.extract_metadata,
                continue_on_error=job.continue_on_error,
                ignore_ssl_errors=job.ignore_ssl_errors
            )
            
            # Create scraper
            scraper = ScraperFactory.create_scraper(config)
            
            # Scrape data
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                scraped_data = []
                total_records = 0
                
                # Handle pagination if configured
                if job.pagination:
                    pages_scraped = 0
                    max_pages = job.pagination.get("max_pages", 10)
                    current_url = job.url
                    
                    while current_url and pages_scraped < max_pages:
                        # Update scraper config for current URL
                        scraper.config.url = current_url
                        
                        # Scrape current page
                        session_data = loop.run_until_complete(scraper.scrape_page(current_url))
                        
                        if not session_data.is_successful:
                            logger.error(f"Failed to scrape page {pages_scraped + 1}: {session_data.error}")
                            break
                        
                        # Add scraped data
                        if session_data.data:
                            scraped_data.extend(session_data.data)
                            total_records += session_data.record_count
                        
                        # Find next page
                        next_url = scraper._get_next_page_url(session_data)
                        current_url = next_url
                        pages_scraped += 1
                        
                        # Rate limiting
                        if current_url:
                            loop.run_until_complete(asyncio.sleep(job.delay))
                else:
                    # Single page scraping
                    session_data = loop.run_until_complete(scraper.scrape_page(job.url))
                    
                    if session_data.is_successful:
                        scraped_data = session_data.data
                        total_records = session_data.record_count
                    else:
                        raise Exception(f"Scraping failed: {session_data.error}")
                
                # Process data
                pipeline = DataProcessingPipeline()
                processed_data = loop.run_until_complete(pipeline.process(scraped_data))
                
                # Export data
                exporter = ExporterFactory.create_exporter(job.config.get("output_format", "csv"))
                from exporters.base import ExportConfig
                
                export_config = ExportConfig(
                    filename=f"job_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    format=job.config.get("output_format", "csv"),
                    include_headers=job.config.get("include_headers", True),
                    encoding=job.config.get("encoding", "utf-8")
                )
                
                export_result = exporter.export_with_stats(processed_data, export_config)
                
                # Update job with results
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                job.records_processed = total_records
                job.records_total = total_records
                job.result_path = export_result.file_path
                job.file_size = export_result.file_size
                job.success_rate = 100.0
                job.duration = (job.completed_at - job.started_at).total_seconds()
                session.commit()
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "records_processed": total_records,
                    "file_path": export_result.file_path,
                    "file_size": export_result.file_size,
                    "duration": job.duration
                }
                
            finally:
                loop.close()
                
    except Exception as e:
        logger.error(f"Error scraping job {job_id}: {str(e)}")
        
        # Update job status to failed
        try:
            with SessionLocal() as session:
                job = session.query(JobModel).filter(JobModel.id == job_id).first()
                if job:
                    job.status = "failed"
                    job.completed_at = datetime.utcnow()
                    job.error_message = str(e)
                    job.success_rate = 0.0
                    session.commit()
        except Exception as update_error:
            logger.error(f"Error updating job {job_id} status: {str(update_error)}")
        
        # Retry the task if retries are available
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            "success": False,
            "job_id": job_id,
            "error": str(e)
        }


@celery_app.task(name='processors.tasks.process_data')
def process_data(data: List[Dict[str, Any]], processing_config: Dict[str, Any]) -> Dict[str, Any]:
    """Process scraped data"""
    try:
        pipeline = DataProcessingPipeline()
        
        # Add processors based on configuration
        if processing_config.get("clean_data", True):
            from processors.cleaner import DataCleaner
            pipeline.add_processor(DataCleaner(processing_config.get("cleaning_options", {})))
        
        if processing_config.get("validate_data", True):
            from processors.validator import DataValidator
            pipeline.add_processor(DataValidator(processing_config.get("validation_rules", [])))
        
        if processing_config.get("transform_data", False):
            from processors.transformer import DataTransformer
            pipeline.add_processor(DataTransformer(processing_config.get("transformations", [])))
        
        # Process data
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            processed_data = loop.run_until_complete(pipeline.process(data))
            
            return {
                "success": True,
                "processed_count": len(processed_data),
                "original_count": len(data),
                "data": processed_data
            }
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(name='exporters.tasks.export_data')
def export_data(data: List[Dict[str, Any]], export_config: Dict[str, Any]) -> Dict[str, Any]:
    """Export data to specified format"""
    try:
        # Create exporter
        exporter = ExporterFactory.create_exporter(export_config.get("format", "csv"))
        
        # Create export configuration
        from exporters.base import ExportConfig
        config = ExportConfig(
            filename=export_config.get("filename"),
            format=export_config.get("format", "csv"),
            include_headers=export_config.get("include_headers", True),
            encoding=export_config.get("encoding", "utf-8"),
            delimiter=export_config.get("delimiter", ",")
        )
        
        # Export data
        result = exporter.export_with_stats(data, config)
        
        return {
            "success": result.success,
            "file_path": result.file_path,
            "record_count": result.record_count,
            "file_size": result.file_size,
            "export_time": result.export_time,
            "error_message": result.error_message
        }
        
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(name='jobs.tasks.cleanup_old_logs')
def cleanup_old_logs() -> Dict[str, Any]:
    """Clean up old log files"""
    try:
        import os
        from datetime import datetime, timedelta
        
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            return {"success": True, "cleaned_files": 0}
        
        # Clean up log files older than 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        cleaned_files = 0
        
        for filename in os.listdir(logs_dir):
            file_path = os.path.join(logs_dir, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    cleaned_files += 1
                    logger.info(f"Cleaned up old log file: {filename}")
        
        return {
            "success": True,
            "cleaned_files": cleaned_files
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(name='jobs.tasks.cleanup_temp_files')
def cleanup_temp_files() -> Dict[str, Any]:
    """Clean up temporary files"""
    try:
        import os
        from datetime import datetime, timedelta
        
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            return {"success": True, "cleaned_files": 0}
        
        # Clean up temp files older than 1 hour
        cutoff_date = datetime.utcnow() - timedelta(hours=1)
        cleaned_files = 0
        
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    cleaned_files += 1
                    logger.info(f"Cleaned up temp file: {filename}")
        
        return {
            "success": True,
            "cleaned_files": cleaned_files
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(name='jobs.tasks.backup_database')
def backup_database() -> Dict[str, Any]:
    """Create database backup"""
    try:
        from backups.backup_manager import backup_manager
        
        result = backup_manager.perform_backup()
        
        return {
            "success": result["success"],
            "backup_path": result.get("backup_path"),
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@celery.app.task(name='monitoring.tasks.check_system_health')
def check_system_health() -> Dict[str, Any]:
    """Check system health"""
    try:
        from config.database import check_connection
        from config.celery import check_celery_health
        
        # Check database
        db_healthy = check_connection()
        
        # Check Celery
        celery_health = check_celery_health()
        
        # Check disk space
        import psutil
        disk_usage = psutil.disk_usage('/')
        disk_healthy = disk_usage.percent < 90
        
        # Check memory
        memory = psutil.virtual_memory()
        memory_healthy = memory.percent < 90
        
        overall_healthy = db_healthy and celery_health.get("status") == "healthy" and disk_healthy and memory_healthy
        
        return {
            "success": True,
            "overall_healthy": overall_healthy,
            "database": "healthy" if db_healthy else "unhealthy",
            "celery": celery_health.get("status", "unknown"),
            "disk_usage": disk_usage.percent,
            "memory_usage": memory.percent,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking system health: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(name='monitoring.tasks.collect_metrics')
def collect_metrics() -> Dict[str, Any]:
    """Collect system metrics"""
    try:
        import psutil
        from config.database import SessionLocal
        from jobs.models import Job as JobModel
        
        # System metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Application metrics
        with SessionLocal() as session:
            total_jobs = session.query(JobModel).count()
            active_jobs = session.query(JobModel).filter(JobModel.status == "running").count()
            completed_jobs = session.query(JobModel).filter(JobModel.status == "completed").count()
            failed_jobs = session.query(JobModel).filter(JobModel.status == "failed").count()
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "network_io": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            },
            "application": {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs
            }
        }
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(name='scrapers.tasks.validate_selectors')
def validate_selectors(url: str, selectors: Dict[str, str], scraper_type: str = "static") -> Dict[str, Any]:
    """Validate CSS selectors against a webpage"""
    try:
        # Create scraper configuration
        config = ScraperConfig(
            url=url,
            selectors=selectors,
            scraper_type=ScraperType(scraper_type),
            delay=0.1,  # Fast for validation
            timeout=10
        )
        
        # Create scraper
        scraper = ScraperFactory.create_scraper(config)
        
        # Scrape page
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            session = loop.run_until_complete(scraper.scrape_page(url))
            
            if not session.is_successful:
                return {
                    "success": False,
                    "error": session.error
                }
            
            # Validate selectors
            validation_results = {}
            for field_name, selector in selectors.items():
                try:
                    elements = session.data.get(field_name, [])
                    
                    validation_results[field_name] = {
                        "selector": selector,
                        "found": len(elements) > 0,
                        "count": len(elements),
                        "sample": elements[:3] if elements else [],
                        "valid": True
                    }
                    
                except Exception as e:
                    validation_results[field_name] = {
                        "selector": selector,
                        "found": False,
                        "count": 0,
                        "sample": [],
                        "valid": False,
                        "error": str(e)
                    }
            
            return {
                "success": True,
                "url": url,
                "scraper_type": scraper_type,
                "validation_results": validation_results,
                "total_selectors": len(selectors),
                "valid_selectors": len([r for r in validation_results.values() if r["valid"]])
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error validating selectors: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# Periodic tasks
@celery_app.task(name='jobs.tasks.periodic_cleanup')
def periodic_cleanup():
    """Periodic cleanup task"""
    try:
        # Clean up old logs
        log_result = cleanup_old_logs.delay()
        
        # Clean up temp files
        temp_result = cleanup_temp_files.delay()
        
        # Collect metrics
        metrics_result = collect_metrics.delay()
        
        return {
            "success": True,
            "tasks": {
                "cleanup_logs": log_result.id,
                "cleanup_temp": temp_result.id,
                "collect_metrics": metrics_result.id
            }
        }
        
    except Exception as e:
        logger.error(f"Error in periodic cleanup: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# Task utilities
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get task status"""
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
            "traceback": result.traceback,
            "date_done": result.date_done
        }
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e)
        }


def revoke_task(task_id: str, terminate: bool = False) -> Dict[str, Any]:
    """Revoke a task"""
    try:
        celery_app.control.revoke(task_id, terminate=terminate)
        return {
            "task_id": task_id,
            "revoked": True,
            "terminated": terminate
        }
    except Exception as e:
        logger.error(f"Error revoking task: {str(e)}")
        return {
            "task_id": task_id,
            "revoked": False,
            "error": str(e)
        }


def get_active_tasks() -> Dict[str, Any]:
    """Get list of active tasks"""
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        return {
            "success": True,
            "active_tasks": active_tasks
        }
    except Exception as e:
        logger.error(f"Error getting active tasks: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_scheduled_tasks() -> Dict[str, Any]:
    """Get list of scheduled tasks"""
    try:
        inspect = celery_app.control.inspect()
        scheduled_tasks = inspect.scheduled()
        return {
            "success": True,
            "scheduled_tasks": scheduled_tasks
        }
    except Exception as e:
        logger.error(f"Error getting scheduled tasks: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Test tasks
    print("Testing Celery tasks...")
    
    # Test system health
    health_result = check_system_health()
    print(f"System health: {health_result}")
    
    # Test metrics collection
    metrics_result = collect_metrics()
    print(f"Metrics: {metrics_result}")
    
    print("Task tests completed")
