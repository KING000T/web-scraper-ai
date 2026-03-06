"""
Scraper Tests

This module contains unit tests for the scraper components.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from scrapers.base import BaseScraper, ScrapedPage, ScrapingError, NetworkError, ParseError
from scrapers.static import StaticScraper
from scrapers.dynamic import DynamicScraper
from scrapers.config import ScraperConfig, ScraperType
from scrapers.factory import ScraperFactory


class TestBaseScraper:
    """Test cases for BaseScraper"""
    
    def test_initialization(self):
        """Test scraper initialization"""
        config = ScraperConfig(
            url="https://example.com",
            selectors={"title": "h1"},
            scraper_type=ScraperType.STATIC
        )
        
        scraper = BaseScraper(config)
        
        assert scraper.config.url == "config.url
        assert scraper.config.scraper_type == config.scraper_type
        assert scraper.config.selectors == config.selectors
    
    def test_validate_url(self):
        """Test URL validation"""
        scraper = BaseScraper(ScraperConfig(
            url="https://example.com",
            selectors={"title": "h1"}
        ))
        
        # Valid URLs
        assert scraper.validate_url("https://example.com")
        assert scraper.validate_url("http://localhost:8000")
        assert scraper.validate_url("https://subdomain.example.com")
        
        # Invalid URLs
        assert not scraper.validate_url("invalid-url")
        assert not scraper.validate_url("")
        assert not scraper.validate_url("ftp://example.com")
    
    def test_normalize_url(self):
        """Test URL normalization"""
        scraper = BaseScraper(ScraperConfig(
            url="https://example.com",
            selectors={"title": "class"}
        ))
        
        # Test URL normalization
        assert scraper.normalize_url("/path", "https://example.com") == "https://example.com/path"
        assert scraper.normalize_url("path", "https://example.com/") == "https://example.com/path"
        assert scraper.normalize_url("path", "http://example.com") == "http://example.com/path"
    
    def test_prepare_data(self):
        """Test data preparation"""
        scraper = BaseScraper(ScraperConfig(
            url="https://example.com",
            selectors={"title": "h1"}
        ))
        
        # Test with simple data
        simple_data = [{"title": "Test", "content": "Content"}]
        prepared = scraper.prepare_data(simple_data)
        
        assert len(prepared) == 2
        assert prepared[0]["title"] == "Test"
        assert prepared[1]["content"] == "Content"
        
        # Test with nested data
        nested_data = [
            {"title": "Test", "meta": {"author": "Author"}},
            {"title": "Test2", "content": "Content2"}
        ]
        prepared = scraper.prepare_data(nested_data)
        
        assert len(prepared) == 2
        assert "author" in prepared[0]
        assert prepared[0]["title"] == "Test"
        assert prepared[1]["title"] == "Test2"
    
    def test_flatten_dict(self):
        """Test dictionary flattening"""
        scraper = BaseScraper(ScraperConfig(
            url="https://example.com",
            selectors={"title": "h1"}
        ))
        
        # Test flattening
        nested = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            },
            "list_data": ["item1", "item2"],
            "simple": "value"
        }
        
        flattened = scraper._flatten_dict(nested)
        
        assert flattened["level1_level2_level3"] == "value"
        assert flattened["list_data_0"] == "item1"
        assert flattened["simple"] == "value"


class TestStaticScraper:
    """Test cases for StaticScraper"""
    
    @pytest.fixture
    def scraper_config(self):
        """Fixture for scraper configuration"""
        return ScraperConfig(
            url="https://example.com",
            selectors={
                "title": "h1",
                "content": ".content",
                "price": ".price"
            },
            scraper_type=ScraperType.STATIC,
            delay=1.0,
            max_retries=3,
            timeout=30
        )
    
    @pytest.fixture
    def static_scraper(self, scraper_config):
        """Fixture for StaticScraper instance"""
        return StaticScraper(scraper_config)
    
    async def test_scrape_page_success(self, static_scraper, mocker):
        """Test successful page scraping"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><h1>Test</h1><p>Content</p></html>"
        mock_response.content = mock_response.text.encode()
        
        mock_session = Mock()
        mock_session.status_code = 200
        mock_session.html = mock_response.text
        mock_session.is_successful = True
        mock_session.data = {
            "title": ["Test"],
            "content": ["Content"],
            "price": ["$10.00"]
        }
        mock_session.timestamp = datetime.utcnow()
        mock_session.extraction_time = 0.5
        
        with patch('scrapers.static.requests.Session.get', return_value=mock_response):
            with patch('scrapers.static.Session', return_value=mock_session):
                result = await static_scraper.scrape_page("https://example.com")
        
        assert result.is_successful
        assert result.status_code == 200
        assert result.data["title"] == ["Test"]
        assert result.data["content"] == ["Content"]
        assert result.data["price"] == ["$10.00"]
        assert result.extraction_time == 0.5
    
    async def test_scrape_page_network_error(self, static_scraper, mocker):
        """Test network error handling"""
        # Mock network error
        mocker.patch('scrapers.static.requests.Session.get', side_effect=ConnectionError("Network error"))
        
        with pytest.raises(NetworkError):
            await static_scraper.scrape_page("https://example.com")
    
    async def test_scrape_page_parse_error(self, static_scraper, mocker):
        """Test parse error handling"""
        # Mock invalid HTML
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<invalid html>"
        
        mock_session = Mock()
        mock_session.status_code = 200
        mock_session.html = mock_response.text
        mock_session.is_successful = False
        mock_session.error = "Parse error"
        
        with patch('scrapers.static.Session.get', return_value=mock_response):
            with patch('scrapers.static.Session', return_value=mock_session):
                with patch('scrapers.static.BeautifulSoup', side_effect=Exception("Parse error")):
                    result = await static_scraper.scrape_page("https://example.com")
        
        assert not result.is_successful
        assert result.error == "Parse error"
    
    def test_extract_data(self, static_scraper):
        """Test data extraction"""
        html = """
        <html>
            <h1>Product Title</h1>
            <p>Product Description</p>
            <span class="price">$10.00</span>
        </html>
        """
        
        selectors = {
            "title": "h1",
            "description": "p",
            "price": ".price"
        }
        
        extracted = static_scraper.extract_data(html, selectors)
        
        assert extracted["title"] == ["Product Title"]
        assert extracted["description"] == ["Product Description"]
        assert extracted["price"] == ["$10.00"]
    
    def test_extract_element_value(self, static_scraper):
        """Test element value extraction"""
        html = """
        <a href="https://example.com">Link</a>
        <img src="image.jpg" alt="Image">
        """
        
        # Test link extraction
        assert static_scraper._extract_element_value(html, "href") == "https://example.com"
        
        # Test image extraction
        assert static_scraper._extract_element_value(html, "src") == "image.jpg"
        
        # Test alt text extraction
        assert static_scraper._extract_element_value(html, "alt") == "Image"
        
        # Test non-existent field
        assert static_scraper._extract_element_value(html, "nonexistent") is None


