# System Architecture Document

## 1. Architecture Overview

### 1.1 System Purpose
The Web Scraping and Data Extraction Automation System is built on a modular, microservices-oriented architecture that enables scalable, reliable, and maintainable data extraction from web sources.

### 1.2 Architectural Goals
- **Scalability**: Horizontal scaling for large workloads
- **Reliability**: 99.9% uptime with fault tolerance
- **Modularity**: Independent, replaceable components
- **Performance**: High-throughput data processing
- **Maintainability**: Clean separation of concerns

### 1.3 Core Architectural Patterns
- **Event-Driven Architecture**: Asynchronous task processing
- **Repository Pattern**: Data access abstraction
- **Factory Pattern**: Dynamic component creation
- **Observer Pattern**: Real-time monitoring and notifications
- **Strategy Pattern**: Pluggable scraping and processing strategies

## 2. High-Level System Architecture

### 2.1 System Diagram
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Web Scraping System                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │   Web Frontend  │    │   REST API      │    │   WebSocket     │           │
│  │                 │◄──►│                 │◄──►│                 │           │
│  │ - Dashboard     │    │ - FastAPI       │    │ - Real-time     │           │
│  │ - Job Config    │    │ - Endpoints     │    │ - Updates       │           │
│  │ - Results View  │    │ - Auth          │    │ - Notifications │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│           │                       │                       │                   │
│           └───────────────────────┼───────────────────────┘                   │
│                                   │                                           │
├───────────────────────────────────┼───────────────────────────────────────────┤
│                                   │                                           │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐ │
│  │                    Application Layer                                     │ │
│  │                                                                           │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │ │
│  │  │   Job Manager   │  │ Data Processor  │  │ Export Engine   │           │ │
│  │  │                 │  │                 │  │                 │           │ │
│  │  │ - Scheduling    │  │ - Cleaning      │  │ - CSV/JSON      │           │ │
│  │  │ - Queue Mgmt    │  │ - Validation    │  │ - Google Sheets │           │ │
│  │  │ - Monitoring    │  │ - Transform     │  │ - Database      │           │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘           │ │
│  └─────────────────────────────────┼─────────────────────────────────────────┘ │
│                                  │                                           │
├───────────────────────────────────┼───────────────────────────────────────────┤
│                                  │                                           │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐ │
│  │                    Service Layer                                         │ │
│  │                                                                           │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │ │
│  │  │ Scraper Engine  │  │  Validation     │  │  Notification   │           │ │
│  │  │                 │  │  Service        │  │  Service        │           │ │
│  │  │ - Static HTML   │  │ - Rules Engine  │  │ - Email Alerts  │           │ │
│  │  │ - Dynamic JS    │  │ - Quality Check │  │ - Webhooks      │           │ │
│  │  │ - Browser Mgmt  │  │ - Reporting     │  │ - Dashboard     │           │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘           │ │
│  └─────────────────────────────────┼─────────────────────────────────────────┘ │
│                                  │                                           │
├───────────────────────────────────┼───────────────────────────────────────────┤
│                                  │                                           │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐ │
│  │                    Infrastructure Layer                                  │ │
│  │                                                                           │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │ │
│  │  │   Task Queue    │  │    Database      │  │   File Storage  │           │ │
│  │  │                 │  │                 │  │                 │           │ │
│  │  │ - Celery        │  │ - PostgreSQL    │  │ - Local Files   │           │ │
│  │  │ - Redis         │  │ - Connection    │  │ - Cloud Storage │           │ │
│  │  │ - Workers       │  │ - Pooling       │  │ - Backups       │           │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘           │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Architecture
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User      │    │   Job       │    │   Scraper   │    │   Data      │
│   Request   │──►│   Manager   │──►│   Engine    │──►│ Processor   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │   Task      │    │   Raw       │    │   Clean     │
                   │   Queue     │    │   Data      │    │   Data      │
                   └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │   Worker    │    │   Storage   │    │   Export    │
                   │   Process   │    │   Layer     │    │   Engine    │
                   └─────────────┘    └─────────────┘    └─────────────┘
