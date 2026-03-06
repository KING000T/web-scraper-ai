"""
Base Exporter Module

This module defines the abstract base class for all data exporters
and common data structures used throughout the export system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import os


class ExportError(Exception):
    """Base exception for export errors"""
    pass


class FileNotFoundError(ExportError):
    """File-related export errors"""
    pass


class FormatError(ExportError):
    """Data format-related export errors"""
    pass


class PermissionError(ExportError):
    """Permission-related export errors"""
    pass


@dataclass
class ExportConfig:
    """Configuration for data export"""
    
    format: str = "csv"
    filename: Optional[str] = None
    directory: str = "exports"
    include_headers: bool = True
    encoding: str = "utf-8"
    delimiter: str = ","
    date_format: str = "%Y-%m-%d"
    float_format: str = "%.2f"
    null_value: str = ""
    overwrite: bool = True
    compress: bool = False
    
    def __post_init__(self):
        """Validate export configuration"""
        if self.format not in ['csv', 'json', 'xlsx', 'google_sheets']:
            raise ValueError(f"Unsupported export format: {self.format}")
        
        if self.encoding not in ['utf-8', 'utf-16', 'ascii', 'latin-1']:
            raise ValueError(f"Unsupported encoding: {self.encoding}")
    
    def get_full_path(self) -> str:
        """Get full file path for export"""
        if not self.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.filename = f"export_{timestamp}"
        
        # Add extension if not present
        if not self.filename.endswith(self._get_extension()):
            self.filename += self._get_extension()
        
        return os.path.join(self.directory, self.filename)
    
    def _get_extension(self) -> str:
        """Get file extension for format"""
        extensions = {
            'csv': '.csv',
            'json': '.json',
            'xlsx': '.xlsx',
            'google_sheets': '.csv'  # Google Sheets exports as CSV
        }
        return extensions.get(self.format, '.csv')


@dataclass
class ExportResult:
    """Result of data export operation"""
    
    success: bool
    file_path: Optional[str] = None
    record_count: int = 0
    file_size: int = 0
    export_time: float = 0.0
    exporter_name: str = ""
    format: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB"""
        return self.file_size / (1024 * 1024)
    
    @property
    def records_per_second(self) -> float:
        """Get export speed in records per second"""
        return self.record_count / self.export_time if self.export_time > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'success': self.success,
            'file_path': self.file_path,
            'record_count': self.record_count,
            'file_size': self.file_size,
            'file_size_mb': self.file_size_mb,
            'export_time': self.export_time,
            'records_per_second': self.records_per_second,
            'exporter_name': self.exporter_name,
            'format': self.format,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'error_message': self.error_message
        }


