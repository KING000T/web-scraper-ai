"""
Data Validator Module

This module implements data validation functionality with support for
various validation rules, custom validators, and quality scoring.
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime
from enum import Enum
import logging

from .base import BaseProcessor, ValidationResult, ValidationError


class ValidationType(Enum):
    """Supported validation types"""
    REQUIRED = "required"
    TYPE = "type"
    FORMAT = "format"
    LENGTH = "length"
    RANGE = "range"
    PATTERN = "pattern"
    CUSTOM = "custom"


@dataclass
class ValidationRule:
    """Validation rule configuration"""
    
    field_name: str
    validation_type: ValidationType
    required: bool = False
    data_type: Optional[str] = None
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    custom_validator: Optional[Callable] = None
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate rule configuration"""
        if self.validation_type == ValidationType.TYPE and not self.data_type:
            raise ValueError("data_type is required for type validation")
        
        if self.validation_type == ValidationType.PATTERN and not self.pattern:
            raise ValueError("pattern is required for pattern validation")
        
        if self.validation_type == ValidationType.CUSTOM and not self.custom_validator:
            raise ValueError("custom_validator is required for custom validation")


class DataValidator(BaseProcessor):
    """Data validator with comprehensive validation rules"""
    
    def __init__(self, validation_rules: List[ValidationRule] = None):
        """Initialize validator with validation rules"""
        super().__init__("DataValidator")
        self.validation_rules = validation_rules or []
        self.field_rules = self._organize_rules_by_field()
        
        # Pre-compile regex patterns for performance
        self._compile_patterns()
        
        # Built-in validators
        self.builtin_validators = {
            'email': self._validate_email,
            'url': self._validate_url,
            'phone': self._validate_phone,
            'date': self._validate_date,
            'number': self._validate_number,
            'integer': self._validate_integer,
            'float': self._validate_float,
            'boolean': self._validate_boolean
        }
    
    def _organize_rules_by_field(self) -> Dict[str, List[ValidationRule]]:
        """Organize validation rules by field name"""
        field_rules = {}
        for rule in self.validation_rules:
            if rule.field_name not in field_rules:
                field_rules[rule.field_name] = []
            field_rules[rule.field_name].append(rule)
        return field_rules
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for better performance"""
        self.compiled_patterns = {}
        for rule in self.validation_rules:
            if rule.pattern:
                try:
                    self.compiled_patterns[rule.field_name] = re.compile(rule.pattern)
                except re.error as e:
                    self.logger.error(f"Invalid regex pattern for field {rule.field_name}: {str(e)}")
    
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate data records"""
        if not data:
            return []
        
        validated_data = []
        validation_results = []
        
        for i, record in enumerate(data):
            try:
                # Validate record
                validation_result = await self._validate_record(record)
                validation_results.append(validation_result)
                
                # Only include valid records if strict validation
                if validation_result.is_valid:
                    validated_data.append(record)
                else:
                    self.logger.warning(f"Record {i+1} failed validation: {validation_result.errors}")
                
            except Exception as e:
                self.logger.error(f"Error validating record {i+1}: {str(e)}")
                # Keep record but note validation error
                error_result = ValidationResult(
                    is_valid=False,
                    errors=[f"Validation error: {str(e)}"]
                )
                validation_results.append(error_result)
        
        # Store validation results in metadata
        self.last_validation_results = validation_results
        
        return validated_data
    
    async def _validate_record(self, record: Dict[str, Any]) -> ValidationResult:
        """Validate a single record"""
        result = ValidationResult(is_valid=True)
        
        for field_name, field_rules in self.field_rules.items():
            field_value = record.get(field_name)
            
            for rule in field_rules:
                try:
                    await self._apply_validation_rule(rule, field_value, result)
                except Exception as e:
                    error_msg = f"Validation error for field '{field_name}': {str(e)}"
                    self.logger.error(error_msg)
                    result.add_error(field_name, error_msg)
        
        return result
    
    async def _apply_validation_rule(self, rule: ValidationRule, value: Any, result: ValidationResult):
        """Apply a single validation rule"""
        field_name = rule.field_name
        
        # Check if field is required
        if rule.validation_type == ValidationType.REQUIRED:
            if rule.required and (value is None or value == ''):
                error_msg = rule.error_message or f"Field '{field_name}' is required"
                result.add_error(field_name, error_msg)
            result.field_results[field_name] = not (rule.required and (value is None or value == ''))
            return
        
        # Skip validation if value is empty and not required
        if value is None or value == '':
            result.field_results[field_name] = True
            return
        
        # Apply validation based on type
        if rule.validation_type == ValidationType.TYPE:
            await self._validate_type(rule, value, result)
        
        elif rule.validation_type == ValidationType.FORMAT:
            await self._validate_format(rule, value, result)
        
        elif rule.validation_type == ValidationType.LENGTH:
            await self._validate_length(rule, value, result)
        
        elif rule.validation_type == ValidationType.RANGE:
            await self._validate_range(rule, value, result)
        
        elif rule.validation_type == ValidationType.PATTERN:
            await self._validate_pattern_rule(rule, value, result)
        
        elif rule.validation_type == ValidationType.CUSTOM:
            await self._validate_custom(rule, value, result)
    
    async def _validate_type(self, rule: ValidationRule, value: Any, result: ValidationResult):
        """Validate data type"""
        field_name = rule.field_name
        expected_type = rule.data_type.lower()
        
        # Use built-in validators if available
        if expected_type in self.builtin_validators:
            is_valid = self.builtin_validators[expected_type](value)
        else:
            # Generic type validation
            type_mapping = {
                'string': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict
            }
            
            expected_python_type = type_mapping.get(expected_type)
            if expected_python_type:
                is_valid = isinstance(value, expected_python_type)
            else:
                is_valid = True  # Unknown type, assume valid
        
        if not is_valid:
            error_msg = rule.error_message or f"Field '{field_name}' must be of type {expected_type}"
            result.add_error(field_name, error_msg)
        
        result.field_results[field_name] = is_valid
    
    async def _validate_format(self, rule: ValidationRule, value: Any, result: ValidationResult):
        """Validate data format"""
        field_name = rule.field_name
        
        if not isinstance(value, str):
            error_msg = rule.error_message or f"Field '{field_name}' must be a string for format validation"
            result.add_error(field_name, error_msg)
            result.field_results[field_name] = False
            return
        
        # Check if value matches allowed values
        if rule.allowed_values:
            is_valid = value in rule.allowed_values
            if not is_valid:
                error_msg = rule.error_message or f"Field '{field_name}' must be one of: {rule.allowed_values}"
                result.add_error(field_name, error_msg)
            result.field_results[field_name] = is_valid
            return
        
        # Use built-in format validators
        format_validators = {
            'email': self._validate_email,
            'url': self._validate_url,
            'phone': self._validate_phone,
            'date': self._validate_date
        }
        
        if rule.data_type in format_validators:
            is_valid = format_validators[rule.data_type](value)
        else:
            is_valid = True  # Unknown format, assume valid
        
        if not is_valid:
            error_msg = rule.error_message or f"Field '{field_name}' has invalid {rule.data_type} format"
            result.add_error(field_name, error_msg)
        
        result.field_results[field_name] = is_valid
    
    async def _validate_length(self, rule: ValidationRule, value: Any, result: ValidationResult):
        """Validate field length"""
        field_name = rule.field_name
        
        if not isinstance(value, (str, list)):
            error_msg = rule.error_message or f"Field '{field_name}' must be a string or list for length validation"
            result.add_error(field_name, error_msg)
            result.field_results[field_name] = False
            return
        
        length = len(value)
        is_valid = True
        
        if rule.min_length is not None and length < rule.min_length:
            error_msg = rule.error_message or f"Field '{field_name}' must be at least {rule.min_length} characters"
            result.add_error(field_name, error_msg)
            is_valid = False
        
        if rule.max_length is not None and length > rule.max_length:
            error_msg = rule.error_message or f"Field '{field_name}' must be at most {rule.max_length} characters"
            result.add_error(field_name, error_msg)
            is_valid = False
        
        result.field_results[field_name] = is_valid
    
    async def _validate_range(self, rule: ValidationRule, value: Any, result: ValidationResult):
        """Validate numeric range"""
        field_name = rule.field_name
        
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            error_msg = rule.error_message or f"Field '{field_name}' must be a number for range validation"
            result.add_error(field_name, error_msg)
            result.field_results[field_name] = False
            return
        
        is_valid = True
        
        if rule.min_value is not None and numeric_value < rule.min_value:
            error_msg = rule.error_message or f"Field '{field_name}' must be at least {rule.min_value}"
            result.add_error(field_name, error_msg)
            is_valid = False
        
        if rule.max_value is not None and numeric_value > rule.max_value:
            error_msg = rule.error_message or f"Field '{field_name}' must be at most {rule.max_value}"
            result.add_error(field_name, error_msg)
            is_valid = False
        
        result.field_results[field_name] = is_valid
    
    async def _validate_pattern_rule(self, rule: ValidationRule, value: Any, result: ValidationResult):
        """Validate regex pattern"""
        field_name = rule.field_name
        
        if not isinstance(value, str):
            error_msg = rule.error_message or f"Field '{field_name}' must be a string for pattern validation"
            result.add_error(field_name, error_msg)
            result.field_results[field_name] = False
            return
        
        pattern = self.compiled_patterns.get(field_name)
        if not pattern:
            error_msg = f"No compiled pattern found for field '{field_name}'"
            result.add_error(field_name, error_msg)
            result.field_results[field_name] = False
            return
        
        is_valid = bool(pattern.match(value))
        
        if not is_valid:
            error_msg = rule.error_message or f"Field '{field_name}' does not match required pattern"
            result.add_error(field_name, error_msg)
        
        result.field_results[field_name] = is_valid
    
    async def _validate_custom(self, rule: ValidationRule, value: Any, result: ValidationResult):
        """Validate using custom validator function"""
        field_name = rule.field_name
        
        if not callable(rule.custom_validator):
            error_msg = f"Custom validator for field '{field_name}' is not callable"
            result.add_error(field_name, error_msg)
            result.field_results[field_name] = False
            return
        
        try:
            # Call custom validator
            is_valid = rule.custom_validator(value)
            
            if not isinstance(is_valid, bool):
                error_msg = f"Custom validator for field '{field_name}' must return boolean"
                result.add_error(field_name, error_msg)
                result.field_results[field_name] = False
                return
            
            if not is_valid:
                error_msg = rule.error_message or f"Field '{field_name}' failed custom validation"
                result.add_error(field_name, error_msg)
            
            result.field_results[field_name] = is_valid
            
        except Exception as e:
            error_msg = f"Custom validator error for field '{field_name}': {str(e)}"
            result.add_error(field_name, error_msg)
            result.field_results[field_name] = False
    
    # Built-in validators
    def _validate_email(self, value: str) -> bool:
        """Validate email format"""
        if not isinstance(value, str):
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    def _validate_url(self, value: str) -> bool:
        """Validate URL format"""
        if not isinstance(value, str):
            return False
        
        pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?'
        return bool(re.match(pattern, value))
    
    def _validate_phone(self, value: str) -> bool:
        """Validate phone number format"""
        if not isinstance(value, str):
            return False
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', value)
        
        # Check for valid phone number length (10-15 digits)
        return 10 <= len(digits) <= 15
    
    def _validate_date(self, value: str) -> bool:
        """Validate date format"""
        if not isinstance(value, str):
            return False
        
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%m/%d/%Y',
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
    
    def _validate_number(self, value: Any) -> bool:
        """Validate numeric value"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _validate_integer(self, value: Any) -> bool:
        """Validate integer value"""
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _validate_float(self, value: Any) -> bool:
        """Validate float value"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _validate_boolean(self, value: Any) -> bool:
        """Validate boolean value"""
        if isinstance(value, bool):
            return True
        
        if isinstance(value, str):
            return value.lower() in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off')
        
        return isinstance(value, (int, float)) and value in (0, 1)
    
    def add_validation_rule(self, rule: ValidationRule):
        """Add a validation rule"""
        self.validation_rules.append(rule)
        self._organize_rules_by_field()
        
        # Re-compile patterns if needed
        if rule.pattern:
            try:
                self.compiled_patterns[rule.field_name] = re.compile(rule.pattern)
            except re.error as e:
                self.logger.error(f"Invalid regex pattern for field {rule.field_name}: {str(e)}")
    
    def remove_validation_rule(self, field_name: str, validation_type: Optional[ValidationType] = None):
        """Remove validation rules for a field"""
        self.validation_rules = [
            rule for rule in self.validation_rules
            if not (rule.field_name == field_name and 
                   (validation_type is None or rule.validation_type == validation_type))
        ]
        self._organize_rules_by_field()
        
        # Remove compiled pattern if no more rules for field
        if field_name not in self.field_rules:
            self.compiled_patterns.pop(field_name, None)
    
    def get_validation_summary(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Get summary of validation results"""
        total_records = len(validation_results)
        valid_records = sum(1 for result in validation_results if result.is_valid)
        
        # Collect all errors and warnings
        all_errors = []
        all_warnings = []
        field_errors = {}
        
        for result in validation_results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            
            for error in result.errors:
                field_name = error.split(':')[0]
                if field_name not in field_errors:
                    field_errors[field_name] = 0
                field_errors[field_name] += 1
        
        return {
            'total_records': total_records,
            'valid_records': valid_records,
            'invalid_records': total_records - valid_records,
            'success_rate': (valid_records / total_records * 100) if total_records > 0 else 0,
            'total_errors': len(all_errors),
            'total_warnings': len(all_warnings),
            'field_errors': field_errors,
            'most_common_errors': self._get_most_common_errors(all_errors)
        }
    
    def _get_most_common_errors(self, errors: List[str]) -> List[Dict[str, Any]]:
        """Get most common validation errors"""
        from collections import Counter
        
        error_counts = Counter(errors)
        most_common = error_counts.most_common(10)
        
        return [
            {'error': error, 'count': count}
            for error, count in most_common
        ]


# Convenience functions for creating validation rules
def required_field(field_name: str, error_message: Optional[str] = None) -> ValidationRule:
    """Create a required field validation rule"""
    return ValidationRule(
        field_name=field_name,
        validation_type=ValidationType.REQUIRED,
        required=True,
        error_message=error_message
    )


def email_field(field_name: str, required: bool = False, error_message: Optional[str] = None) -> ValidationRule:
    """Create an email validation rule"""
    return ValidationRule(
        field_name=field_name,
        validation_type=ValidationType.FORMAT,
        data_type='email',
        required=required,
        error_message=error_message
    )


def url_field(field_name: str, required: bool = False, error_message: Optional[str] = None) -> ValidationRule:
    """Create a URL validation rule"""
    return ValidationRule(
        field_name=field_name,
        validation_type=ValidationType.FORMAT,
        data_type='url',
        required=required,
        error_message=error_message
    )


def phone_field(field_name: str, required: bool = False, error_message: Optional[str] = None) -> ValidationRule:
    """Create a phone number validation rule"""
    return ValidationRule(
        field_name=field_name,
        validation_type=ValidationType.FORMAT,
        data_type='phone',
        required=required,
        error_message=error_message
    )


def numeric_field(field_name: str, min_value: Optional[Union[int, float]] = None,
                   max_value: Optional[Union[int, float]] = None, required: bool = False,
                   error_message: Optional[str] = None) -> ValidationRule:
    """Create a numeric validation rule"""
    return ValidationRule(
        field_name=field_name,
        validation_type=ValidationType.RANGE,
        min_value=min_value,
        max_value=max_value,
        required=required,
        error_message=error_message
    )


def length_field(field_name: str, min_length: Optional[int] = None,
                 max_length: Optional[int] = None, required: bool = False,
                 error_message: Optional[str] = None) -> ValidationRule:
    """Create a length validation rule"""
    return ValidationRule(
        field_name=field_name,
        validation_type=ValidationType.LENGTH,
        min_length=min_length,
        max_length=max_length,
        required=required,
        error_message=error_message
    )


def pattern_field(field_name: str, pattern: str, required: bool = False,
                  error_message: Optional[str] = None) -> ValidationRule:
    """Create a regex pattern validation rule"""
    return ValidationRule(
        field_name=field_name,
        validation_type=ValidationType.PATTERN,
        pattern=pattern,
        required=required,
        error_message=error_message
    )


def custom_field(field_name: str, validator: Callable, required: bool = False,
                 error_message: Optional[str] = None) -> ValidationRule:
    """Create a custom validation rule"""
    return ValidationRule(
        field_name=field_name,
        validation_type=ValidationType.CUSTOM,
        custom_validator=validator,
        required=required,
        error_message=error_message
    )
