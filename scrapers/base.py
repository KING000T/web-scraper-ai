"""
Base Scraper Module

This module defines the abstract base class for all scrapers and
common data structures used throughout the scraping system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
import logging
import hashlib


class ScrapingError(Exception):
    """Base exception for scraping-related errors"""
    pass


class NetworkError(ScrapingError):
    """Network-related scraping errors"""
    pass


class ParseError(ScrapingError):
    """HTML parsing errors"""
    pass


class ValidationError(ScrapingError):
    """Data validation errors"""
    pass


class RateLimitError(ScrapingError):
    """Rate limiting errors"""
    pass


@dataclass
class ScrapedPage:
    """Represents a scraped web page with extracted data"""
    
    url: str
    data: Dict[str, Any]
    status_code: int
    html: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    extraction_time: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metadata"""
        if not self.metadata:
            self.metadata = {}
    
    @property
    def is_successful(self) -> bool:
        """Check if scraping was successful"""
        return self.error is None and self.status_code == 200
    
    @property
    def record_count(self) -> int:
        """Get the number of records extracted"""
        if not self.data:
            return 0
        
        # If data is a list, return its length
        if isinstance(self.data, list):
            return len(self.data)
        
        # If data is a dict with list values, return the length of the longest list
        if isinstance(self.data, dict):
            list_lengths = [len(v) for v in self.data.values() if isinstance(v, list)]
            return max(list_lengths) if list_lengths else 0
        
        return 1
    
    def get_field_value(self, field_name: str, index: int = 0) -> Any:
        """Get a specific field value by index"""
        if field_name not in self.data:
            return None
        
        value = self.data[field_name]
        
        if isinstance(value, list):
            return value[index] if index < len(value) else None
        
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'url': self.url,
            'data': self.data,
            'status_code': self.status_code,
            'html': self.html,
            'timestamp': self.timestamp.isoformat(),
            'extraction_time': self.extraction_time,
            'error': self.error,
            'metadata': self.metadata,
            'is_successful': self.is_successful,
            'record_count': self.record_count
        }


@dataclass
class ScrapingSession:
    """Represents a scraping session with multiple pages"""
    
    job_id: str
    start_url: str
    pages: List[ScrapedPage] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_pages: int = 0
    successful_pages: int = 0
    failed_pages: int = 0
    total_records: int = 0
    
    @property
    def duration(self) -> Optional[float]:
        """Get session duration in seconds"""
        if not self.end_time:
            return None
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage"""
        if self.total_pages == 0:
            return 0.0
        return (self.successful_pages / self.total_pages) * 100
    
    @property
    def pages_per_minute(self) -> float:
        """Get pages scraped per minute"""
        if not self.duration or self.duration == 0:
            return 0.0
        return (self.total_pages / self.duration) * 60
    
    def add_page(self, page: ScrapedPage):
        """Add a scraped page to the session"""
        self.pages.append(page)
        self.total_pages += 1
        
        if page.is_successful:
            self.successful_pages += 1
            self.total_records += page.record_count
        else:
            self.failed_pages += 1
    
    def finish(self):
        """Mark the session as finished"""
        self.end_time = datetime.utcnow()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session summary"""
        return {
            'job_id': self.job_id,
            'start_url': self.start_url,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'total_pages': self.total_pages,
            'successful_pages': self.successful_pages,
            'failed_pages': self.failed_pages,
            'success_rate': self.success_rate,
            'total_records': self.total_records,
            'pages_per_minute': self.pages_per_minute
        }


