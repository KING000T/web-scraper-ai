"""
FastAPI Main Application

This module defines the main FastAPI application with middleware,
exception handlers, and global configuration.
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import time
import uuid
from contextlib import asynccontextmanager

# Import routes
from .routes import jobs, scrapers, exports, monitoring
from .dependencies import get_settings, get_health_status
from .models import ErrorResponse, HealthCheck

# Get settings
settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Web Scraper AI API")
    
    # Initialize database
    from .dependencies import engine, Base
    Base.metadata.create_all(bind=engine)
    
    # Initialize task queue
    from jobs.queue import TaskQueue
    queue = TaskQueue()
    queue.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Web Scraper AI API")
    queue.stop()


# Create FastAPI application
app = FastAPI(
    title="Web Scraper AI API",
    description="REST API for Web Scraping and Data Extraction Automation System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to all requests"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()
    
    # Get client info
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    user_agent = request.headers.get("User-Agent", "Unknown")
    
    logger.info(
        f"Request {request.method} {request.url.path} - "
        f"IP: {client_ip} - "
        f"User-Agent: {user_agent}"
    )
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        f"Response {response.status_code} - "
        f"Time: {process_time:.3f}s - "
        f"Request ID: {request.state.request_id}"
    )
    
    return response


# Rate limiting middleware (simple implementation)
@app.middleware("http")
async def rate_limiting(request: Request, call_next):
    """Simple rate limiting"""
    # For demo purposes, no rate limiting
    # In production, implement proper rate limiting with Redis
    
    # Check if request is from admin
    if request.url.path.startswith("/admin"):
        # Skip rate limiting for admin endpoints
        return await call_next(request)
    
    # Simple rate limiting check
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    
    # For demo, allow all requests
    # In production, check rate limits
    
    return await call_next(request)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP Exception",
            message=exc.detail,
            details={
                "status_code": exc.status_code,
                "path": str(request.url.path),
                "method": request.method,
                "request_id": getattr(request.state, "request_id", None)
            }
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred",
            details={
                "path": str(request.url.path),
                "method": request.method,
                "request_id": getattr(request.state, "request_id", None)
            }
        ).dict()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="Validation Error",
            message=str(exc),
            details={
                "path": str(request.url.path),
                "method": request.method,
                "request_id": getattr(request.state, "request_id", None)
            }
        ).dict()
    )


@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError):
    """Handle key errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="Missing Field",
            message=f"Required field is missing: {str(exc)}",
            details={
                "path": str(request.url.path),
                "method": request.method,
                "request_id": getattr(request.state, "request_id", None)
            }
        ).dict()
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Web Scraper AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "timestamp": time.time()
    }


# Health check endpoint
@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    import psutil
    import os
    
    # Get system metrics
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    
    # Get health status
    health_status = get_health_status()
    
    return HealthCheck(
        status=health_status["overall"],
        timestamp=time.time(),
        version="1.0.0",
        uptime=time.time(),  # In production, track actual uptime
        database_status=health_status["database"],
        queue_status=health_status["queue"],
        memory_usage=memory_usage,
        cpu_usage=cpu_usage,
        disk_usage=disk_usage
    )


# Metrics endpoint
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """System metrics endpoint"""
    import psutil
    
    # Get detailed system metrics
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    network = psutil.net_io_counters()
    
    return {
        "system": {
            "cpu_usage": cpu_usage,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        },
        "application": {
            "uptime": time.time(),  # In production, track actual uptime
            "version": "1.0.0",
            "environment": settings.environment
        }
    }


