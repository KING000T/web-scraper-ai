"""
Dynamic Scraper Module

This module implements dynamic web scraping using browser automation
with Selenium and Playwright for JavaScript-rendered content.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime
from abc import ABC, abstractmethod

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    WebDriverException, StaleElementReferenceException
)

from .base import BaseScraper, ScrapedPage, ScrapingSession, NetworkError, ParseError
from .config import ScraperConfig, BrowserConfig


class DynamicScraper(BaseScraper):
    """Scraper for dynamic JavaScript-rendered content using browser automation"""
    
    def __init__(self, config: ScraperConfig):
        """Initialize dynamic scraper with configuration"""
        super().__init__(config)
        self.driver = None
        self.browser_type = self.config.browser_options.get('browser_type', 'chrome') if isinstance(self.config.browser_options, dict) else 'chrome'
        self._setup_browser()
    
    def _setup_browser(self):
        """Setup browser driver based on configuration"""
        try:
            if self.browser_type.lower() == 'chrome':
                self.driver = self._setup_chrome_driver()
            elif self.browser_type.lower() == 'firefox':
                self.driver = self._setup_firefox_driver()
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")
            
            self.logger.info(f"Initialized {self.browser_type} browser driver")
            
        except Exception as e:
            raise NetworkError(f"Failed to setup browser driver: {str(e)}")
    
    def _setup_chrome_driver(self) -> webdriver.Chrome:
        """Setup Chrome browser driver"""
        options = ChromeOptions()
        
        # Add browser options from config
        if isinstance(self.config.browser_options, list):
            for option in self.config.browser_options:
                options.add_argument(option)
        elif isinstance(self.config.browser_options, dict):
            browser_config = BrowserConfig()
            for option in browser_config.get_options():
                options.add_argument(option)
        else:
            # Default options
            default_options = [
                '--headless',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-javascript',
                '--disable-css'
            ]
            for option in default_options:
                options.add_argument(option)
        
        # Set preferences
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'profile.managed_default_content_settings.images': 2,
            'profile.default_content_settings.popups': 0
        }
        options.add_experimental_option('prefs', prefs)
        
        # Create driver
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.config.timeout)
            driver.implicitly_wait(10)
            return driver
        except Exception as e:
            raise NetworkError(f"Failed to create Chrome driver: {str(e)}")
    
    def _setup_firefox_driver(self) -> webdriver.Firefox:
        """Setup Firefox browser driver"""
        options = FirefoxOptions()
        
        # Add browser options
        if isinstance(self.config.browser_options, list):
            for option in self.config.browser_options:
                options.add_argument(option)
        
        # Set preferences
        options.set_preference('permissions.default.image', 2)
        options.set_preference('dom.popup_maximum', 0)
        options.set_preference('permissions.default.popup', 0)
        
        # Create driver
        try:
            driver = webdriver.Firefox(options=options)
            driver.set_page_load_timeout(self.config.timeout)
            driver.implicitly_wait(10)
            return driver
        except Exception as e:
            raise NetworkError(f"Failed to create Firefox driver: {str(e)}")
    
    async def scrape_page(self, url: str) -> ScrapedPage:
        """Scrape a single dynamic page using browser automation"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Scraping dynamic page: {url}")
            
            # Validate URL
            if not self.validate_url(url):
                raise ValueError(f"Invalid URL: {url}")
            
            # Navigate to page
            await self._navigate_to_page(url)
            
            # Wait for content to load
            await self._wait_for_content()
            
            # Handle scrolling if needed
            await self._handle_scroll_behavior()
            
            # Extract HTML
            html = self.driver.page_source
            
            # Parse HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract data
            extracted_data = await self._extract_data_from_soup(soup)
            
            # Extract metadata
            metadata = await self._extract_dynamic_metadata()
            
            # Create scraped page
            page = ScrapedPage(
                url=url,
                data=extracted_data,
                status_code=200,  # Selenium doesn't easily provide status codes
                html=html,
                extraction_time=time.time() - start_time,
                metadata=metadata
            )
            
            self.logger.info(
                f"Successfully scraped dynamic page {url} - "
                f"Records: {page.record_count}, "
                f"Time: {page.extraction_time:.2f}s"
            )
            
            return page
            
        except Exception as e:
            error_msg = f"Error scraping dynamic page {url}: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, url)
    
    async def _navigate_to_page(self, url: str):
        """Navigate to the specified URL"""
        try:
            self.driver.get(url)
            
            # Check if navigation was successful
            current_url = self.driver.current_url
            if "about:blank" in current_url or "chrome-error:" in current_url:
                raise NetworkError(f"Failed to navigate to {url}")
            
        except TimeoutException:
            self.logger.warning(f"Page load timeout for {url}, continuing anyway")
        except WebDriverException as e:
            raise NetworkError(f"WebDriver error navigating to {url}: {str(e)}")
    
    async def _wait_for_content(self):
        """Wait for dynamic content to load based on strategy"""
        wait_strategy = getattr(self.config, 'wait_strategy', 'networkidle')
        wait_timeout = getattr(self.config, 'wait_timeout', 10)
        
        try:
            if wait_strategy == 'networkidle':
                # Wait for network to be idle
                await self._wait_for_network_idle(wait_timeout)
            elif wait_strategy == 'domcontentloaded':
                # Wait for DOM content to be loaded
                WebDriverWait(self.driver, wait_timeout).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            elif wait_strategy == 'manual':
                # Wait for specific elements based on selectors
                await self._wait_for_elements(wait_timeout)
            else:
                # Default wait
                time.sleep(2)
                
        except TimeoutException:
            self.logger.warning(f"Content loading timeout after {wait_timeout} seconds")
        except Exception as e:
            self.logger.warning(f"Error waiting for content: {str(e)}")
    
    async def _wait_for_network_idle(self, timeout: int):
        """Wait for network to be idle (no active requests)"""
        try:
            # Use JavaScript to check for active XHR/fetch requests
            script = """
            return window.XMLHttpRequest ? 
                (window.XMLHttpRequest.readyState || 0) === 0 : true;
            """
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    is_idle = self.driver.execute_script(script)
                    if is_idle:
                        break
                except:
                    pass
                await asyncio.sleep(0.5)
                
        except Exception as e:
            self.logger.warning(f"Network idle check failed: {str(e)}")
    
    async def _wait_for_elements(self, timeout: int):
        """Wait for specific elements to be present"""
        if not self.config.selectors:
            return
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            
            # Wait for at least one selector to be present
            for selector in self.config.selectors.values():
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Element waiting failed: {str(e)}")
    
    async def _handle_scroll_behavior(self):
        """Handle scrolling behavior based on configuration"""
        scroll_behavior = getattr(self.config, 'scroll_behavior', 'none')
        
        try:
            if scroll_behavior == 'down':
                await self._scroll_down()
            elif scroll_behavior == 'up':
                await self._scroll_up()
            elif scroll_behavior == 'multiple':
                await self._scroll_multiple()
            elif scroll_behavior == 'infinite':
                await self._handle_infinite_scroll()
                
        except Exception as e:
            self.logger.warning(f"Scroll behavior failed: {str(e)}")
    
    async def _scroll_down(self):
        """Scroll down to the bottom of the page"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        await asyncio.sleep(1)  # Wait for content to load
    
    async def _scroll_up(self):
        """Scroll up to the top of the page"""
        self.driver.execute_script("window.scrollTo(0, 0);")
        await asyncio.sleep(1)
    
    async def _scroll_multiple(self):
        """Scroll through the page in multiple steps"""
        scroll_height = self.driver.execute_script("return document.body.scrollHeight")
        viewport_height = self.driver.execute_script("return window.innerHeight")
        
        steps = max(1, scroll_height // viewport_height)
        for i in range(steps + 1):
            scroll_position = i * viewport_height
            self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            await asyncio.sleep(0.5)
    
    async def _handle_infinite_scroll(self):
        """Handle infinite scroll by scrolling until no new content loads"""
        last_height = 0
        max_scrolls = 10  # Prevent infinite loops
        scroll_count = 0
        
        while scroll_count < max_scrolls:
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(2)
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            
            last_height = new_height
            scroll_count += 1
    
    async def _extract_data_from_soup(self, soup) -> Dict[str, Any]:
        """Extract data using CSS selectors from BeautifulSoup"""
        extracted_data = {}
        
        for field_name, selector in self.config.selectors.items():
            try:
                elements = soup.select(selector)
                
                if not elements:
                    self.logger.warning(f"No elements found for selector '{selector}' (field: {field_name})")
                    extracted_data[field_name] = []
                    continue
                
                # Extract data from elements
                field_data = []
                
                for element in elements:
                    value = self._extract_element_value(element)
                    if value is not None:
                        field_data.append(value)
                
                extracted_data[field_name] = field_data
                self.logger.debug(f"Extracted {len(field_data)} values for field '{field_name}'")
                
            except Exception as e:
                self.logger.error(f"Error extracting field '{field_name}': {str(e)}")
                extracted_data[field_name] = []
        
        return extracted_data
    
    def _extract_element_value(self, element) -> Optional[str]:
        """Extract value from HTML element (same as static scraper)"""
        if not element:
            return None
        
        # Handle different element types
        if element.name == 'a':
            href = element.get('href')
            text = element.get_text(strip=True)
            if href:
                return href
            return text if text else None
        
        elif element.name == 'img':
            src = element.get('src')
            alt = element.get('alt')
            if src:
                return src
            return alt if alt else None
        
        else:
            # For other elements, extract text content
            text = element.get_text(strip=True)
            if text:
                return text
            
            # If no text, try to extract from attributes
            for attr in ['href', 'src', 'value', 'content', 'alt', 'title']:
                value = element.get(attr)
                if value:
                    return value
        
        return None
    
    async def _extract_dynamic_metadata(self) -> Dict[str, Any]:
        """Extract metadata specific to dynamic pages"""
        metadata = {}
        
        try:
            # Current URL (might be different from start URL due to redirects)
            metadata['current_url'] = self.driver.current_url
            metadata['window_title'] = self.driver.title
            
            # Page dimensions
            metadata['page_dimensions'] = self.driver.execute_script("""
                return {
                    width: window.innerWidth,
                    height: window.innerHeight,
                    scroll_width: document.documentElement.scrollWidth,
                    scroll_height: document.documentElement.scrollHeight
                };
            """)
            
            # Check for JavaScript errors
            logs = self.driver.get_log('browser')
            if logs:
                metadata['browser_logs'] = logs[-5:]  # Last 5 log entries
            
            # Check for console errors
            try:
                console_logs = self.driver.get_log('console')
                if console_logs:
                    metadata['console_errors'] = [log for log in console_logs if log['level'] == 'SEVERE']
            except:
                pass
            
            # Performance metrics
            try:
                metrics = self.driver.execute_script("""
                    if (window.performance && window.performance.timing) {
                        var timing = window.performance.timing;
                        return {
                            load_time: timing.loadEventEnd - timing.navigationStart,
                            dom_ready: timing.domContentLoadedEventEnd - timing.navigationStart
                        };
                    }
                    return null;
                """)
                if metrics:
                    metadata['performance_metrics'] = metrics
            except:
                pass
            
        except Exception as e:
            self.logger.warning(f"Error extracting dynamic metadata: {str(e)}")
        
        return metadata
    
    def extract_data(self, html: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data from HTML using provided selectors"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            return asyncio.run(self._extract_data_from_soup(soup))
        except Exception as e:
            self.logger.error(f"Error extracting data: {str(e)}")
            return {}
    
    async def execute_javascript(self, script: str) -> Any:
        """Execute JavaScript in the browser context"""
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            self.logger.error(f"JavaScript execution failed: {str(e)}")
            return None
    
    async def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot of the current page"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            self.driver.save_screenshot(filename)
            self.logger.info(f"Screenshot saved: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Screenshot failed: {str(e)}")
            raise
    
    async def wait_for_element(self, selector: str, timeout: int = 10) -> bool:
        """Wait for a specific element to appear"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return True
        except TimeoutException:
            return False
    
    async def click_element(self, selector: str, wait: bool = True) -> bool:
        """Click an element by CSS selector"""
        try:
            if wait:
                if not await self.wait_for_element(selector):
                    return False
            
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            await asyncio.sleep(0.5)
            
            # Click the element
            element.click()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to click element '{selector}': {str(e)}")
            return False
    
    def close(self):
        """Close the browser and clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser driver closed")
            except Exception as e:
                self.logger.error(f"Error closing browser driver: {str(e)}")
            finally:
                self.driver = None
    
    def __del__(self):
        """Cleanup when scraper is destroyed"""
        try:
            self.close()
        except:
            pass


class PlaywrightScraper(DynamicScraper):
    """Alternative dynamic scraper using Playwright (more modern than Selenium)"""
    
    def __init__(self, config: ScraperConfig):
        """Initialize Playwright scraper"""
        super().__init__(config)
        # Note: This would require playwright installation
        # Implementation would use playwright's async API
        self.logger.warning("Playwright scraper not fully implemented yet")
    
    async def scrape_page(self, url: str) -> ScrapedPage:
        """Scrape page using Playwright (placeholder implementation)"""
        # This would be implemented with playwright's async API
        self.logger.info("Playwright scraping not yet implemented, falling back to Selenium")
        return await super().scrape_page(url)
