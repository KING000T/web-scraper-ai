"""
Multi-Level E-commerce Scraper Example

This module demonstrates a complete multi-level scraping implementation
for an e-commerce website with category → subcategory → product hierarchy.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

from scrapers.factory import ScraperFactory
from scrapers.config import ScraperConfig, ScraperType
from processors.pipeline import DataProcessingPipeline
from exporters.factory import ExporterFactory

logger = logging.getLogger(__name__)


class MultiLevelScraper:
    """Multi-level scraper for e-commerce websites with category hierarchy"""
    
    def __init__(self, base_url: str, config: Optional[Dict[str, Any]] = None):
        """Initialize multi-level scraper"""
        self.base_url = base_url
        self.config = config or {}
        
        # Scraper configuration
        self.scraper_config = ScraperConfig(
            url=base_url,
            selectors={},  # Will be set per level
            scraper_type=ScraperType.DYNAMIC,
            delay=self.config.get('delay', 2.0),
            max_retries=self.config.get('max_retries', 3),
            timeout=self.config.get('timeout', 30),
            user_agent=self.config.get('user_agent', 'MultiLevelScraper/1.0'),
            browser_options=self.config.get('browser_options', [
                '--headless',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]),
            wait_strategy='networkidle',
            scroll_behavior='down'
        )
        
        # Create scraper
        self.scraper = ScraperFactory.create_scraper(self.scraper_config)
        
        # Data storage
        self.categories = []
        self.products = []
        self.scraped_urls = set()
        
        # Processing pipeline
        self.pipeline = DataProcessingPipeline()
        
        # Exporter
        self.exporter = ExporterFactory.create_exporter('json')
        
        logger.info(f"Initialized multi-level scraper for {base_url}")
    
    async def scrape_all_levels(self) -> Dict[str, Any]:
        """Scrape all levels: categories → subcategories → products"""
        logger.info("Starting multi-level scraping")
        
        # Level 1: Scrape categories
        await self._scrape_categories()
        
        # Level 2: Scrape subcategories for each category
        await self._scrape_subcategories()
        
        # Level 3: Scrape products for each subcategory
        await self._scrape_products()
        
        # Process and export data
        await self._process_and_export_data()
        
        return {
            'categories': self.categories,
            'products': self.products,
            'total_categories': len(self.categories),
            'total_products': len(self.products),
            'scraped_urls': len(self.scraped_urls)
        }
    
    async def _scrape_categories(self):
        """Scrape top-level categories"""
        logger.info("Scraping categories")
        
        # Category page selectors
        category_selectors = {
            'category_name': '.category-item .category-name',
            'category_url': '.category-item a',
            'product_count': '.category-item .product-count'
        }
        
        # Update scraper config for categories
        self.scraper.config.selectors = category_selectors
        
        # Scrape category page
        session = await self.scraper.scrape_page(self.base_url)
        
        if not session.is_successful:
            raise Exception(f"Failed to scrape categories: {session.error}")
        
        # Extract category data
        for category_data in session.data.get('category_name', []):
            if category_data:
                category_url = self._get_category_url(session.data, category_data)
                if category_url and category_url not in self.scraped_urls:
                    self.categories.append({
                        'name': category_data,
                        'url': category_url,
                        'product_count': self._get_product_count(session.data, category_data),
                        'subcategories': [],
                        'products': []
                    })
                    self.scraped_urls.add(category_url)
        
        logger.info(f"Found {len(self.categories)} categories")
    
    async def _scrape_subcategories(self):
        """Scrape subcategories for each category"""
        logger.info("Scraping subcategories")
        
        # Subcategory selectors
        subcategory_selectors = {
            'subcategory_name': '.subcategory-item .subcategory-name',
            'subcategory_url': '.subcategory-item a',
            'product_count': '.subcategory-item .product-count'
        }
        
        for category in self.categories:
            category_url = category['url']
            
            if category_url in self.scraped_urls:
                continue  # Skip if already scraped
            
            logger.info(f"Scraping subcategories for: {category['name']}")
            
            # Update scraper config for subcategories
            self.scraper.config.url = category_url
            self.scraper.config.selectors = subcategory_selectors
            
            # Scrape subcategory page
            session = await self.scraper.scrape_page(category_url)
            
            if not session.is_successful:
                logger.warning(f"Failed to scrape subcategories for {category['name']}: {session.error}")
                continue
            
            # Extract subcategory data
            for subcategory_data in session.data.get('subcategory_name', []):
                if subcategory_data:
                    subcategory_url = self._get_subcategory_url(session.data, subcategory_data)
                    if subcategory_url and subcategory_url not in self.scraped_urls:
                        subcategory = {
                            'name': subcategory_data,
                            'url': subcategory_url,
                            'product_count': self._get_product_count(session.data, subcategory_data),
                            'products': []
                        }
                        category['subcategories'].append(subcategory)
                        self.scraped_urls.add(subcategory_url)
        
        # Update total product counts
        for category in self.categories:
            total_products = sum(subcat['product_count'] for subcat in category['subcategories'])
            category['product_count'] = total_products
        
        logger.info(f"Found {sum(len(cat['subcategories']) for cat in self.categories)} subcategories")
    
    async def _scrape_products(self):
        """Scrape products for each subcategory"""
        logger.info("Scraping products")
        
        # Product selectors
        product_selectors = {
            'product_name': '.product-item .product-name',
            'price': '.product-item .price',
            'rating': '.product-item .rating',
            'availability': '.product-item .stock-status',
            'image_url': '.product-item .product-image img',
            'description': '.product-item .description',
            'brand': '.product-item .brand',
            'sku': '.product-item .sku'
        }
        
        for category in self.categories:
            for subcategory in category['subcategories']:
                subcategory_url = subcategory['url']
                
                if subcategory_url in self.scraped_urls:
                    continue  # Skip if already scraped
                
                logger.info(f"Scraping products for: {category['name']} → {subcategory['name']}")
                
                # Update scraper config for products
                self.scraper.config.url = subcategory_url
                self.scraper.config.selectors = product_selectors
                self.scraper.config.pagination = {
                    'next_selector': '.pagination .next-page',
                    'max_pages': self.config.get('max_pages_per_subcategory', 10)
                }
                
                # Scrape products with pagination
                products = await self._scrape_products_with_pagination(subcategory_url, product_selectors)
                
                # Add products to subcategory
                subcategory['products'] = products
                category['products'].extend(products)
                self.scraped_urls.add(subcategory_url)
        
        logger.info(f"Found {len(self.products)} total products")
    
    async def _scrape_products_with_pagination(self, url: str, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Scrape products with pagination support"""
        all_products = []
        current_url = url
        page = 1
        
        while current_url and page <= self.config.get('max_pages_per_subcategory', 10):
            logger.info(f"Scraping page {page} of {current_url}")
            
            # Update scraper config
            self.scraper.config.url = current_url
            self.scraper.config.selectors = selectors
            
            # Scrape current page
            session = await self.scraper.scrape_page(current_url)
            
            if not session.is_successful:
                logger.warning(f"Failed to scrape page {page}: {session.error}")
                break
            
            # Add products from this page
            page_products = []
            for product_data in session.data.get('product_name', []):
                if product_data:
                    product = {
                        'name': product_data,
                        'price': self._get_field_value(session.data, 'price', product_data),
                        'rating': self._get_field_value(session.data, 'rating', product_data),
                        'availability': self._get_field_value(session.data, 'availability', product_data),
                        'image_url': self._get_field_value(session.data, 'image_url', product_data),
                        'description': self._get_field_value(session.data, 'description', product_data),
                        'brand': self._get_field_value(session.data, 'brand', product_data),
                        'sku': self._get_field_value(session.data, 'sku', product_data),
                        'category': self._get_category_from_url(current_url),
                        'subcategory': self._get_subcategory_from_url(current_url),
                        'url': current_url,
                        'scraped_at': session.timestamp.isoformat()
                    }
                    page_products.append(product)
            
            all_products.extend(page_products)
            
            # Find next page URL
            next_url = self._get_next_page_url(session)
            if not next_url:
                break
            
            current_url = next_url
            page += 1
            
            # Rate limiting
            await asyncio.sleep(self.scraper.config.delay)
        
        return all_products
    
    def _get_category_url(self, data: Dict[str, List[str]], category_name: str) -> Optional[str]:
        """Extract category URL from scraped data"""
        category_index = data.get('category_name', []).index(category_name) if category_name in data.get('category_name', []) else -1
        
        if category_index >= 0 and 'category_url' in data:
            urls = data['category_url']
            if category_index < len(urls):
                return urls[category_index]
        
        return None
    
    def _get_subcategory_url(self, data: Dict[str, List[str]], subcategory_name: str) -> Optional[str]:
        """Extract subcategory URL from scraped data"""
        subcategory_index = data.get('subcategory_name', []).index(subcategory_name) if subcategory_name in data.get('subcategory_name', []) else -1
        
        if subcategory_index >= 0 and 'subcategory_url' in data:
            urls = data['subcategory_url']
            if subcategory_index < len(urls):
                return urls[subcategory_index]
        
        return None
    
    def _get_product_count(self, data: Dict[str, List[str]], item_name: str) -> int:
        """Extract product count for an item"""
        item_index = data.get('product_count', []).index(item_name) if item_name in data.get('product_count', []) else -1
        
        if item_index >= 0 and 'product_count' in data:
            counts = data['product_count']
            if item_index < len(counts):
                try:
                    return int(counts[item_index])
                except (ValueError, TypeError):
                    return 0
        
        return 0
    
    def _get_field_value(self, data: Dict[str, List[str]], field: str, item_name: str) -> Any:
        """Get field value for a specific item"""
        item_index = data.get(field, []).index(item_name) if item_name in data.get(field, []) else -1
        
        if item_index >= 0 and field in data:
            values = data[field]
            if item_index < len(values):
                return values[item_index]
        
        return None
    
    def _get_next_page_url(self, session) -> Optional[str]:
        """Get next page URL from session metadata"""
        if session.metadata and 'pagination' in session.metadata:
            pagination = session.metadata['pagination']
            return pagination.get('next_url')
        return None
    
    def _get_category_from_url(self, url: str) -> str:
        """Extract category name from URL"""
        # For demo, extract from URL path
        path = urlparse(url).path
        parts = path.strip('/').split('/')
        if len(parts) >= 2:
            return parts[1]
        return "unknown"
    
    def _get_subcategory_from_url(self, url: str) -> str:
        """Extract subcategory name from URL"""
        # For demo, extract from URL path
        path = urlparse(url).path
        parts = path.strip('/').split('/')
        if len(parts) >= 3:
            return parts[2]
        return "unknown"
    
    async def _process_and_export_data(self):
        """Process scraped data and export results"""
        logger.info("Processing and exporting data")
        
        # Process all data
        processed_data = []
        
        # Add categories
        for category in self.categories:
            processed_data.extend([{
                'type': 'category',
                'data': category
            }])
            
            # Add subcategories
            for subcategory in category['subcategories']:
                processed_data.extend([{
                    'type': 'subcategory',
                    'data': subcategory,
                    'category_name': category['name']
                }])
            
            # Add products
            for product in category['products']:
                processed_data.extend([{
                    'type': 'product',
                    'data': product,
                    'category_name': category['name'],
                    'subcategory_name': self._get_subcategory_from_url(product['url'])
                }])
        
        # Process data through pipeline
        if self.pipeline:
            processed_data = await self.pipeline.process(processed_data)
        
        # Export results
        if self.exporter:
            from exporters.base import ExportConfig
            
            export_config = ExportConfig(
                filename=f"multi_level_scrap_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                format='json',
                include_headers=True,
                encoding='utf-8'
            )
            
            result = self.exporter.export_with_stats(processed_data, export_config)
            
            if result.success:
                logger.info(f"Exported {result.record_count} records to {result.file_path}")
            else:
                logger.error(f"Export failed: {result.error_message}")
        
        return processed_data
    
    async def scrape_category_only(self, category_name: str) -> Dict[str, Any]:
        """Scrape only a specific category"""
        logger.info(f"Scraping category: {category_name}")
        
        # Find category
        category = next((cat for cat in self.categories if cat['name'] == category_name), None)
        if not category:
            raise ValueError(f"Category '{category_name}' not found")
        
        # Scrape subcategories and products
        await self._scrape_subcategories_for_category(category)
        await self._scrape_products_for_category(category)
        
        return {
            'category': category,
            'total_subcategories': len(category['subcategories']),
            'total_products': len(category['products']),
            'scraped_urls': len(self.scraped_urls)
        }
    
    async def _scrape_subcategories_for_category(self, category: Dict[str, Any]):
        """Scrape subcategories for a specific category"""
        subcategory_selectors = {
            'subcategory_name': '.subcategory-item .subcategory-name',
            'subcategory_url': '.subcategory-item a',
            'product_count': '.subcategory-item .product-count'
        }
        
        for subcategory in category['subcategories']:
            subcategory_url = subcategory['url']
            
            if subcategory_url in self.scraped_urls:
                continue
            
            # Update scraper config
            self.scraper.config.url = subcategory_url
            self.scraper.config.selectors = subcategory_selectors
            
            # Scrape subcategory
            session = await self.scraper.scrape_page(subcategory_url)
            
            if session.is_successful:
                # Update subcategory data
                for subcategory_data in session.data.get('subcategory_name', []):
                    if subcategory_data:
                        subcategory_url = self._get_subcategory_url(session.data, subcategory_data)
                        if subcategory_url:
                            subcategory['url'] = subcategory_url
                            subcategory['product_count'] = self._get_product_count(session.data, subcategory_data)
                            self.scraped_urls.add(subcategory_url)
    
    async def _scrape_products_for_category(self, category: Dict[str, Any]):
        """Scrape products for a specific category"""
        product_selectors = {
            'product_name': '.product-item .product-name',
            'price': '.product-item .price',
            'rating': '.product-item .rating',
            'availability': '.product-item .stock-status',
            'image_url': '.product-item .product-image img',
            'description': '.product-item .description',
            'brand': '.product-item .brand',
            'sku': '.product-item .sku'
        }
        
        for subcategory in category['subcategories']:
            subcategory_url = subcategory['url']
            
            if subcategory_url in self.scraped_urls:
                continue
            
            # Update scraper config
            self.scraper.config.url = subcategory_url
            self.scraper.config.selectors = product_selectors
            self.scraper.config.pagination = {
                'next_selector': '.pagination .next-page',
                'max_pages': 10
            }
            
            # Scrape products
            products = await self._scrape_products_with_pagination(subcategory_url, product_selectors)
            
            # Add products to category
            subcategory['products'] = products
            category['products'].extend(products)
            self.scraped_urls.add(subcategory_url)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        return {
            'total_categories': len(self.categories),
            'total_subcategories': sum(len(cat['subcategories']) for cat in self.categories),
            'total_products': len(self.products),
            'scraped_urls': len(self.scraped_urls),
            'categories_with_products': len([cat for cat in self.categories if cat['products']]),
            'average_products_per_category': len(self.products) / len(self.categories) if self.categories else 0,
            'average_subcategories_per_category': sum(len(cat['subcategories']) for cat in self.categories) / len(self.categories) if self.categories else 0
        }


# Example usage
async def main():
    """Example usage of multi-level scraper"""
    
    # Create scraper for demo e-commerce site
    scraper = MultiLevelScraper(
        base_url="https://example-ecommerce.com",
        config={
            'delay': 2.0,
            'max_retries': 3,
            'timeout': 30,
            'max_pages_per_subcategory': 10
        }
    )
    
    # Scrape all levels
    results = await scraper.scrape_all_levels()
    
    print(f"Scraping completed:")
    print(f"Categories: {results['total_categories']}")
    print(f"Products: {results['total_products']}")
    print(f"Scraped URLs: {results['scraped_urls']}")
    
    # Get statistics
    stats = scraper.get_statistics()
    print(f"Statistics: {stats}")
    
    # Example: Scrape specific category
    electronics_results = await scraper.scrape_category_only("Electronics")
    print(f"Electronics category: {electronics_results['total_products']} products")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    # Run example
    asyncio.run(main())