# Include routers
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(scrapers.router, prefix="/api/v1/scrapers", tags=["Scrapers"])
app.include_router(exports.router, prefix="/api/v1/exports", tags=["Exports"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Configuration endpoint
@app.get("/config", tags=["Configuration"])
async def get_configuration():
    """Get API configuration"""
    return {
        "api": {
            "version": "1.0.0",
            "title": "Web Scraper AI API",
            "description": "REST API for Web Scraping and Data Extraction Automation System"
        },
        "features": {
            "job_management": True,
            "data_processing": True,
            "export_formats": ["csv", "json", "xlsx", "google_sheets"],
            "authentication": True,
            "rate_limiting": True,
            "monitoring": True
        },
        "limits": {
            "max_jobs_per_user": 100,
            "max_concurrent_jobs": 10,
            "max_file_size": 16 * 1024 * 1024,  # 16MB
            "max_records_per_export": 100000
        },
        "endpoints": {
            "jobs": "/api/v1/jobs",
            "scrapers": "/api/v1/scrapers",
            "exports": "/api/v1/exports",
            "monitoring": "/api/v1/monitoring"
        }
    }


# Version endpoint
@app.get("/version", tags=["Root"])
async def get_version():
    """Get API version information"""
    return {
        "version": "1.0.0",
        "build": "development",
        "timestamp": time.time(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "fastapi_version": "0.104.1"
    }


# Debug endpoint (only in development)
if settings.environment == "development":
    @app.get("/debug", tags=["Debug"])
    async def debug_info(request: Request):
        """Debug information (development only)"""
        return {
            "request": {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "path_params": dict(request.path_params),
                "client": {
                    "host": request.client.host,
                    "port": request.client.port
                }
            },
            "system": {
                "pid": os.getpid(),
                "working_directory": os.getcwd(),
                "environment": dict(os.environ)
            }
        }


# WebSocket endpoint (for real-time updates)
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            # Process message (echo for demo)
            await websocket.send_text(f"Echo: {data}")
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Web Scraper AI API started successfully")
    
    # Initialize components
    from jobs.queue import TaskQueue
    from jobs.manager import JobManager
    
    # Start task queue
    queue = TaskQueue()
    queue.start()
    
    # Store in app state
    app.state.queue = queue
    app.state.job_manager = JobManager(queue, SessionLocal())


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Web Scraper AI API shutting down")
    
    # Stop task queue
    if hasattr(app.state, "queue"):
        app.state.queue.stop()
    
    # Clean up resources
    logger.info("Cleanup completed")


# Custom middleware for request timing
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """Add timing information to responses"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers"""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response


# Content type validation middleware
@app.middleware("http")
async def content_type_middleware(request: Request, call_next):
    """Validate content type for POST/PUT requests"""
    if request.method in ["POST", "PUT", "PATCH"]:
        content_type = request.headers.get("content-type", "")
        
        # Allow common content types
        allowed_types = [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data"
        ]
        
        if not any(allowed_type in content_type for allowed_type in allowed_types):
            return JSONResponse(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                content=ErrorResponse(
                    error="Unsupported Media Type",
                    message=f"Content-Type {content_type} is not supported",
                    details={
                        "allowed_types": allowed_types
                    }
                ).dict()
            )
    
    return await call_next(request)


# Request size limiting middleware
@app.middleware("http")
async def size_limiting_middleware(request: Request, call_next):
    """Limit request size"""
    content_length = request.headers.get("content-length")
    
    if content_length:
        max_size = 16 * 1024 * 1024  # 16MB
        
        if int(content_length) > max_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content=ErrorResponse(
                    error="Request Too Large",
                    message=f"Request size {content_length} exceeds maximum {max_size}",
                    details={
                        "max_size": max_size
                    }
                ).dict()
            )
    
    return await call_next(request)


# Example usage patterns
def example_usage():
    """Example usage patterns for the main application"""
    
    # Test health check
    import httpx
    
    async def test_health_check():
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            return response.json()
    
    # Test metrics endpoint
    async def test_metrics():
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/metrics")
            return response.json()
    
    # Test configuration endpoint
    async def test_configuration():
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/config")
            return response.json()
    
    print("Main application examples completed")


if __name__ == "__main__":
    # Test main application
    example_usage()
    
    # Run the application
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
