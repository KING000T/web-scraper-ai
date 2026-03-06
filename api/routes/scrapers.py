"""
Scrapers API Routes

This module defines API endpoints for immediate scraping operations,
scraper configuration, and real-time scraping control.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import logging
import asyncio

from ..dependencies import get_database, get_current_user, get_scraper_engine, get_data_processor, get_export_engine
from ..models import (
    ScrapingRequest, ScrapingResult, ExportRequest, ExportResult,
    SuccessResponse, ErrorResponse, ExportFormat
)
from scrapers.factory import ScraperFactory
from processors.pipeline import DataProcessingPipeline
from exporters.factory import ExporterFactory

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/scrape", response_model=ScrapingResult)
async def scrape_immediate(
    scraping_request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Perform immediate scraping without creating a job"""
    try:
        # Create scraper configuration
        from scrapers.config import ScraperConfig, ScraperType
        
        config = ScraperConfig(
            url=scraping_request.url,
            selectors=scraping_request.selectors,
            scraper_type=ScraperType(scraping_request.scraper_type),
            delay=scraping_request.delay,
            timeout=scraping_request.timeout,
            user_agent=scraping_request.user_agent,
            headers=scraping_request.headers,
            cookies=scraping_request.cookies,
            proxy=scraping_request.proxy,
            pagination=scraping_request.pagination,
            extract_links=scraping_request.extract_links,
            extract_images=scraping_request.extract_images,
            extract_metadata=scraping_request.extract_metadata,
            continue_on_error=scraping_request.continue_on_error,
            ignore_ssl_errors=scraping_request.ignore_ssl_errors
        )
        
        # Create scraper
        scraper = ScraperFactory.create_scraper(config)
        
        # Perform scraping
        logger.info(f"Starting immediate scraping for {scraping_request.url}")
        session = await scraper.scrape_page(scraping_request.url)
        
        if not session.is_successful:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Scraping failed: {session.error}"
            )
        
        # Process data if processor is available
        processed_data = session.data
        if get_data_processor():
            processor = get_data_processor()
            processed_data = await processor.process(session.data)
        
        # Create result
        result = ScrapingResult(
            url=session.url,
            data=processed_data,
            status_code=session.status_code,
            html=session.html,
            timestamp=session.timestamp,
            extraction_time=session.extraction_time,
            error=session.error,
            metadata=session.metadata,
            is_successful=session.is_successful,
            record_count=session.record_count
        )
        
        logger.info(f"Immediate scraping completed: {result.record_count} records")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in immediate scraping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform scraping"
        )


@router.post("/scrape-batch", response_model=List[ScrapingResult])
async def scrape_batch(
    urls: List[str],
    selectors: Dict[str, str],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user),
    scraper_type: str = "static",
    delay: float = 1.0,
    timeout: int = 30,
    max_concurrent: int = 3
):
    """Perform batch scraping of multiple URLs"""
    try:
        if len(urls) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 URLs allowed for batch scraping"
            )
        
        if max_concurrent > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 concurrent requests allowed"
            )
        
        # Create scraper configuration
        from scrapers.config import ScraperConfig, ScraperType
        
        config = ScraperConfig(
            url="placeholder",  # Will be overridden
            selectors=selectors,
            scraper_type=ScraperType(scraper_type),
            delay=delay,
            timeout=timeout
        )
        
        # Create scraper
        scraper = ScraperFactory.create_scraper(config)
        
        # Scrape URLs concurrently
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_single_url(url: str):
            async with semaphore:
                try:
                    # Update config URL
                    config.url = url
                    
                    # Create new scraper for this URL
                    url_scraper = ScraperFactory.create_scraper(config)
                    
                    # Scrape
                    session = await url_scraper.scrape_page(url)
                    
                    # Process data
                    processed_data = session.data
                    if get_data_processor():
                        processor = get_data_processor()
                        processed_data = await processor.process(session.data)
                    
                    return ScrapingResult(
                        url=session.url,
                        data=processed_data,
                        status_code=session.status_code,
                        html=session.html,
                        timestamp=session.timestamp,
                        extraction_time=session.extraction_time,
                        error=session.error,
                        metadata=session.metadata,
                        is_successful=session.is_successful,
                        record_count=session.record_count
                    )
                    
                except Exception as e:
                    logger.error(f"Error scraping {url}: {str(e)}")
                    return ScrapingResult(
                        url=url,
                        data={},
                        status_code=0,
                        html=None,
                        timestamp=datetime.utcnow(),
                        extraction_time=0.0,
                        error=str(e),
                        metadata={},
                        is_successful=False,
                        record_count=0
                    )
        
        # Execute batch scraping
        results = await asyncio.gather(*[scrape_single_url(url) for url in urls])
        
        successful_results = [r for r in results if r.is_successful]
        failed_results = [r for r in results if not r.is_successful]
        
        logger.info(f"Batch scraping completed: {len(successful_results)}/{len(urls)} successful")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch scraping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform batch scraping"
        )


