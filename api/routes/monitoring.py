"""
Monitoring API Routes

This module defines API endpoints for system monitoring, health checks,
performance metrics, and real-time status updates.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import logging
import psutil
import time
from datetime import datetime, timedelta

from ..dependencies import get_database, get_current_admin_user, get_system_metrics, get_health_status
from ..models import HealthCheck, SystemMetrics, Alert, PerformanceMetrics

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Get system metrics
        metrics = get_system_metrics()
        
        # Get health status
        health_status = get_health_status()
        
        return HealthCheck(
            status=health_status["overall"],
            timestamp=time.time(),
            version="1.0.0",
            uptime=time.time(),  # In production, track actual uptime
            database_status=health_status["database"],
            queue_status=health_status["queue"],
            memory_usage=metrics["memory_usage"],
            cpu_usage=metrics["cpu_usage"],
            disk_usage=metrics["disk_usage"]
        )
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics():
    """Get detailed system metrics"""
    try:
        # Get CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Get memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Get disk metrics
        disk = psutil.disk_usage('/')
        
        # Get network metrics
        network = psutil.net_io_counters()
        
        # Get process metrics
        process_count = len(psutil.pids())
        
        # Get boot time
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        return SystemMetrics(
            timestamp=time.time(),
            cpu={
                "usage_percent": cpu_percent,
                "count": cpu_count,
                "frequency": cpu_freq.current if cpu_freq else None,
                "min_frequency": cpu_freq.min if cpu_freq else None,
                "max_frequency": cpu_freq.max if cpu_freq else None
            },
            memory={
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "free": memory.free,
                "percent": memory.percent,
                "active": memory.active,
                "inactive": memory.inactive,
                "buffers": memory.buffers,
                "cached": memory.cached,
                "shared": memory.shared,
                "slab": memory.slab
            },
            swap={
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent
            },
            disk={
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            network={
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
                "errin": network.errin,
                "errout": network.errout,
                "dropin": network.dropin,
                "dropout": network.dropout
            },
            system={
                "uptime": uptime,
                "boot_time": boot_time,
                "process_count": process_count,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system metrics"
        )


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    duration_minutes: int = Query(5, ge=1, le=60),
    db: Session = Depends(get_database),
    current_user = Depends(get_current_admin_user)
):
    """Get performance metrics over time period"""
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=duration_minutes)
        
        # Get performance data from database
        # In production, query performance metrics table
        
        # For demo, return mock data
        performance_data = []
        
        # Generate sample data points
        current_time = start_time
        while current_time <= end_time:
            # Sample metrics
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            network_io = psutil.net_io_counters()
            
            performance_data.append({
                "timestamp": current_time,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": psutil.disk_usage('/').percent,
                "network_io": {
                    "bytes_sent": network_io.bytes_sent,
                    "bytes_recv": network_io.bytes_recv
                },
                "active_connections": len(psutil.net_connections()),
                "request_rate": 0.0,  # Would need to track this
                "error_rate": 0.0,  # Would need to track this
                "response_time": 0.0  # Would need to track this
            })
            
            current_time += timedelta(minutes=1)
        
        return PerformanceMetrics(
            metrics=performance_data,
            period_minutes=duration_minutes,
            start_time=start_time,
            end_time=end_time,
            total_points=len(performance_data)
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance metrics"
        )


@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_database),
    current_user = Depends(get_current_admin_user)
):
    """Get system alerts"""
    try:
        # Query alerts from database
        # In production, query alerts table
        
        # For demo, return mock alerts
        alerts = []
        
        # Generate sample alerts
        if psutil.cpu_percent() > 80:
            alerts.append({
                "id": 1,
                "level": "warning",
                "message": "High CPU usage detected",
                "source": "system_monitor",
                "details": {
                    "cpu_usage": psutil.cpu_percent(),
                    "threshold": 80
                },
                "created_at": datetime.utcnow(),
                "resolved_at": None
            })
        
        if psutil.virtual_memory().percent > 85:
            alerts.append({
                "id": 2,
                "level": "critical",
                "message": "High memory usage detected",
                "source": "system_monitor",
                "details": {
                    "memory_usage": psutil.virtual_memory().percent(),
                    "threshold": 85
                },
                "created_at": datetime.utcnow(),
                "resolved_at": None
            })
        
        if psutil.disk_usage('/').percent > 90:
            alerts.append({
                "id": 3,
                "level": "warning",
                "message": "Low disk space",
                "source": "system_monitor",
                "details": {
                    "disk_usage": psutil.disk_usage('/').percent,
                    "threshold": 90
                },
                "created_at": datetime.utcnow(),
                "resolved_at": None
            })
        
        # Filter alerts
        if severity:
            alerts = [alert for alert in alerts if alert["level"] == severity]
        
        if resolved is not None:
            alerts = [alert for alert in alerts if (alert["resolved_at"] is not None) == resolved]
        
        # Limit results
        alerts = alerts[:limit]
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alerts"
        )


@router.get("/logs")
async def get_logs(
    level: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    since: Optional[str] = None,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_admin_user)
):
    """Get system logs"""
    try:
        # Parse since parameter
        since_time = None
        if since:
            try:
                since_time = datetime.fromisoformat(since)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid since parameter format. Use ISO format."
                )
        
        # Get logs from database
        # In production, query logs table
        
        # For demo, return mock logs
        logs = []
        
        # Generate sample logs
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for i in range(min(limit, 50)):
            log_level = level or log_levels[i % len(log_levels)]
            
            logs.append({
                "id": i + 1,
                "level": log_level,
                "message": f"Sample log message {i + 1}",
                "source": "system",
                "details": {},
                "timestamp": datetime.utcnow() - timedelta(minutes=i),
                "thread": "main"
            })
        
        # Filter by level
        if level:
            logs = [log for log in logs if log["level"] == level.upper()]
        
        # Filter by time
        if since_time:
            logs = [log for log in logs if log["timestamp"] >= since_time]
        
        # Sort by timestamp
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return logs
        
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get logs"
        )


@router.get("/queue-status")
async def get_queue_status():
    """Get task queue status"""
    try:
        from jobs.queue import TaskQueue
        
        queue = TaskQueue()
        
        status = queue.get_queue_status()
        
        return {
            "queue_size": status.get("queue_size", 0),
            "active_jobs": status.get("active_jobs", 0),
            "queued_jobs": status.get("queued_jobs", []),
            "failed_jobs": status.get("failed_jobs", []),
            "success_rate": status.get("success_rate", 0.0),
            "worker_count": status.get("worker_count", 0),
            "last_processed": status.get("last_processed"),
            "queue_health": "healthy" if status.get("active_jobs", 0) < 10 else "degraded"
        }
        
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get queue status"
        )


@router.get("/database-status")
async def get_database_status(
    db: Session = Depends(get_database),
    current_user = Depends(get_current_admin_user)
):
    """Get database connection status"""
    try:
        # Test database connection
        try:
            db.execute("SELECT 1")
            connection_status = "connected"
        except Exception as e:
            connection_status = f"error: {str(e)}"
        
        # Get database stats
        try:
            # For SQLite
            from sqlalchemy import text
            
            # Get table info
            tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            
            # Get database size
            import os
            db_size = os.path.getsize("scraper.db") if os.path.exists("scraper.db") else 0
            
            database_info = {
                "connection_status": connection_status,
                "tables": [table[0] for table in tables],
                "size_bytes": db_size,
                "size_mb": db_size / (1024 * 1024),
                "type": "SQLite"
            }
            
        except Exception as e:
            database_info = {
                "connection_status": connection_status,
                "error": str(e)
            }
        
        return database_info
        
    except Exception as e:
        logger.error(f"Error getting database status: {str(e)}")
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get database status"
        )


@router.get("/job-status/{job_id}")
async def get_job_status(
    job_id: int,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get detailed status for a specific job"""
    try:
        # Get job from database
        from jobs.models import Job as JobModel
        
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
        if not job:
            raise HTTPException(
                status=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check permissions
        if not current_user.is_admin and job.user_id != current_user.id:
            raise HTTPException(
                status=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get detailed status
        status_info = {
            "job_id": job.id,
            "name": job.name,
            "status": job.status,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "updated_at": job.updated_at,
            "records_processed": job.records_processed,
            "records_total": job.records_total,
            "success_rate": job.success_rate,
            "duration": job.duration,
            "error_message": job.error_message,
            "retry_count": job.retry_count,
            "max_retries": job.max_retries,
            "result_path": job.result_path,
            "file_size": job.file_size,
            "is_running": job.is_running,
            "is_finished": job.is_finished,
            "can_retry": job.can_retry,
            "should_retry": job.should_retry,
            "metadata": job.metadata or {}
        }
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {str(e)}")
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job status"
        )


@router.get("/system-info")
async def get_system_info(
    current_user = Depends(get_current_admin_user)
):
    """Get detailed system information"""
    try:
        # Get system information
        import platform
        import socket
        
        system_info = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "architecture": platform.architecture(),
                "node": platform.node(),
                "python_version": platform.python_version()
            },
            "network": {
                "hostname": socket.gethostname(),
                "ip_address": socket.gethostbyname(socket.gethostname()),
                "interfaces": psutil.net_if_addrs()
            },
            "processes": {
                "total": len(psutil.pids()),
                "running": len([p for p in psutil.process_iter() if p.status() == psutil.STATUS_RUNNING])
            },
            "boot_time": psutil.boot_time(),
            "uptime": time.time() - psutil.boot_time()
        }
        
        return system_info
        
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system information"
        )


