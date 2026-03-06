"""
Data Cleaner Module

This module implements data cleaning and normalization functionality
for scraped data, including HTML removal, text normalization, and formatting.
"""

import asyncio
import re
import html
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

from .base import BaseProcessor, ProcessingResult, ProcessingError


class DataCleaner(BaseProcessor):
    """Data cleaner for normalizing and cleaning scraped data"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize data cleaner with configuration"""
        super().__init__("DataCleaner")
        self.config = config or {}
        
        # Cleaning options
        self.remove_html = self.config.get('remove_html', True)
        self.normalize_whitespace = self.config.get('normalize_whitespace', True)
        self.remove_special_chars = self.config.get('remove_special_chars', False)
        self.decode_html_entities = self.config.get('decode_html_entities', True)
        self.trim_strings = self.config.get('trim_strings', True)
        self.empty_string_to_null = self.config.get('empty_string_to_null', False)
        
        # Field-specific cleaning rules
        self.field_rules = self.config.get('field_rules', {})
        
        # Compile regex patterns for performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        self.html_tag_pattern = re.compile(r'<[^>]+>')
        self.whitespace_pattern = re.compile(r'\s+')
        self.special_chars_pattern = re.compile(r'[^\w\s\-_.,!?@#$%^&*()]')
        self.url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and normalize data records"""
        if not data:
            return []
        
        cleaned_data = []
        
        for i, record in enumerate(data):
            try:
                cleaned_record = await self._clean_record(record)
                cleaned_data.append(cleaned_record)
                
                self.logger.debug(f"Cleaned record {i+1}/{len(data)}")
                
            except Exception as e:
                self.logger.error(f"Error cleaning record {i+1}: {str(e)}")
                # Keep original record if cleaning fails
                cleaned_data.append(record)
        
        return cleaned_data
    
    async def _clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a single record"""
        cleaned_record = {}
        
        for field_name, value in record.items():
            try:
                # Apply field-specific rules if available
                if field_name in self.field_rules:
                    cleaned_value = await self._apply_field_rules(field_name, value)
                else:
                    cleaned_value = await self._clean_value(value)
                
                cleaned_record[field_name] = cleaned_value
                
            except Exception as e:
                self.logger.warning(f"Error cleaning field '{field_name}': {str(e)}")
                cleaned_record[field_name] = value
        
        return cleaned_record
    
    async def _clean_value(self, value: Any) -> Any:
        """Clean a single value"""
        if value is None:
            return None
        
        if isinstance(value, list):
            # Clean list elements
            return [await self._clean_value(item) for item in value]
        
        if isinstance(value, dict):
            # Clean dictionary values
            return {k: await self._clean_value(v) for k, v in value.items()}
        
        if not isinstance(value, str):
            # Non-string values (numbers, booleans) are returned as-is
            return value
        
        # Start with original string
        cleaned = value
        
        # Decode HTML entities
        if self.decode_html_entities:
            cleaned = html.unescape(cleaned)
        
        # Remove HTML tags
        if self.remove_html:
            cleaned = self.html_tag_pattern.sub('', cleaned)
        
        # Normalize whitespace
        if self.normalize_whitespace:
            cleaned = self.whitespace_pattern.sub(' ', cleaned)
        
        # Remove special characters
        if self.remove_special_chars:
            cleaned = self.special_chars_pattern.sub('', cleaned)
        
        # Trim strings
        if self.trim_strings:
            cleaned = cleaned.strip()
        
        # Handle empty strings
        if self.empty_string_to_null and not cleaned:
            return None
        
        return cleaned
    
    async def _apply_field_rules(self, field_name: str, value: Any) -> Any:
        """Apply field-specific cleaning rules"""
        rules = self.field_rules[field_name]
        
        if not isinstance(rules, dict):
            return await self._clean_value(value)
        
        cleaned_value = value
        
        # Apply type conversion
        if 'type' in rules:
            cleaned_value = await self._convert_type(cleaned_value, rules['type'])
        
        # Apply custom cleaning function
        if 'cleaner' in rules:
            cleaner_func = rules['cleaner']
            if callable(cleaner_func):
                cleaned_value = cleaner_func(cleaned_value)
        
        # Apply default cleaning
        if rules.get('apply_default_cleaning', True):
            cleaned_value = await self._clean_value(cleaned_value)
        
        return cleaned_value
    
    async def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert value to specified type"""
        if value is None:
            return None
        
        try:
            if target_type == 'string':
                return str(value)
            
            elif target_type == 'integer':
                if isinstance(value, str):
                    # Extract number from string
                    number_match = re.search(r'-?\d+', value.replace(',', ''))
                    if number_match:
                        return int(number_match.group())
                return int(value)
            
            elif target_type == 'float':
                if isinstance(value, str):
                    # Extract number from string
                    number_match = re.search(r'-?\d+\.?\d*', value.replace(',', ''))
                    if number_match:
                        return float(number_match.group())
                return float(value)
            
            elif target_type == 'boolean':
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            
            elif target_type == 'url':
                if isinstance(value, str):
                    # Ensure URL has protocol
                    if not value.startswith(('http://', 'https://')):
                        return f'http://{value}'
                return value
            
            elif target_type == 'email':
                if isinstance(value, str):
                    # Convert to lowercase
                    return value.lower().strip()
                return value
            
            else:
                return value
                
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Type conversion failed for value '{value}' to {target_type}: {str(e)}")
            return value
    
    def clean_text(self, text: str) -> str:
        """Clean text string (synchronous version)"""
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        
        cleaned = text
        
        if self.decode_html_entities:
            cleaned = html.unescape(cleaned)
        
        if self.remove_html:
            cleaned = self.html_tag_pattern.sub('', cleaned)
        
        if self.normalize_whitespace:
            cleaned = self.whitespace_pattern.sub(' ', cleaned)
        
        if self.trim_strings:
            cleaned = cleaned.strip()
        
        return cleaned
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        if not isinstance(text, str):
            return []
        
        return self.url_pattern.findall(text)
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        if not isinstance(text, str):
            return []
        
        return self.email_pattern.findall(text)
    
    def remove_duplicates(self, data: List[Dict[str, Any]], key_field: str = None) -> List[Dict[str, Any]]:
        """Remove duplicate records"""
        if not data:
            return []
        
        seen = set()
        unique_data = []
        
        for record in data:
            if key_field and key_field in record:
                # Use specific field for deduplication
                key = record[key_field]
            else:
                # Use entire record for deduplication
                key = tuple(sorted(record.items()))
            
            if key not in seen:
                seen.add(key)
                unique_data.append(record)
        
        return unique_data
    
    def normalize_phone_numbers(self, phone: str) -> str:
        """Normalize phone number format"""
        if not isinstance(phone, str):
            return str(phone) if phone is not None else ""
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle different lengths
        if len(digits) == 10:
            # US format: (XXX) XXX-XXXX
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            # US format with country code: +1 (XXX) XXX-XXXX
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            # Return original format if can't normalize
            return phone
    
    def clean_price(self, price: str) -> Optional[float]:
        """Extract and clean price value"""
        if not isinstance(price, str):
            return float(price) if isinstance(price, (int, float)) else None
        
        # Remove currency symbols and extract number
        price_clean = re.sub(r'[^\d.,]', '', price)
        
        if not price_clean:
            return None
        
        try:
            # Handle different decimal separators
            if ',' in price_clean and '.' in price_clean:
                # Assume comma is thousands separator
                price_clean = price_clean.replace(',', '')
            elif ',' in price_clean and '.' not in price_clean:
                # Assume comma is decimal separator
                price_clean = price_clean.replace(',', '.')
            
            return float(price_clean)
        except ValueError:
            return None
    
    def clean_date(self, date_str: str, output_format: str = '%Y-%m-%d') -> Optional[str]:
        """Clean and standardize date format"""
        if not isinstance(date_str, str):
            return None
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d %b %Y',
            '%d %B %Y',
            '%b %d, %Y',
            '%B %d, %Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S'
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime(output_format)
            except ValueError:
                continue
        
        return None
    
    def get_cleaning_stats(self, original_data: List[Dict[str, Any]], 
                          cleaned_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about cleaning operations"""
        stats = {
            'original_records': len(original_data),
            'cleaned_records': len(cleaned_data),
            'records_removed': len(original_data) - len(cleaned_data),
            'fields_cleaned': 0,
            'null_values_added': 0,
            'empty_strings_removed': 0,
            'html_tags_removed': 0
        }
        
        # Compare original and cleaned data
        for orig_record, clean_record in zip(original_data, cleaned_data):
            for field_name, orig_value in orig_record.items():
                clean_value = clean_record.get(field_name)
                
                if orig_value != clean_value:
                    stats['fields_cleaned'] += 1
                    
                    if orig_value and clean_value is None:
                        stats['null_values_added'] += 1
                    
                    if isinstance(orig_value, str) and orig_value.strip() and not clean_value:
                        stats['empty_strings_removed'] += 1
                    
                    if isinstance(orig_value, str) and '<' in orig_value and '<' not in (clean_value or ''):
                        stats['html_tags_removed'] += 1
        
        return stats


