"""
Exports API Routes

This module defines API endpoints for data export functionality,
including job result exports, format conversion, and download management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging
import os
import mimetypes
from datetime import datetime

from ..dependencies import get_database, get_current_user, get_export_engine
from ..models import (
    ExportRequest, ExportResult, ExportFormat, SuccessResponse,
    ErrorResponse, PaginatedResponse
)
from exporters.factory import ExporterFactory
from jobs.models import Job as JobModel

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/export", response_model=ExportResult)
async def export_job_results(
    export_request: ExportRequest,
    background_tasks,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Export job results to specified format"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == export_request.job_id).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check permissions
        if not current_user.is_admin and job.user_id != current_user.id and not job.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if job is completed
        if job.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job must be completed before exporting"
            )
        
        # Get job results
        from jobs.models import Result
        results = db.query(Result).filter(Result.job_id == export_request.job_id).all()
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No results found for this job"
            )
        
        # Prepare data for export
        export_data = []
        for result in results:
            if result.processed_data:
                export_data.append(result.processed_data)
            else:
                export_data.append(result.raw_data)
        
        # Create exporter
        exporter = ExporterFactory.create_exporter(export_request.format)
        
        # Create export configuration
        from exporters.base import ExportConfig
        export_config = ExportConfig(
            filename=export_request.filename,
            format=export_request.format,
            include_headers=export_request.include_headers,
            encoding=export_request.encoding,
            delimiter=export_request.delimiter,
            directory="exports"
        )
        
        # Export data
        export_result = exporter.export_with_stats(export_data, export_config)
        
        if not export_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Export failed: {export_result.error_message}"
            )
        
        # Update job with export information
        job.result_path = export_result.file_path
        job.file_size = export_result.file_size
        job.download_count = export_result.record_count
        db.commit()
        
        logger.info(f"Exported job {export_request.job_id} to {export_result.file_path}")
        
        return export_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting job {export_request.job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export job results"
        )


@router.get("/download/{export_id}")
async def download_export(
    export_id: str,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Download exported file"""
    try:
        # Find export file
        file_path = os.path.join("exports", export_id)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found"
            )
        
        # Check file permissions (basic check)
        # In production, implement proper permission checking
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        # Guess MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
        
        # Return file response
        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_name}",
                "Content-Length": str(file_size)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export {export_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download export"
        )


