"""
Scraper Factory Module

This module provides a factory pattern for creating appropriate scrapers
based on configuration and requirements.
"""

from typing import Optional, Dict, Any
import logging
from enum import Enum

from .base import BaseScraper
from .static import StaticScraper
from .dynamic import DynamicScraper, PlaywrightScraper
from .config import ScraperConfig, ScraperType


class ScraperEngine(Enum):
    """Available scraper engines"""
    BEAUTIFULSOUP = "beautifulsoup"
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"
    AUTO = "auto"


class ScraperFactory:
    """Factory class for creating appropriate scrapers"""
    
    _scraper_registry = {
        ScraperType.STATIC: StaticScraper,
        ScraperType.DYNAMIC: DynamicScraper,
        ScraperType.ADVANCED: DynamicScraper,  # Could be Playwright in future
    }
    
    @classmethod
    def create_scraper(cls, config: ScraperConfig, engine: Optional[ScraperEngine] = None) -> BaseScraper:
        """Create scraper based on configuration and engine preference"""
        
        # Determine scraper type
        scraper_type = cls._determine_scraper_type(config, engine)
        
        # Get scraper class
        scraper_class = cls._scraper_registry.get(scraper_type)
        if not scraper_class:
            raise ValueError(f"No scraper implementation found for type: {scraper_type}")
        
        # Create scraper instance
        try:
            scraper = scraper_class(config)
            logging.info(f"Created {scraper_type.value} scraper: {scraper}")
            return scraper
        except Exception as e:
            logging.error(f"Failed to create scraper: {str(e)}")
            raise
    
    @classmethod
    def _determine_scraper_type(cls, config: ScraperConfig, engine: Optional[ScraperEngine] = None) -> ScraperType:
        """Determine the appropriate scraper type"""
        
        # If engine is explicitly specified
        if engine:
            return cls._engine_to_type(engine)
        
        # Use configuration scraper type
        if config.scraper_type:
            return config.scraper_type
        
        # Auto-detect based on configuration
        return cls._auto_detect_type(config)
    
    @classmethod
    def _engine_to_type(cls, engine: ScraperEngine) -> ScraperType:
        """Convert engine enum to scraper type"""
        mapping = {
            ScraperEngine.BEAUTIFULSOUP: ScraperType.STATIC,
            ScraperEngine.SELENIUM: ScraperType.DYNAMIC,
            ScraperEngine.PLAYWRIGHT: ScraperType.ADVANCED,
            ScraperEngine.AUTO: ScraperType.STATIC  # Default for auto
        }
        return mapping.get(engine, ScraperType.STATIC)
    
    @classmethod
    def _auto_detect_type(cls, config: ScraperConfig) -> ScraperType:
        """Auto-detect scraper type based on configuration"""
        
        # Check for dynamic scraping indicators
        dynamic_indicators = [
            hasattr(config, 'browser_options') and config.browser_options,
            hasattr(config, 'wait_strategy') and config.wait_strategy != 'none',
            hasattr(config, 'scroll_behavior') and config.scroll_behavior != 'none',
            hasattr(config, 'javascript_required') and config.javascript_required
        ]
        
        # If any dynamic indicators are present, use dynamic scraper
        if any(dynamic_indicators):
            logging.info("Dynamic scraping requirements detected, using dynamic scraper")
            return ScraperType.DYNAMIC
        
        # Default to static scraper
        logging.info("Using static scraper for HTML content")
        return ScraperType.STATIC
    
    @classmethod
    def register_scraper(cls, scraper_type: ScraperType, scraper_class: type):
        """Register a custom scraper class"""
        if not issubclass(scraper_class, BaseScraper):
            raise ValueError("Scraper class must inherit from BaseScraper")
        
        cls._scraper_registry[scraper_type] = scraper_class
        logging.info(f"Registered custom scraper for type: {scraper_type}")
    
    @classmethod
    def get_available_scrapers(cls) -> Dict[str, str]:
        """Get list of available scraper types"""
        return {
            scraper_type.value: scraper_class.__name__
            for scraper_type, scraper_class in cls._scraper_registry.items()
        }
    
    @classmethod
    def validate_config(cls, config: ScraperConfig) -> bool:
        """Validate scraper configuration"""
        try:
            # Basic validation
            if not config.url:
                raise ValueError("URL is required")
            
            if not config.selectors:
                raise ValueError("At least one selector is required")
            
            # Type-specific validation
            scraper_type = cls._determine_scraper_type(config)
            
            if scraper_type == ScraperType.DYNAMIC:
                # Validate dynamic scraper requirements
                if hasattr(config, 'browser_options') and config.browser_options:
                    if isinstance(config.browser_options, list):
                        # Validate browser options
                        invalid_options = [opt for opt in config.browser_options if not isinstance(opt, str)]
                        if invalid_options:
                            raise ValueError(f"Invalid browser options: {invalid_options}")
            
            return True
            
        except Exception as e:
            logging.error(f"Configuration validation failed: {str(e)}")
            return False


