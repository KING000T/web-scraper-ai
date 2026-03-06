"""
Static Scraper Module

This module implements static HTML scraping using requests and BeautifulSoup.
It handles traditional websites without JavaScript rendering requirements.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup, Tag
import logging
from datetime import datetime

from .base import BaseScraper, ScrapedPage, ScrapingSession, NetworkError, ParseError
from .config import ScraperConfig


class StaticScraper(BaseScraper):
    """Scraper for static HTML content using requests and BeautifulSoup"""
    
    def __init__(self, config: ScraperConfig):
        """Initialize static scraper with configuration"""
        super().__init__(config)
        self.session = self._create_session()
        self._setup_session()
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with configuration"""
        session = requests.Session()
        
        # Set default headers
        default_headers = {
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        session.headers.update(default_headers)
        
        # Add custom headers
        if self.config.headers:
            session.headers.update(self.config.headers)
        
        # Set up authentication
        if self.config.auth:
            session.auth = self.config.auth
        
        # Set up proxy
        if self.config.proxy:
            session.proxies = {
                'http': self.config.proxy,
                'https': self.config.proxy
            }
            
            if self.config.proxy_auth:
                session.proxies.update({
                    'http': f"http://{self.config.proxy_auth[0]}:{self.config.proxy_auth[1]}@{self.config.proxy.replace('http://', '')}",
                    'https': f"http://{self.config.proxy_auth[0]}:{self.config.proxy_auth[1]}@{self.config.proxy.replace('https://', '')}"
                })
        
        return session
    
    def _setup_session(self):
        """Configure session settings"""
        # Set timeout
        self.session.timeout = (self.config.timeout, self.config.timeout + 10)
        
        # Configure retries
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    async def scrape_page(self, url: str) -> ScrapedPage:
        """Scrape a single static HTML page"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Scraping static page: {url}")
            
            # Validate URL
            if not self.validate_url(url):
                raise ValueError(f"Invalid URL: {url}")
            
            # Make HTTP request
            response = await self._make_request(url)
            
            # Parse HTML
            soup = await self._parse_html(response.text)
            
            # Extract data
            extracted_data = await self._extract_data_from_soup(soup)
            
            # Extract metadata
            metadata = await self._extract_metadata(soup, response)
            
            # Create scraped page
            page = ScrapedPage(
                url=url,
                data=extracted_data,
                status_code=response.status_code,
                html=response.text,
                extraction_time=time.time() - start_time,
                metadata=metadata
            )
            
            self.logger.info(
                f"Successfully scraped {url} - "
                f"Status: {response.status_code}, "
                f"Records: {page.record_count}, "
                f"Time: {page.extraction_time:.2f}s"
            )
            
            return page
            
        except requests.RequestException as e:
            error_msg = f"Network error scraping {url}: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(NetworkError(error_msg), url)
        
        except Exception as e:
            error_msg = f"Error scraping {url}: {str(e)}"
            self.logger.error(error_msg)
            return self.handle_error(e, url)
    
    async def _make_request(self, url: str) -> requests.Response:
        """Make HTTP request with error handling"""
        try:
            response = self.session.get(url, allow_redirects=True)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout as e:
            raise NetworkError(f"Request timeout for {url}: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection error for {url}: {str(e)}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limited for {url}: {str(e)}")
            elif e.response.status_code >= 500:
                raise NetworkError(f"Server error for {url}: {str(e)}")
            else:
                raise NetworkError(f"HTTP error for {url}: {str(e)}")
    
    async def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup"""
        try:
            # Try different parsers in order of preference
            parsers = ['lxml', 'html.parser', 'html5lib']
            
            for parser in parsers:
                try:
                    soup = BeautifulSoup(html, parser)
                    # Test if parsing was successful
                    if soup.find('html') or soup.find('body') or soup.contents:
                        self.logger.debug(f"Successfully parsed HTML using {parser}")
                        return soup
                except Exception as e:
                    self.logger.warning(f"Parser {parser} failed: {str(e)}")
                    continue
            
            # Fallback to default parser
            soup = BeautifulSoup(html, 'html.parser')
            return soup
            
        except Exception as e:
            raise ParseError(f"Failed to parse HTML: {str(e)}")
    
    async def _extract_data_from_soup(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data using CSS selectors"""
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
    
    def _extract_element_value(self, element: Tag) -> Optional[str]:
        """Extract value from HTML element"""
        if not element:
            return None
        
        # Handle different element types
        if element.name == 'a':
            # For links, extract href and text
            href = element.get('href')
            text = element.get_text(strip=True)
            if href:
                return href
            return text if text else None
        
        elif element.name == 'img':
            # For images, extract src and alt
            src = element.get('src')
            alt = element.get('alt')
            if src:
                return src
            return alt if alt else None
        
        elif element.name in ['input', 'textarea', 'select']:
            # For form elements
            if element.name == 'input':
                value = element.get('value')
                return value if value else element.get('placeholder')
            elif element.name == 'textarea':
                return element.get_text(strip=True)
            elif element.name == 'select':
                selected_option = element.find('option', selected=True)
                if selected_option:
                    return selected_option.get_text(strip=True)
                return None
        
        elif element.name in ['meta', 'link']:
            # For metadata elements
            if element.name == 'meta':
                content = element.get('content')
                name = element.get('name') or element.get('property')
                return content if content else name
            elif element.name == 'link':
                return element.get('href')
        
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
    
    async def _extract_metadata(self, soup: BeautifulSoup, response: requests.Response) -> Dict[str, Any]:
        """Extract metadata from the page"""
        metadata = {}
        
        try:
            # Basic page information
            metadata['title'] = soup.title.get_text(strip=True) if soup.title else None
            metadata['url'] = response.url
            metadata['status_code'] = response.status_code
            metadata['content_type'] = response.headers.get('content-type')
            metadata['content_length'] = len(response.content)
            
            # Meta tags
            meta_tags = {}
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    meta_tags[name] = content
            
            metadata['meta_tags'] = meta_tags
            
            # Links
            if self.config.extract_links:
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = self.normalize_url(href, response.url)
                    links.append({
                        'url': full_url,
                        'text': link.get_text(strip=True),
                        'title': link.get('title')
                    })
                metadata['links'] = links
            
            # Images
            if self.config.extract_images:
                images = []
                for img in soup.find_all('img', src=True):
                    src = img['src']
                    full_url = self.normalize_url(src, response.url)
                    images.append({
                        'url': full_url,
                        'alt': img.get('alt'),
                        'title': img.get('title')
                    })
                metadata['images'] = images
            
            # Structural information
            metadata['headings'] = {
                'h1': [h.get_text(strip=True) for h in soup.find_all('h1')],
                'h2': [h.get_text(strip=True) for h in soup.find_all('h2')],
                'h3': [h.get_text(strip=True) for h in soup.find_all('h3')]
            }
            
            # Language
            html_tag = soup.find('html')
            if html_tag:
                metadata['language'] = html_tag.get('lang')
            
        except Exception as e:
            self.logger.warning(f"Error extracting metadata: {str(e)}")
        
        return metadata
    
    def extract_data(self, html: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data from HTML using provided selectors"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            return asyncio.run(self._extract_data_from_soup(soup))
        except Exception as e:
            self.logger.error(f"Error extracting data: {str(e)}")
            return {}
    
    async def scrape_with_pagination(self, start_url: str) -> ScrapingSession:
        """Scrape multiple pages with pagination support"""
        if not self.config.pagination:
            # Fall back to regular scraping
            return await self.scrape_multiple([start_url])
        
        session = self.create_session(start_url)
        current_url = start_url
        page_count = 0
        max_pages = self.config.pagination.get('max_pages', 10)
        
        self.logger.info(f"Starting pagination scraping from {start_url}")
        
        while current_url and page_count < max_pages:
            try:
                # Scrape current page
                page = await self.scrape_page(current_url)
                session.add_page(page)
                
                page_count += 1
                self.logger.info(f"Scraped page {page_count}/{max_pages}: {current_url}")
                
                # Check for stop condition
                if self._should_stop_pagination(page):
                    self.logger.info("Pagination stop condition met")
                    break
                
                # Find next page URL
                current_url = await self._get_next_page_url(page)
                
                if not current_url:
                    self.logger.info("No more pages found")
                    break
                
                # Apply rate limiting
                self.apply_rate_limit()
                
            except Exception as e:
                self.logger.error(f"Error in pagination scraping: {str(e)}")
                if not self.config.continue_on_error:
                    break
                current_url = None
        
        session.finish()
        self.logger.info(f"Pagination scraping completed: {session.get_summary()}")
        
        return session
    
    def _should_stop_pagination(self, page: ScrapedPage) -> bool:
        """Check if pagination should stop based on stop selector"""
        stop_selector = self.config.pagination.get('stop_selector')
        if not stop_selector:
            return False
        
        try:
            if page.html:
                soup = BeautifulSoup(page.html, 'html.parser')
                stop_elements = soup.select(stop_selector)
                return len(stop_elements) > 0
        except Exception as e:
            self.logger.warning(f"Error checking stop selector: {str(e)}")
        
        return False
    
    async def _get_next_page_url(self, page: ScrapedPage) -> Optional[str]:
        """Get URL for next page in pagination"""
        if not page.html:
            return None
        
        try:
            soup = BeautifulSoup(page.html, 'html.parser')
            next_selector = self.config.pagination.get('next_selector')
            
            if not next_selector:
                return None
            
            next_elements = soup.select(next_selector)
            
            if not next_elements:
                return None
            
            # Get href from first matching element
            next_element = next_elements[0]
            href = next_element.get('href')
            
            if href:
                return self.normalize_url(href, page.url)
            
        except Exception as e:
            self.logger.warning(f"Error finding next page URL: {str(e)}")
        
        return None
    
    def close(self):
        """Close the scraper and clean up resources"""
        if hasattr(self, 'session'):
            self.session.close()
            self.logger.info("HTTP session closed")
    
    def __del__(self):
        """Cleanup when scraper is destroyed"""
        try:
            self.close()
        except:
            pass
