"""
Job Manager Module

This module provides job management, scheduling, and coordination
for web scraping operations with Celery task queue integration.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging

from .models import Job, JobStatus, JobPriority, Result, JobMetrics
from .queue import TaskQueue
from .scheduler import JobScheduler
from .worker import ScrapingWorker
from .config import JobConfig


class JobManager:
    """Manages scraping jobs with scheduling and monitoring"""
    
    def __init__(self, task_queue: TaskQueue, db_session):
        self.task_queue = task_queue
        self.db_session = db_session
        self.scheduler = JobScheduler(db_session)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.active_jobs = {}
        self.job_history = []
        
        # Performance tracking
        self.metrics = {}
        self.start_time = datetime.utcnow()
        
        # Configuration
        self.max_concurrent_jobs = 10
        self.default_delay = 1.0
        self.max_retries = 3
        job_timeout = 30
    
    async def create_job(self, job_config: Union[JobConfig, Dict[str, Any]]) -> Job:
        """Create a new scraping job"""
        try:
            # Validate configuration
            if isinstance(job_config, dict):
                job_config = JobConfig(**job_config)
            
            # Create job instance
            job = create_job(**job_config.__dict__)
            
            # Add to database
            self.db_session.add(job)
            self.db_session.commit()
            
            # Add to active jobs
            self.active_jobs[job.id] = job
            
            # Log job creation
            self.logger.info(f"Created job '{job.name}' (ID: {job.id})")
            
            return job
            
        except Exception as e:
            self.logger.error(f"Failed to create job: {str(e)}")
            raise
    
    async def start_job(self, job_id: int) -> bool:
        """Start a scraping job"""
        job = self.get_job(job_id)
        
        if not job:
            self.logger.error(f"Job {job_id} not found")
            return False
        
        if job.status != JobStatus.PENDING:
            self.logger.warning(f"Job {job_id} is not in pending state (status: {job.status.value})")
            return False
        
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            job.retry_count = 0
            self.db_session.commit()
            
            # Queue job for execution
            await self.task_queue.enqueue('run_scraping_job', job.id)
            
            # Add to active jobs
            self.active_jobs[job.id] = job
            
            self.logger.info(f"Started job '{job.name}' (ID: {job.id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start job {job_id}: {str(e)}")
            
            # Mark as failed
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self.db_session.commit()
            
            return False
    
    async def stop_job(self, job_id: int) -> bool:
        """Stop a running job"""
        job = self.get_job(job_id)
        
        if not job:
            self.logger.error(f"Job {job_id} not found")
            return False
        
        if not job.is_running:
            self.logger.warning(f"Job {job_id} is not running (status: {job.status.value})")
            return False
        
        try:
            # Update job status
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            self.db_session.commit()
            
            # Cancel task in queue
            await self.task_queue.cancel_task(job.id)
            
            # Remove from active jobs
            if job.id in self.active_jobs:
                del self.active_jobs[job.id]
            
            self.logger.info(f"Stopped job '{job.name}' (ID: {job.id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop job {job_id}: {str(e)}")
            return False
    
    async def pause_job(self, job_id: int) -> bool:
        """Pause a running job"""
        job = self.get_job(job_id)
        
        if not job:
            self.logger.error(f"Job {job_id} not found")
            return False
        
        if job.status != JobStatus.RUNNING:
            self.logger.warning(f"Job {job_id} is not running (status: {job.status.value})")
            return False
        
        try:
            # Update job status
            job.status = JobStatus.PAUSED
            self.db_session.commit()
            
            # Pause task in queue
            await self.task_queue.pause_task(job.id)
            
            self.logger.info(f"Paused job '{job.name}' (ID: {job.id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause job {job_id}: {str(e)}")
            return False
    
    async def resume_job(self, job_id: int) -> bool:
        """Resume a paused job"""
        job = self.get_job(job_id)
        
        if not job:
            self.logger.error(f"Job {job_id} not found")
            return False
        
        if job.status != JobStatus.PAUSED:
            self.logger.warning(f"Job {job_id} is not paused (status: {job.status.value})")
            return False
        
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.retry_count = 0
            self.db_session.commit()
            
            # Resume task in queue
            await self.task_queue.resume_task(job.id)
            
            # Add back to active jobs
            self.active_jobs[job.id] = job
            
            self.logger.info(f"Resumed job '{job.name}' (ID: {job.id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume job {job_id}: {str(e)}")
            return False
    
    async def retry_job(self, job_id: int) -> bool:
        """Retry a failed job"""
        job = self.get_job(job_id)
        
        if not job:
            self.logger.error(f"Job {job_id} not found")
            return False
        
        if not job.can_retry():
            self.logger.warning(f"Job {job_id} cannot be retried (max retries reached: {job.max_retries})")
            return False
        
        try:
            # Update job status
            job.status = JobStatus.RETRYING
            job.retry_count += 1
            job.started_at = datetime.utcnow()
            self.db_session.commit()
            
            # Re-queue job
            await self.task_queue.enqueue('run_scraping_job', job.id)
            
            # Add back to active jobs
            self.active_jobs[job.id] = job
            
            self.logger.info(f"Retrying job '{job.name}' (ID: {job.id}) - Attempt {job.retry_count}/{job.max_retries}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to retry job {job_id}: {str(e)}")
            return False
    
    def get_job(self, job_id: int) -> Optional[Job]:
        """Get job by ID"""
        return self.db_session.query(Job).filter(Job.id == job_id).first()
    
    def get_jobs(self, status: Optional[JobStatus] = None, limit: int = 50) -> List[Job]:
        """Get jobs with optional status filter"""
        query = self.db_session.query(Job)
        
        if status:
            query = query.filter(Job.status == status)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_active_jobs(self) -> List[Job]:
        """Get currently active jobs"""
        return list(self.active_jobs.values())
    
    def get_job_history(self, days: int = 30, limit: int = 100) -> List[Job]:
        """Get job history"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return self.db_session.query(Job).filter(
            Job.created_at >= cutoff_date
        ).order_by(Job.created_at.desc).limit(limit).all()
    
    def get_job_statistics(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive job statistics"""
        return get_job_statistics(job_id, self.db_session)
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        total_jobs = self.db_session.query(Job).count()
        active_jobs = len(self.active_jobs)
        completed_jobs = self.db_session.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
        failed_jobs = self.db_session.query(Job.status == JobStatus.FAILED).count()
        
        return {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs: failed_jobs,
            'success_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            'uptime': (datetime.utcnow() - self.start_time).total_seconds() / 3600  # hours
        }
    
    def cancel_all_jobs(self) -> int:
        """Cancel all running jobs"""
        cancelled_count = 0
        
        for job_id in list(self.active_jobs.keys()):
            if self.stop_job(job_id):
                cancelled_count += 1
        
        return cancelled_count
    
    def cleanup_completed_jobs(self, days: int = 30) -> int:
        """Clean up old completed jobs"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = self.db_session.query(Job).filter(
            Job.status == JobStatus.COMPLETED,
            Job.created_at < cutoff_date
        ).delete()
        
        self.db_session.commit()
        return deleted_count
    
    def get_performance_metrics(self, job_id: int) -> Dict[str, Any]:
        """Get performance metrics for a specific job"""
        metrics = self.db_session.query(JobMetrics).filter(Job.job_id == job_id).first()
        
        if not metrics:
            return {}
        
        return {
            'job_id': metrics.job_id,
            'pages_scraped': metrics.pages_scraped,
            'pages_failed': metrics.pages_failed,
            'data_extracted': metrics.data_extracted,
            'processing_time': metrics.processing_time,
            'memory_usage': metrics.memory_usage,
            'cpu_usage': metrics.cpu_usage,
            'network_requests': metrics.network_requests,
            'error_count': metrics.error_count
        }
    
    def export_job_results(self, job_id: int, format: str = 'csv') -> Optional[str]:
        """Export job results to specified format"""
        job = self.get_job(job_id)
        
        if not job:
            return None
        
        # Get results
        results = self.db_session.query(Result).filter(Result.job_id == job_id).all()
        
        if not results:
            return None
        
        # Export results
        from exporters.factory import ExporterFactory
        
        try:
            exporter = ExporterFactory.create_exporter(format)
            config = ExportConfig(
                filename=f"job_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                format=format
            )
            
            # Prepare data for export
            export_data = []
            for result in results:
                export_data.append(result.processed_data or result.raw_data)
            
            result = exporter.export_with_stats(export_data, config)
            
            return result.file_path
            
        except Exception as e:
            self.logger.error(f"Failed to export results for job {job_id}: {str(e}")
            return None
    
    def get_job_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return self.task_queue.get_queue_status()
    
    def clear_queue(self) -> int:
        """Clear all jobs from queue"""
        return self.task_queue.clear_queue()
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.task_queue.get_queue_size()


