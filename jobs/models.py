"""
Job Models Module

This module defines the data models for job management, including
job status, priority, scheduling, and execution tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(Enum):
    """Job priority levels"""
    LOW = 1
    NORMAL = 3
    HIGH = 5
    URGENT = 8
    CRITICAL = 10


@dataclass
class JobConfig:
    """Job configuration dataclass"""
    name: str
    url: str
    selectors: Dict[str, str]
    scraper_type: str = "static"
    config: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    delay: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    user_agent: str = "WebScraper/1.0"
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[Dict[str, str]] = None
    proxy: Optional[str] = None
    pagination: Optional[Dict[str, Any]] = None
    extract_links: bool = False
    extract_images: bool = False
    extract_metadata: bool = True
    continue_on_error: bool = True
    ignore_ssl_errors: bool = False
    output_format: str = "csv"
    include_headers: bool = True
    encoding: str = "utf-8"
    tags: List[str] = field(default_factory=list)
    is_public: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class Job(Base):
    """Job model for database storage"""
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(Text, nullable=False)
    selectors = Column(JSON, nullable=False)
    config = Column(JSON, nullable=False)
    
    # Status and priority
    status = Column(String(20), default=JobStatus.PENDING.value)
    priority = Column(Integer, default=JobPriority.NORMAL.value)
    
    # Scheduling
    scheduled_at = Column(DateTime, nullable=True)
    cron_expression = Column(String(100), nullable=True)
    timezone = Column(String(50), default='UTC')
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    
    # Execution tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Results tracking
    records_processed = Column(Integer, default=0)
    records_total = Column(Integer, default=0)
    result_path = Column(Text, nullable=True)
    file_size = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # User and permissions
    user_id = Column(Integer, nullable=True)  # Will add foreign key later
    is_public = Column(Boolean, default=False)
    tags = Column(JSON, default=list)
    
    # Additional metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    results = relationship("Result", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="job", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(id={self.id}, name='{self.name}', status='{self.status}')"
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.records_total == 0:
            return 0.0
        return (self.records_processed / self.records_total) * 100
    
    @property
    def is_running(self) -> bool:
        """Check if job is currently running"""
        return self.status in [JobStatus.RUNNING, JobStatus.PAUSED, JobStatus.RETRYING]
    
    @property
    def is_finished(self) -> bool:
        """Check if job is finished (completed, failed, or cancelled)"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    
    @property
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.retry_count < self.max_retries
    
    @property
    def should_retry(self) -> bool:
        """Check if job should be retried based on error type"""
        return self.status == JobStatus.FAILED and self.can_retry


class Result(Base):
    """Result model for storing scraped data"""
    __tablename__ = 'results'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'))
    url = Column(Text, nullable=False)
    raw_data = Column(JSON, nullable=False)
    processed_data = JSON, nullable=True)
    validation_status = Column(String(50), default='pending')
    validation_errors = Column(JSON, nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA-256 hash
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="job")
    
    def __repr__(self):
        return f"<Result(id={self.id}, job_id={self.job_id}, url='{self.url[:50]}...')"


class JobLog(Base):
    """Log entries for job execution"""
    __tablename__ = 'job_logs'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'))
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    context = Column(JSON, nullable=True)
    source = Column(String(100), nullable=True)
    stack_trace = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="job")


class Schedule(Base):
    """Job scheduling configuration"""
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'))
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default='UTC')
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    max_runs = Column(Integer, nullable=True)
    run_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="job")


class Export(Base):
    """Export configuration and results"""
    __tablename__ = 'exports'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'))
    format = Column(String(20), nullable=False)
    file_path = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, default=0)
    record_count = Integer, default=0)
    download_count = Integer, default=0)
    is_public = Boolean, default=False)
    share_token = Column(String(64), unique=True, nullable=True)
    expires_at = DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_downloaded = DateTime, nullable=True)
    
    # Relationships
    job = relationship("Job", back_populates="job")


class JobMetrics(Base):
    """Job execution metrics and performance data"""
    __tablename__ = 'job_metrics'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'))
    pages_scraped = Integer, default=0)
    pages_failed = Integer, default=0)
    data_extracted = Integer, default=0)
    processing_time = Float, default=0.0)
    memory_usage = Float, default=0.0)
    cpu_usage = Float, default=0.0)
    network_requests = Integer, default=0)
    error_count = Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="job")


