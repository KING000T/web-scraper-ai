"""
Exporter Factory Module

This module provides a factory pattern for creating appropriate exporters
based on format requirements and configuration.
"""

from typing import Optional, Dict, Any, List
import logging

from .base import BaseExporter, ExportError
from .csv_exporter import CSVExporter, AdvancedCSVExporter
from .json_exporter import JSONExporter, JSONLinesExporter, StreamingJSONExporter
from .excel_exporter import ExcelExporter, MultiSheetExcelExporter
from .google_sheets_exporter import GoogleSheetsExporter


class ExporterFactory:
    """Factory class for creating appropriate exporters"""
    
    _exporter_registry = {
        'csv': CSVExporter,
        'json': JSONExporter,
        'jsonlines': JSONLinesExporter,
        'json_streaming': StreamingJSONExporter,
        'xlsx': ExcelExporter,
        'excel': ExcelExporter,
        'google_sheets': GoogleSheetsExporter,
        'advanced_csv': AdvancedCSVExporter,
        'multi_sheet_excel': MultiSheetExcelExporter
    }
    
    @classmethod
    def create_exporter(cls, format: str, config: Optional[Dict[str, Any]] = None) -> BaseExporter:
        """Create exporter based on format"""
        format = format.lower()
        
        if format not in cls._exporter_registry:
            available_formats = list(cls._exporter_registry.keys())
            raise ExportError(f"Unsupported export format: {format}. Available formats: {available_formats}")
        
        exporter_class = cls._exporter_registry[format]
        
        # Create configuration
        if config:
            from .base import ExportConfig
            export_config = ExportConfig(format=format, **config)
        else:
            from .base import ExportConfig
            export_config = ExportConfig(format=format)
        
        try:
            return exporter_class(export_config)
        except Exception as e:
            raise ExportError(f"Failed to create {format} exporter: {str(e)}")
    
    @classmethod
    def create_csv_exporter(cls, **kwargs) -> CSVExporter:
        """Create CSV exporter with custom configuration"""
        config = {'format': 'csv', **kwargs}
        from .base import ExportConfig
        return CSVExporter(ExportConfig(**config))
    
    @classmethod
    def create_json_exporter(cls, **kwargs) -> JSONExporter:
        """Create JSON exporter with custom configuration"""
        config = {'format': 'json', **kwargs}
        from .base import ExportConfig
        return JSONExporter(ExportConfig(**config))
    
    @classmethod
    def create_excel_exporter(cls, **kwargs) -> ExcelExporter:
        """Create Excel exporter with custom configuration"""
        config = {'format': 'xlsx', **kwargs}
        from .base import ExportConfig
        return ExcelExporter(ExportConfig(**config))
    
    @classmethod
    def create_google_sheets_exporter(cls, **kwargs) -> GoogleSheetsExporter:
        """Create Google Sheets exporter with custom configuration"""
        config = {'format': 'google_sheets', **kwargs}
        from .base import ExportConfig
        return GoogleSheetsExporter(ExportConfig(**config))
    
    @classmethod
    def create_advanced_csv_exporter(cls, **kwargs) -> AdvancedCSVExporter:
        """Create advanced CSV exporter with custom configuration"""
        config = {'format': 'csv', **kwargs}
        from .base import ExportConfig
        return AdvancedCSVExporter(ExportConfig(**config))
    
    @classmethod
    def create_jsonlines_exporter(cls, **kwargs) -> JSONLinesExporter:
        """Create JSON Lines exporter with custom configuration"""
        config = {'format': 'jsonlines', **kwargs}
        from .base import ExportConfig
        return JSONLinesExporter(ExportConfig(**config))
    
    @classmethod
    def create_streaming_json_exporter(cls, **kwargs) -> StreamingJSONExporter:
        """Create streaming JSON exporter with custom configuration"""
        config = {'format': 'json', **kwargs}
        from .base import ExportConfig
        return StreamingJSONExporter(ExportConfig(**config))
    
    @classmethod
    def create_multi_sheet_excel_exporter(cls, **kwargs) -> MultiSheetExcelExporter:
        """Create multi-sheet Excel exporter with custom configuration"""
        config = {'format': 'xlsx', **kwargs}
        from .base import ExportConfig
        return MultiSheetExcelExporter(ExportConfig(**config))
    
    @classmethod
    def get_available_formats(cls) -> List[str]:
        """Get list of available export formats"""
        return list(cls._exporter_registry.keys())
    
    @classmethod
    def register_exporter(cls, format: str, exporter_class: type):
        """Register a custom exporter class"""
        if not issubclass(exporter_class, BaseExporter):
            raise ValueError("Exporter class must inherit from BaseExporter")
        
        cls._exporter_registry[format.lower()] = exporter_class
        logging.info(f"Registered custom exporter for format: {format}")
    
    @classmethod
    def auto_detect_format(cls, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Auto-detect best export format based on data characteristics"""
        if filename:
            # Try to detect format from filename extension
            extension = filename.lower().split('.')[-1]
            if extension in ['csv', 'json', 'xlsx', 'xls']:
                return extension
            if extension == 'jsonl':
                return 'jsonlines'
        
        # Analyze data characteristics
        if not data:
            return 'json'  # Default to JSON for empty data
        
        # Check for nested objects
        has_nested = any(
            isinstance(value, (dict, list)) 
            for record in data 
            for value in record.values()
        )
        
        # Check for numeric data
        has_numeric = any(
            isinstance(value, (int, float)) 
            for record in data 
            for value in record.values()
            if value is not None
        )
        
        # Check for datetime objects
        has_datetime = any(
            isinstance(value, (datetime, date)) 
            for record in data 
            for value in record.values()
        )
        
        # Decision logic
        if has_nested and len(data) > 100:
            return 'json'  # JSON for complex nested data
        elif has_numeric and has_datetime:
            return 'xlsx'  # Excel for mixed data types
        elif has_numeric:
            return 'csv'   # CSV for simple tabular data
        elif has_nested:
            return 'json'   # JSON for nested data
        else:
            return 'csv'   # Default to CSV for simple data
    
    @classmethod
    def create_optimal_exporter(cls, data: List[Dict[str, Any]], filename: Optional[str] = None) -> BaseExporter:
        """Create the optimal exporter based on data characteristics"""
        detected_format = cls.auto_detect_format(data, filename)
        logging.info(f"Auto-detected optimal format: {detected_format}")
        return cls.create_exporter(detected_format)
    
    @classmethod
    def export_to_best_format(cls, data: List[Dict[str, Any]], filename: str, **kwargs) -> ExportResult:
        """Export data to the best format automatically detected"""
        exporter = cls.create_optimal_exporter(data, filename)
        return exporter.export_with_stats(data)


class ExporterBuilder:
    """Builder pattern for creating complex export configurations"""
    
    def __init__(self):
        self.format = 'csv'
        self.config = {}
        self.custom_formatters = []
        self.custom_transformers = []
        self.filters = []
    
    def format(self, format: str) -> 'ExporterBuilder':
        """Set export format"""
        self.format = format.lower()
        return self
    
    def filename(self, filename: str) -> 'ExporterBuilder':
        """Set export filename"""
        self.config['filename'] = filename
        return self
    
    def directory(self, directory: str) -> 'ExporterBuilder':
        """Set export directory"""
        self.config['directory'] = directory
        return self
    
    def encoding(self, encoding: str) -> 'ExporterBuilder':
        """Set file encoding"""
        self.config['encoding'] = encoding
        return self
    
    def include_headers(self, include: bool = True) -> 'ExporterBuilder':
        """Set whether to include headers"""
        self.config['include_headers'] = include
        return self
    
    def delimiter(self, delimiter: str) -> 'ExporterBuilder':
        """Set CSV delimiter"""
        self.config['delimiter'] = delimiter
        return self
    
    def pretty_print(self, pretty: bool = True) -> 'ExporterBuilder':
        """Set JSON pretty printing"""
        self.config['pretty_print'] = pretty
        return self
    
    def add_custom_formatter(self, column: str, formatter: callable) -> 'ExporterBuilder':
        """Add custom formatter for CSV export"""
        self.custom_formatters.append((column, formatter))
        return self
    
    def add_data_filter(self, filter_func: callable) -> 'ExporterBuilder':
        """Add data filter function"""
        self.filters.append(filter_func)
        return self
    
    def build(self) -> BaseExporter:
        """Build the exporter with current configuration"""
        # Create base exporter
        exporter = ExporterFactory.create_exporter(self.format, self.config)
        
        # Apply custom features for specific exporters
        if isinstance(exporter, AdvancedCSVExporter) and self.custom_formatters:
            for column, formatter in self.custom_formatters:
                exporter.add_column_formatter(column, formatter)
        
        if isinstance(exporter, MultiSheetExcelExporter) and self.filters:
            # For multi-sheet, we'd need to implement filter support
            pass  # Would need to extend MultiSheetExcelExporter
        
        return exporter


# Convenience functions for common export patterns
def export_auto(data: List[Dict[str, Any]], filename: str, **kwargs) -> ExportResult:
    """Auto-detect and export to optimal format"""
    return ExporterFactory.export_to_best_format(data, filename, **kwargs)


def export_by_format(data: List[Dict[str, Any]], format: str, filename: str, **kwargs) -> ExportResult:
    """Export data to specified format"""
    exporter = ExporterFactory.create_exporter(format)
    config = ExportConfig(filename=filename, format=format, **kwargs)
    return exporter.export_with_stats(data, config)


# Example usage patterns
def example_usage():
    """Example usage patterns for exporter factory"""
    
    # Pattern 1: Simple format-specific export
    data = [
        {'name': 'John', 'age': 30, 'city': 'New York'},
        {'name': 'Jane', 'age': 25, 'city': 'Los Angeles'}
    ]
    
    csv_result = export_by_format(data, 'csv', 'people.csv')
    json_result = export_by_format(data, 'json', 'people.json')
    excel_result = export_by_format(data, 'xlsx', 'people.xlsx')
    
    # Pattern 2: Builder pattern with custom configuration
    exporter = (ExporterBuilder()
                .format('csv')
                .filename('people_custom.csv')
                .delimiter(';')
                .encoding('utf-8')
                .include_headers(True)
                .add_custom_formatter('name', lambda x: x.upper())
                .build())
    
    builder_result = exporter.export_with_stats(data)
    
    # Pattern 3: Auto-detection
    auto_result = export_auto(data, 'auto_export')
    
    # Pattern 4: Advanced CSV with custom features
    advanced_exporter = ExporterFactory.create_advanced_csv_exporter(
        delimiter='|',
        encoding='utf-8'
    )
    advanced_exporter.add_column_formatter('name', lambda x: x.title())
    advanced_exporter.add_data_filter(lambda record: record.get('age', 0) >= 18)
    
    advanced_result = advanced_exporter.export_with_stats(data)
    
    print(f"CSV Export Result: {csv_result.to_dict()}")
    print(f"JSON Export Result: {json_result.to_dict()}")
    print(f"Excel Export Result: {excel_result.to_dict()}")
    print(f"Builder Export Result: {builder_result.to_dict()}")
    print(f"Auto Export Result: {auto_result.to_dict()}")
    print(f"Advanced CSV Export Result: {advanced_result.to_dict()}")


if __name__ == "__main__":
    # Test exporter factory
    logging.basicConfig(level=logging.INFO)
    
    # Create test data
    test_data = [
        {'name': 'John Doe', 'email': 'john@example.com', 'age': 30, 'salary': 50000.50, 'department': 'Engineering'},
        {'name': 'Jane Smith', 'email': 'jane@example.com', 'age': 25, 'salary': 60000.00, 'department': 'Marketing'},
        {'name': 'Bob Johnson', 'email': 'bob@example.com', 'age': 35, 'salary': 75000.75, 'department': 'Engineering'}
    ]
    
    # Test different export patterns
    example_usage()
    
    # Show available formats
    print(f"Available export formats: {ExporterFactory.get_available_formats()}")