class BaseScraper(ABC):
    """Abstract base class for all web scrapers"""
    
    def __init__(self, config):
        """Initialize scraper with configuration"""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session_id = self._generate_session_id()
        self._setup_logging()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.utcnow().isoformat()
        content = f"{self.__class__.__name__}-{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _setup_logging(self):
        """Setup logging for this scraper instance"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.__class__.__name__} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    @abstractmethod
    async def scrape_page(self, url: str) -> ScrapedPage:
        """Scrape a single page - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def extract_data(self, html: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data from HTML using selectors"""
        pass
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is accessible and scrapeable"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def normalize_url(self, url: str, base_url: str) -> str:
        """Normalize URL relative to base URL"""
        if url.startswith(('http://', 'https://')):
            return url
        
        return urljoin(base_url, url)
    
    def apply_rate_limit(self):
        """Apply rate limiting between requests"""
        if self.config.delay > 0:
            self.logger.debug(f"Applying rate limit: {self.config.delay}s delay")
            time.sleep(self.config.delay)
    
    def handle_error(self, error: Exception, url: str) -> ScrapedPage:
        """Handle scraping errors and create error page"""
        error_message = f"Error scraping {url}: {str(error)}"
        self.logger.error(error_message)
        
        return ScrapedPage(
            url=url,
            data={},
            status_code=0,
            error=error_message,
            timestamp=datetime.utcnow()
        )
    
    def create_session(self, start_url: str) -> ScrapingSession:
        """Create a new scraping session"""
        return ScrapingSession(
            job_id=self.session_id,
            start_url=start_url
        )
    
    async def scrape_multiple(self, urls: List[str]) -> ScrapingSession:
        """Scrape multiple URLs"""
        session = self.create_session(urls[0] if urls else "")
        
        self.logger.info(f"Starting to scrape {len(urls)} URLs")
        
        for i, url in enumerate(urls):
            try:
                self.logger.info(f"Scraping URL {i+1}/{len(urls)}: {url}")
                
                # Apply rate limiting
                self.apply_rate_limit()
                
                # Scrape the page
                page = await self.scrape_page(url)
                session.add_page(page)
                
                self.logger.info(
                    f"Scraped {url} - Status: {page.status_code}, "
                    f"Records: {page.record_count}"
                )
                
            except Exception as e:
                error_page = self.handle_error(e, url)
                session.add_page(error_page)
        
        session.finish()
        self.logger.info(f"Completed scraping session: {session.get_summary()}")
        
        return session
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scraper statistics"""
        return {
            'scraper_type': self.__class__.__name__,
            'session_id': self.session_id,
            'config': {
                'delay': self.config.delay,
                'max_retries': self.config.max_retries,
                'timeout': self.config.timeout,
                'user_agent': self.config.user_agent
            }
        }
    
    def __str__(self) -> str:
        """String representation of scraper"""
        return f"{self.__class__.__name__}(session_id={self.session_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (
            f"{self.__class__.__name__}("
            f"session_id={self.session_id}, "
            f"scraper_type={self.config.scraper_type.value}, "
            f"url={self.config.url})"
        )


class SelectorUtils:
    """Utility functions for CSS selectors"""
    
    @staticmethod
    def validate_selector(selector: str) -> bool:
        """Validate CSS selector syntax"""
        try:
            # Basic validation - check for balanced brackets
            if selector.count('[') != selector.count(']'):
                return False
            if selector.count('(') != selector.count(')'):
                return False
            
            # Check for invalid characters
            invalid_chars = ['<', '>', '"', "'"]
            if any(char in selector for char in invalid_chars):
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def optimize_selector(selector: str) -> str:
        """Optimize CSS selector for better performance"""
        # Remove redundant whitespace
        selector = ' '.join(selector.split())
        
        # Convert descendant selectors to child selectors where possible
        if ' ' in selector and '>' not in selector:
            # This is a simplified optimization
            parts = selector.split()
            if len(parts) == 2:
                selector = f"{parts[0]} > {parts[1]}"
        
        return selector
    
    @staticmethod
    def get_selector_type(selector: str) -> str:
        """Get the type of selector (class, id, tag, attribute, etc.)"""
        if selector.startswith('#'):
            return 'id'
        elif selector.startswith('.'):
            return 'class'
        elif selector.startswith('['):
            return 'attribute'
        elif ':' in selector:
            return 'pseudo'
        else:
            return 'tag'


class DataUtils:
    """Utility functions for data processing"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'"
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        return text.strip()
    
    @staticmethod
    def extract_number(text: str) -> Optional[float]:
        """Extract numeric value from text"""
        if not text:
            return None
        
        import re
        # Find numbers (including decimals and commas)
        numbers = re.findall(r'[\d,]+\.?\d*', text.replace(',', ''))
        
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
        
        return None
    
    @staticmethod
    def extract_url(text: str) -> Optional[str]:
        """Extract URL from text"""
        if not text:
            return None
        
        import re
        url_pattern = re.compile(
            r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?'
        )
        
        match = url_pattern.search(text)
        return match.group(0) if match else None
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        
        import re
        # Remove common formatting characters
        clean_phone = re.sub(r'[\s\-\(\)]+', '', phone)
        
        # Check if it's all digits and reasonable length
        return clean_phone.isdigit() and 10 <= len(clean_phone) <= 15
