"""
Base Processor Module

This module defines the abstract base class for all data processors
and common data structures used throughout the processing pipeline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging


class ProcessingError(Exception):
    """Base exception for data processing errors"""
    pass


class ValidationError(ProcessingError):
    """Data validation errors"""
    pass


class TransformationError(ProcessingError):
    """Data transformation errors"""
    pass


class QualityError(ProcessingError):
    """Data quality assessment errors"""
    pass


@dataclass
class ValidationResult:
    """Result of data validation"""
    
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    field_results: Dict[str, bool] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def error_count(self) -> int:
        """Get number of errors"""
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        """Get number of warnings"""
        return len(self.warnings)
    
    @property
    def valid_fields(self) -> List[str]:
        """Get list of valid fields"""
        return [field for field, is_valid in self.field_results.items() if is_valid]
    
    @property
    def invalid_fields(self) -> List[str]:
        """Get list of invalid fields"""
        return [field for field, is_valid in self.field_results.items() if not is_valid]
    
    def add_error(self, field: str, message: str):
        """Add an error for a specific field"""
        self.errors.append(f"{field}: {message}")
        self.field_results[field] = False
        self.is_valid = False
    
    def add_warning(self, field: str, message: str):
        """Add a warning for a specific field"""
        self.warnings.append(f"{field}: {message}")
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.field_results.update(other.field_results)
        self.is_valid = self.is_valid and other.is_valid
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'field_results': self.field_results,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'valid_fields': self.valid_fields,
            'invalid_fields': self.invalid_fields,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ProcessingResult:
    """Result of data processing"""
    
    data: List[Dict[str, Any]]
    original_data: List[Dict[str, Any]]
    processing_time: float
    processor_name: str
    validation_result: Optional[ValidationResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def record_count(self) -> int:
        """Get number of processed records"""
        return len(self.data)
    
    @property
    def is_valid(self) -> bool:
        """Check if all data is valid"""
        return self.validation_result.is_valid if self.validation_result else True
    
    @property
    def has_data(self) -> bool:
        """Check if there is any data"""
        return len(self.data) > 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary"""
        return {
            'processor_name': self.processor_name,
            'record_count': self.record_count,
            'processing_time': self.processing_time,
            'records_per_second': self.record_count / self.processing_time if self.processing_time > 0 else 0,
            'is_valid': self.is_valid,
            'validation_errors': self.validation_result.error_count if self.validation_result else 0,
            'validation_warnings': self.validation_result.warning_count if self.validation_result else 0,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ProcessingStats:
    """Statistics for processing operations"""
    
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    validation_errors: int = 0
    transformation_errors: int = 0
    processing_time: float = 0.0
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage"""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100
    
    @property
    def error_rate(self) -> float:
        """Get error rate as percentage"""
        if self.total_records == 0:
            return 0.0
        return (self.failed_records / self.total_records) * 100
    
    @property
    def records_per_second(self) -> float:
        """Get processing speed"""
        duration = self.duration
        return self.processed_records / duration if duration > 0 else 0.0
    
    @property
    def duration(self) -> float:
        """Get total processing duration"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return self.processing_time
    
    def update(self, result: ProcessingResult):
        """Update stats with processing result"""
        self.total_records += len(result.original_data)
        self.processed_records += len(result.data)
        self.processing_time += result.processing_time
        
        if result.validation_result:
            self.validation_errors += result.validation_result.error_count
        
        self.end_time = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'total_records': self.total_records,
            'processed_records': self.processed_records,
            'failed_records': self.failed_records,
            'validation_errors': self.validation_errors,
            'transformation_errors': self.transformation_errors,
            'processing_time': self.processing_time,
            'duration': self.duration,
            'success_rate': self.success_rate,
            'error_rate': self.error_rate,
            'records_per_second': self.records_per_second,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None
        }