class ScraperBuilder:
    """Builder pattern for complex scraper configuration"""
    
    def __init__(self):
        self._config = {}
        self._engine = None
    
    def url(self, url: str) -> 'ScraperBuilder':
        """Set target URL"""
        self._config['url'] = url
        return self
    
    def selectors(self, selectors: Dict[str, str]) -> 'ScraperBuilder':
        """Set CSS selectors"""
        self._config['selectors'] = selectors
        return self
    
    def delay(self, delay: float) -> 'ScraperBuilder':
        """Set delay between requests"""
        self._config['delay'] = delay
        return self
    
    def timeout(self, timeout: int) -> 'ScraperBuilder':
        """Set request timeout"""
        self._config['timeout'] = timeout
        return self
    
    def user_agent(self, user_agent: str) -> 'ScraperBuilder':
        """Set user agent"""
        self._config['user_agent'] = user_agent
        return self
    
    def headers(self, headers: Dict[str, str]) -> 'ScraperBuilder':
        """Set custom headers"""
        self._config['headers'] = headers
        return self
    
    def proxy(self, proxy: str) -> 'ScraperBuilder':
        """Set proxy"""
        self._config['proxy'] = proxy
        return self
    
    def engine(self, engine: ScraperEngine) -> 'ScraperBuilder':
        """Set scraper engine preference"""
        self._engine = engine
        return self
    
    def dynamic(self, wait_strategy: str = "networkidle", scroll_behavior: str = "none") -> 'ScraperBuilder':
        """Configure for dynamic scraping"""
        self._config['scraper_type'] = ScraperType.DYNAMIC
        self._config['wait_strategy'] = wait_strategy
        self._config['scroll_behavior'] = scroll_behavior
        return self
    
    def static(self) -> 'ScraperBuilder':
        """Configure for static scraping"""
        self._config['scraper_type'] = ScraperType.STATIC
        return self
    
    def pagination(self, next_selector: str, max_pages: int = 10) -> 'ScraperBuilder':
        """Configure pagination"""
        self._config['pagination'] = {
            'next_selector': next_selector,
            'max_pages': max_pages
        }
        return self
    
    def build(self) -> BaseScraper:
        """Build the scraper instance"""
        # Create configuration
        config = ScraperConfig(**self._config)
        
        # Validate configuration
        if not ScraperFactory.validate_config(config):
            raise ValueError("Invalid scraper configuration")
        
        # Create scraper
        return ScraperFactory.create_scraper(config, self._engine)


# Convenience functions for common use cases
def create_static_scraper(url: str, selectors: Dict[str, str], **kwargs) -> StaticScraper:
    """Create a static scraper with minimal configuration"""
    config = ScraperConfig(
        url=url,
        selectors=selectors,
        scraper_type=ScraperType.STATIC,
        **kwargs
    )
    return StaticScraper(config)


def create_dynamic_scraper(url: str, selectors: Dict[str, str], **kwargs) -> DynamicScraper:
    """Create a dynamic scraper with minimal configuration"""
    config = ScraperConfig(
        url=url,
        selectors=selectors,
        scraper_type=ScraperType.DYNAMIC,
        **kwargs
    )
    return DynamicScraper(config)


def create_scraper_from_dict(config_dict: Dict[str, Any]) -> BaseScraper:
    """Create scraper from dictionary configuration"""
    config = ScraperConfig.from_dict(config_dict)
    return ScraperFactory.create_scraper(config)


# Example usage patterns
def example_usage():
    """Example usage patterns for the scraper factory"""
    
    # Pattern 1: Simple static scraper
    scraper = create_static_scraper(
        url="https://example.com",
        selectors={"title": "h1", "content": ".content"},
        delay=1.0
    )
    
    # Pattern 2: Dynamic scraper with builder
    scraper = (ScraperBuilder()
               .url("https://dynamic-site.com")
               .selectors({"products": ".product", "prices": ".price"})
               .delay(2.0)
               .dynamic(wait_strategy="networkidle", scroll_behavior="down")
               .build())
    
    # Pattern 3: Factory with explicit engine
    config = ScraperConfig(
        url="https://example.com",
        selectors={"data": ".data-item"},
        scraper_type=ScraperType.STATIC
    )
    scraper = ScraperFactory.create_scraper(config, ScraperEngine.BEAUTIFULSOUP)
    
    # Pattern 4: From dictionary
    config_dict = {
        "url": "https://example.com",
        "selectors": {"title": "h1"},
        "scraper_type": "static",
        "delay": 1.0
    }
    scraper = create_scraper_from_dict(config_dict)


if __name__ == "__main__":
    # Test the factory
    logging.basicConfig(level=logging.INFO)
    
    print("Available scrapers:", ScraperFactory.get_available_scrapers())
    
    # Test builder pattern
    scraper = (ScraperBuilder()
               .url("https://example.com")
               .selectors({"title": "h1"})
               .delay(1.0)
               .static()
               .build())
    
    print(f"Created scraper: {scraper}")
    print(f"Scraper statistics: {scraper.get_statistics()}")
