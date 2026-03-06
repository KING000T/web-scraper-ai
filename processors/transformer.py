"""
Data Transformer Module

This module implements data transformation functionality with support for
field mapping, calculations, conditional logic, and data enrichment.
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime
from enum import Enum
import logging

from .base import BaseProcessor, ProcessingResult, TransformationError


class TransformationType(Enum):
    """Supported transformation types"""
    FIELD_MAPPING = "field_mapping"
    CALCULATION = "calculation"
    CONDITIONAL = "conditional"
    CONCATENATION = "concatenation"
    SPLIT = "split"
    FORMAT = "format"
    NORMALIZE = "normalize"
    ENRICH = "enrich"
    CUSTOM = "custom"


@dataclass
class Transformation:
    """Transformation configuration"""
    
    name: str
    transformation_type: TransformationType
    source_field: Optional[str] = None
    target_field: Optional[str] = None
    source_fields: Optional[List[str]] = None
    expression: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    custom_function: Optional[Callable] = None
    condition: Optional[str] = None
    default_value: Any = None
    
    def __post_init__(self):
        """Validate transformation configuration"""
        if self.transformation_type == TransformationType.FIELD_MAPPING and not self.source_field:
            raise ValueError("source_field is required for field mapping")
        
        if self.transformation_type == TransformationType.CALCULATION and not self.expression:
            raise ValueError("expression is required for calculation")
        
        if self.transformation_type == TransformationType.CUSTOM and not self.custom_function:
            raise ValueError("custom_function is required for custom transformation")


class DataTransformer(BaseProcessor):
    """Data transformer with comprehensive transformation capabilities"""
    
    def __init__(self, transformations: List[Transformation] = None):
        """Initialize transformer with transformations"""
        super().__init__("DataTransformer")
        self.transformations = transformations or []
        self.field_transformations = self._organize_transformations_by_target()
        
        # Built-in transformation functions
        self.builtin_functions = {
            'upper': str.upper,
            'lower': str.lower,
            'title': str.title,
            'strip': str.strip,
            'capitalize': str.capitalize,
            'abs': abs,
            'round': round,
            'len': len,
            'sum': sum,
            'avg': lambda x: sum(x) / len(x) if x else 0,
            'min': min,
            'max': max
        }
        
        # Safe evaluation context
        self.safe_context = {
            '__builtins__': {},
            **self.builtin_functions
        }
    
    def _organize_transformations_by_target(self) -> Dict[str, List[Transformation]]:
        """Organize transformations by target field"""
        field_transformations = {}
        for transformation in self.transformations:
            target = transformation.target_field or transformation.name
            if target not in field_transformations:
                field_transformations[target] = []
            field_transformations[target].append(transformation)
        return field_transformations
    
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform data records"""
        if not data:
            return []
        
        transformed_data = []
        
        for i, record in enumerate(data):
            try:
                transformed_record = await self._transform_record(record)
                transformed_data.append(transformed_record)
                
                self.logger.debug(f"Transformed record {i+1}/{len(data)}")
                
            except Exception as e:
                self.logger.error(f"Error transforming record {i+1}: {str(e)}")
                # Keep original record if transformation fails
                transformed_data.append(record)
        
        return transformed_data
    
    async def _transform_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single record"""
        transformed_record = record.copy()
        
        for target_field, transformations in self.field_transformations.items():
            try:
                # Apply transformations in order
                for transformation in transformations:
                    value = await self._apply_transformation(transformation, transformed_record)
                    
                    if transformation.target_field:
                        transformed_record[transformation.target_field] = value
                    else:
                        # Update the source field if no target specified
                        if transformation.source_field:
                            transformed_record[transformation.source_field] = value
                
            except Exception as e:
                self.logger.warning(f"Error applying transformation for field '{target_field}': {str(e)}")
                # Use default value if available
                transformation = transformations[0]  # First transformation
                if transformation.default_value is not None and transformation.target_field:
                    transformed_record[transformation.target_field] = transformation.default_value
        
        return transformed_record
    
    async def _apply_transformation(self, transformation: Transformation, record: Dict[str, Any]) -> Any:
        """Apply a single transformation"""
        if transformation.transformation_type == TransformationType.FIELD_MAPPING:
            return await self._apply_field_mapping(transformation, record)
        
        elif transformation.transformation_type == TransformationType.CALCULATION:
            return await self._apply_calculation(transformation, record)
        
        elif transformation.transformation_type == TransformationType.CONDITIONAL:
            return await self._apply_conditional(transformation, record)
        
        elif transformation.transformation_type == TransformationType.CONCATENATION:
            return await self._apply_concatenation(transformation, record)
        
        elif transformation.transformation_type == TransformationType.SPLIT:
            return await self._apply_split(transformation, record)
        
        elif transformation.transformation_type == TransformationType.FORMAT:
            return await self._apply_format(transformation, record)
        
        elif transformation.transformation_type == TransformationType.NORMALIZE:
            return await self._apply_normalize(transformation, record)
        
        elif transformation.transformation_type == TransformationType.CUSTOM:
            return await self._apply_custom(transformation, record)
        
        else:
            raise TransformationError(f"Unknown transformation type: {transformation.transformation_type}")
    
    async def _apply_field_mapping(self, transformation: Transformation, record: Dict[str, Any]) -> Any:
        """Apply field mapping transformation"""
        source_value = record.get(transformation.source_field)
        
        # Apply field mapping rules
        if transformation.parameters:
            mapping_rules = transformation.parameters.get('mapping', {})
            default_value = transformation.parameters.get('default')
            
            if isinstance(mapping_rules, dict):
                return mapping_rules.get(source_value, default_value)
        
        return source_value
    
    async def _apply_calculation(self, transformation: Transformation, record: Dict[str, Any]) -> Any:
        """Apply calculation transformation"""
        expression = transformation.expression
        
        # Create safe evaluation context with record values
        context = self.safe_context.copy()
        
        # Add record values to context
        for key, value in record.items():
            # Sanitize key name for Python identifier
            safe_key = re.sub(r'[^a-zA-Z0-9_]', '_', key)
            if safe_key not in context:
                context[safe_key] = value
        
        try:
            # Evaluate expression safely
            result = eval(expression, context)
            return result
        except Exception as e:
            self.logger.error(f"Error evaluating expression '{expression}': {str(e)}")
            return transformation.default_value
    
    async def _apply_conditional(self, transformation: Transformation, record: Dict[str, Any]) -> Any:
        """Apply conditional transformation"""
        condition = transformation.condition
        
        if not condition:
            return record.get(transformation.source_field)
        
        # Create safe evaluation context
        context = self.safe_context.copy()
        for key, value in record.items():
            safe_key = re.sub(r'[^a-zA-Z0-9_]', '_', key)
            if safe_key not in context:
                context[safe_key] = value
        
        try:
            # Evaluate condition
            condition_result = eval(condition, context)
            
            if condition_result:
                # Return true value or source field
                true_value = transformation.parameters.get('true_value') if transformation.parameters else None
                return true_value if true_value is not None else record.get(transformation.source_field)
            else:
                # Return false value or default
                false_value = transformation.parameters.get('false_value') if transformation.parameters else None
                return false_value if false_value is not None else transformation.default_value
                
        except Exception as e:
            self.logger.error(f"Error evaluating condition '{condition}': {str(e)}")
            return transformation.default_value
    
    async def _apply_concatenation(self, transformation: Transformation, record: Dict[str, Any]) -> Any:
        """Apply concatenation transformation"""
        source_fields = transformation.source_fields or []
        
        if not source_fields:
            return ""
        
        values = []
        for field in source_fields:
            value = record.get(field, "")
            if value is not None:
                values.append(str(value))
        
        separator = transformation.parameters.get('separator', '') if transformation.parameters else ''
        
        return separator.join(values)
    
    async def _apply_split(self, transformation: Transformation, record: Dict[str, Any]) -> Any:
        """Apply split transformation"""
        source_value = record.get(transformation.source_field, "")
        
        if not isinstance(source_value, str):
            return [source_value]
        
        separator = transformation.parameters.get('separator', ',') if transformation.parameters else ','
        max_split = transformation.parameters.get('max_split', -1) if transformation.parameters else -1
        
        return source_value.split(separator, max_split)
    
    async def _apply_format(self, transformation: Transformation, record: Dict[str, Any]) -> Any:
        """Apply format transformation"""
        source_value = record.get(transformation.source_field, "")
        
        format_string = transformation.expression
        if not format_string:
            return source_value
        
        try:
            # Create context for formatting
            context = {'value': source_value, **record}
            
            # Format the string
            result = format_string.format(**context)
            return result
            
        except Exception as e:
            self.logger.error(f"Error formatting string '{format_string}': {str(e)}")
            return transformation.default_value
    
    async def _apply_normalize(self, transformation: Transformation, record: Dict[str, Any]) -> Any:
        """Apply normalization transformation"""
        source_value = record.get(transformation.source_field, "")
        
        if not isinstance(source_value, str):
            return source_value
        
        normalization_type = transformation.parameters.get('type', 'lower') if transformation.parameters else 'lower'
        
        if normalization_type == 'lower':
            return source_value.lower()
        elif normalization_type == 'upper':
            return source_value.upper()
        elif normalization_type == 'title':
            return source_value.title()
        elif normalization_type == 'strip':
            return source_value.strip()
        elif normalization_type == 'normalize_whitespace':
            return re.sub(r'\s+', ' ', source_value.strip())
        elif normalization_type == 'remove_special_chars':
            return re.sub(r'[^a-zA-Z0-9\s]', '', source_value)
        else:
            return source_value
    
    async def _apply_custom(self, transformation: Transformation, record: Dict[str, Any]) -> Any:
        """Apply custom transformation"""
        if not callable(transformation.custom_function):
            raise TransformationError("Custom function is not callable")
        
        try:
            source_value = record.get(transformation.source_field)
            
            # Call custom function
            if transformation.source_fields:
                # Multiple source fields
                field_values = [record.get(field) for field in transformation.source_fields]
                return transformation.custom_function(*field_values)
            else:
                # Single source field
                return transformation.custom_function(source_value)
                
        except Exception as e:
            self.logger.error(f"Error in custom transformation: {str(e)}")
            return transformation.default_value
    
    def add_transformation(self, transformation: Transformation):
        """Add a transformation"""
        self.transformations.append(transformation)
        self._organize_transformations_by_target()
    
    def remove_transformation(self, name: str):
        """Remove a transformation by name"""
        self.transformations = [t for t in self.transformations if t.name != name]
        self._organize_transformations_by_target()
    
    def get_transformation_summary(self) -> Dict[str, Any]:
        """Get summary of configured transformations"""
        summary = {
            'total_transformations': len(self.transformations),
            'transformation_types': {},
            'target_fields': list(self.field_transformations.keys())
        }
        
        # Count transformation types
        for transformation in self.transformations:
            type_name = transformation.transformation_type.value
            if type_name not in summary['transformation_types']:
                summary['transformation_types'][type_name] = 0
            summary['transformation_types'][type_name] += 1
        
        return summary


# Convenience functions for creating transformations
def map_field(source_field: str, target_field: str, mapping: Dict[str, Any], 
              default: Any = None) -> Transformation:
    """Create a field mapping transformation"""
    return Transformation(
        name=f"map_{source_field}_to_{target_field}",
        transformation_type=TransformationType.FIELD_MAPPING,
        source_field=source_field,
        target_field=target_field,
        parameters={'mapping': mapping, 'default': default}
    )


def calculate_field(target_field: str, expression: str, default: Any = None) -> Transformation:
    """Create a calculation transformation"""
    return Transformation(
        name=f"calc_{target_field}",
        transformation_type=TransformationType.CALCULATION,
        target_field=target_field,
        expression=expression,
        default_value=default
    )


def conditional_field(target_field: str, condition: str, true_value: Any = None, 
                     false_value: Any = None, source_field: str = None) -> Transformation:
    """Create a conditional transformation"""
    return Transformation(
        name=f"conditional_{target_field}",
        transformation_type=TransformationType.CONDITIONAL,
        target_field=target_field,
        condition=condition,
        source_field=source_field,
        parameters={'true_value': true_value, 'false_value': false_value}
    )


def concatenate_fields(target_field: str, source_fields: List[str], 
                       separator: str = '') -> Transformation:
    """Create a concatenation transformation"""
    return Transformation(
        name=f"concat_{target_field}",
        transformation_type=TransformationType.CONCATENATION,
        target_field=target_field,
        source_fields=source_fields,
        parameters={'separator': separator}
    )


def split_field(target_field: str, source_field: str, separator: str = ',', 
                max_split: int = -1) -> Transformation:
    """Create a split transformation"""
    return Transformation(
        name=f"split_{target_field}",
        transformation_type=TransformationType.SPLIT,
        target_field=target_field,
        source_field=source_field,
        parameters={'separator': separator, 'max_split': max_split}
    )


def format_field(target_field: str, source_field: str, format_string: str) -> Transformation:
    """Create a format transformation"""
    return Transformation(
        name=f"format_{target_field}",
        transformation_type=TransformationType.FORMAT,
        target_field=target_field,
        source_field=source_field,
        expression=format_string
    )


def normalize_field(target_field: str, source_field: str, 
                   normalization_type: str = 'lower') -> Transformation:
    """Create a normalization transformation"""
    return Transformation(
        name=f"normalize_{target_field}",
        transformation_type=TransformationType.NORMALIZE,
        target_field=target_field,
        source_field=source_field,
        parameters={'type': normalization_type}
    )


def custom_field(target_field: str, custom_function: Callable, 
                source_field: str = None, source_fields: List[str] = None,
                default: Any = None) -> Transformation:
    """Create a custom transformation"""
    return Transformation(
        name=f"custom_{target_field}",
        transformation_type=TransformationType.CUSTOM,
        target_field=target_field,
        source_field=source_field,
        source_fields=source_fields,
        custom_function=custom_function,
        default_value=default
    )


# Built-in custom functions
def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    if not isinstance(url, str):
        return ""
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return ""


def extract_numbers(text: str) -> List[float]:
    """Extract all numbers from text"""
    if not isinstance(text, str):
        return []
    
    numbers = re.findall(r'-?\d+\.?\d*', text)
    return [float(num) for num in numbers]


def calculate_age(birth_date: str) -> Optional[int]:
    """Calculate age from birth date"""
    if not isinstance(birth_date, str):
        return None
    
    try:
        birth = datetime.strptime(birth_date, '%Y-%m-%d')
        today = datetime.now()
        age = today.year - birth.year
        
        # Adjust for birthday hasn't occurred yet this year
        if today.month < birth.month or (today.month == birth.month and today.day < birth.day):
            age -= 1
        
        return age
    except:
        return None


def calculate_bmi(weight: float, height: float) -> Optional[float]:
    """Calculate BMI from weight (kg) and height (m)"""
    try:
        return weight / (height ** 2)
    except:
        return None
