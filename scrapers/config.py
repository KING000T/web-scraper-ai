"""
Scraper Configuration Module

This module defines configuration classes for web scraping jobs,
including validation and default settings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import re


class ScraperType(Enum):
    """Supported scraper types"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    ADVANCED = "advanced"


@dataclass
class ScraperConfig:
    """Configuration for web scraping jobs"""
    
    # Basic configuration
    url: str
    selectors: Dict[str, str]
    scraper_type: ScraperType = ScraperType.STATIC
    name: Optional[str] = None
    
    # Request configuration
    delay: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    user_agent: str = "WebScraper/1.0"
    
    # Headers and authentication
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[Dict[str, str]] = None
    auth: Optional[tuple] = None
    
    # Proxy configuration
    proxy: Optional[str] = None
    proxy_auth: Optional[tuple] = None
    
    # Browser configuration (for dynamic scraping)
    browser_options: List[str] = field(default_factory=lambda: [
        "--headless",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--window-size=1920,1080"
    ])
    wait_strategy: str = "networkidle"  # networkidle, domcontentloaded, manual
    wait_timeout: int = 10
    scroll_behavior: str = "none"  # none, down, up, multiple
    
    # Pagination configuration
    pagination: Optional[Dict[str, Any]] = None
    
    # Data extraction configuration
    extract_links: bool = False
    extract_images: bool = False
    extract_metadata: bool = True
    
    # Error handling
    continue_on_error: bool = True
    ignore_ssl_errors: bool = False
    
    # Output configuration
    output_format: str = "dict"  # dict, list, pandas
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate_url()
        self._validate_selectors()
        self._validate_delay()
        self._validate_pagination()
    
    def _validate_url(self):
        """Validate the URL"""
        if not self.url:
            raise ValueError("URL is required")
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(self.url):
            raise ValueError(f"Invalid URL: {self.url}")
    
    def _validate_selectors(self):
        """Validate CSS selectors"""
        if not self.selectors:
            raise ValueError("At least one selector is required")
        
        # Basic CSS selector validation
        for field, selector in self.selectors.items():
            if not selector or not selector.strip():
                raise ValueError(f"Empty selector for field: {field}")
            
            # Check for potentially problematic selectors
            if selector.startswith('javascript:'):
                raise ValueError(f"JavaScript selector not allowed: {selector}")
    
    def _validate_delay(self):
        """Validate delay settings"""
        if self.delay < 0:
            raise ValueError("Delay must be non-negative")
        
        if self.delay > 60:
            raise ValueError("Delay cannot exceed 60 seconds")
    
    def _validate_pagination(self):
        """Validate pagination configuration"""
        if self.pagination:
            required_keys = ['next_selector', 'max_pages']
            for key in required_keys:
                if key not in self.pagination:
                    raise ValueError(f"Pagination configuration missing required key: {key}")
            
            max_pages = self.pagination.get('max_pages')
            if max_pages and (not isinstance(max_pages, int) or max_pages < 1):
                raise ValueError("max_pages must be a positive integer")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'url': self.url,
            'selectors': self.selectors,
            'scraper_type': self.scraper_type.value,
            'name': self.name,
            'delay': self.delay,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'user_agent': self.user_agent,
            'headers': self.headers,
            'cookies': self.cookies,
            'auth': self.auth,
            'proxy': self.proxy,
            'proxy_auth': self.proxy_auth,
            'browser_options': self.browser_options,
            'wait_strategy': self.wait_strategy,
            'wait_timeout': self.wait_timeout,
            'scroll_behavior': self.scroll_behavior,
            'pagination': self.pagination,
            'extract_links': self.extract_links,
            'extract_images': self.extract_images,
            'extract_metadata': self.extract_metadata,
            'continue_on_error': self.continue_on_error,
            'ignore_ssl_errors': self.ignore_ssl_errors,
            'output_format': self.output_format
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScraperConfig':
        """Create configuration from dictionary"""
        # Handle enum conversion
        if 'scraper_type' in data:
            if isinstance(data['scraper_type'], str):
                data['scraper_type'] = ScraperType(data['scraper_type'])
        
        return cls(**data)


@dataclass
class PaginationConfig:
    """Configuration for handling paginated content"""
    
    next_selector: str  # CSS selector for next page link
    max_pages: int = 10  # Maximum number of pages to scrape
    stop_selector: Optional[str] = None  # Selector that indicates last page
    page_param: Optional[str] = None  # URL parameter for page number
    start_page: int = 1  # Starting page number
    
    def __post_init__(self):
        """Validate pagination configuration"""
        if not self.next_selector:
            raise ValueError("next_selector is required")
        
        if self.max_pages < 1:
            raise ValueError("max_pages must be positive")
        
        if self.start_page < 1:
            raise ValueError("start_page must be positive")


@dataclass
class BrowserConfig:
    """Configuration for browser-based scraping"""
    
    browser_type: str = "chrome"  # chrome, firefox, safari
    headless: bool = True
    window_size: tuple = (1920, 1080)
    user_data_dir: Optional[str] = None  # Browser profile directory
    extensions: List[str] = field(default_factory=list)
    
    # Performance settings
    disable_images: bool = False
    disable_css: bool = False
    disable_javascript: bool = False
    
    # Network settings
    ignore_certificate_errors: bool = False
    proxy: Optional[str] = None
    
    def get_options(self) -> List[str]:
        """Get browser command line options"""
        options = []
        
        if self.headless:
            options.append("--headless")
        
        options.extend([
            f"--window-size={self.window_size[0]},{self.window_size[1]}",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu"
        ])
        
        if self.disable_images:
            options.append("--blink-settings=imagesEnabled=false")
        
        if self.ignore_certificate_errors:
            options.append("--ignore-certificate-errors")
        
        if self.proxy:
            options.append(f"--proxy-server={self.proxy}")
        
        return options