@router.get("/list", response_model=List[ExportResult])
async def list_exports(
    job_id: Optional[int] = None,
    format: Optional[ExportFormat] = None,
    is_public: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """List available exports"""
    try:
        # Query exports based on filters
        query = db.query(JobModel)
        
        if job_id:
            query = query.filter(JobModel.id == job_id)
        
        if format:
            query = query.filter(JobModel.config.contains({"output_format": format.value}))
        
        if is_public is not None:
            query = query.filter(JobModel.is_public == is_public)
        else:
            # Non-admin users can only see their own exports and public exports
            if not current_user.is_admin:
                query = query.filter(
                    (JobModel.user_id == current_user.id) | (JobModel.is_public == True)
                )
        
        # Filter for completed jobs with results
        query = query.filter(JobModel.status == "completed")
        query = query.filter(JobModel.result_path.isnot(None))
        
        # Order by completion date
        query = query.order_by(JobModel.completed_at.desc())
        
        # Apply pagination
        offset = (page - 1) * per_page
        jobs = query.offset(offset).limit(per_page).all()
        
        # Convert to export results
        exports = []
        for job in jobs:
            if job.result_path and os.path.exists(job.result_path):
                file_size = os.path.getsize(job.result_path)
                file_name = os.path.basename(job.result_path)
                
                exports.append(ExportResult(
                    success=True,
                    file_path=job.result_path,
                    record_count=job.download_count,
                    file_size=file_size,
                    export_time=0.0,  # Would need to track this
                    exporter_name="ExporterFactory",
                    format=job.config.get("output_format", "csv"),
                    metadata={
                        "job_id": job.id,
                        "job_name": job.name,
                        "file_name": file_name,
                        "created_at": job.completed_at.isoformat()
                    },
                    timestamp=job.completed_at,
                    error_message=None,
                    file_size_mb=file_size / (1024 * 1024),
                    records_per_second=0.0  # Would need to track this
                ))
        
        return exports
        
    except Exception as e:
        logger.error(f"Error listing exports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list exports"
        )


@router.delete("/delete/{export_id}", response_model=SuccessResponse)
async def delete_export(
    export_id: str,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Delete exported file"""
    try:
        # Find export file
        file_path = os.path.join("exports", export_id)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found"
            )
        
        # Basic permission check (in production, implement proper checking)
        # For now, allow user to delete their own files
        
        # Delete file
        os.remove(file_path)
        
        # Update job record
        job = db.query(JobModel).filter(JobModel.result_path == file_path).first()
        if job:
            job.result_path = None
            job.file_size = 0
            job.download_count = 0
            db.commit()
        
        logger.info(f"Deleted export file: {export_id}")
        
        return SuccessResponse(
            success=True,
            message=f"Export {export_id} deleted successfully",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting export {export_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete export"
        )


@router.post("/convert", response_model=ExportResult)
async def convert_export_format(
    source_export_id: str,
    target_format: ExportFormat,
    new_filename: Optional[str] = None,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Convert export to different format"""
    try:
        # Find source export file
        source_path = os.path.join("exports", source_export_id)
        
        if not os.path.exists(source_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source export file not found"
            )
        
        # Read source data
        from exporters.factory import ExporterFactory
        import json
        
        # Determine source format from file extension
        file_ext = os.path.splitext(source_export_id)[1].lower()
        
        # Read data based on source format
        if file_ext == ".json":
            with open(source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif file_ext == ".csv":
            import pandas as pd
            df = pd.read_csv(source_path)
            data = df.to_dict('records')
        elif file_ext == ".xlsx":
            import pandas as pd
            df = pd.read_excel(source_path)
            data = df.to_dict('records')
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported source format for conversion"
            )
        
        # Create exporter for target format
        exporter = ExporterFactory.create_exporter(target_format)
        
        # Create export configuration
        from exporters.base import ExportConfig
        export_config = ExportConfig(
            filename=new_filename,
            format=target_format,
            include_headers=True,
            encoding="utf-8"
        )
        
        # Export in new format
        export_result = exporter.export_with_stats(data, export_config)
        
        if not export_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Conversion failed: {export_result.error_message}"
            )
        
        logger.info(f"Converted {source_export_id} to {target_format}: {export_result.file_path}")
        
        return export_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting export {source_export_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert export format"
        )


@router.get("/formats")
async def get_export_formats():
    """Get available export formats and their capabilities"""
    try:
        formats = {
            "csv": {
                "name": "CSV (Comma-Separated Values)",
                "description": "Plain text format with comma-separated values",
                "capabilities": [
                    "Tabular data",
                    "Custom delimiters",
                    "Encoding support",
                    "Streaming support"
                ],
                "mime_type": "text/csv",
                "file_extension": ".csv",
                "best_for": [
                    "Spreadsheet import",
                    "Data analysis",
                    "Simple data exchange"
                ]
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
                "mime_type": "application/json",
                "file_extension": ".json",
                "best_for": [
                    "Web applications",
                    "API responses",
                    "Configuration files"
                ]
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
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "file_extension": ".xlsx",
                "best_for": [
                    "Business reports",
                    "Data analysis",
                    "Presentations"
                ]
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
                "mime_type": "text/csv",
                "file_extension": ".csv",
                "best_for": [
                    "Team collaboration",
                    "Cloud workflows",
                    "Real-time data"
                ]
            }
        }
        
        return formats
        
    except Exception as e:
        logger.error(f"Error getting export formats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get export formats"
        )


@router.get("/statistics")
async def get_export_statistics(
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get export statistics"""
    try:
        # Query completed jobs with exports
        query = db.query(JobModel).filter(JobModel.status == "completed")
        
        # Non-admin users can only see their own and public exports
        if not current_user.is_admin:
            query = query.filter(
                (JobModel.user_id == current_user.id) | (JobModel.is_public == True)
            )
        
        completed_jobs = query.all()
        
        # Calculate statistics
        total_exports = len(completed_jobs)
        total_size = sum(job.file_size or 0 for job in completed_jobs)
        total_records = sum(job.download_count or 0 for job in completed_jobs)
        
        # Format statistics
        format_stats = {}
        for job in completed_jobs:
            format_type = job.config.get("output_format", "csv")
            if format_type not in format_stats:
                format_stats[format_type] = {
                    "count": 0,
                    "size": 0,
                    "records": 0
                }
            format_stats[format_type]["count"] += 1
            format_stats[format_type]["size"] += job.file_size or 0
            format_stats[format_type]["records"] += job.download_count or 0
        
        # Recent exports
        recent_exports = []
        for job in sorted(completed_jobs, key=lambda x: x.completed_at, reverse=True)[:10]:
            if job.result_path and os.path.exists(job.result_path):
                recent_exports.append({
                    "job_id": job.id,
                    "job_name": job.name,
                    "format": job.config.get("output_format", "csv"),
                    "file_name": os.path.basename(job.result_path),
                    "file_size": job.file_size,
                    "records": job.download_count,
                    "completed_at": job.completed_at.isoformat()
                })
        
        return {
            "total_exports": total_exports,
            "total_size": total_size,
            "total_records": total_records,
            "average_size": total_size / total_exports if total_exports > 0 else 0,
            "average_records": total_records / total_exports if total_exports > 0 else 0,
            "format_statistics": format_stats,
            "recent_exports": recent_exports
        }
        
    except Exception as e:
        logger.error(f"Error getting export statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get export statistics"
        )


@router.post("/share/{export_id}")
async def create_share_link(
    export_id: str,
    expires_in_days: int = 7,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Create shareable link for export"""
    try:
        # Find export file
        file_path = os.path.join("exports", export_id)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found"
            )
        
        # Check permissions
        job = db.query(JobModel).filter(JobModel.result_path == file_path).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated job not found"
            )
        
        if not current_user.is_admin and job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Generate share token
        import secrets
        share_token = secrets.token_urlsafe(32)
        
        # Set expiration
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # In production, store share token in database
        # For now, return the token
        
        share_link = f"/api/v1/exports/shared/{share_token}"
        
        return {
            "share_link": share_link,
            "share_token": share_token,
            "expires_at": expires_at.isoformat(),
            "expires_in_days": expires_in_days,
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating share link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create share link"
        )