@router.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring"""
    await websocket.accept()
    
    try:
        while True:
            # Get current metrics
            metrics = get_system_metrics()
            
            # Send metrics
            await websocket.send_json({
                "type": "metrics",
                "data": metrics,
                "timestamp": time.time()
            })
            
            # Wait for client message or send next update
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            
            # Small delay to prevent overwhelming the client
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()


@router.post("/test-performance")
async def test_performance(
    duration_seconds: int = Query(60, ge=10, le=300),
    db: Session = Depends(get_database),
    current_user = Depends(get_current_admin_user)
):
    """Run performance test"""
    try:
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        results = []
        
        while time.time() < end_time:
            # Get current metrics
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            
            results.append({
                "timestamp": time.time(),
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "elapsed": time.time() - start_time
            })
            
            # Small delay
            await asyncio.sleep(1)
        
        # Calculate statistics
        cpu_values = [r["cpu_usage"] for r in results]
        memory_values = [r["memory_usage"] for r in results]
        
        return {
            "duration_seconds": duration_seconds,
            "samples": len(results),
            "cpu": {
                "average": sum(cpu_values) / len(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values),
                "current": cpu_values[-1] if cpu_values else 0
            },
            "memory": {
                "average": sum(memory_values) / len(memory_values),
                "min": min(memory_values),
                "max": max(memory_values),
                "current": memory_values[-1] if memory_values else 0
            },
            "elapsed_time": time.time() - start_time,
            "samples_per_second": len(results) / duration_seconds
        }
        
    except Exception as e:
        logger.error(f"Error in performance test: {str(e)}")
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Performance test failed"
        )


# Example usage patterns
def example_usage():
    """Example usage patterns for monitoring API"""
    
    # Health check
    health_data = HealthCheck(
        status="healthy",
        timestamp=time.time(),
        version="1.0.0",
        uptime=3600.0,
        database_status="connected",
        queue_status="healthy",
        memory_usage=45.2,
        cpu_usage=23.5,
        disk_usage=67.8
    )
    
    # System metrics
    system_metrics = SystemMetrics(
        timestamp=time.time(),
        cpu={"usage_percent": 25.5},
        memory={"total": 8589934592, "used": 2147483648, "percent": 25.0},
        disk={"total": 500110592, "used": 33554432, "percent": 67.0},
        network={"bytes_sent": 12345678, "bytes_recv": 98765432},
        system={"uptime": 3600.0, "process_count": 156}
    )
    
    print("Monitoring API examples completed")


if __name__ == "__main__":
    # Test monitoring API
    example_usage()