class BaseProcessor(ABC):
    """Abstract base class for all data processors"""
    
    def __init__(self, name: Optional[str] = None):
        """Initialize processor with optional name"""
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stats = ProcessingStats()
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for this processor instance"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.__class__.__name__} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    @abstractmethod
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process data - must be implemented by subclasses"""
        pass
    
    def validate_input(self, data: List[Dict[str, Any]]) -> bool:
        """Validate input data"""
        if not isinstance(data, list):
            raise ValidationError("Input data must be a list")
        
        if not data:
            self.logger.warning("Empty input data provided")
            return True
        
        if not all(isinstance(record, dict) for record in data):
            raise ValidationError("All records must be dictionaries")
        
        return True
    
    def process_with_stats(self, data: List[Dict[str, Any]]) -> ProcessingResult:
        """Process data with statistics tracking"""
        start_time = datetime.utcnow()
        original_data = data.copy()
        
        try:
            # Validate input
            self.validate_input(data)
            
            # Process data
            self.logger.info(f"Starting to process {len(data)} records with {self.name}")
            processed_data = asyncio.run(self.process(data))
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create result
            result = ProcessingResult(
                data=processed_data,
                original_data=original_data,
                processing_time=processing_time,
                processor_name=self.name
            )
            
            # Update stats
            self.stats.update(result)
            
            self.logger.info(
                f"Processed {len(processed_data)} records in {processing_time:.2f}s "
                f"({self.stats.records_per_second:.1f} records/sec)"
            )
            
            return result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Error processing data with {self.name}: {str(e)}"
            self.logger.error(error_msg)
            
            # Return error result
            return ProcessingResult(
                data=[],
                original_data=original_data,
                processing_time=processing_time,
                processor_name=self.name,
                metadata={'error': error_msg}
            )
    
    def get_stats(self) -> ProcessingStats:
        """Get current processing statistics"""
        return self.stats
    
    def reset_stats(self):
        """Reset processing statistics"""
        self.stats = ProcessingStats()
    
    def __str__(self) -> str:
        """String representation of processor"""
        return f"{self.__class__.__name__}(name={self.name})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, "
            f"processed_records={self.stats.processed_records}, "
            f"success_rate={self.stats.success_rate:.1f}%)"
        )


class ProcessorUtils:
    """Utility functions for data processing"""
    
    @staticmethod
    def deep_copy_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of a dictionary"""
        import copy
        return copy.deepcopy(data)
    
    @staticmethod
    def flatten_dict(data: Dict[str, Any], separator: str = "_") -> Dict[str, Any]:
        """Flatten nested dictionary"""
        def _flatten(obj, parent_key=''):
            items = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{parent_key}{separator}{key}" if parent_key else key
                    items.extend(_flatten(value, new_key).items())
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    new_key = f"{parent_key}{separator}{i}" if parent_key else str(i)
                    items.extend(_flatten(value, new_key).items())
            else:
                items.append((parent_key, obj))
            
            return dict(items)
        
        return _flatten(data)
    
    @staticmethod
    def unflatten_dict(data: Dict[str, Any], separator: str = "_") -> Dict[str, Any]:
        """Unflatten dictionary"""
        result = {}
        
        for key, value in data.items():
            keys = key.split(separator)
            current = result
            
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = value
        
        return result
    
    @staticmethod
    def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two dictionaries recursively"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ProcessorUtils.merge_dicts(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def sanitize_field_name(field_name: str) -> str:
        """Sanitize field name for database/storage compatibility"""
        import re
        
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', field_name)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure it starts with a letter or underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = f"field_{sanitized}"
        
        # Convert to lowercase
        sanitized = sanitized.lower()
        
        return sanitized or "unknown_field"
    
    @staticmethod
    def detect_data_type(value: Any) -> str:
        """Detect data type of a value"""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            # Check for specific string types
            if value.lower() in ('true', 'false'):
                return "boolean"
            elif value.isdigit():
                return "integer"
            elif ProcessorUtils._is_float_string(value):
                return "float"
            elif ProcessorUtils._is_email(value):
                return "email"
            elif ProcessorUtils._is_url(value):
                return "url"
            elif ProcessorUtils._is_date_string(value):
                return "date"
            else:
                return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"
    
    @staticmethod
    def _is_float_string(value: str) -> bool:
        """Check if string represents a float"""
        try:
            float(value)
            return '.' in value
        except ValueError:
            return False
    
    @staticmethod
    def _is_email(value: str) -> bool:
        """Check if string is an email address"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def _is_url(value: str) -> bool:
        """Check if string is a URL"""
        import re
        pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def _is_date_string(value: str) -> bool:
        """Check if string is a date"""
        from datetime import datetime
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S'
        ]
        
        for fmt in date_formats:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue
        
        return False
