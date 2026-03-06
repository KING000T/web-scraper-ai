"""
API Models Module

This module defines Pydantic models for API request/response validation
and serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(str, Enum):
    """Job priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class ScraperType(str, Enum):
    """Scraper type enumeration"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    ADVANCED = "advanced"


class ExportFormat(str, Enum):
    """Export format enumeration"""
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    GOOGLE_SHEETS = "google_sheets"


# Request Models
class JobCreateRequest(BaseModel):
    """Request model for creating a job"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    url: str = Field(..., min_length=1)
    selectors: Dict[str, str] = Field(..., min_items=1)
    scraper_type: ScraperType = ScraperType.STATIC
    delay: float = Field(1.0, ge=0, le=60)
    max_retries: int = Field(3, ge=0, le=10)
    timeout: int = Field(30, ge=1, le=300)
    user_agent: str = Field("WebScraper/1.0", min_length=1)
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[Dict[str, str]] = None
    proxy: Optional[str] = None
    pagination: Optional[Dict[str, Any]] = None
    extract_links: bool = False
    extract_images: bool = False
    extract_metadata: bool = True
    continue_on_error: bool = True
    ignore_ssl_errors: bool = False
    output_format: ExportFormat = ExportFormat.CSV
    include_headers: bool = True
    encoding: str = Field("utf-8", min_length=1)
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('url')
    def validate_url(cls, v):
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        
        return v
    
    @validator('selectors')
    def validate_selectors(cls, v):
        if not v or not isinstance(v, dict):
            raise ValueError('Selectors must be a non-empty dictionary')
        
        for key, selector in v.items():
            if not selector or not selector.strip():
                raise ValueError(f'Empty selector for field: {key}')
        
        return v


class JobUpdateRequest(BaseModel):
    """Request model for updating a job"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    url: Optional[str] = Field(None, min_length=1)
    selectors: Optional[Dict[str, str]] = Field(None, min_items=1)
    delay: Optional[float] = Field(None, ge=0, le=60)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    timeout: Optional[int] = Field(None, ge=1, le=300)
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class JobScheduleRequest(BaseModel):
    """Request model for scheduling a job"""
    cron_expression: str = Field(..., min_length=1)
    timezone: str = Field("UTC", min_length=1)
    max_runs: Optional[int] = Field(None, ge=1)


class ScrapingRequest(BaseModel):
    """Request model for immediate scraping"""
    url: str = Field(..., min_length=1)
    selectors: Dict[str, str] = Field(..., min_items=1)
    scraper_type: ScraperType = ScraperType.STATIC
    delay: float = Field(1.0, ge=0, le=60)
    timeout: int = Field(30, ge=1, le=300)
    user_agent: str = Field("WebScraper/1.0", min_length=1)
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[Dict[str, str]] = None
    proxy: Optional[str] = None
    pagination: Optional[Dict[str, Any]] = None
    extract_links: bool = False
    extract_images: bool = False
    extract_metadata: bool = True
    continue_on_error: bool = True
    ignore_ssl_errors: bool = False


class ExportRequest(BaseModel):
    """Request model for data export"""
    job_id: int = Field(..., ge=1)
    format: ExportFormat = ExportFormat.CSV
    filename: Optional[str] = Field(None, min_length=1)
    include_headers: bool = True
    encoding: str = Field("utf-8", min_length=1)
    delimiter: str = Field(",", min_length=1, max_length=1)
    pretty_print: bool = True


# Response Models
class JobResponse(BaseModel):
    """Response model for job data"""
    id: int
    name: str
    description: Optional[str]
    url: str
    selectors: Dict[str, str]
    scraper_type: ScraperType
    status: JobStatus
    priority: JobPriority
    delay: float
    max_retries: int
    timeout: int
    user_agent: str
    headers: Optional[Dict[str, str]]
    cookies: Optional[Dict[str, str]]
    proxy: Optional[str]
    pagination: Optional[Dict[str, Any]]
    extract_links: bool
    extract_images: bool
    extract_metadata: bool
    continue_on_error: bool
    ignore_ssl_errors: bool
    output_format: ExportFormat
    include_headers: bool
    encoding: str
    tags: List[str]
    is_public: bool
    metadata: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime
    records_processed: int
    records_total: int
    result_path: Optional[str]
    file_size: int
    error_message: Optional[str]
    retry_count: int
    duration: Optional[float]
    success_rate: float
    is_running: bool
    is_finished: bool
    can_retry: bool
    should_retry: bool
    
    class Config:
        from_attributes = True


class JobSummary(BaseModel):
    """Summary model for job list responses"""
    id: int
    name: str
    status: JobStatus
    priority: JobPriority
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    records_processed: int
    records_total: int
    success_rate: float
    duration: Optional[float]
    tags: List[str]
    
    class Config:
        from_attributes = True


class JobStatistics(BaseModel):
    """Response model for job statistics"""
    job_id: int
    job_name: str
    status: JobStatus
    pages_scraped: int
    pages_failed: int
    data_extracted: int
    processing_time: float
    memory_usage: float
    cpu_usage: float
    network_requests: int
    error_count: int
    created_at: datetime
    updated_at: datetime


class ScrapingResult(BaseModel):
    """Response model for scraping results"""
    url: str
    data: Dict[str, Any]
    status_code: int
    html: Optional[str]
    timestamp: datetime
    extraction_time: Optional[float]
    error: Optional[str]
    metadata: Dict[str, Any]
    is_successful: bool
    record_count: int
    
    class Config:
        from_attributes = True


class ExportResult(BaseModel):
    """Response model for export results"""
    success: bool
    file_path: Optional[str]
    record_count: int
    file_size: int
    export_time: float
    exporter_name: str
    format: str
    metadata: Dict[str, Any]
    timestamp: datetime
    error_message: Optional[str]
    file_size_mb: float
    records_per_second: float
    
    class Config:
        from_attributes = True


class SystemStatistics(BaseModel):
    """Response model for system statistics"""
    total_jobs: int
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    success_rate: float
    uptime: float
    queue_size: int
    queued_jobs: List[int]
    failed_jobs_queue: List[int]
    success_rate_queue: float


class HealthCheck(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: datetime
    version: str
    uptime: float
    database_status: str
    queue_status: str
    memory_usage: float
    cpu_usage: float
    disk_usage: float


class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str
    message: str
    details: Optional[Dict[str, Any]]
    timestamp: datetime


class SuccessResponse(BaseModel):
    """Response model for success operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]]
    timestamp: datetime


