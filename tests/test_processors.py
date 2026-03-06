"""
Processor Tests

This module contains unit tests for the data processing components.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime
from typing import List, Dict, Any

from processors.base import BaseProcessor, ProcessingResult, ProcessingError
from processors.cleaner import DataCleaner
from processors.validator import DataValidator, ValidationRule, required_field, email_field
from processors.transformer import DataTransformer, map_field, calculate_field
from processors.pipeline import DataProcessingPipeline
from processors.quality import DataQualityChecker, create_data_quality_checker

from scrapers.base import ScrapedPage


class TestDataCleaner:
    """Test cases for DataCleaner"""
    
    @pytest.fixture
    def cleaner_config(self):
        """Fixture for cleaner configuration"""
        return {
            'remove_html': True,
            'normalize_whitespace': True,
            'decode_html_entities': True,
            'trim_strings': True,
            'empty_string_to_null': False
        }
    
    @pytest.fixture
    def data_cleaner(self, cleaner_config):
        """Fixture for DataCleaner instance"""
        return DataCleaner(cleaner_config)
    
    def test_clean_text(self, data_cleaner):
        """Test text cleaning"""
        dirty_text = "  <div>  <p>   Content with  spaces  </p>  </div>  "
        
        cleaned = data_cleaner.clean_text(dirty_text)
        
        assert "Content with spaces" == cleaned
        assert cleaned_text.strip() == "Content with spaces"
    
    def test_remove_html_tags(self, data_cleaner):
        """Test HTML tag removal"""
        html_content = "<div><h1>Title</h1><p>Content</p></div>"
        
        cleaned = data_cleaner.clean_text(html_content)
        
        assert "<h1>" not in cleaned
        assert "Title" in cleaned
        assert "Content" in cleaned
    
    def test_normalize_whitespace(self, data_cleaner):
        """Test whitespace normalization"""
        text_with_spaces = "  Multiple    spaces   here  "
        
        normalized = data_cleaner.clean_text(text_with_spaces)
        
        assert normalized == "Multiple spaces here"
    
    def test_decode_html_entities(self, data_cleaner):
        """Test HTML entity decoding"""
        text_with_entities = "Hello &amp; World &quot; Test"
        
        decoded = data_cleaner.clean_text(text_with_entities)
        
        assert decoded == "Hello & World " Test"
    
    def test_trim_strings(self, data_cleaner):
        """Test string trimming"""
        text_with_spaces = "  Content with spaces  "
        
        trimmed = data_cleaner.clean_text(text_with_spaces)
        
        assert trimmed == "Content with spaces"
        assert trimmed.strip() == "Content with spaces"
    
    def test_empty_string_handling(self, data_cleaner):
        """Test empty string handling"""
        empty_string = ""
        non_empty_string = "Non-empty string"
        
        # Test with empty_string_to_null=False
        result_empty = data_cleaner.clean_text(empty_string)
        result_non_empty = data_cleaner.clean_text(non_empty_string)
        
        assert result_empty == ""
        assert result_non_empty == "Non-empty string"
        
        # Test with empty_string_to_null=True
        cleaner_with_null = DataCleaner({'empty_string_to_null': True})
        
        assert cleaner_with_null.clean_text(empty_string) is None
        assert cleaner_with_null.clean_text(non_empty_string) == "Non-empty string"


class TestDataValidator:
    """Test cases for DataValidator"""
    
    @pytest.fixture
    def validation_rules(self):
        """Fixture for validation rules"""
        return [
            required_field('name', 'Name is required'),
            email_field('email', 'Email is required'),
            price_field('price', 'Price must be numeric'),
            rating_field('rating', 'Rating must be numeric')
        ]
    
    @pytest.fixture
    def data_validator(self, validation_rules):
        """Fixture for DataValidator instance"""
        return DataValidator(validation_rules)
    
    def test_required_field_validation(self, data_validator):
        """Test required field validation"""
        # Valid data
        valid_data = [
            {"name": "Test", "email": "test@example.com"},
            {"name": "Test", "email": "test@example.com", "price": 10.0}
        ]
        
        result = data_validator.process(valid_data)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_required_field_validation_missing(self, data_validator):
        """Test required field validation with missing field"""
        invalid_data = [
            {"email": "test@example.com"},  # Missing 'name'
            {"name": "Test", "email": "test@example.com", "price": 10.0}  # Missing 'name'
        ]
        
        result = data_validator.process(invalid_data)
        
        assert not result.is_valid
        assert len(result.errors) == 2
        assert any("Name is required" in error.message for error in result.errors)
    
    def test_email_validation(self, data_validator):
        """Test email field validation"""
        # Valid emails
        valid_emails = [
            {"email": "test@example.com"},
            {"email": "user@domain.com"},
            {"email": "test.email@domain.co.uk"}
        ]
        
        for email_data in valid_emails:
            result = data_validator.process(email_data)
            assert result.is_valid
        
        # Invalid emails
        invalid_emails = [
            {"email": "invalid-email"},
            {"email": "test@"},
            {"email": "@domain.com"},  # Missing domain
            {"email": "test@.@@.@"}  # Invalid format
        ]
        
        for email_data in invalid_emails:
            result = data_validator.process(email_data)
            assert not result.is_valid
            assert "Invalid email format" in error.message for error in result.errors
    
    def test_numeric_validation(self, data_validator):
        """Test numeric field validation"""
        # Valid numbers
        valid_numbers = [
            {"price": 10.0},
            {"price": 25.50},
            {"quantity": 5},
            {"rating": 4.5}
        ]
        
        for number_data in valid_numbers:
            result = data_validator.process(number_data)
            assert result.is_valid
        
        # Invalid numbers
        invalid_numbers = [
            {"price": "ten dollars"},
            {"price": "10.5.5"},
            {"quantity": "five"},
            {"rating": "four point five"}
        ]
        
        for number_data in invalid_numbers:
            result = data_validator.process(number_data)
            assert not result.is_valid
            assert "Invalid number format" in error.message for error in result.errors
    
    def test_validation_result_merge(self, data_validator):
        """Test validation result merging"""
        # Create two validation results
        result1 = data_validator.process([
            {"name": "Test", "email": "test@example.com"}
        ])
        
        result2 = data_validator.process([
            {"price": 10.0}
        ])
        
        # Merge results
        result1.merge(result2)
        
        assert len(result1.errors) == 0
        assert result1.is_valid
        assert len(result1.warnings) == 0
    
    def test_field_results(self, data_validator):
        """Test field-level validation results"""
        data = [
            {"name": "Test", "email": "test@example.com"},
            {"name": "Test", "email": "test@example.com", "price": 10.0}
        ]
        
        result = data_validator.process(data)
        
        # Check field results
        assert result.field_results.get('name') == True
        assert result.field_results.get('email') == True
        result.field_results.get('price') == True
        assert len(result.field_results) == 3
    
    def test_validation_errors(self, data_validator):
        """Test validation error messages"""
        data = [
            {"name": "", "email": "test@example.com"},  # Missing required field
            {"name": "Test", "email": "invalid-email"}  # Invalid email format
            {"name": "Test", "price": "expensive"}  # Invalid number format
        ]
        
        result = data_validator.process(data)
        
        assert not result.is_valid
        assert len(result.errors) == 3
        assert any("Name is required" in error.message for error in result.errors)
        assert "Invalid email format" in error.message for error in result.errors)
        assert "Invalid number format" in error.message for error in result.errors


class TestDataTransformer:
    """Test cases for DataTransformer"""
    
    @pytest.fixture
    def transformer_config(self):
        """Fixture for transformer configuration"""
        return {
            "transformations": [
                map_field('title', lambda x: x.upper() if isinstance(x, str) else str(x)),
                calculate_field('price', lambda x: float(x) * 1.1 if isinstance(x, (int, float)) else x),
                calculate_field('rating', lambda x: min(5.0, float(x) if isinstance(x, (int, float)) else x))
            ]
        }
    
    @pytest.fixture
    def data_transformer(self, transformer_config):
        """Fixture for DataTransformer instance"""
        return DataTransformer(transformer_config)
    
    def test_field_mapping(self, data_transformer):
        """Test field mapping transformation"""
        data = [
            {"title": "product title", "brand": "brand"},
            {"price": "price", "amount": 100},
            "rating": "rating": 4.5}
        ]
        
        result = data_transformer.process(data)
        
        # Check mapped fields
        assert result[0]['title'] == "PRODUCT TITLE"
        assert result[0]['brand'] == "BRAND"
        assert result[0]['amount'] == 110.0
        assert result[0]['rating'] == 5.0
    
    def calculate_field_value(self, data_transformer):
        """Test calculation transformation"""
        # Test price calculation
        price_data = [{"price": 100}, {"price": 50}, {"price": "25}]
        
        result = data_transformer.process(price_data)
        
        assert result[0]['amount'] == 110.0  # 100 * 1.1
        assert result[1]['amount'] == 55.0   # 50 * 1.1
        assert result[2]['amount'] == 27.5   # 25 * 1.1
    
    def test_conditional_transformation(self, data_transformer):
        """Test conditional transformation"""
        data = [
            {"price": 100, "category": "electronics"},
            {"price": 50, "category": "books"},
            {"price": 25, "category": "books"}
        ]
        
        # Add conditional transformation
        conditional_transformer = DataTransformer([
            calculate_field('price', lambda x: x * 1.2 if x < 50 else x),
            map_field('category', lambda x: x.upper())
        ])
        
        result = conditional_transformer.process(data)
        
        assert result[0]['amount'] == 120.0  # 100 * 1.2
        assert result[0]['category'] == "ELECTRONICS"  # electronics
        assert result[1]['amount'] == 60.0   # 50 * 1.2
        assert result[2]['amount'] == 30.0   # 25 * 1.2
    
    def test_concatenation_transformation(self, data_transformer):
        """Test concatenation transformation"""
        data = [
            {"first_name": "John", "last_name": "Doe"},
            {"first_name": "Jane", "last_name": "Smith"},
            {"first_name": "Bob", "last_name": "Johnson"}
        ]
        
        concat_transformer = DataTransformer([
            map_field('full_name', lambda x: f"{x['first_name']} {x['last_name']}")
        ])
        
        result = concat_transformer.process(data)
        
        assert result[0]['full_name'] == "John Doe"
        assert result[1]['full_name'] == "Jane Smith"
        assert result[2]['full_name'] == "Bob Johnson"
    
    def test_split_transformation(self, data_transformer):
        """Test split transformation"""
        data = [
            {"full_name": "John Doe", "tags": "python,data,python,automation"},
            {"full_name": "Jane Smith", "tags": "python,data,automation"}
        ]
        
        split_transformer = DataTransformer([
            split_field('tags', separator=',')
        ])
        
        result = split_transformer.process(data)
        
        assert result[0]['tags'] == ["python", "data", "automation"]
        assert result[1]['tags'] == ["python", "data", "automation"]
    
    def test_format_transformation(self, data_transformer):
        """Test format transformation"""
        data = [
            {"name": "test", "created_at": "2023-01-01T12:00:00"},
            {"name": "test", "created_at": "2023-01-02T12:00:00"}
        ]
        
        format_transformer = DataTransformer([
            calculate_field('created_at', lambda x: datetime.fromisoformat(x).strftime('%Y-%m-%d'))
        ])
        
        result = format_transformer.process(data)
        
        assert isinstance(result[0]['created_at'], datetime)
        assert result[1]['created_at'].year == 2023
        assert result[0]['created_at'].month == 1
        assert result[1]['created_at'].day == 1


class TestDataQualityChecker:
    """Test cases for DataQualityChecker"""
    
    @pytest.fixture
    def quality_checker(self):
        """Fixture for DataQualityChecker instance"""
        return create_data_quality_checker()
    
    def test_completeness_score(self, quality_checker):
        """Test completeness scoring"""
        # Test complete data
        complete_data = [
            {"name": "Test", "email": "test@example.com", "price": 10.0},
            {"name": "Test", "email": "test@example.com", "price": 10.0},
            {"name": "Test", "email": "test@example.com", "price": 10.0}
        ]
        
        score = quality_checker.calculate_completeness(complete_data)
        
        assert score == 100.0
        
        # Test incomplete data
        incomplete_data = [
            {"name": "Test", "email": "test@example.com"},  # Missing price
            {"name": "Test", "email": "test@example.com", "price": 10.0}
        ]
        
        score = quality_checker.calculate_completeness(incomplete_data)
        assert score < 100.0
        assert score == 66.7  # 2 out of 3 fields present
    
    def test_consistency_score(self, quality_checker):
        """Test consistency scoring"""
        # Consistent data
        consistent_data = [
            {"name": "Test", "brand": "Apple", "category": "Electronics"},
            {"name": "Test", "brand": "Apple", "category": "Electronics"},
            {"name": "Test", "brand": "Apple", "category": "Electronics"}
        ]
        
        score = quality_checker.calculate_consistency(consistent_data)
        
        assert score == 100.0
        
        # Inconsistent data
        inconsistent_data = [
            {"name": "Test", "brand": "Apple", "category": "Electronics"},
            {"name": "Test", "brand": "Samsung", "category": "Electronics"},
            {"name": "Test", "brand": "Sony", "category": "Electronics"}
        ]
        
        score = quality_checker.calculate_consistency(inconsistent_data)
        assert score < 100.0
        assert score == 66.7  # 2 out of 3 brands match
        
    def test_uniqueness_score(self, quality_checker):
        """Test uniqueness scoring"""
        # Unique data
        unique_data = [
            {"name": "Test1", "email": "test1@example.com"},
            {"name": "Test2", "email": "test2@example.com"},
            {"name": "Test3", "email": "test3@example.com"}
        ]
        
        score = quality_checker.calculate_uniqueness(unique_data)
        
        assert score == 100.0
        
        # Duplicate data
        duplicate_data = [
            {"name": "Test", "email": "test@example.com"},
            {"name": "Test", "email": "test@example.com"},
            {"name": "Test", "email": "test@example.com"}
        ]
        
        score = quality_checker.calculate_uniqueness(duplicate_data)
        assert score == 33.3  # 1 out of 3 unique
        
    def test_data_quality_score(self, quality_checker):
        """Test overall data quality scoring"""
        # High quality data
        high_quality_data = [
            {
                "name": "Test Product",
                "email": "test@example.com",
                "price": 29.99,
                "rating": 4.5,
                "brand": "Apple",
                "availability": "In Stock",
                "description": "High-quality product"
            }
        ]
        
        score = quality_checker.calculate_data_quality_score(high_quality_data)
        
        assert score >= 90.0
        
        # Low quality data
        low_quality_data = [
            {
                "name": "",  # Missing name
                "email": "invalid-email",  # Invalid email
                "price": "expensive",  # Invalid number
                "rating": 0.0, # Invalid rating
                "brand": "",  # Missing brand
                "availability": "unknown",  # Unknown status
                "description": ""  # Missing description
            }
        ]
        
        score = quality_checker.calculate_data_quality_score(low_quality_data)
        assert score < 50.0
    
    def get_quality_report(self, quality_checker):
        """Get comprehensive quality report"""
        # Test with sample data
        sample_data = [
            {
                "name": "Test Product",
                "email": "test@example.com",
                "price": 29.99,
                "rating": 4.5,
                "brand": "Apple",
                "availability": "In Stock",
                "description": "High-quality product"
            }
        ]
        
        report = quality_checker.get_quality_report(sample_data)
        
        assert report['overall_score'] >= 90.0
        assert len(report['issues']) == 0
        assert len(report['recommendations']) >= 0
        assert report['record_count'] == 1
        assert report['field_count'] == 7
    
    def test_field_coverage(self, quality_checker):
        """Test field coverage calculation"""
        # Data with good coverage
        good_data = [
            {
                "name": "Test Product",
                "email": "test@example.com",
                "price": 29.99,
                "rating": 4.5,
                "brand": "Apple",
                "availability": "In Stock",
                "description": "High-quality product"
            }
        ]
        
        coverage = quality_checker._calculate_field_coverage([good_data])
        
        assert coverage == 100.0
        
        # Data with poor coverage
        poor_data = [
            {"name": "Test Product"},
            {"price": "29.99"},
            {"rating": "4.5"}
        ]
        
        coverage = quality_checker._calculate_field_coverage(poor_data)
        assert coverage < 100.0
        assert coverage == 33.3  # 1 out of 3 fields present


def create_data_quality_checker():
    """Create a DataQualityChecker instance for testing"""
    return DataQualityChecker({
        'thresholds': {
            'completeness': 0.8,
            'accuracy': 0.9,
            'consistency': 0.85,
            'validity': 0.9,
            'uniqueness': 0.95
        }
    })


# Integration tests
class TestProcessorIntegration:
    """Integration tests for data processing"""
    
    @pytest.fixture
    def processing_pipeline(self):
        """Fixture for processing pipeline"""
        pipeline = DataProcessingPipeline()
        
        # Add processors
        from processors.cleaner import DataCleaner
        from processors.validator import DataValidator
        from processors.transformer import DataTransformer
        
        pipeline.add_processor(DataCleaner({
            'remove_html': True,
            'normalize_whitespace': True
        }))
        
        pipeline.add_processor(DataValidator([
            required_field('name'),
            email_field('email'),
            price_field('price')
        ]))
        
        pipeline.add_processor(DataTransformer([
            map_field('price', lambda x: float(x) if x else 0),
            calculate_field('rating', lambda x: float(x) if x else 0)
        ]))
        
        return pipeline
    
    async def test_end_to_end_processing(self, processing_pipeline):
        """Test complete processing workflow"""
        # Test data with all processors
        test_data = [
            {
                "name": "Test Product",
                "email": "test@example.com",
                "price": 29.99,
                "rating": 4.5,
                "brand": "Apple",
                "availability": "In Stock",
                "description": "High-quality product"
            },
            {
                "name": "Another Product",
                "email": "another@example.com",
                "price": 19.99,
                "rating": 3.5,
                "brand": "Samsung",
                "availability": "Out of Stock",
                "description": "Budget product"
            }
        ]
        
        processed_data = await processing_pipeline.process(test_data)
        
        assert len(processed_data) == 2
        assert processed_data[0]['name'] == "TEST PRODUCT"  # Uppercase due to cleaning
        assert processed_data[0]['email'] == "test@example.com"  # Uppercase due to cleaning
        assert processed_data[0]['price'] == 29.99  # Uppercase due to cleaning
        assert processed_data[0]['rating'] == 4.5  # Uppercase due to cleaning
        assert processed_data[0]['brand'] == "APPLE"  # Uppercase due to cleaning
        
        # Check processed data quality
        from processors.quality import DataQualityChecker
        quality_checker = create_data_quality_checker()
        score = quality_checker.calculate_data_quality_score(processed_data)
        
        assert score >= 90.0


# Example usage
def example_usage():
    """Example usage of processor tests"""
    print("Running processor tests...")
    
    # Run tests
    pytest.main(["-v", "tests/test_processors.py"])
    
    print("Processor tests completed")


if __name__name__main__":
    example_usage()