@dataclass
class ExportStats:
    """Statistics for export operations"""
    
    total_exports: int = 0
    successful_exports: int = 0
    failed_exports: int = 0
    total_records_exported: int = 0
    total_file_size: int = 0
    total_export_time: float = 0.0
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage"""
        if self.total_exports == 0:
            return 0.0
        return (self.successful_exports / self.total_exports) * 100
    
    @property
    def average_export_time(self) -> float:
        """Get average export time"""
        if self.successful_exports == 0:
            return 0.0
        return self.total_export_time / self.successful_exports
    
    @property
    def average_records_per_export(self) -> float:
        """Get average records per export"""
        if self.successful_exports == 0:
            return 0.0
        return self.total_records_exported / self.successful_exports
    
    @property
    def total_file_size_mb(self) -> float:
        """Get total file size in MB"""
        return self.total_file_size / (1024 * 1024)
    
    def update(self, result: ExportResult):
        """Update stats with export result"""
        self.total_exports += 1
        
        if result.success:
            self.successful_exports += 1
            self.total_records_exported += result.record_count
            self.total_file_size += result.file_size
        else:
            self.failed_exports += 1
        
        self.total_export_time += result.export_time
        self.end_time = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'total_exports': self.total_exports,
            'successful_exports': self.successful_exports,
            'failed_exports': self.failed_exports,
            'success_rate': self.success_rate,
            'total_records_exported': self.total_records_exported,
            'total_file_size': self.total_file_size,
            'total_file_size_mb': self.total_file_size_mb,
            'total_export_time': self.total_export_time,
            'average_export_time': self.average_export_time,
            'average_records_per_export': self.average_records_per_export,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None
        }


class BaseExporter(ABC):
    """Abstract base class for all data exporters"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """Initialize exporter with configuration"""
        self.config = config or ExportConfig()
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stats = ExportStats()
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for this exporter instance"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.__class__.__name__} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    @abstractmethod
    async def export(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None) -> ExportResult:
        """Export data to specified format - must be implemented by subclasses"""
        pass
    
    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate input data"""
        if not isinstance(data, list):
            raise FormatError("Input data must be a list")
        
        if not data:
            self.logger.warning("Empty data provided for export")
            return True
        
        if not all(isinstance(record, dict) for record in data):
            raise FormatError("All records must be dictionaries")
        
        return True
    
    def prepare_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare data for export (flatten, normalize, etc.)"""
        if not data:
            return []
        
        prepared_data = []
        
        for record in data:
            # Deep copy record to avoid modifying original
            import copy
            prepared_record = copy.deepcopy(record)
            
            # Handle nested objects
            flattened = self._flatten_dict(prepared_record)
            
            # Normalize values
            normalized = self._normalize_values(flattened)
            
            prepared_data.append(normalized)
        
        return prepared_data
    
    def _flatten_dict(self, data: Dict[str, Any], separator: str = "_") -> Dict[str, Any]:
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
    
    def _normalize_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize values for export"""
        normalized = {}
        
        for key, value in data.items():
            if value is None:
                normalized[key] = self.config.null_value
            elif isinstance(value, datetime):
                normalized[key] = value.strftime(self.config.date_format)
            elif isinstance(value, (int, float)):
                if isinstance(value, float):
                    normalized[key] = value if not value.isnan() else self.config.null_value
                else:
                    normalized[key] = value
            elif isinstance(value, (list, tuple)):
                # Convert list/tuple to string
                normalized[key] = '; '.join(str(v) for v in value if v is not None)
            elif isinstance(value, dict):
                # Convert dict to JSON string
                import json
                normalized[key] = json.dumps(value, ensure_ascii=False)
            else:
                normalized[key] = str(value) if value is not None else self.config.null_value
        
        return normalized
    
    def ensure_directory(self, directory: str) -> bool:
        """Ensure export directory exists"""
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except OSError as e:
            self.logger.error(f"Failed to create directory {directory}: {str(e)}")
            return False
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    def export_with_stats(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None) -> ExportResult:
        """Export data with statistics tracking"""
        start_time = datetime.utcnow()
        
        try:
            # Use provided config or default
            export_config = config or self.config
            
            # Validate data
            self.validate_data(data)
            
            # Ensure directory exists
            if not self.ensure_directory(export_config.directory):
                return ExportResult(
                    success=False,
                    exporter_name=self.name,
                    format=export_config.format,
                    error_message="Failed to create export directory"
                )
            
            # Export data
            self.logger.info(f"Starting export of {len(data)} records to {export_config.format}")
            
            result = asyncio.run(self.export(data, export_config))
            
            # Update stats
            self.stats.update(result)
            
            self.logger.info(
                f"Export completed: {result.record_count} records, "
                f"file size: {result.file_size_mb:.2f}MB, "
                f"time: {result.export_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            export_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Error exporting data: {str(e)}"
            self.logger.error(error_msg)
            
            return ExportResult(
                success=False,
                exporter_name=self.name,
                format=self.config.format,
                export_time=export_time,
                error_message=error_msg
            )
    
    def get_stats(self) -> ExportStats:
        """Get current export statistics"""
        return self.stats
    
    def reset_stats(self):
        """Reset export statistics"""
        self.stats = ExportStats()
    
    def __str__(self) -> str:
        """String representation of exporter"""
        return f"{self.__class__.__name__}(format={self.config.format})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (
            f"{self.__class__.__name__}("
            f"format={self.config.format}, "
            f"exports={self.stats.total_exports}, "
            f"success_rate={self.stats.success_rate:.1f}%)"
        )


class ExportUtils:
    """Utility functions for data export"""
    
    @staticmethod
    def generate_filename(prefix: str, format: str, timestamp: Optional[datetime] = None) -> str:
        """Generate filename with timestamp"""
        if not timestamp:
            timestamp = datetime.now()
        
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        extension = format.lower().replace('google_sheets', 'csv')
        
        return f"{prefix}_{timestamp_str}.{extension}"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for file system compatibility"""
        import re
        
        # Remove invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = "export"
        
        return sanitized
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}"
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Validate filename for file system compatibility"""
        if not filename:
            return False
        
        # Check for invalid characters (Windows)
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        if any(char in filename for char in invalid_chars):
            return False
        
        # Check for reserved names (Windows)
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in reserved_names:
            return False
        
        # Check length (Windows limit is 260 characters)
        if len(filename) > 255:
            return False
        
        return True
    
    @staticmethod
    def compress_file(file_path: str) -> str:
        """Compress file using gzip"""
        import gzip
        
        compressed_path = f"{file_path}.gz"
        
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            return compressed_path
            
        except Exception as e:
            raise ExportError(f"Failed to compress file {file_path}: {str(e)}")
    
    @staticmethod
    def get_mime_type(format: str) -> str:
        """Get MIME type for export format"""
        mime_types = {
            'csv': 'text/csv',
            'json': 'application/json',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'google_sheets': 'text/csv'
        }
        
        return mime_types.get(format.lower(), 'application/octet-stream')