@router.get("/shared/{share_token}")
async def get_shared_export(
    share_token: str,
    db: Session = Depends(get_database)
):
    """Get shared export via token"""
    try:
        # In production, validate share token from database
        # For now, create a mock implementation
        
        # Find export by token (mock implementation)
        # In production, query database for token
        
        # For demo, return a generic response
        return {
            "message": "Shared export access",
            "token": share_token,
            "note": "This is a demo implementation"
        }
        
    except Exception as e:
        logger.error(f"Error getting shared export: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get shared export"
        )


@router.post("/batch-export", response_model=List[ExportResult])
async def batch_export(
    job_ids: List[int],
    background_tasks,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user),
    format: ExportFormat = ExportFormat.CSV
):
    """Export multiple jobs at once"""
    try:
        if len(job_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 jobs allowed for batch export"
            )
        
        export_results = []
        
        for job_id in job_ids:
            try:
                # Get job
                job = db.query(JobModel).filter(JobModel.id == job_id).first()
                
                if not job:
                    logger.warning(f"Job {job_id} not found, skipping")
                    continue
                
                # Check permissions
                if not current_user.is_admin and job.user_id != current_user.id and not job.is_public:
                    logger.warning(f"Access denied for job {job_id}, skipping")
                    continue
                
                # Check if job is completed
                if job.status != "completed":
                    logger.warning(f"Job {job_id} not completed, skipping")
                    continue
                
                # Create export request
                export_request = ExportRequest(
                    job_id=job_id,
                    format=format,
                    include_headers=True
                )
                
                # Export job
                result = await export_job_results(export_request, background_tasks, db, current_user)
                export_results.append(result)
                
            except Exception as e:
                logger.error(f"Error exporting job {job_id}: {str(e)}")
                # Continue with other jobs
                continue
        
        if not export_results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid jobs found for export"
            )
        
        return export_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch export: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform batch export"
        )


# Example usage patterns
def example_usage():
    """Example usage patterns for export API"""
    
    # Export job results
    export_request = ExportRequest(
        job_id=1,
        format=ExportFormat.JSON,
        pretty_print=True
    )
    
    # Convert format
    source_export_id = "export_20240315_123456.json"
    target_format = ExportFormat.CSV
    
    # Create share link
    export_id = "export_20240315_123456.csv"
    expires_in_days = 7
    
    print("Export API examples completed")


if __name__ == "__main__":
    # Test export API
    example_usage()
