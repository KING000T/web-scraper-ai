"""
Web Scraper AI - Main Application Entry Point

This is the main entry point for the Web Scraping and Data Extraction
Automation System. It provides both CLI and web server functionality.
"""

import asyncio
import argparse
import logging
import sys
from typing import Optional
from pathlib import Path

# Import core components
from scrapers.factory import ScraperFactory
from processors.pipeline import DataProcessingPipeline
from exporters.factory import ExporterFactory
from jobs.manager import JobManager

# Import configuration
from config.settings import Settings


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/app.log')
        ]
    )


def create_scraper(url: str, selectors: dict, scraper_type: str = "static") -> object:
    """Create scraper instance"""
    from scrapers.config import ScraperConfig, ScraperType
    
    config = ScraperConfig(
        url=url,
        selectors=selectors,
        scraper_type=ScraperType(scraper_type)
    )
    
    return ScraperFactory.create_scraper(config)


def create_processing_pipeline():
    """Create data processing pipeline"""
    from processors.cleaner import DataCleaner
    from processors.validator import DataValidator, required_field
    from processors.transformer import DataTransformer
    
    # Create processors
    cleaner = DataCleaner({
        'remove_html': True,
        'normalize_whitespace': True,
        'decode_html_entities': True
    })
    
    validator = DataValidator([
        required_field('name', 'Name is required'),
        required_field('email', 'Email is required')
    ])
    
    transformer = DataTransformer([
        # Add transformations as needed
    ])
    
    # Create pipeline
    pipeline = DataProcessingPipeline()
    pipeline.add_processor(cleaner)
    pipeline.add_processor(validator)
    pipeline.add_processor(transformer)
    
    return pipeline


async def run_single_scrape(url: str, selectors: dict, output_format: str = "csv"):
    """Run a single scraping job"""
    logger = logging.getLogger(__name__)
    
    try:
        # Create scraper
        scraper = create_scraper(url, selectors)
        
        # Scrape data
        logger.info(f"Scraping {url}")
        session = await scraper.scrape_page(url)
        
        if not session.is_successful:
            logger.error(f"Scraping failed: {session.error}")
            return None
        
        logger.info(f"Scraped {session.record_count} records")
        
        # Process data
        pipeline = create_processing_pipeline()
        processed_data = await pipeline.process(session.data)
        
        logger.info(f"Processed {len(processed_data)} records")
        
        # Export results
        exporter = ExporterFactory.create_exporter(output_format)
        result = exporter.export_with_stats(processed_data)
        
        if result.success:
            logger.info(f"Exported {result.record_count} records to {result.file_path}")
            return result.file_path
        else:
            logger.error(f"Export failed: {result.error_message}")
            return None
            
    except Exception as e:
        logger.error(f"Error in scraping job: {str(e)}")
        return None


async def run_batch_scrape(config_file: str):
    """Run batch scraping from configuration file"""
    logger = logging.getLogger(__name__)
    
    try:
        import json
        
        # Load configuration
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Process each job
        for job in config.get('jobs', []):
            logger.info(f"Processing job: {job.get('name', 'Unnamed')}")
            
            url = job['url']
            selectors = job['selectors']
            output_format = job.get('output_format', 'csv')
            
            result = await run_single_scrape(url, selectors, output_format)
            
            if result:
                logger.info(f"Job completed: {result}")
            else:
                logger.error(f"Job failed")
                
    except Exception as e:
        logger.error(f"Error in batch scraping: {str(e)}")


def start_web_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the web server"""
    logger = logging.getLogger(__name__)
    
    try:
        import uvicorn
        from api.main import app
        
        logger.info(f"Starting web server on {host}:{port}")
        uvicorn.run(app, host=host, port=port)
        
    except ImportError:
        logger.error("FastAPI not installed. Install with: pip install fastapi uvicorn")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting web server: {str(e)}")
        sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Web Scraper AI")
    parser.add_argument("--mode", choices=["scrape", "batch", "server"], default="server",
                       help="Run mode: scrape (single), batch (multiple), or server (web)")
    parser.add_argument("--url", help="URL to scrape")
    parser.add_argument("--selectors", help="JSON string with CSS selectors")
    parser.add_argument("--config", help="Configuration file for batch mode")
    parser.add_argument("--output", choices=["csv", "json", "xlsx"], default="csv",
                       help="Output format")
    parser.add_argument("--host", default="0.0.0.0", help="Web server host")
    parser.add_argument("--port", type=int, default=8000, help="Web server port")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Ensure directories exist
    Path("logs").mkdir(exist_ok=True)
    Path("exports").mkdir(exist_ok=True)
    Path("uploads").mkdir(exist_ok=True)
    
    # Run based on mode
    if args.mode == "scrape":
        if not args.url or not args.selectors:
            logger.error("URL and selectors are required for scrape mode")
            sys.exit(1)
        
        import json
        selectors = json.loads(args.selectors)
        
        # Run single scrape
        result = asyncio.run(run_single_scrape(args.url, selectors, args.output))
        
        if result:
            logger.info(f"Scraping completed: {result}")
        else:
            logger.error("Scraping failed")
            sys.exit(1)
    
    elif args.mode == "batch":
        if not args.config:
            logger.error("Configuration file is required for batch mode")
            sys.exit(1)
        
        # Run batch scrape
        asyncio.run(run_batch_scrape(args.config))
    
    elif args.mode == "server":
        # Start web server
        start_web_server(args.host, args.port)
    
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