class TextNormalizer:
    """Advanced text normalization utilities"""
    
    @staticmethod
    def normalize_case(text: str, case_type: str = 'title') -> str:
        """Normalize text case"""
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        
        if case_type == 'lower':
            return text.lower()
        elif case_type == 'upper':
            return text.upper()
        elif case_type == 'title':
            return text.title()
        elif case_type == 'sentence':
            return text.capitalize()
        else:
            return text
    
    @staticmethod
    def remove_accents(text: str) -> str:
        """Remove accented characters"""
        import unicodedata
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        
        # Normalize to NFD and remove combining characters
        normalized = unicodedata.normalize('NFD', text)
        return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    
    @staticmethod
    def standardize_punctuation(text: str) -> str:
        """Standardize punctuation marks"""
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        
        # Replace various quotes with standard quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Replace en/em dashes with hyphens
        text = text.replace('–', '-').replace('—', '-')
        
        # Replace ellipsis with three dots
        text = text.replace('...', '...')
        
        return text
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize all whitespace characters"""
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        
        # Replace all whitespace sequences with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        return text.strip()
    
    @staticmethod
    def clean_numeric_text(text: str) -> str:
        """Clean text containing numbers"""
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        
        # Remove common number formatting
        text = re.sub(r'[,]', '', text)  # Remove commas
        text = re.sub(r'[\$€£]', '', text)  # Remove currency symbols
        
        return text.strip()