# Data validation functions
def validate_job_config(config: Dict[str, Any]) -> bool:
    """Validate job configuration"""
    required_fields = ['name', 'url', 'selectors']
    
    for field in required_fields:
        if field not in config or not config[field]:
            return False
    
    # Validate URL format
    import re
    url_pattern = r'^https?://(?:[-\w.])+(?:[^\s.])+(?:[:\d]+)?(?:/[^\s]*)?)*$'
    if not re.match(url_pattern, config['url']):
        return False
    
    # Validate selectors
    if not isinstance(config['selectors'], dict) or not config['selectors']:
        return False
    
    return True


def validate_job_priority(priority: Union[str, int]) -> bool:
    """Validate job priority"""
    if isinstance(priority, str):
        try:
            return priority.lower() in [p.value for p in JobPriority]
        except ValueError:
            return False
    
    if isinstance(priority, int):
        return priority in [p.value for p in JobPriority]
    
    return False


def validate_job_status(status: Union[str, JobStatus]) -> bool:
    """Validate job status"""
    if isinstance(status, str):
        try:
            return status.lower() in [s.value for s in JobStatus]
        except ValueError:
            return False
    
    if isinstance(status, JobStatus):
        return status in JobStatus
    
    return False


# Helper functions
def create_job_config(name: str, url: str, selectors: Dict[str, str], **kwargs) -> JobConfig:
    """Create JobConfig from parameters"""
    return JobConfig(
        name=name,
        url=url,
        selectors=selectors,
        **kwargs
    )


def get_job_by_id(job_id: int, session) -> Optional[Job]:
    """Get job by ID"""
    return session.query(Job).filter(Job.id == job_id).first()


def get_jobs_by_status(status: JobStatus, session, limit: int = 50) -> List[Job]:
    """Get jobs by status"""
    return session.query(Job).filter(Job.status == status).limit(limit).all()


def get_active_jobs(session, limit: int = 50) -> List[Job]:
    """Get currently running jobs"""
    return session.query(Job).filter(
        Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
    ).limit(limit).all()


def get_user_jobs(user_id: int, session, limit: int = 50) -> List[Job]:
    """Get jobs for a specific user"""
    return session.query(Job).filter(Job.user_id == user_id).limit(limit).all()


def get_job_statistics(job_id: int, session) -> Optional[Dict[str, Any]]:
    """Get comprehensive job statistics"""
    job = get_job_by_id(job_id, session)
    if not job:
        return None
    
    metrics = session.query(JobMetrics).filter(Job.job_id == job_id).first()
    
    return {
        'job_id': job.id,
        'job_name': job.name,
        'status': job.status.value,
        'pages_scraped': metrics.pages_scraped,
        'pages_failed': metrics.pages_failed,
        'data_extracted': metrics.data_extracted,
        'processing_time': metrics.processing_time,
        'success_rate': job.success_rate,
        'duration': job.duration,
        'created_at': job.created_at.isoformat(),
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'error_message': job.error_message
    }


# Factory functions for creating jobs
def create_job(name: str, url: str, selectors: Dict[str, str], **kwargs) -> Job:
    """Create a new job instance"""
    config = create_job_config(name, url, selectors, **kwargs)
    
    job = Job(
        name=name,
        url=url,
        selectors=config.selectors,
        config=config.config,
        priority=config.priority,
        delay=config.delay,
        max_retries=config.max_retries,
        timeout=config.timeout,
        user_agent=config.user_agent,
        headers=config.headers,
        cookies=config.cookies,
        proxy=config.proxy,
        pagination=config.pagination,
        extract_links=config.extract_links,
        extract_images=config.extract_images,
        extract_metadata=config.extract_metadata,
        continue_on_error=config.continue_on_error,
        ignore_ssl_errors=config.ignore_ssl_errors,
        output_format=config.output_format,
        include_headers=config.include_headers,
        encoding=config.encoding,
        tags=config.tags,
        is_public=config.is_public,
        metadata=config.metadata
    )
    
    return job


def create_job_from_dict(job_data: Dict[str, Any]) -> Job:
    """Create job from dictionary"""
    return Job(**job_data)


def create_batch_jobs(job_configs: List[Dict[str, Any]]) -> List[Job]:
    """Create multiple jobs from configurations"""
    jobs = []
    
    for job_config in job_configs:
        job = create_job(**job_config)
        jobs.append(job)
    
    return jobs


