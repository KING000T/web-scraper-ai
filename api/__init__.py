"""
REST API Module

This module provides REST API endpoints for the Web Scraping and Data
Extraction Automation System using FastAPI.
"""

from .main import app
from .routes import jobs, scrapers, exports, monitoring
from .models import *
from .dependencies import *

__all__ = [
    "app",
    "jobs",
    "scrapers", 
    "exports",
    "monitoring"
]
