"""
API Routes Module

This module contains all API route definitions for the Web Scraper AI API.
"""

from . import jobs
from . import scrapers
from . import exports
from . import monitoring

__all__ = ["jobs", "scrapers", "exports", "monitoring"]