# Query helper functions
def get_jobs_by_tag(tag: str, session, limit: int = 50) -> List[Job]:
    """Get jobs by tag"""
    return session.query(Job).filter(Job.tags.contains([tag]).limit(limit).all()


def get_jobs_by_priority(priority: JobPriority, session, limit: int = 50) -> List[Job]:
    """Get jobs by priority"""
    return session.query(Job).filter(Job.priority == priority).limit(limit).all()


def get_recent_jobs(session, days: int = 7, limit: int = 50) -> List[Job]:
    """Get recent jobs from the last N days"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    return session.query(Job).filter(Job.created_at >= cutoff_date).limit(limit).all()


# Status transition helpers
def can_transition_to(current_status: JobStatus, new_status: JobStatus) -> bool:
    """Check if status transition is valid"""
    valid_transitions = {
        JobStatus.PENDING: [JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.FAILED, JobStatus.CANCELLED],
        JobStatus.QUEUED: [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.FAILED, JobStatus.CANCELLED],
        JobStatus.RUNNING: [JobStatus.PAUSED, JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED],
        JobStatus.PAUSED: [JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED],
        JobStatus.RETRYING: [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING],
        JobStatus.COMPLETED: [JobStatus.FAILED, JobStatus.CANCELLED],
        JobStatus.FAILED: [JobStatus.RETRYING, JobStatus.PENDING],
        JobStatus.CANCELLED: [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.FAILED]
    }
    
    return new_status in valid_transitions.get(current_status, [])


def get_next_status(current_status: JobStatus, has_errors: bool = False) -> JobStatus:
    """Determine next status based on current status and error state"""
    if has_errors:
        if current_status in [JobStatus.RUNNING, JobStatus.RETRYING]:
            return JobStatus.FAILED
        elif current_status == JobStatus.PENDING:
            return JobStatus.FAILED
    
    # Normal status progression
    status_flow = {
        JobStatus.PENDING: JobStatus.QUEUED,
        JobStatus.QUEUED: JobStatus.RUNNING,
        JobStatus.RUNNING: JobStatus.COMPLETED,
        JobStatus.COMPLETED: JobStatus.FINISHED,
        JobStatus.FAILED: JobStatus.RETRYING,
        JobStatus.CANCELLED: JobStatus.FINISHED
    }
    
    return status_flow.get(current_status, JobStatus.FINISHED)


# Example usage patterns
def example_usage():
    """Example usage patterns for job models"""
    
    # Create a simple job
    job = create_job(
        name="Test Job",
        url="https://example.com",
        selectors={"title": "h1", "content": ".content"}
    )
    
    # Create a complex job with all options
    advanced_job = create_job(
        name="Advanced Job",
        url="https://example.com/products",
        selectors={
            "title": ".product-title",
            "price": ".product-price",
            "rating": ".product-rating",
            "availability": ".stock-status"
        },
        scraper_type="dynamic",
        delay=2.0,
        max_retries=5,
        timeout=60,
        pagination={
            "next_selector": ".next-page",
            "max_pages": 100,
            "stop_selector": ".no-results"
        },
        extract_links=True,
        extract_images=True,
        priority=JobPriority.HIGH,
        tags=["products", "e-commerce"],
        metadata={"source": "automated"}
    )
    
    # Create multiple jobs from configurations
    job_configs = [
        {
            "name": "Job 1",
            "url": "https://site1.com",
            "selectors": {"title": "h1"}
        },
        {
            "name": "Job 2",
            "url": "https://site2.com",
            "selectors": {"content": ".content"}
        }
    ]
    
    batch_jobs = create_batch_jobs(job_configs)
    
    print(f"Created job: {job}")
    print(f"Created advanced job: {advanced_job}")
    print(f"Created {len(batch_jobs)} batch jobs")


if __name__ == "__main__":
    # Test job models
    logging.basicConfig(level=logging.INFO)
    
    # Test job creation and validation
    try:
        job = create_job(
            name="Test Job",
            url="https://example.com",
            selectors={"title": "h1", "content": ".content"}
        )
        
        print(f"Created job: {job}")
        print(f"Job ID: {job.id}")
        print(f"Job Status: {job.status.value}")
        
        # Test validation
        config_dict = {
            'name': 'Test Job',
            'url': 'https://example.com',
            'selectors': {'title': 'h1'}
        }
        
        is_valid = validate_job_config(config_dict)
        print(f"Config validation: {is_valid}")
        
        # Test priority validation
        is_valid_priority = validate_job_priority('high')
        print(f"Priority validation: {is_valid_priority}")
        
        # Test status validation
        is_valid_status = validate_job_status('pending')
        print(f"Status validation: {is_valid_status}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    example_usage()
