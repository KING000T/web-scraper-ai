"""
Data Processing Pipeline

This module provides data processing, cleaning, validation, and transformation
functionality for scraped data.
"""

from .base import BaseProcessor, ProcessingError, ValidationResult
from .cleaner import DataCleaner
from .validator import DataValidator, ValidationRule
from .transformer import DataTransformer, Transformation
from .pipeline import DataProcessingPipeline
from .quality import DataQualityChecker, QualityScore

__version__ = "1.0.0"
__all__ = [
    "BaseProcessor",
    "ProcessingError", 
    "ValidationResult",
    "DataCleaner",
    "DataValidator",
    "ValidationRule",
    "DataTransformer",
    "Transformation",
    "DataProcessingPipeline",
    "DataQualityChecker",
    "QualityScore"
]