class PaginatedResponse(BaseModel):
    """Response model for paginated results"""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


# Query Parameters
class JobQueryParams(BaseModel):
    """Query parameters for job filtering"""
    status: Optional[JobStatus] = None
    priority: Optional[JobPriority] = None
    scraper_type: Optional[ScraperType] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(50, ge=1, le=100)
    sort_by: str = Field("created_at", min_length=1)
    sort_order: str = Field("desc", regex="^(asc|desc)$")


class ExportQueryParams(BaseModel):
    """Query parameters for export filtering"""
    format: Optional[ExportFormat] = None
    is_public: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(50, ge=1, le=100)


# Utility Models
class ValidationMessage(BaseModel):
    """Model for validation messages"""
    field: str
    message: str
    code: str


class ValidationResult(BaseModel):
    """Model for validation results"""
    is_valid: bool
    errors: List[ValidationMessage]
    warnings: List[ValidationMessage]


class ConfigurationSchema(BaseModel):
    """Model for configuration schema"""
    name: str
    description: str
    schema: Dict[str, Any]
    examples: List[Dict[str, Any]]


# WebSocket Models
class JobUpdate(BaseModel):
    """Model for job status updates via WebSocket"""
    job_id: int
    status: JobStatus
    progress: Optional[float] = None
    records_processed: Optional[int] = None
    records_total: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: datetime


class SystemMetrics(BaseModel):
    """Model for system metrics via WebSocket"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_jobs: int
    queue_size: int
    timestamp: datetime


# Authentication Models
class User(BaseModel):
    """User model for authentication"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token model for authentication"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token data model"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    scopes: List[str] = []


# Configuration Models
class ScraperConfig(BaseModel):
    """Configuration model for scrapers"""
    name: str
    description: str
    default_settings: Dict[str, Any]
    supported_options: List[str]
    examples: List[Dict[str, Any]]


class ExportConfig(BaseModel):
    """Configuration model for exporters"""
    name: str
    description: str
    supported_formats: List[str]
    default_settings: Dict[str, Any]
    examples: List[Dict[str, Any]]