class JobScheduler:
    """Handles job scheduling and cron-based scheduling"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load existing schedules
        self._load_schedules()
    
    def _load_schedules(self):
        """Load existing schedules from database"""
        schedules = self.db_session.query(Schedule).filter(Schedule.is_active == True).all()
        
        for schedule in schedules:
            self._schedule_jobs[schedule.id] = schedule
    
    def add_schedule(self, job_id: int, cron_expression: str, timezone: str = 'UTC') -> bool:
        """Add cron-based schedule for job"""
        job = self.db_session.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            self.logger.error(f"Job {job_id} not found")
            return False
        
        try:
            # Create schedule
            schedule = Schedule(
                job_id=job.id,
                cron_expression=cron_expression,
                timezone=timezone,
                is_active=True,
                max_runs=None,
                run_count=0
            )
            
            self.db_session.add(schedule)
            self.db_session.commit()
            
            # Schedule next run
            self._update_next_run(schedule)
            
            self.logger.info(f"Added schedule for job '{job.name}' (ID: {job_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create schedule: {str(e)}")
            return False
    
    def remove_schedule(self, schedule_id: int) -> bool:
        """Remove job schedule"""
        schedule = self.db_session.query(Schedule).filter(Schedule.id == schedule_id).first()
        
        if not schedule:
            self.logger.error(f"Schedule {schedule_id} not found")
            return False
        
        try:
            self.db_session.delete(schedule)
            self.db_session.commit()
            
            self._remove_schedule_cache(schedule_id)
            
            self.logger.info(f"Removed schedule for job {schedule.job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove schedule: {str(e)}")
            return False
    
    def _update_next_run(self, schedule: Schedule):
        """Update next run time for schedule"""
        try:
            import crontab
            schedule.next_run = croniter(croniter(schedule.cron_expression, start_time=schedule.next_run)
            schedule.next_run = schedule.next_run.replace(tzinfo(schedule.timezone))
            
            self.db_session.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to update next run: {str(e)}")
    
    def _remove_schedule_cache(self, schedule_id: int):
        """Remove schedule from cache"""
        if schedule_id in self._schedule_jobs:
            del self._schedule_jobs[schedule_id]
    
    def get_schedule(self, schedule_id: int) -> Optional[Schedule]:
        """Get schedule by ID"""
        return self.db_session.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    def get_active_schedules(self) -> List[Schedule]:
        """Get all active schedules"""
        return self.db_session.query(Schedule).filter(Schedule.is_active == True).all()
    
    def get_schedules_for_job(self, job_id: int) -> List[Schedule]:
        """Get all schedules for a specific job"""
        return self.db_session.query(Schedule).filter(Schedule.job_id == job_id).all()
    
    def get_pending_runs(self) -> List[Schedule]:
        """Get all pending scheduled runs"""
        return self.db_session.query(Schedule).filter(
            Schedule.next_run <= datetime.utcnow(),
            Schedule.is_active == True
        ).all()
    
    def update_schedule_runs(self):
        """Update all scheduled runs"""
        schedules = self.get_pending_runs()
        
        for schedule in schedules:
            if schedule.next_run <= datetime.utcnow():
                self._update_next_run(schedule)
        
        self.db_session.commit()
    
    def get_next_run_time(self, schedule_id: int) -> Optional[datetime]:
        """Get next run time for schedule"""
        schedule = self.get_schedule(schedule_id)
        return schedule.next_run if schedule else None
    
    def enable_schedule(self, schedule_id: int) -> bool:
        """Enable a schedule"""
        schedule = self.get_schedule(schedule_id)
        
        if not schedule:
            return False
        
        try:
            schedule.is_active = True
            self.db_session.commit()
            self._update_next_run(schedule)
            
            self.logger.info(f"Enabled schedule for job {schedule.job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable schedule {schedule_id}: {str(e)}")
            return False
    
    def disable_schedule(self, schedule_id: int) -> bool:
        """Disable a schedule"""
        schedule = self.get_schedule(schedule_id)
        
        if not schedule:
            return False
        
        try:
            schedule.is_active = False
            self.db_session.commit()
            
            self.logger.info(f"Disabled schedule for job {schedule.job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disable schedule {schedule_id}: {str(e)}")
            return False


class ScrapingWorker:
    """Celery worker for executing scraping jobs"""
    
    def __init__(self, scraper_engine, data_processor, export_engine, config: Optional[Dict[str, Any]] = None):
        """Initialize scraping worker"""
        self.scraper_engine = scraper_engine
        self.data_processor = data_processor
        self.export_engine = export_engine
        self.config = config or {}
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Performance settings
        self.max_concurrent_jobs = self.config.get('max_concurrent_jobs', 4)
        self.default_delay = self.config.get('default_delay', 1.0)
        self.max_retries = self.config.get('max_retries', 3)
        self.timeout = self.config.get('timeout', 30)
    
    @celery.task(bind=True, max_retries=3)
    def run_scraping_job(self, task_id: str) -> Dict[str, Any]:
        """Execute scraping job"""
        try:
            # Get job from database
            job_id = int(task_id)
            job = self._get_job_from_db(job_id)
            
            if not job:
                self.logger.error(f"Job {job_id} not found")
                return {'status': 'error', 'message': f"Job {job_id} not found"}
            
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            job.retry_count = 0
            job.updated_at = datetime.utcnow()
            self.db_session.commit()
            
            # Initialize statistics
            scraped_pages = 0
            failed_pages = 0
            data_extracted = 0
            processing_time = 0.0
            
            self.logger.info(f"Starting job '{job.name}' (ID: {job_id})")
            
            # Get URLs to scrape
            urls = self._get_urls_to_scrape(job)
            
            if not urls:
                self.logger.warning(f"No URLs found for job {job.name}")
                return {'status': 'warning', 'message': f"No URLs found for job {job.name}"}
            
            # Scrape pages
            for i, url in enumerate(urls):
                try:
                    # Apply rate limiting
                    if self.default_delay > 0:
                        await asyncio.sleep(self.default_delay)
                    
                    # Scrape page
                    page_data = await self.scraper_engine.scrape_page(url, job.config)
                    
                    scraped_pages += 1
                    
                    # Process data
                    if self.data_processor:
                        processed_data = await self.data_processor.process([page_data])
                        data_extracted += len(processed_data)
                    else:
                        data_extracted += len(page_data.data)
                    
                    # Update progress
                    progress = (i + 1) / len(urls) * 100
                    self.update_state(
                        task_id=task_id,
                        meta={'progress': progress}
                    )
                    
                    # Handle errors
                    if page_data.error:
                        failed_pages += 1
                        self.logger.error(f"Error scraping {url}: {page_data.error}")
                    
                except Exception as e:
                    failed_pages += 1
                    self.logger.error(f"Error scraping {url}: {str(e}")
            
            # Update job completion
            job.status = JobStatus.COMPLETED if failed_pages == 0 else JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.records_processed = data_extracted
            job.records_total = len(urls)
            job.error_count = failed_pages
            job.processing_time = processing_time
            
            # Update database
            self.db_session.commit()
            
            # Export results
            if self.export_engine and job.records_processed > 0:
                try:
                    export_result = self.export_engine.export_with_stats(
                        [r for r in self._get_results_from_db(job_id)],
                        config=ExportConfig(
                            filename=f"job_{job.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            format='json'
                        )
                    )
                    
                    job.result_path = export_result.file_path
                    job.file_size = export_result.file_size
                    job.download_count = export_result.record_count
                    
                    self.logger.info(f"Exported {job.download_count} records to {export_result.file_path}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to export results: {str(e}")
            
            # Update metrics
            metrics = JobMetrics(
                job_id=job.id,
                pages_scraped=scraped_pages,
                pages_failed=failed_pages,
                data_extracted=data_extracted,
                processing_time=processing_time
            )
            
            self.db_session.add(metrics)
            self.db_session.commit()
            
            self.logger.info(f"Job '{job.name}' completed: {job.records_processed}/{job.records_total} records")
            
            return {
                'status': 'completed',
                'job_id': job.id,
                'records_processed': job.records_processed,
                'file_path': job.result_path,
                'file_size': job.file_size,
                'processing_time': job.processing_time,
                'pages_scraped': scraped_pages,
                'pages_failed': failed_pages,
                'error_count': job.error_count
            }
            
        except Exception as e:
            # Handle job failure
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            job.retry_count += 1
            job.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            
            self.logger.error(f"Job '{job.name}' failed: {str(e)}")
            
            return {
                'status': 'failed',
                'job_id': job.id,
                'error_message': job.error_message,
                'retry_count': job.retry_count
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f"Unexpected error: {str(e)}"
            }
    
    def _get_job_from_db(self, job_id: int) -> Optional[Job]:
        """Get job from database"""
        return self.db_session.query(Job).filter(Job.id == job_id).first()
    
    def _get_urls_to_scrape(self, job: Job) -> List[str]:
        """Get URLs to scrape for job"""
        urls = [job.url]
        
        # Handle pagination
        if job.config and job.config.get('pagination'):
            pagination = job.config['pagination']
            next_selector = pagination.get('next_selector')
            max_pages = pagination.get('max_pages', 10)
            
            # Extract first page
            base_url = job.url
            urls.append(base_url)
            
            # Extract pagination links
            if next_selector:
                page_count = 0
                while page_count < max_pages:
                    try:
                    # Load next page
                    next_page_url = self._get_next_page(base_url, next_selector)
                    if not next_page_url:
                        break
                    
                    urls.append(next_page)
                    page_count += 1
                    
                    base_url = next_page
                    
                except Exception as e:
                    self.logger.warning(f"Error getting next page: {str(e)}")
                    break
        
        return urls
    
    def _get_next_page(self, base_url: str, next_selector: str) -> Optional[str]:
        """Get next page URL from pagination"""
        try:
            # Use the scraper engine to find next page
            test_page = self.scraper_engine.scrape_page(base_url)
            
            # Find next page link
            if test_page.data:
                links = test_page.data.get('links', [])
                for link in links:
                    if link.get('href'):
                        return link['href']
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error finding next page: {str(e)}")
            return None
    
    def _get_results_from_db(self, job_id: int) -> List[Result]:
        """Get results for a job from database"""
        return self.db_session.query(Result).filter(Result.job_id == job_id).all()
    
    def update_job_progress(self, task_id: str, meta: Dict[str, Any]):
        """Update job progress from task metadata"""
        if task_id in self.active_jobs:
            job = self.active_jobs.get(task_id)
            if job:
                progress = meta.get('progress', 0)
                job.records_processed = meta.get('current', 0)
                
                # Update progress
                progress_percentage = (job.records_processed / job.records_total) * 100 if job.records_total > 0 else 0
                job.progress_percentage = progress_percentage
                
                # Update database
                self.db_session.commit()
                
                self.logger.info(f"Job {job.name} progress: {progress_percentage:.1f}%")
    
    def get_job_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'queue_size': self.task_queue.get_queue_size(),
            'active_jobs': len(self.active_jobs),
            'queued_jobs': self.task_queue.get_queued_jobs(),
            'failed_jobs': self.task_queue.get_failed_jobs(),
            'success_rate': self.task_queue.get_success_rate()
        }
    
    def get_job_metrics(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive job metrics"""
        job = self.get_job(job_id)
        
        if not job:
            return None
        
        # Get metrics
        metrics = self.db_session.query(JobMetrics).filter(JobMetrics.job_id == job_id).first()
        
        if not metrics:
            return None
        
        return {
            'job_id': job.id,
            'job_name': job.name,
            'status': job.status.value,
            'pages_scraped': metrics.pages_scraped,
            'pages_failed': metrics.pages_failed,
            'data_extracted': metrics.data_extracted,
            'processing_time': metrics.processing_time,
            'memory_usage': metrics.memory_usage,
            'cpu_usage': metrics.cpu_usage,
            'network_requests': metrics.network_requests,
            'error_count': metrics.error_count,
            'created_at': metrics.created_at,
            'updated_at': metrics.updated_at
        }
    
    def cleanup_completed_jobs(self, days: int = 30):
        """Clean up old completed jobs"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = self.db_session.query(Job).filter(
            Job.status == JobStatus.COMPLETED,
            Job.created_at < cutoff_date
        ).delete()
        
        self.db_session.commit()
        
        return deleted_count
    
    def get_job_summary(self, job_id: int) -> Dict[str, Any]:
        """Get comprehensive job summary"""
        job = self.get_job(job_id)
        
        if not job:
            return {}
        
        metrics = self.get_job_metrics(job_id)
        
        results = self.get_results_from_db(job_id)
        logs = self.db_session.query(JobLog).filter(Job.job_id == job_id).order_by(Job.created_at.desc()).all()
        
        return {
            'job': {
                'id': job.id,
                'name': job.name,
                'status': job.status.value,
                'url': job.url,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'duration': job.duration,
                'records_processed': job.records_processed,
                'success_rate': job.success_rate,
                'error_count': job.error_count
            },
            'metrics': metrics,
            'results': {
                'total_results': len(results),
                'sample_results': results[:5] if results else [],
                'field_coverage': self._calculate_field_coverage(results),
                'data_quality': self._calculate_data_quality(results)
            },
            'logs': {
                'total_logs': len(logs),
                'error_logs': len([log for log in logs if log.level in ['ERROR', 'CRITICAL']),
                'warning_logs': len([log for log in logs if log.level in ['WARNING']),
                'info_logs': len([log for log in logs if log.level in ['INFO', 'DEBUG'])
            },
            'recent_errors': [log.message for log in logs if log.level in ['ERROR', 'CRITICAL']][-5:],
            'recent_warnings': [log.message for log in logs if log.level in ['WARNING']][-5:]],
            'recent_info': [log.message for log in logs if log.level in ['INFO']][-5:]]
            }
        }
    
    def _calculate_field_coverage(self, results: List[Dict[str, Any]]) -> float:
        """Calculate field coverage percentage"""
        if not results:
            return 0.0
        
        if not results[0]:
            return 0.0
        
        # Get all unique field names
        all_fields = set()
        for result in results:
            all_fields.update(result.get('processed_data', {}))
        
        if not all_fields:
            return 0.0
        
        # Calculate coverage for each field
        field_coverage = {}
        
        for field_name in all_fields:
            field_count = sum(1 for result in results if field_name in result.get('processed_data', {}))
            field_coverage[field_name] = (field_count / len(results)) * 100
        
        return sum(field_coverage.values()) / len(all_fields)
    
    def _calculate_data_quality(self, results: List[Dict[str, Any]]) -> float:
        """Calculate data quality score"""
        if not results:
            return 0.0
        
        quality_scores = []
        
        for result in results:
            score = 0.0
            
            # Check for empty or null values
            non_null_values = sum(1 for value in result.get('processed_data', {}).values() if value)
            total_values = sum(1 for value in result.get('processed_data').values() if value is not None)
            
            if total_values > 0:
                score = non_null_values / total_values
                score -= 0.1 if score <= 0.9 else 0.0
            else:
                score = 0.0
            
            quality_scores.append(score)
        
        return statistics.mean(quality_scores) if quality_scores else 0.0
    
    def get_job_performance_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze job performance trends"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get metrics for the period
        metrics = self.db_session.query(JobMetrics).filter(
            Job.created_at >= cutoff_date
        ).all()
        
        if not metrics:
            return {'status': 'insufficient_data'}
        
        # Calculate trends
        trends = {
            'period_days': days,
            'total_jobs': len(metrics),
            'avg_processing_time': sum(m.processing_time) / len(metrics) if metrics else 0,
            'avg_records_per_job': sum(m.records_extracted) / len(metrics) if metrics else 0,
            'avg_success_rate': sum(m.success_rate for m in metrics if m.success_rate is not None else 0) / len(metrics) if m.success_rate else 0,
            'avg_error_rate': sum(m.error_rate for m in metrics if m.error_rate is not None else 0) / len(m) if m.error_rate else 0
        }
        
        return trends
    
    def export_job_results(self, job_id: int, format: str = 'csv') -> Optional[str]:
        """Export job results to specified format"""
        return self.export_job_results(job_id, format)
    
    def get_job_history(self, job_id: int) -> List[Dict[str, Any]]:
        """Get complete job history"""
        job = self.get_job(job_id)
        logs = self.db_session.query(JobLog).filter(Job.job_id == job_id).order_by(Job.created_at.desc()).all()
        
        return [
            {
                'timestamp': log.created_at.isoformat(),
                'level': log.level,
                'message': log.message,
                'details': log.details,
                'source': log.source
            } for log in logs
        ]
    
    def export_job_results(self, job_id: int, format: str = 'csv') -> Optional[str]:
        """Export job results to specified format"""
        job = self.get_job(job_id)
        
        if not job or job.status != JobStatus.COMPLETED:
            return None
        
        # Get results
        results = self.get_results_from_db(job_id)
        
        if not results:
            return None
        
        # Create exporter
        from exporters.factory import ExporterFactory
        
        export_config = ExportConfig(
            filename=f"job_{job.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            format=format
        )
        
        exporter = ExporterFactory.create_exporter(format)
        
        # Prepare data for export
        export_data = []
        
        for result in results:
            export_data.append(result.processed_data or result.raw_data)
        
        # Export data
        try:
            result = exporter.export_with_stats(export_data, export_config)
            return result.file_path
        except Exception as e:
            self.logger.error(f"Failed to export results for job {job_id}: {str(e)}")
            return None
    
    def get_results_from_db(self, job_id: int) -> List[Result]:
        """Get results from database for a job"""
        return self.db_session.query(Result).filter(Result.job_id == job_id).all()
    
    def create_job_from_dict(self, job_data: Dict[str, Any]) -> Job:
        """Create job from dictionary"""
        return Job(**job_data)
    
    def update_job(self, job_id: int, **updates: Dict[str, Any]) -> bool:
        """Update job properties"""
        job = self.get_job(job_id)
        
        if not job:
            return False
        
        try:
            # Update job properties
            for key, value in updates.items():
                if hasattr(job, key) and hasattr(job, key):
                    setattr(job, key, value)
            
            job.updated_at = datetime.utcnow()
            self.db_session.commit()
            
            self.logger.info(f"Updated job {job.name} (ID: {job.id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update job {job_id}: {str(e)}")
            return False
    
    def delete_job(self, job_id: int) -> bool:
        """Delete a job and all associated data"""
        job = self.get_job(job_id)
        
        if not job:
            return False
        
        try:
            # Delete results
            self.db.query(Result).filter(Result.job_id == job_id).delete()
            
            # Delete logs
            self.db.query(JobLog).filter(Job.job_id == job_id).delete()
            
            # Delete job
            self.db_session.delete(job)
            self.db_session.commit()
            
            self.logger.info(f"Deleted job {job.name} (ID: {job_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete job {job_id}: {str(e)}")
            return False
    
    def clone_job(self, job_id: int, new_name: Optional[str] = None) -> Optional[str]:
        """Clone a job configuration"""
        job = self.get_job(job_id)
        
        if not job:
            return None
        
        try:
            # Create new job with same configuration
            new_job = Job(
                name=new_name or f"{job.name} (Copy)",
                url=job.url,
                selectors=job.selectors,
                config=job.config,
                priority=job.priority,
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
                ignore_ssl_errors=job.ignore_ssl_errors,
                output_format=job.output_format,
                include_headers=job.include_headers,
                encoding=job.encoding,
                tags=job.tags,
                is_public=job.is_public,
                metadata=job.metadata
            )
            
            self.db.add(new_job)
            self.db.commit()
            self.db.commit()
            
            return new_job.id
            
        except Exception as e:
            self.logger.error(f"Failed to clone job {job_id}: {str(e)}")
            return None
    
    def get_job_config(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get job configuration"""
        job = self.get_job(job_id)
        
        if not job:
            return None
        
        return {
            'id': job.id,
            'name': job.name,
            'url': job.url,
            'selectors': job.selectors,
            'config': job.config,
            'priority': job.priority.value,
            'delay': job.delay,
            'max_retries': job.max_retries,
            'timeout': job.timeout,
            'user_agent': job.user_agent,
            'headers': job.headers,
            'cookies': job.cookies,
            'proxy': job.proxy,
            'pagination': job.pagination,
            'extract_links': job.extract_links,
            'extract_images': job.extract_images,
            'extract_metadata': job.extract_metadata,
            'continue_on_error': job.continue_on_error,
            'ignore_ssl_errors': job.ignore_ssl_errors,
            'output_format': job.output_format,
            'include_headers': job.include_headers,
            'encoding': job.encoding,
            'tags': job.tags,
            'is_public': job.is_public,
            'metadata': job.metadata
        }
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return self.get_system_statistics()
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        total_jobs = self.db_session.query(Job).count()
        active_jobs = len(self.active_jobs)
        completed_jobs = self.db_session.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
        failed_jobs = self.db_session.query(Job.status == JobStatus.FAILED).count()
        pending_jobs = self.db_session.query(Job.status == JobStatus.PENDING).count()
        
        return {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'pending_jobs': pending_jobs,
            'success_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            'jobs_per_hour': self._calculate_jobs_per_hour(),
            'queue_status': self.get_job_queue_status()
        }
    
    def _calculate_jobs_per_hour(self) -> float:
        """Calculate average jobs per hour"""
        if not self.start_time:
            return 0.0
        
        hours_elapsed = (datetime.utcnow() - self.start_time).total_seconds() / 3600
        total_jobs = self.db_session.query(Job).count()
        
        if hours_elapsed > 0 and total_jobs > 0:
            return total_jobs / hours_elapsed
        
        return 0.0
    
    def _calculate_jobs_per_hour(self) -> float:
        """Calculate average jobs per hour"""
        if not self.start_time:
            return 0.0
        
        hours_elapsed = (datetime.utcnow() - self.start_time).total_seconds() / 3600
        total_jobs = self.db_session.query(Job).count()
        
        if hours_elapsed > 0 and total_jobs > 0:
            return total_jobs / hours_elapsed
        
        return 0.0


