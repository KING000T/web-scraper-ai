"""
Web Scraping Engine

This module provides the core scraping functionality for extracting data
from websites, including both static and dynamic content handling.
"""

from .base import BaseScraper, ScrapedPage, ScrapingError
from .static import StaticScraper
from .dynamic import DynamicScraper
from .factory import ScraperFactory
from .config import ScraperConfig

__version__ = "1.0.0"
__all__ = [
    "BaseScraper",
    "ScrapedPage", 
    "ScrapingError",
    "StaticScraper",
    "DynamicScraper",
    "ScraperFactory",
    "ScraperConfig"
]