@router.post("/validate-selectors")
async def validate_selectors(
    url: str,
    selectors: Dict[str, str],
    scraper_type: str = "static",
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Validate CSS selectors against a webpage"""
    try:
        # Create scraper configuration
        from scrapers.config import ScraperConfig, ScraperType
        
        config = ScraperConfig(
            url=url,
            selectors=selectors,
            scraper_type=ScraperType(scraper_type),
            delay=0.1,  # Fast for validation
            timeout=10
        )
        
        # Create scraper
        scraper = ScraperFactory.create_scraper(config)
        
        # Scrape page
        session = await scraper.scrape_page(url)
        
        if not session.is_successful:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load page: {session.error}"
            )
        
        # Validate selectors
        validation_results = {}
        
        for field_name, selector in selectors.items():
            try:
                # Check if selector finds elements
                elements = session.data.get(field_name, [])
                
                validation_results[field_name] = {
                    "selector": selector,
                    "found": len(elements) > 0,
                    "count": len(elements),
                    "sample": elements[:3] if elements else [],
                    "valid": True
                }
                
            except Exception as e:
                validation_results[field_name] = {
                    "selector": selector,
                    "found": False,
                    "count": 0,
                    "sample": [],
                    "valid": False,
                    "error": str(e)
                }
        
        return {
            "url": url,
            "scraper_type": scraper_type,
            "validation_results": validation_results,
            "page_loaded": True,
            "total_selectors": len(selectors),
            "valid_selectors": len([r for r in validation_results.values() if r["valid"]])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating selectors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate selectors"
        )


@router.get("/preview/{url:path}")
async def preview_page(
    url: str,
    scraper_type: str = "static",
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Preview webpage structure and extractable elements"""
    try:
        # Create scraper configuration
        from scrapers.config import ScraperConfig, ScraperType
        
        config = ScraperConfig(
            url=url,
            selectors={},  # No selectors for preview
            scraper_type=ScraperType(scraper_type),
            delay=0.1,
            timeout=10
        )
        
        # Create scraper
        scraper = ScraperFactory.create_scraper(config)
        
        # Scrape page
        session = await scraper.scrape_page(url)
        
        if not session.is_successful:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load page: {session.error}"
            )
        
        # Extract page structure
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(session.html, 'html.parser')
        
        # Extract common elements
        structure = {
            "title": soup.title.get_text(strip=True) if soup.title else "",
            "headings": {
                "h1": [h.get_text(strip=True) for h in soup.find_all('h1')],
                "h2": [h.get_text(strip=True) for h in soup.find_all('h2')],
                "h3": [h.get_text(strip=True) for h in soup.find_all('h3')]
            },
            "links": [
                {
                    "text": a.get_text(strip=True),
                    "href": a.get('href'),
                    "title": a.get('title')
                }
                for a in soup.find_all('a', href=True)
            ],
            "images": [
                {
                    "src": img.get('src'),
                    "alt": img.get('alt'),
                    "title": img.get('title')
                }
                for img in soup.find_all('img', src=True)
            ],
            "forms": [
                {
                    "action": form.get('action'),
                    "method": form.get('method', 'get'),
                    "inputs": [
                        {
                            "name": inp.get('name'),
                            "type": inp.get('type'),
                            "placeholder": inp.get('placeholder')
                        }
                        for inp in form.find_all('input')
                    ]
                }
                for form in soup.find_all('form')
            ],
            "tables": [
                {
                    "rows": len(table.find_all('tr')),
                    "columns": len(table.find_all('tr')[0].find_all('th')) if table.find_all('tr') else 0
                }
                for table in soup.find_all('table')
            ]
        }
        
        return {
            "url": url,
            "scraper_type": scraper_type,
            "title": structure["title"],
            "structure": structure,
            "metadata": session.metadata,
            "load_time": session.extraction_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing page: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to preview page"
        )


