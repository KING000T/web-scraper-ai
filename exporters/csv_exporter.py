"""
CSV Exporter Module

This module implements CSV export functionality with support for
custom delimiters, encoding, and data formatting options.
"""

import asyncio
import csv
import os
from typing import Dict, List, Optional, Any
import logging

from .base import BaseExporter, ExportConfig, ExportResult, ExportError


class CSVExporter(BaseExporter):
    """CSV exporter with comprehensive formatting options"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """Initialize CSV exporter with configuration"""
        super().__init__(config)
        self.delimiter = self.config.delimiter
        self.quoting = csv.QUOTE_MINIMAL
        self.escape_char = '\\'
        self.lineterminator = '\n'
    
    async def export(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None) -> ExportResult:
        """Export data to CSV format"""
        export_config = config or self.config
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Prepare data
            prepared_data = self.prepare_data(data)
            
            if not prepared_data:
                return ExportResult(
                    success=True,
                    exporter_name=self.name,
                    format=export_config.format,
                    record_count=0,
                    export_time=0.0
                )
            
            # Get file path
            file_path = export_config.get_full_path()
            
            # Write CSV file
            await self._write_csv_file(file_path, prepared_data, export_config)
            
            # Get file size
            file_size = self.get_file_size(file_path)
            
            # Calculate export time
            export_time = asyncio.get_event_loop().time() - start_time
            
            return ExportResult(
                success=True,
                file_path=file_path,
                record_count=len(prepared_data),
                file_size=file_size,
                export_time=export_time,
                exporter_name=self.name,
                format=export_config.format,
                metadata={
                    'delimiter': export_config.delimiter,
                    'encoding': export_config.encoding,
                    'include_headers': export_config.include_headers
                }
            )
            
        except Exception as e:
            export_time = asyncio.get_event_loop().time() - start_time
            return ExportResult(
                success=False,
                exporter_name=self.name,
                format=export_config.format,
                export_time=export_time,
                error_message=str(e)
            )
    
    async def _write_csv_file(self, file_path: str, data: List[Dict[str, Any]], config: ExportConfig):
        """Write data to CSV file"""
        try:
            with open(file_path, 'w', newline='', encoding=config.encoding) as csvfile:
                # Get field names
                if data:
                    fieldnames = list(data[0].keys())
                else:
                    fieldnames = []
                
                # Create CSV writer
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=fieldnames,
                    delimiter=self.delimiter,
                    quotechar='"',
                    quoting=self.quoting,
                    escapechar=self.escape_char,
                    lineterminator=self.lineterminator
                )
                
                # Write headers
                if config.include_headers and fieldnames:
                    writer.writeheader(fieldnames)
                
                # Write data rows
                for row in data:
                    writer.writerow(row)
                    
        except IOError as e:
            raise ExportError(f"Failed to write CSV file {file_path}: {str(e)}")
        except csv.Error as e:
            raise ExportError(f"CSV formatting error: {str(e)}")
    
    def export_to_string(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None) -> str:
        """Export data to CSV string"""
        import io
        
        export_config = config or self.config
        prepared_data = self.prepare_data(data)
        
        if not prepared_data:
            return ""
        
        # Create string buffer
        output = io.StringIO()
        
        try:
            # Get field names
            fieldnames = list(prepared_data[0].keys())
            
            # Create CSV writer
            writer = csv.DictWriter(
                output,
                fieldnames=fieldnames,
                delimiter=self.delimiter,
                quotechar='"',
                quoting=self.quoting,
                escapechar=self.escape_char,
                lineterminator=self.lineterminator
            )
            
            # Write headers
            if export_config.include_headers and fieldnames:
                writer.writeheader(fieldnames)
            
            # Write data rows
            for row in prepared_data:
                writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            raise ExportError(f"Failed to generate CSV string: {str(e)}")
        finally:
            output.close()
    
    def export_streaming(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None):
        """Export data as a generator (for large datasets)"""
        export_config = config or self.config
        prepared_data = self.prepare_data(data)
        
        if not prepared_data:
            return
        
        # Get field names
        fieldnames = list(prepared_data[0].keys())
        
        # Create string buffer for headers
        import io
        output = io.StringIO()
        
        try:
            # Create CSV writer
            writer = csv.DictWriter(
                output,
                fieldnames=fieldnames,
                delimiter=self.delimiter,
                quotechar='"',
                quoting=self.quoting,
                escapechar=self.escape_char,
                lineterminator=self.lineterminator
            )
            
            # Write headers
            if export_config.include_headers and fieldnames:
                writer.writeheader(fieldnames)
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
            
            # Write data rows one by one
            for row in prepared_data:
                writer.writerow(row)
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
                
        except Exception as e:
            raise ExportError(f"Streaming CSV export failed: {str(e)}")
        finally:
            output.close()
    
    def set_delimiter(self, delimiter: str):
        """Set CSV delimiter"""
        if len(delimiter) != 1:
            raise ValueError("Delimiter must be a single character")
        
        self.delimiter = delimiter
        self.config.delimiter = delimiter
    
    def set_quoting(self, quoting: int):
        """Set CSV quoting style"""
        valid_quoting = [csv.QUOTE_ALL, csv.QUOTE_MINIMAL, csv.QUOTE_NONNUMERIC, csv.QUOTE_NONE]
        
        if quoting not in valid_quoting:
            raise ValueError(f"Invalid quoting style: {quoting}")
        
        self.quoting = quoting
    
    def set_escape_char(self, escape_char: str):
        """Set CSV escape character"""
        if len(escape_char) != 1:
            raise ValueError("Escape character must be a single character")
        
        self.escape_char = escape_char


class AdvancedCSVExporter(CSVExporter):
    """Advanced CSV exporter with additional features"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """Initialize advanced CSV exporter"""
        super().__init__(config)
        
        # Advanced features
        self.custom_formatters = {}
        self.column_transformers = {}
        self.data_filters = []
    
    def add_column_formatter(self, column_name: str, formatter: callable):
        """Add custom formatter for a specific column"""
        self.custom_formatters[column_name] = formatter
    
    def add_column_transformer(self, column_name: str, transformer: callable):
        """Add transformer for a specific column"""
        self.column_transformers[column_name] = transformer
    
    def add_data_filter(self, filter_func: callable):
        """Add data filter function"""
        self.data_filters.append(filter_func)
    
    async def export(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None) -> ExportResult:
        """Export data with advanced features"""
        export_config = config or self.config
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Apply data filters
            filtered_data = self._apply_filters(data)
            
            # Apply column transformers
            transformed_data = self._apply_transformers(filtered_data)
            
            # Apply column formatters
            formatted_data = self._apply_formatters(transformed_data)
            
            # Export using parent method
            result = await super().export(formatted_data, config)
            
            # Update metadata
            if result.metadata:
                result.metadata.update({
                    'advanced_features': True,
                    'filtered_records': len(data) - len(filtered_data),
                    'transformed_columns': list(self.column_transformers.keys()),
                    'formatted_columns': list(self.custom_formatters.keys())
                })
            
            return result
            
        except Exception as e:
            export_time = asyncio.get_event_loop().time() - start_time
            return ExportResult(
                success=False,
                exporter_name=self.name,
                format=export_config.format,
                export_time=export_time,
                error_message=str(e)
            )
    
    def _apply_filters(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply data filters"""
        filtered_data = data
        
        for filter_func in self.data_filters:
            filtered_data = [record for record in filtered_data if filter_func(record)]
        
        return filtered_data
    
    def _apply_transformers(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply column transformers"""
        transformed_data = []
        
        for record in data:
            transformed_record = record.copy()
            
            for column, transformer in self.column_transformers.items():
                if column in transformed_record:
                    try:
                        transformed_record[column] = transformer(transformed_record[column])
                    except Exception as e:
                        self.logger.warning(f"Transformer failed for column '{column}': {str(e)}")
            
            transformed_data.append(transformed_record)
        
        return transformed_data
    
    def _apply_formatters(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply column formatters"""
        formatted_data = []
        
        for record in data:
            formatted_record = record.copy()
            
            for column, formatter in self.custom_formatters.items():
                if column in formatted_record:
                    try:
                        formatted_record[column] = formatter(formatted_record[column])
                    except Exception as e:
                        self.logger.warning(f"Formatter failed for column '{column}': {str(e)}")
            
            formatted_data.append(formatted_record)
        
        return formatted_data


# Convenience functions for common CSV export scenarios
def export_to_csv(data: List[Dict[str, Any]], filename: str, **kwargs) -> str:
    """Quick CSV export function"""
    config = ExportConfig(filename=filename, **kwargs)
    exporter = CSVExporter(config)
    result = exporter.export_to_string(data, config)
    return result


def export_csv_file(data: List[Dict[str, Any]], file_path: str, **kwargs) -> ExportResult:
    """Quick CSV file export function"""
    config = ExportConfig(filename=os.path.basename(file_path), directory=os.path.dirname(file_path), **kwargs)
    exporter = CSVExporter(config)
    return exporter.export_with_stats(data, config)


def create_csv_exporter(delimiter: str = ',', encoding: str = 'utf-8') -> CSVExporter:
    """Create CSV exporter with common settings"""
    config = ExportConfig(
        format='csv',
        delimiter=delimiter,
        encoding=encoding
    )
    return CSVExporter(config)


def create_tsv_exporter(encoding: str = 'utf-8') -> CSVExporter:
    """Create TSV (tab-separated values) exporter"""
    config = ExportConfig(
        format='csv',
        delimiter='\t',
        encoding=encoding
    )
    return CSVExporter(config)


# Example usage patterns
def example_usage():
    """Example usage patterns for CSV export"""
    
    # Pattern 1: Basic CSV export
    data = [
        {'name': 'John', 'age': 30, 'city': 'New York'},
        {'name': 'Jane', 'age': 25, 'city': 'Los Angeles'}
    ]
    
    csv_string = export_to_csv(data, 'people.csv')
    
    # Pattern 2: Advanced CSV export with custom formatting
    exporter = AdvancedCSVExporter()
    
    # Add custom formatter for names
    exporter.add_column_formatter('name', lambda x: x.upper())
    
    # Add transformer for age
    exporter.add_column_transformer('age', lambda x: x + 1)
    
    # Add filter for adults only
    exporter.add_data_filter(lambda record: record.get('age', 0) >= 18)
    
    result = asyncio.run(exporter.export(data))
    
    # Pattern 3: Streaming export for large datasets
    exporter = CSVExporter()
    
    for chunk in exporter.export_streaming(data):
        print(chunk)  # Process chunk
    
    print(f"CSV export completed: {result.to_dict()}")


if __name__ == "__main__":
    # Test CSV exporter
    logging.basicConfig(level=logging.INFO)
    
    # Create test data
    test_data = [
        {'name': 'John Doe', 'email': 'john@example.com', 'age': 30, 'salary': 50000.50},
        {'name': 'Jane Smith', 'email': 'jane@example.com', 'age': 25, 'salary': 60000.00},
        {'name': 'Bob Johnson', 'email': 'bob@example.com', 'age': 35, 'salary': 75000.75}
    ]
    
    # Create and run CSV exporter
    exporter = create_csv_exporter()
    result = exporter.export_with_stats(test_data)
    
    print(f"CSV Export Result: {result.to_dict()}")
    
    # Test advanced exporter
    advanced_exporter = AdvancedCSVExporter()
    advanced_exporter.add_column_formatter('name', lambda x: x.upper())
    advanced_exporter.add_column_transformer('salary', lambda x: x * 1.1)
    
    advanced_result = advanced_exporter.export_with_stats(test_data)
    print(f"Advanced CSV Export Result: {advanced_result.to_dict()}")
