"""
JSON Exporter Module

This module implements JSON export functionality with support for
pretty printing, nested data structures, and custom formatting.
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
import logging

from .base import BaseExporter, ExportConfig, ExportResult, ExportError


class JSONExporter(BaseExporter):
    """JSON exporter with comprehensive formatting options"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """Initialize JSON exporter with configuration"""
        super().__init__(config)
        self.indent = 2 if self.config.format == 'json' else None
        self.sort_keys = False
        self.ensure_ascii = False
        self.allow_nan = True
    
    async def export(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None) -> ExportResult:
        """Export data to JSON format"""
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
            
            # Write JSON file
            await self._write_json_file(file_path, prepared_data, export_config)
            
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
                    'encoding': export_config.encoding,
                    'pretty_print': self.indent is not None,
                    'nested_objects': self._has_nested_objects(prepared_data)
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
    
    async def _write_json_file(self, file_path: str, data: List[Dict[str, Any]], config: ExportConfig):
        """Write data to JSON file"""
        try:
            with open(file_path, 'w', encoding=config.encoding) as jsonfile:
                json.dump(
                    data,
                    jsonfile,
                    indent=self.indent,
                    sort_keys=self.sort_keys,
                    ensure_ascii=self.ensure_ascii,
                    allow_nan=self.allow_nan,
                    default=self._json_serializer
                )
                
        except IOError as e:
            raise ExportError(f"Failed to write JSON file {file_path}: {str(e)}")
        except TypeError as e:
            raise ExportError(f"JSON serialization error: {str(e)}")
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            return list(obj)
        else:
            return str(obj)
    
    def export_to_string(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None) -> str:
        """Export data to JSON string"""
        export_config = config or self.config
        prepared_data = self.prepare_data(data)
        
        if not prepared_data:
            return "[]"
        
        try:
            return json.dumps(
                prepared_data,
                indent=self.indent,
                sort_keys=self.sort_keys,
                ensure_ascii=self.ensure_ascii,
                allow_nan=self.allow_nan,
                default=self._json_serializer
            )
        except Exception as e:
            raise ExportError(f"Failed to generate JSON string: {str(e)}")
    
    def export_compact(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None) -> str:
        """Export data to compact JSON string (no pretty printing)"""
        # Temporarily disable pretty printing
        original_indent = self.indent
        self.indent = None
        
        try:
            result = self.export_to_string(data, config)
            return result
        finally:
            self.indent = original_indent
    
    def export_pretty(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None) -> str:
        """Export data to pretty-printed JSON string"""
        # Temporarily enable pretty printing
        original_indent = self.indent
        self.indent = 2
        
        try:
            result = self.export_to_string(data, config)
            return result
        finally:
            self.indent = original_indent
    
    def export_ndjson(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None) -> str:
        """Export data to NDJSON (newline-delimited JSON) string"""
        export_config = config or self.config
        prepared_data = self.prepare_data(data)
        
        if not prepared_data:
            return ""
        
        try:
            lines = []
            for record in prepared_data:
                json_line = json.dumps(
                    record,
                    ensure_ascii=self.ensure_ascii,
                    allow_nan=self.allow_nan,
                    default=self._json_serializer
                )
                lines.append(json_line)
            
            return '\n'.join(lines)
            
        except Exception as e:
            raise ExportError(f"Failed to generate NDJSON string: {str(e)}")
    
    def _has_nested_objects(self, data: List[Dict[str, Any]]) -> bool:
        """Check if data contains nested objects"""
        if not data:
            return False
        
        for record in data:
            for value in record.values():
                if isinstance(value, (dict, list)):
                    return True
                # Check for complex objects
                if hasattr(value, '__dict__') or (hasattr(value, '__iter__') and not isinstance(value, (str, bytes))):
                    return True
        
        return False
    
    def set_indent(self, indent: Optional[int]):
        """Set JSON indentation level"""
        if indent is not None and indent < 0:
            raise ValueError("Indent must be non-negative")
        
        self.indent = indent
    
    def set_sort_keys(self, sort_keys: bool):
        """Set whether to sort keys in JSON output"""
        self.sort_keys = sort_keys
    
    def set_ensure_ascii(self, ensure_ascii: bool):
        """Set whether to ensure ASCII encoding"""
        self.ensure_ascii = ensure_ascii
    
    def set_allow_nan(self, allow_nan: bool):
        """Set whether to allow NaN values"""
        self.allow_nan = allow_nan


class JSONLinesExporter(JSONExporter):
    """Specialized exporter for JSON Lines (NDJSON) format"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """Initialize JSON Lines exporter"""
        super().__init__(config)
        # Override format for NDJSON
        self.config.format = 'jsonlines'
    
    async def export(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None) -> ExportResult:
        """Export data to JSON Lines format"""
        export_config = config or self.config
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Prepare data
            prepared_data = self.prepare_data(data)
            
            if not prepared_data:
                return ExportResult(
                    success=True,
                    exporter_name=self.name,
                    format='jsonlines',
                    record_count=0,
                    export_time=0.0
                )
            
            # Get file path
            file_path = export_config.get_full_path()
            
            # Write JSON Lines file
            await self._write_jsonlines_file(file_path, prepared_data, export_config)
            
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
                format='jsonlines',
                metadata={
                    'encoding': export_config.encoding,
                    'line_delimited': True
                }
            )
            
        except Exception as e:
            export_time = asyncio.get_event_loop().time() - start_time
            return ExportResult(
                success=False,
                exporter_name=self.name,
                format='jsonlines',
                export_time=export_time,
                error_message=str(e)
            )
    
    async def _write_jsonlines_file(self, file_path: str, data: List[Dict[str, Any]], config: ExportConfig):
        """Write data to JSON Lines file"""
        try:
            with open(file_path, 'w', encoding=config.encoding) as jsonfile:
                for record in data:
                    json_line = json.dumps(
                        record,
                        ensure_ascii=self.ensure_ascii,
                        allow_nan=self.allow_nan,
                        default=self._json_serializer
                    )
                    jsonfile.write(json_line + '\n')
                    
        except IOError as e:
            raise ExportError(f"Failed to write JSON Lines file {file_path}: {str(e)}")


class StreamingJSONExporter(JSONExporter):
    """Streaming JSON exporter for large datasets"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """Initialize streaming JSON exporter"""
        super().__init__(config)
        self.chunk_size = 1000  # Records per chunk
    
    def set_chunk_size(self, chunk_size: int):
        """Set chunk size for streaming"""
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        
        self.chunk_size = chunk_size
    
    def export_streaming(self, data: List[Dict[str, Any]], config: Optional[ExportConfig] = None):
        """Export data as streaming chunks"""
        export_config = config or self.config
        prepared_data = self.prepare_data(data)
        
        if not prepared_data:
            return
        
        # Split data into chunks
        for i in range(0, len(prepared_data), self.chunk_size):
            chunk = prepared_data[i:i + self.chunk_size]
            
            # Export chunk
            chunk_result = self.export_to_string(chunk, config)
            
            yield {
                'chunk_index': i // self.chunk_size + 1,
                'chunk_size': len(chunk),
                'data': chunk_result
            }
    
    def export_streaming_to_file(self, data: List[Dict[str, Any]], file_path: str, config: Optional[ExportConfig] = None):
        """Export streaming data directly to file"""
        export_config = config or self.config
        
        try:
            # Ensure directory exists
            self.ensure_directory(os.path.dirname(file_path))
            
            with open(file_path, 'w', encoding=export_config.encoding) as jsonfile:
                # Write opening bracket
                jsonfile.write('[\n')
                
                # Write data records
                for i, record in enumerate(prepared_data):
                    json_record = json.dumps(
                        record,
                        indent=self.indent,
                        ensure_ascii=self.ensure_ascii,
                        allow_nan=self.allow_nan,
                        default=self._json_serializer
                    )
                    
                    # Add comma except for last record
                    if i < len(prepared_data) - 1:
                        json_record += ','
                    
                    jsonfile.write(json_record + '\n')
                
                # Write closing bracket
                jsonfile.write(']')
                
        except Exception as e:
            raise ExportError(f"Failed to write streaming JSON file {file_path}: {str(e)}")


# Convenience functions for common JSON export scenarios
def export_to_json(data: List[Dict[str, Any]], filename: str, **kwargs) -> str:
    """Quick JSON export function"""
    config = ExportConfig(filename=filename, format='json', **kwargs)
    exporter = JSONExporter(config)
    result = exporter.export_to_string(data, config)
    return result


def export_pretty_json(data: List[Dict[str, Any]], filename: str, **kwargs) -> str:
    """Quick pretty-printed JSON export function"""
    config = ExportConfig(filename=filename, format='json', **kwargs)
    exporter = JSONExporter(config)
    result = exporter.export_pretty(data, config)
    return result


def export_compact_json(data: List[Dict[str, Any]], filename: str, **kwargs) -> str:
    """Quick compact JSON export function"""
    config = ExportConfig(filename=filename, format='json', **kwargs)
    exporter = JSONExporter(config)
    result = exporter.export_compact(data, config)
    return result


def export_ndjson(data: List[Dict[str, Any]], filename: str, **kwargs) -> str:
    """Quick NDJSON export function"""
    config = ExportConfig(filename=filename, format='jsonlines', **kwargs)
    exporter = JSONExporter(config)
    result = exporter.export_ndjson(data, config)
    return result


def export_json_file(data: List[Dict[str, Any]], file_path: str, **kwargs) -> ExportResult:
    """Quick JSON file export function"""
    config = ExportConfig(filename=os.path.basename(file_path), directory=os.path.dirname(file_path), format='json', **kwargs)
    exporter = JSONExporter(config)
    return exporter.export_with_stats(data, config)


def create_json_exporter(pretty_print: bool = True, sort_keys: bool = False, encoding: str = 'utf-8') -> JSONExporter:
    """Create JSON exporter with common settings"""
    config = ExportConfig(
        format='json',
        encoding=encoding
    )
    
    exporter = JSONExporter(config)
    exporter.set_indent(2 if pretty_print else None)
    exporter.set_sort_keys(sort_keys)
    
    return exporter


def create_jsonlines_exporter(encoding: str = 'utf-8') -> JSONLinesExporter:
    """Create JSON Lines exporter with common settings"""
    config = ExportConfig(
        format='jsonlines',
        encoding=encoding
    )
    return JSONLinesExporter(config)


# Example usage patterns
def example_usage():
    """Example usage patterns for JSON export"""
    
    # Pattern 1: Basic JSON export
    data = [
        {'name': 'John', 'age': 30, 'city': 'New York', 'skills': ['Python', 'JavaScript']},
        {'name': 'Jane', 'age': 25, 'city': 'Los Angeles', 'skills': ['Java', 'C++']}
    ]
    
    json_string = export_to_json(data, 'people.json')
    
    # Pattern 2: Pretty-printed JSON
    pretty_json = export_pretty_json(data, 'people_pretty.json')
    
    # Pattern 3: NDJSON (JSON Lines)
    ndjson_string = export_ndjson(data, 'people.ndjson')
    
    # Pattern 4: Streaming export for large datasets
    exporter = StreamingJSONExporter()
    
    for chunk in exporter.export_streaming(data):
        print(f"Chunk {chunk['chunk_index']}: {chunk['chunk_size']} records")
        # Process chunk
    
    # Pattern 5: Advanced JSON with custom formatting
    exporter = create_json_exporter(pretty_print=True, sort_keys=True)
    exporter.set_allow_nan(False)  # Disallow NaN values
    
    result = exporter.export_with_stats(data)
    
    print(f"JSON Export Result: {result.to_dict()}")


if __name__ == "__main__":
    # Test JSON exporter
    logging.basicConfig(level=logging.INFO)
    
    # Create test data with complex structures
    test_data = [
        {
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30,
            'address': {
                'street': '123 Main St',
                'city': 'New York',
                'zipcode': '10001'
            },
            'skills': ['Python', 'JavaScript', 'SQL'],
            'created_at': datetime.now(),
            'active': True,
            'salary': None  # Test NaN handling
        },
        {
            'id': 2,
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'age': 25,
            'address': {
                'street': '456 Oak Ave',
                'city': 'Los Angeles',
                'zipcode': '90001'
            },
            'skills': ['Java', 'C++', 'Python'],
            'created_at': datetime.now(),
            'active': False,
            'salary': 75000.50
        }
    ]
    
    # Create and run JSON exporter
    exporter = create_json_exporter(pretty_print=True, sort_keys=True)
    result = exporter.export_with_stats(test_data)
    
    print(f"JSON Export Result: {result.to_dict()}")
    
    # Test JSON Lines exporter
    ndjson_exporter = create_jsonlines_exporter()
    ndjson_result = ndjson_exporter.export_with_stats(test_data)
    
    print(f"JSON Lines Export Result: {ndjson_result.to_dict()}")
    
    # Test streaming exporter
    streaming_exporter = StreamingJSONExporter()
    streaming_exporter.set_chunk_size(1)  # One record per chunk for demo
    
    print("Streaming JSON Export:")
    for chunk in streaming_exporter.export_streaming(test_data):
        print(chunk['data'])