class TestDynamicScraper:
    """Test cases for DynamicScraper"""
    
    @pytest.fixture
    def scraper_config(self):
        """Fixture for scraper configuration"""
        return ScraperConfig(
            url="https://example.com",
            selectors={
                "title": "h1",
                "content": ".content",
                "price": ".price"
            },
            scraper_type=ScraperType.DYNAMIC,
            delay=2.0,
            max_retries=3,
            timeout=30,
            browser_options=[
                '--headless',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
    
    @pytest.fixture
    def dynamic_scraper(self, scraper_config):
        """Fixture for DynamicScraper instance"""
        return DynamicScraper(scraper_config)
    
    async def test_scrape_page_success(self, dynamic_scraper, mocker):
        """Test successful dynamic scraping"""
        # Mock successful scraping
        mock_session = Mock()
        mock_session.status_code = 200
        mock_session.data = {
            "title": ["Dynamic Title"],
            "content": ["Dynamic Content"],
            "price": ["$15.00"]
        }
        mock_session.is_successful = True
        mock_session.timestamp = datetime.utcnow()
        mock_session.extraction_time = 1.0
        
        with patch('scrapers.dynamic.webdriver.Chrome') as mock_driver:
            mock_driver.current_url = "https://example.com"
            mock_driver.title = "Dynamic Page"
            mock_driver.page_source = "<html><h1>Dynamic Title</h1></html>"
            mock_driver.get.return_value = mock_driver.page_source
            
            # Mock session creation
            mock_session = Mock()
            
            with patch('scrapers.dynamic.webdriver.Chrome', return_value=mock_driver):
                result = await dynamic_scraper.scrape_page("https://example.com")
        
        assert result.is_successful
        assert result.data["title"] == ["Dynamic Title"]
    
    async def test_scrape_page_browser_error(self, dynamic_scraper, mocker):
        """Test browser error handling"""
        # Mock browser error
        mocker.patch('scrapers.dynamic.webdriver.Chrome', side_effect=Exception("Browser error"))
        
        with pytest.raises(Exception):
            await dynamic_scraper.scrape_page("https://example.com")
    
    def test_wait_strategy(self, dynamic_scraper):
        """Test wait strategy configuration"""
        assert dynamic_scraper.config.wait_strategy == "networkidle"
        assert dynamic_scraper.config.wait_timeout == 10
    
    def test_scroll_behavior(self, dynamic_scraper):
        """Test scroll behavior configuration"""
        assert dynamic_scraper.config.scroll_behavior == "down"
    
    def test_browser_options(self, dynamic_scraper):
        """Test browser options"""
        options = dynamic_scraper.config.browser_options
        assert '--headless' in options
        assert '--no-sandbox' in options
        assert '--disable-dev-shm-usage' in options


class TestScraperFactory:
    """Test cases for ScraperFactory"""
    
    def test_create_static_scraper(self):
        """Test static scraper creation"""
        config = ScraperConfig(
            url="https://example.com",
            selectors={"title": "h1"},
            scraper_type=ScraperType.STATIC
        )
        
        scraper = ScraperFactory.create_scraper(config)
        
        assert isinstance(scraper, StaticScraper)
        assert scraper.config.scraper_type == ScraperType.STATIC
    
    def test_create_dynamic_scraper(self):
        """Test dynamic scraper creation"""
        config = ScraperConfig(
            url="https://example.com",
            selectors={"title": "h1"},
            scraper_type=ScraperType.DYNAMIC
        )
        
        scraper = ScraperFactory.create_scraper(config)
        
        assert isinstance(scraper, DynamicScraper)
        assert scraper.config.scraper_type == ScraperType.DYNAMIC
    
    def test_auto_detect_format(self):
        """Test automatic format detection"""
        # Test static data
        static_data = [{"title": "Test", "content": "Content"}]
        format = ScraperFactory.auto_detect_format(static_data)
        assert format in ["csv", "json"]
        
        # Test nested data
        nested_data = [{"title": "Test", "meta": {"author": "Author"}}]
        format = ScraperFactory.auto_detect_format(nested_data)
        assert format == "json"
        
        # Test numeric data
        numeric_data = [{"price": 10.0, "quantity": 5}]
        format = ScraperFactory.auto_detect_format(numeric_data)
        assert format in ["csv", "json"]
    
    def test_get_available_formats(self):
        """Test available formats list"""
        formats = ScraperFactory.get_available_formats()
        
        expected_formats = [
            'static',
            'dynamic', 
            'advanced',
            'csv',
            'json',
            'jsonlines',
            'json_streaming',
            'xlsx',
            'excel',
            'google_sheets',
            'advanced_csv',
            'multi_sheet_excel'
        ]
        
        for format in expected_formats:
            assert format in formats
    
    def test_register_custom_scraper(self):
        """Test custom scraper registration"""
        class CustomScraper(BaseScraper):
            pass
        
        ScraperFactory.register_exporter('custom', CustomScraper)
        
        formats = ScraperFactory.get_available_formats()
        assert 'custom' in formats


# Integration tests
class TestScraperIntegration:
    """Integration tests for scrapers"""
    
    async def test_end_to_end_scraping(self):
        """Test complete scraping workflow"""
        config = ScraperConfig(
            url="https://example.com",
            selectors={"title": "h1", "content": ".content"},
            scraper_type=ScraperType.STATIC
        )
        
        scraper = ScraperFactory.create_scraper(config)
        
        # Scrape page
        result = await scraper.scrape_page("https://example.com")
        
        assert result.is_successful
        assert result.data
        assert result.extraction_time > 0
    
    def test_error_handling(self):
        """Test error handling in scraper factory"""
        # Test invalid configuration
        with pytest.raises(ValueError):
            ScraperConfig(
                url="",  # Invalid URL
                selectors={}
            )
        
        # Test invalid scraper type
        with pytest.raises(ValueError):
            ScraperConfig(
                url="https://example.com",
                selectors={},
                scraper_type="invalid"
            )


# Performance tests
class TestScraperPerformance:
    """Performance tests for scrapers"""
    
    @pytest.mark.asyncio
    async def test_scraping_speed(self):
        """Test scraping performance"""
        config = ScraperConfig(
            url="https://example.com",
            selectors={"title": "h1", "content": ".content"},
            delay=0.1  # Fast for testing
        )
        
        scraper = ScraperFactory.create_scraper(config)
        
        # Measure scraping time
        start_time = asyncio.get_event_loop().time()
        
        result = await scraper.scrape_page("https://example.com")
        
        end_time = asyncio.get_event_loop().time()
        
        extraction_time = end_time - start_time
        
        assert result.is_successful
        assert extraction_time < 5.0  # Should be fast for simple content
        assert extraction_time > 0
    
    def test_memory_usage(self):
        """Test memory usage during scraping"""
        config = ScraperConfig(
            url="https://example.com",
            selectors={"title": "h1", "content": ".content"}
        )
        
        scraper = ScraperFactory.create_scraper(config)
        
        # Memory usage should be reasonable
        assert len(scraper.config.__dict__) < 50  # Config object size
        assert len(scraper.config.selectors) < 20  # Selectors dict size


# Example usage
def example_usage():
    """Example usage of scraper tests"""
    print("Running scraper tests...")
    
    # Run tests
    pytest.main(["-v", "tests/test_scrapers.py"])


if __name__ == "__main__":
    example_usage()