# Factory function for creating job managers
def create_job_manager(task_queue, db_session) -> JobManager:
    """Create job manager with dependencies"""
    return JobManager(task_queue, db_session)


# Example usage patterns
def example_usage():
    """Example usage patterns for job manager"""
    
    # Create task queue and database session
    from .queue import TaskQueue
    from sqlalchemy import create_engine
    
    engine = create_engine()
    session = engine.connect()
    
    # Create task queue
    queue = TaskQueue()
    
    # Create job manager
    manager = create_job_manager(queue, session)
    
    # Create a test job
    job_config = {
        'name': 'Test Job',
        'url': 'https://example.com',
        'selectors': {'title': 'h1', 'content': '.content'},
        'scraper_type': 'static',
        'delay': 2.0,
        'max_retries': 3,
        'timeout': 30
    }
    
    job = manager.create_job(job_config)
    print(f"Created job: {job.name} (ID: {job.id})")
    
    # Start job
    success = await manager.start_job(job.id)
    print(f"Job started successfully: {success}")
    
    # Get job status
        status = manager.get_job_status(job.id)
        print(f"Job status: {status}")
    
    # Get job statistics
        stats = manager.get_job_statistics()
        print(f"System statistics: {stats}")
    
    # Clean up
    manager.cleanup_completed_jobs(days=7)
    print(f"Cleaned up {manager.cleanup_completed_jobs(days=7)} jobs")