```

## 3. Component Architecture

### 3.1 Scraper Engine Module

#### 3.1.1 Scraper Factory
```python
class ScraperFactory:
    """Factory pattern for creating appropriate scrapers"""
    
    @staticmethod
    def create_scraper(config: ScraperConfig) -> BaseScraper:
        """Create scraper based on configuration"""
        scraper_type = config.scraper_type.lower()
        
        if scraper_type == "static":
            return StaticScraper(config)
        elif scraper_type == "dynamic":
            return DynamicScraper(config)
        elif scraper_type == "advanced":
            return AdvancedScraper(config)
        else:
            raise ValueError(f"Unknown scraper type: {scraper_type}")
```

#### 3.1.2 Scraper Interface
```python
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """Abstract base class for all scrapers"""
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def scrape_page(self, url: str) -> ScrapedPage:
        """Scrape a single page"""
        pass
    
    @abstractmethod
    async def scrape_multiple(self, urls: List[str]) -> List[ScrapedPage]:
        """Scrape multiple pages"""
        pass
    
    def extract_data(self, html: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data using selectors"""
        soup = BeautifulSoup(html, 'html.parser')
        extracted = {}
        
        for field, selector in selectors.items():
            elements = soup.select(selector)
            if elements:
                extracted[field] = [elem.get_text(strip=True) for elem in elements]
            else:
                extracted[field] = []
        
        return extracted
```

#### 3.1.3 Static Scraper Implementation
```python
class StaticScraper(BaseScraper):
    """Scraper for static HTML content"""
    
    def __init__(self, config: ScraperConfig):
        super().__init__(config)
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with configuration"""
        session = requests.Session()
        
        # Set headers
        session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Add custom headers
        if self.config.headers:
            session.headers.update(self.config.headers)
        
        # Set up proxy if configured
        if self.config.proxy:
            session.proxies = {'http': self.config.proxy, 'https': self.config.proxy}
        
        return session
    
    async def scrape_page(self, url: str) -> ScrapedPage:
        """Scrape a single static page"""
        try:
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            
            # Extract data
            data = self.extract_data(response.text, self.config.selectors)
            
            return ScrapedPage(
                url=url,
                status_code=response.status_code,
                data=data,
                html=response.text,
                timestamp=datetime.utcnow()
            )
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to scrape {url}: {e}")
            raise NetworkError(f"Network error for {url}: {e}")
    
    async def scrape_multiple(self, urls: List[str]) -> List[ScrapedPage]:
        """Scrape multiple pages concurrently"""
        tasks = [self.scrape_page(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to scrape {urls[i]}: {result}")
            else:
                successful_results.append(result)
        
        return successful_results
```

### 3.2 Data Processing Module

#### 3.2.1 Processing Pipeline
```python
class DataProcessingPipeline:
    """Pipeline for data processing operations"""
    
    def __init__(self, processors: List[DataProcessor]):
        self.processors = processors
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process data through all pipeline stages"""
        processed_data = data
        
        for i, processor in enumerate(self.processors):
            try:
                processed_data = await processor.process(processed_data)
                self.logger.info(f"Completed processing stage {i+1}: {processor.__class__.__name__}")
            except Exception as e:
                self.logger.error(f"Processing stage {i+1} failed: {e}")
                raise ProcessingError(f"Pipeline failed at stage {i+1}: {e}")
        
        return processed_data
```

#### 3.2.2 Data Processors
```python
class DataProcessor(ABC):
    """Abstract base class for data processors"""
    
    @abstractmethod
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process data"""
        pass

class CleaningProcessor(DataProcessor):
    """Clean and normalize extracted data"""
    
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean data records"""
        cleaned_data = []
        
        for record in data:
            cleaned_record = {}
            for key, value in record.items():
                if isinstance(value, list):
                    cleaned_record[key] = [self._clean_text(item) for item in value if item]
                else:
                    cleaned_record[key] = self._clean_text(value)
            cleaned_data.append(cleaned_record)
        
        return cleaned_data
    
    def _clean_text(self, text: str) -> str:
        """Clean individual text values"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', str(text))
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters (optional)
        text = text.strip()
        
        return text

class ValidationProcessor(DataProcessor):
    """Validate processed data"""
    
    def __init__(self, validation_rules: Dict[str, ValidationRule]):
        self.validation_rules = validation_rules
        self.validator = DataValidator(validation_rules)
    
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate data records"""
        validated_data = []
        validation_errors = []
        
        for i, record in enumerate(data):
            result = self.validator.validate(record)
            
            if result.is_valid:
                validated_data.append(record)
            else:
                validation_errors.extend([
                    f"Record {i}: {error}" for error in result.errors
                ])
        
        if validation_errors:
            self.logger.warning(f"Validation errors found: {validation_errors}")
        
        return validated_data

class TransformationProcessor(DataProcessor):
    """Transform data structure"""
    
    def __init__(self, transformations: Dict[str, Transformation]):
        self.transformations = transformations
    
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply transformations to data"""
        transformed_data = []
        
        for record in data:
            transformed_record = record.copy()
            
            for field, transformation in self.transformations.items():
                try:
                    if field in transformed_record:
                        transformed_record[field] = transformation.apply(transformed_record[field])
                except Exception as e:
                    self.logger.warning(f"Transformation failed for field {field}: {e}")
            
            transformed_data.append(transformed_record)
        
        return transformed_data
```

### 3.3 Job Management Module

#### 3.3.1 Job Scheduler
```python
class JobScheduler:
    """Manages job scheduling and execution"""
    
    def __init__(self, task_queue, db_session):
        self.queue = task_queue
        self.db = db_session
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def schedule_job(self, job_config: JobConfig) -> Job:
        """Schedule a new job for execution"""
        # Create job record
        job = Job(
            name=job_config.name,
            url=job_config.url,
            selectors=job_config.selectors,
            config=job_config.dict(),
            status=JobStatus.PENDING,
            priority=job_config.priority,
            created_at=datetime.utcnow()
        )
        
        self.db.add(job)
        self.db.commit()
        
        # Queue job with priority
        await self.queue.enqueue(
            'run_scraping_job',
            job.id,
            priority=job.priority,
            delay=job_config.schedule_delay
        )
        
        self.logger.info(f"Scheduled job {job.id}: {job.name}")
        return job
    
    async def schedule_recurring_job(self, job_config: JobConfig, cron_expression: str):
        """Schedule recurring job using cron"""
        job = await self.schedule_job(job_config)
        
        # Add to cron scheduler
        scheduler.add_job(
            func=self._execute_recurring_job,
            trigger=CronTrigger.from_crontab(cron_expression),
            args=[job.id],
            id=f"recurring_job_{job.id}",
            replace_existing=True
        )
        
        return job
    
    async def _execute_recurring_job(self, job_id: int):
        """Execute recurring job"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if job and job.status == JobStatus.COMPLETED:
            # Reset job for new execution
            job.status = JobStatus.PENDING
            job.created_at = datetime.utcnow()
            job.started_at = None
            job.completed_at = None
            job.records_processed = 0
            
            await self.queue.enqueue('run_scraping_job', job_id)
```

#### 3.3.2 Job Worker
```python
class ScrapingWorker:
    """Celery worker for executing scraping jobs"""
    
    def __init__(self):
        self.scraper_factory = ScraperFactory()
        self.processing_pipeline = self._create_pipeline()
        self.export_engine = ExportEngine()
    
    @celery.task(bind=True, max_retries=3)
    def run_scraping_job(self, task, job_id: int):
        """Execute scraping job"""
        job = self._get_job(job_id)
        
        try:
            # Update job status
            self._update_job_status(job, JobStatus.RUNNING)
            
            # Create scraper
            config = ScraperConfig(**job.config)
            scraper = self.scraper_factory.create_scraper(config)
            
            # Get URLs to scrape
            urls = self._get_urls_to_scrape(config)
            
            # Scrape pages
            scraped_data = []
            for i, url in enumerate(urls):
                # Update progress
                progress = (i + 1) / len(urls) * 100
                task.update_state(
                    state='PROGRESS',
                    meta={'current': i + 1, 'total': len(urls), 'percent': progress}
                )
                
                # Scrape page
                page_data = scraper.scrape_page(url)
                scraped_data.append(page_data.data)
                
                # Rate limiting
                if config.delay > 0:
                    time.sleep(config.delay)
            
            # Process data
            processed_data = asyncio.run(self.processing_pipeline.process(scraped_data))
            
            # Export results
            export_path = self._export_results(job, processed_data)
            
            # Update job completion
            self._update_job_completion(job, export_path, len(processed_data))
            
            return {
                'status': 'completed',
                'export_path': export_path,
                'records_processed': len(processed_data)
            }
            
        except Exception as exc:
            self._handle_job_failure(job, exc, task)
            raise task.retry(exc=exc, countdown=60)
```

## 4. Data Architecture

### 4.1 Data Models
```python
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class JobStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    selectors = Column(JSON, nullable=False)
    config = Column(JSON, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    records_processed = Column(Integer, default=0)
    result_path = Column(Text)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Relationships
    results = relationship("Result", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="job", cascade="all, delete-orphan")

class Result(Base):
    __tablename__ = 'results'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'))
    url = Column(Text, nullable=False)
    raw_data = Column(JSON, nullable=False)
    processed_data = Column(JSON)
    validation_status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="results")

class Log(Base):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'))
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="logs")

class ScraperConfig(Base):
    __tablename__ = 'scraper_configs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    url_pattern = Column(Text)
    selectors = Column(JSON, nullable=False)
    processing_rules = Column(JSON)
    export_config = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 4.2 Database Architecture
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Database Layer                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │     Jobs        │    │    Results      │    │      Logs       │           │
│  │                 │    │                 │    │                 │           │
│  │ - id (PK)       │◄──►│ - id (PK)       │◄──►│ - id (PK)       │           │
│  │ - name          │    │ - job_id (FK)   │    │ - job_id (FK)   │           │
│  │ - url           │    │ - url           │    │ - level         │           │
│  │ - selectors     │    │ - raw_data      │    │ - message       │           │
│  │ - status        │    │ - processed     │    │ - details       │           │
│  │ - config        │    │ - validation    │    │ - created_at    │           │
│  │ - created_at    │    │ - created_at    │    │                 │           │
│  │ - started_at    │    │                 │    │                 │           │
│  │ - completed_at  │    │                 │    │                 │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│           │                       │                       │                   │
│           └───────────────────────┼───────────────────────┘                   │
│                                   │                                           │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐ │
│  │                    Indexes and Performance                              │ │
│  │                                                                           │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │ │
│  │  │ idx_jobs_status │  │ idx_results_job │  │ idx_logs_job    │           │ │
│  │  │ idx_jobs_created│  │ idx_results_url │  │ idx_logs_level  │           │ │
│  │  │ idx_jobs_url    │  │ idx_results_created│ idx_logs_created│           │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘           │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 5. Service Architecture

### 5.1 Microservices Design
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Service Architecture                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │   API Gateway   │    │  Job Service    │    │ Scraper Service │           │
│  │                 │    │                 │    │                 │           │
│  │ - Load Balancer │◄──►│ - Job Mgmt      │◄──►│ - Data Extraction│           │
│  │ - Auth          │    │ - Scheduling    │    │ - Browser Mgmt  │           │
│  │ - Rate Limiting │    │ - Monitoring    │    │ - Error Handling│           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│           │                       │                       │                   │
│           ▼                       ▼                       ▼                   │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │  Frontend UI    │    │ Data Processing  │    │ Export Service  │           │
│  │                 │    │ Service         │    │                 │           │
│  │ - Dashboard     │    │ - Cleaning      │    │ - File Export   │           │
│  │ - Config UI     │    │ - Validation    │    │ - Format Conv   │           │
│  │ - Results View  │    │ - Transform     │    │ - Storage Mgmt  │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Service Communication
```python
# Service Registry
class ServiceRegistry:
    """Registry for microservice communication"""
    
    def __init__(self):
        self.services = {
            'job_service': 'http://job-service:8001',
            'scraper_service': 'http://scraper-service:8002',
            'processing_service': 'http://processing-service:8003',
            'export_service': 'http://export-service:8004',
            'notification_service': 'http://notification-service:8005'
        }
    
    def get_service_url(self, service_name: str) -> str:
        """Get service URL"""
        return self.services.get(service_name)

# Service Communication
class ServiceClient:
    """Client for inter-service communication"""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.session = requests.Session()
    
    async def call_service(self, service_name: str, endpoint: str, data: dict = None):
        """Call another service"""
        service_url = self.registry.get_service_url(service_name)
        url = f"{service_url}/{endpoint}"
        
        try:
            if data:
                response = self.session.post(url, json=data)
            else:
                response = self.session.get(url)
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Service call failed: {service_name}/{endpoint}: {e}")
            raise ServiceCommunicationError(f"Failed to call {service_name}: {e}")
```

## 6. Infrastructure Architecture

### 6.1 Container Architecture
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Web Frontend
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api-gateway
    environment:
      - REACT_APP_API_URL=http://api-gateway:8000

  # API Gateway
  api-gateway:
    build: ./api-gateway
    ports:
      - "8000:8000"
    depends_on:
      - job-service
      - scraper-service
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@postgres:5432/scraper

  # Job Management Service
  job-service:
    build: ./services/job-service
    ports:
      - "8001:8001"
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/scraper
      - REDIS_URL=redis://redis:6379/0

  # Scraper Service
  scraper-service:
    build: ./services/scraper-service
    ports:
      - "8002:8002"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./downloads:/app/downloads

  # Data Processing Service
  processing-service:
    build: ./services/processing-service
    ports:
      - "8003:8003"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0

  # Export Service
  export-service:
    build: ./services/export-service
    ports:
      - "8004:8004"
    depends_on:
      - redis
      - minio
    environment:
      - REDIS_URL=redis://redis:6379/0
      - STORAGE_URL=minio:9000

  # Notification Service
  notification-service:
    build: ./services/notification-service
    ports:
      - "8005:8005"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0

  # Task Queue Workers
  worker:
    build: ./worker
    depends_on:
      - redis
      - postgres
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/scraper
      - REDIS_URL=redis://redis:6379/0
    command: celery -A worker worker --loglevel=info

  # Infrastructure Services
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=scraper
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
    environment:
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
    command: server /data
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

### 6.2 Cloud Architecture (AWS)
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud Architecture                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │   CloudFront    │    │   API Gateway   │    │  Load Balancer  │           │
│  │                 │    │                 │    │                 │           │
│  │ - CDN           │◄──►│ - REST API      │◄──►│ - ALB           │           │
│  │ - Static Assets │    │ - Auth          │    │ - SSL           │           │
│  │ - Caching       │    │ - Rate Limiting │    │ - Health Checks │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│                                   │                                           │
│                                   ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           ECS/Fargate                                   │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │ Frontend    │  │ API Gateway │  │ Job Service │  │ Scraper     │   │ │
│  │  │ Service     │  │ Service     │  │ Service     │  │ Service     │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │   RDS (PostgreSQL)│  │   ElastiCache    │    │     S3          │           │
│  │                 │    │                 │    │                 │           │
│  │ - Primary DB    │    │ - Redis Cluster  │    │ - File Storage  │           │
│  │ - Read Replicas │    │ - Session Store  │    │ - Backups       │           │
│  │ - Backups       │    │ - Caching        │    │ - Exports       │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │   CloudWatch    │    │   SQS Queue     │    │   Lambda        │           │
│  │                 │    │                 │    │                 │           │
│  │ - Monitoring    │    │ - Task Queue    │    │ - Event Processing│          │
│  │ - Logging       │    │ - Dead Letter   │    │ - Data Processing│          │
│  │ - Alarms        │    │ - FIFO          │    │ - Notifications │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 7. Security Architecture

### 7.1 Security Layers
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Security Architecture                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │   Network       │    │   Application   │    │     Data        │           │
│  │   Security      │    │   Security      │    │   Security      │           │
│  │                 │    │                 │    │                 │           │
│  │ - VPC Isolation │    │ - JWT Auth      │    │ - Encryption    │           │
│  │ - Security Groups│   │ - RBAC          │    │ - Access Control│           │
│  │ - WAF           │    │ - Input Validation│   │ - Audit Logs    │           │
│  │ - DDoS Protection│   │ - Rate Limiting │    │ - Backups       │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Authentication & Authorization
```python
class SecurityConfig:
    """Security configuration"""
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_HOURS = 24
    
    # RBAC Roles
    ROLES = {
        "admin": ["read", "write", "delete", "admin"],
        "user": ["read", "write"],
        "viewer": ["read"]
    }
    
    # Rate Limiting
    RATE_LIMITS = {
        "default": "100/hour",
        "authenticated": "1000/hour",
        "admin": "10000/hour"
    }

class AuthenticationMiddleware:
    """JWT Authentication middleware"""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Extract JWT token
        token = self._extract_token(scope)
        
        if token:
            try:
                # Validate token
                payload = jwt.decode(token, SecurityConfig.JWT_SECRET_KEY, algorithms=[SecurityConfig.JWT_ALGORITHM])
                scope["user"] = payload
            except jwt.JWTError:
                # Invalid token
                await self._send_error(send, 401, "Invalid token")
                return
        
        await self.app(scope, receive, send)
```

## 8. Monitoring & Observability

### 8.1 Monitoring Architecture
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Monitoring Architecture                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │   Application   │    │   Metrics       │    │   Logging       │           │
│  │   Monitoring    │    │   Collection    │    │   Aggregation   │           │
│  │                 │    │                 │    │                 │           │
│  │ - Health Checks │◄──►│ - Prometheus    │◄──►│ - ELK Stack     │           │
│  │ - Performance   │    │ - Grafana       │    │ - Fluentd       │           │
│  │ - Error Tracking│    │ - Custom Metrics│    │ - Logstash     │           │
│  │ - Tracing       │    │ - Alerts       │    │ - Kibana        │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│                                   │                       │                   │
│                                   ▼                       ▼                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      Alerting & Notification                           │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │ PagerDuty   │  │ Slack       │  │ Email       │  │ SMS         │   │ │
│  │  │ Alerts      │  │ Notifications│  │ Alerts      │  │ Alerts      │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Health Checks
```python
class HealthCheck:
    """System health monitoring"""
    
    def __init__(self):
        self.checks = {
            "database": self._check_database,
            "redis": self._check_redis,
            "disk_space": self._check_disk_space,
            "memory": self._check_memory,
            "external_services": self._check_external_services
        }
    
    async def check_all(self) -> Dict[str, bool]:
        """Run all health checks"""
        results = {}
        
        for check_name, check_func in self.checks.items():
            try:
                results[check_name] = await check_func()
            except Exception as e:
                logger.error(f"Health check {check_name} failed: {e}")
                results[check_name] = False
        
        return results
    
    async def _check_database(self) -> bool:
        """Check database connectivity"""
        try:
            # Test database connection
            result = await self.db.execute("SELECT 1")
            return result is not None
        except Exception:
            return False
    
    async def _check_redis(self) -> bool:
        """Check Redis connectivity"""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False
```

This comprehensive system architecture provides a robust, scalable, and maintainable foundation for the web scraping system, supporting both current requirements and future growth.