# Batch Processing Models
class BatchJobRequest(BaseModel):
    """Request model for batch job creation"""
    jobs: List[JobCreateRequest] = Field(..., min_items=1, max_items=100)
    parallel: bool = False
    max_concurrent: int = Field(5, ge=1, le=20)


class BatchJobResponse(BaseModel):
    """Response model for batch job results"""
    batch_id: str
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    job_ids: List[int]
    errors: List[Dict[str, Any]]
    timestamp: datetime


# Monitoring Models
class Alert(BaseModel):
    """Model for system alerts"""
    id: int
    level: str
    message: str
    source: str
    details: Dict[str, Any]
    created_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PerformanceMetrics(BaseModel):
    """Model for performance metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    request_rate: float
    error_rate: float
    response_time: float


# Data Quality Models
class DataQualityReport(BaseModel):
    """Model for data quality reports"""
    job_id: int
    overall_score: float
    grade: str
    metric_scores: Dict[str, float]
    issues: List[str]
    recommendations: List[str]
    record_count: int
    field_count: int
    timestamp: datetime


# File Upload Models
class FileUpload(BaseModel):
    """Model for file upload responses"""
    filename: str
    file_path: str
    file_size: int
    content_type: str
    upload_time: datetime


# Search Models
class SearchQuery(BaseModel):
    """Model for search queries"""
    query: str = Field(..., min_length=1, max_length=500)
    search_type: str = Field("all", regex="^(all|jobs|results|exports)$")
    filters: Optional[Dict[str, Any]] = None
    sort_by: str = Field("relevance", regex="^(relevance|date|name)$")
    limit: int = Field(50, ge=1, le=100)


class SearchResult(BaseModel):
    """Model for search results"""
    type: str
    id: int
    title: str
    description: Optional[str]
    url: Optional[str]
    relevance_score: float
    metadata: Dict[str, Any]


# Integration Models
class WebhookConfig(BaseModel):
    """Model for webhook configuration"""
    url: str = Field(..., min_length=1)
    events: List[str] = Field(..., min_items=1)
    secret: Optional[str] = None
    active: bool = True
    retry_count: int = Field(3, ge=0, le=10)


class WebhookEvent(BaseModel):
    """Model for webhook events"""
    event: str
    data: Dict[str, Any]
    timestamp: datetime
    signature: Optional[str] = None


# Utility functions for model validation
def validate_cron_expression(cron: str) -> bool:
    """Validate cron expression"""
    try:
        from croniter import croniter
        croniter(cron)
        return True
    except:
        return False


def validate_timezone(tz: str) -> bool:
    """Validate timezone string"""
    try:
        import pytz
        pytz.timezone(tz)
        return True
    except:
        return False


def validate_encoding(encoding: str) -> bool:
    """Validate encoding string"""
    try:
        'test'.encode(encoding)
        return True
    except:
        return False


# Example usage patterns
def example_usage():
    """Example usage patterns for API models"""
    
    # Create job request
    job_request = JobCreateRequest(
        name="Test Job",
        url="https://example.com",
        selectors={"title": "h1", "content": ".content"},
        scraper_type=ScraperType.STATIC,
        delay=2.0,
        tags=["test", "example"]
    )
    
    # Create scraping request
    scraping_request = ScrapingRequest(
        url="https://example.com",
        selectors={"title": "h1", "content": ".content"},
        scraper_type=ScraperType.DYNAMIC,
        pagination={"next_selector": ".next-page", "max_pages": 10}
    )
    
    # Create export request
    export_request = ExportRequest(
        job_id=1,
        format=ExportFormat.JSON,
        filename="results.json",
        pretty_print=True
    )
    
    # Create batch job request
    batch_request = BatchJobRequest(
        jobs=[
            JobCreateRequest(
                name="Job 1",
                url="https://site1.com",
                selectors={"title": "h1"}
            ),
            JobCreateRequest(
                name="Job 2", 
                url="https://site2.com",
                selectors={"content": ".content"}
            )
        ],
        parallel=True,
        max_concurrent=5
    )
    
    print(f"Job request: {job_request}")
    print(f"Scraping request: {scraping_request}")
    print(f"Export request: {export_request}")
    print(f"Batch request: {batch_request}")


if __name__ == "__main__":
    # Test API models
    example_usage()