@router.post("/export-scraped-data", response_model=ExportResult)
async def export_scraped_data(
    scraping_request: ScrapingRequest,
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Scrape and immediately export data"""
    try:
        # First perform scraping
        scraping_result = await scrape_immediate(scraping_request, background_tasks, db, current_user)
        
        if not scraping_result.is_successful:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Scraping failed: {scraping_result.error}"
            )
        
        # Export data
        exporter = ExporterFactory.create_exporter(export_request.format)
        
        # Prepare data for export
        export_data = [scraping_result.data] if scraping_result.data else []
        
        # Create export configuration
        from exporters.base import ExportConfig
        export_config = ExportConfig(
            filename=export_request.filename,
            format=export_request.format,
            include_headers=export_request.include_headers,
            encoding=export_request.encoding,
            delimiter=export_request.delimiter
        )
        
        # Export data
        export_result = exporter.export_with_stats(export_data, export_config)
        
        if not export_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Export failed: {export_result.error_message}"
            )
        
        logger.info(f"Scraped and exported data: {export_result.file_path}")
        
        return export_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in scrape and export: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scrape and export data"
        )


@router.get("/scraper-types")
async def get_scraper_types():
    """Get available scraper types and their capabilities"""
    try:
        scraper_types = {
            "static": {
                "name": "Static Scraper",
                "description": "For static HTML content using BeautifulSoup",
                "capabilities": [
                    "HTML parsing",
                    "CSS selectors",
                    "Pagination support",
                    "Rate limiting",
                    "Error handling"
                ],
                "best_for": [
                    "Simple websites",
                    "Blog posts",
                    "News articles",
                    "Product catalogs"
                ],
                "limitations": [
                    "No JavaScript execution",
                    "No dynamic content"
                ]
            },
            "dynamic": {
                "name": "Dynamic Scraper",
                "description": "For JavaScript-rendered content using Selenium",
                "capabilities": [
                    "JavaScript execution",
                    "CSS selectors",
                    "Pagination support",
                    "Scrolling support",
                    "Screenshot capture",
                    "Form interaction"
                ],
                "best_for": [
                    "Single-page applications",
                    "AJAX-heavy sites",
                    "Social media",
                    "E-commerce sites"
                ],
                "limitations": [
                    "Slower performance",
                    "Higher resource usage"
                ]
            },
            "advanced": {
                "name": "Advanced Scraper",
                "description": "For complex websites with advanced features",
                "capabilities": [
                    "JavaScript execution",
                    "Advanced scrolling",
                    "Wait strategies",
                    "Browser automation",
                    "Custom scripts"
                ],
                "best_for": [
                    "Complex web applications",
                    "Dynamic dashboards",
                    "Interactive sites"
                ],
                "limitations": [
                    "Highest resource usage",
                    "Complex configuration"
                ]
            }
        }
        
        return scraper_types
        
    except Exception as e:
        logger.error(f"Error getting scraper types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scraper types"
        )


@router.get("/export-formats")
async def get_export_formats():
    """Get available export formats and their capabilities"""
    try:
        export_formats = {
            "csv": {
                "name": "CSV (Comma-Separated Values)",
                "description": "Plain text format with comma-separated values",
                "capabilities": [
                    "Tabular data",
                    "Custom delimiters",
                    "Encoding support",
                    "Streaming support"
                ],
                "best_for": [
                    "Spreadsheet import",
                    "Data analysis",
                    "Simple data exchange"
                ],
                "file_extension": ".csv"
            },
            "json": {
                "name": "JSON (JavaScript Object Notation)",
                "description": "Structured data format with nested objects",
                "capabilities": [
                    "Nested data",
                    "Data types",
                    "Pretty printing",
                    "API compatibility"
                ],
                "best_for": [
                    "Web applications",
                    "API responses",
                    "Configuration files"
                ],
                "file_extension": ".json"
            },
            "xlsx": {
                "name": "Excel Spreadsheet",
                "description": "Microsoft Excel format with rich formatting",
                "capabilities": [
                    "Rich formatting",
                    "Multiple sheets",
                    "Charts",
                    "Formulas",
                    "Cell styling"
                ],
                "best_for": [
                    "Business reports",
                    "Data analysis",
                    "Presentations"
                ],
                "file_extension": ".xlsx"
            },
            "google_sheets": {
                "name": "Google Sheets",
                "description": "Cloud-based spreadsheet with collaboration",
                "capabilities": [
                    "Cloud storage",
                    "Real-time collaboration",
                    "Integration",
                    "Automatic updates"
                ],
                "best_for": [
                    "Team collaboration",
                    "Cloud workflows",
                    "Real-time data"
                ],
                "file_extension": ".csv"
            }
        }
        
        return export_formats
        
    except Exception as e:
        logger.error(f"Error getting export formats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get export formats"
        )


@router.post("/test-connection")
async def test_connection(
    url: str,
    scraper_type: str = "static",
    timeout: int = 10,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Test connection to a website"""
    try:
        # Create scraper configuration
        from scrapers.config import ScraperConfig, ScraperType
        
        config = ScraperConfig(
            url=url,
            selectors={},
            scraper_type=ScraperType(scraper_type),
            delay=0,
            timeout=timeout
        )
        
        # Create scraper
        scraper = ScraperFactory.create_scraper(config)
        
        # Test connection
        start_time = time.time()
        session = await scraper.scrape_page(url)
        end_time = time.time()
        
        connection_time = end_time - start_time
        
        if not session.is_successful:
            return {
                "url": url,
                "scraper_type": scraper_type,
                "connected": False,
                "error": session.error,
                "connection_time": connection_time,
                "status_code": 0
            }
        
        return {
            "url": url,
            "scraper_type": scraper_type,
            "connected": True,
            "connection_time": connection_time,
            "status_code": session.status_code,
            "page_size": len(session.html) if session.html else 0,
            "title": session.metadata.get("title", ""),
            "encoding": session.metadata.get("encoding", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Error testing connection: {str(e)}")
        return {
            "url": url,
            "scraper_type": scraper_type,
            "connected": False,
            "error": str(e),
            "connection_time": 0,
            "status_code": 0
        }


@router.get("/recent-scrapes")
async def get_recent_scrapes(
    limit: int = 10,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get recent scraping results for the current user"""
    try:
        # Get recent jobs for current user
        from jobs.models import Job as JobModel
        
        query = db.query(JobModel).filter(
            JobModel.user_id == current_user.id
        ).order_by(JobModel.created_at.desc()).limit(limit)
        
        recent_jobs = query.all()
        
        # Convert to response format
        recent_scrapes = []
        for job in recent_jobs:
            recent_scrapes.append({
                "id": job.id,
                "name": job.name,
                "url": job.url,
                "status": job.status,
                "created_at": job.created_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "records_processed": job.records_processed,
                "success_rate": job.success_rate,
                "result_path": job.result_path,
                "file_size": job.file_size
            })
        
        return recent_scrapes
        
    except Exception as e:
        logger.error(f"Error getting recent scrapes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recent scrapes"
        )


@router.delete("/cleanup-cache")
async def cleanup_cache(
    current_user = Depends(get_current_user)
):
    """Clean up temporary files and cache"""
    try:
        import os
        import glob
        from datetime import datetime, timedelta
        
        # Clean up old temporary files
        temp_dir = "temp"
        if os.path.exists(temp_dir):
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            for file_path in glob.glob(os.path.join(temp_dir, "*")):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        logger.info(f"Cleaned up temporary file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove temporary file {file_path}: {str(e)}")
        
        return SuccessResponse(
            success=True,
            message="Cache cleanup completed",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error cleaning up cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean up cache"
        )


# Example usage patterns
def example_usage():
    """Example usage patterns for scraper API"""
    
    # Immediate scraping
    scraping_request = ScrapingRequest(
        url="https://example.com",
        selectors={"title": "h1", "content": ".content"},
        scraper_type="static"
    )
    
    # Export scraped data
    export_request = ExportRequest(
        job_id=1,
        format="json",
        pretty_print=True
    )
    
    # Batch scraping
    urls = ["https://site1.com", "https://site2.com", "https://site3.com"]
    selectors = {"title": "h1", "content": ".content"}
    
    print("Scraper API examples completed")


if __name__ == "__main__":
    # Test scraper API
    example_usage()
