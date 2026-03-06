"""
Jobs API Routes

This module defines API endpoints for job management, including CRUD operations,
scheduling, and monitoring.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from ..dependencies import get_database, get_current_user, get_current_admin_user, get_job_manager
from ..models import (
    JobCreateRequest, JobUpdateRequest, JobResponse, JobSummary,
    JobScheduleRequest, JobStatistics, JobStatus, JobPriority,
    PaginatedResponse, SuccessResponse, ErrorResponse
)
from jobs.models import Job as JobModel
from jobs.manager import JobManager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[JobSummary])
async def get_jobs(
    status: Optional[JobStatus] = None,
    priority: Optional[JobPriority] = None,
    tags: Optional[List[str]] = None,
    is_public: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|name|status|priority)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get list of jobs with filtering and pagination"""
    try:
        # Build query
        query = db.query(JobModel)
        
        # Apply filters
        if status:
            query = query.filter(JobModel.status == status.value)
        
        if priority:
            query = query.filter(JobModel.priority == priority.value)
        
        if is_public is not None:
            query = query.filter(JobModel.is_public == is_public)
        else:
            # Non-admin users can only see their own jobs and public jobs
            if not current_user.is_admin:
                query = query.filter(
                    (JobModel.user_id == current_user.id) | (JobModel.is_public == True)
                )
        
        if tags:
            for tag in tags:
                query = query.filter(JobModel.tags.contains([tag]))
        
        # Apply sorting
        if sort_by == "created_at":
            query = query.order_by(
                JobModel.created_at.desc() if sort_order == "desc" else JobModel.created_at.asc()
            )
        elif sort_by == "name":
            query = query.order_by(
                JobModel.name.desc() if sort_order == "desc" else JobModel.name.asc()
            )
        elif sort_by == "status":
            query = query.order_by(
                JobModel.status.desc() if sort_order == "desc" else JobModel.status.asc()
            )
        elif sort_by == "priority":
            query = query.order_by(
                JobModel.priority.desc() if sort_order == "desc" else JobModel.priority.asc()
            )
        
        # Count total
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        jobs = query.offset(offset).limit(per_page).all()
        
        # Convert to response models
        job_summaries = []
        for job in jobs:
            job_summaries.append(JobSummary(
                id=job.id,
                name=job.name,
                status=JobStatus(job.status),
                priority=JobPriority(job.priority),
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                records_processed=job.records_processed,
                records_total=job.records_total,
                success_rate=job.success_rate,
                duration=job.duration,
                tags=job.tags or []
            ))
        
        return job_summaries
        
    except Exception as e:
        logger.error(f"Error getting jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get detailed information about a specific job"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
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
        
        return JobResponse(
            id=job.id,
            name=job.name,
            description=job.description,
            url=job.url,
            selectors=job.selectors,
            scraper_type=job.config.get("scraper_type", "static"),
            status=JobStatus(job.status),
            priority=JobPriority(job.priority),
            delay=job.config.get("delay", 1.0),
            max_retries=job.max_retries,
            timeout=job.config.get("timeout", 30),
            user_agent=job.config.get("user_agent", "WebScraper/1.0"),
            headers=job.config.get("headers"),
            cookies=job.config.get("cookies"),
            proxy=job.config.get("proxy"),
            pagination=job.config.get("pagination"),
            extract_links=job.config.get("extract_links", False),
            extract_images=job.config.get("extract_images", False),
            extract_metadata=job.config.get("extract_metadata", True),
            continue_on_error=job.config.get("continue_on_error", True),
            ignore_ssl_errors=job.config.get("ignore_ssl_errors", False),
            output_format=job.config.get("output_format", "csv"),
            include_headers=job.config.get("include_headers", True),
            encoding=job.config.get("encoding", "utf-8"),
            tags=job.tags or [],
            is_public=job.is_public,
            metadata=job.metadata or {},
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            updated_at=job.updated_at,
            records_processed=job.records_processed,
            records_total=job.records_total,
            result_path=job.result_path,
            file_size=job.file_size,
            error_message=job.error_message,
            retry_count=job.retry_count,
            duration=job.duration,
            success_rate=job.success_rate,
            is_running=job.is_running,
            is_finished=job.is_finished,
            can_retry=job.can_retry,
            should_retry=job.should_retry
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job"
        )


@router.post("/", response_model=JobResponse)
async def create_job(
    job_request: JobCreateRequest,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Create a new scraping job"""
    try:
        # Create job configuration
        job_config = job_request.dict()
        job_config["user_id"] = current_user.id
        
        # Create job using job manager
        job = await job_manager.create_job(job_config)
        
        # Return created job
        return await get_job(job.id, db, current_user)
        
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_update: JobUpdateRequest,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Update an existing job"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check permissions
        if not current_user.is_admin and job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if job can be updated
        if job.status in [JobStatus.RUNNING, JobStatus.PAUSED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update running job"
            )
        
        # Update job fields
        update_data = job_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(job, field):
                setattr(job, field, value)
        
        # Update configuration if provided
        if "url" in update_data or "selectors" in update_data:
            if not job.config:
                job.config = {}
            
            if "url" in update_data:
                job.config["url"] = update_data["url"]
                job.url = update_data["url"]
            
            if "selectors" in update_data:
                job.config["selectors"] = update_data["selectors"]
                job.selectors = update_data["selectors"]
        
        job.updated_at = datetime.utcnow()
        db.commit()
        
        return await get_job(job_id, db, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job"
        )


@router.delete("/{job_id}", response_model=SuccessResponse)
async def delete_job(
    job_id: int,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Delete a job"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check permissions
        if not current_user.is_admin and job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if job can be deleted
        if job.status == JobStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete running job"
            )
        
        # Delete job
        db.delete(job)
        db.commit()
        
        return SuccessResponse(
            success=True,
            message=f"Job {job_id} deleted successfully",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
        )


@router.post("/{job_id}/start", response_model=SuccessResponse)
async def start_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Start a job"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check permissions
        if not current_user.is_admin and job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Start job
        success = await job_manager.start_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to start job"
            )
        
        return SuccessResponse(
            success=True,
            message=f"Job {job_id} started successfully",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start job"
        )


@router.post("/{job_id}/stop", response_model=SuccessResponse)
async def stop_job(
    job_id: int,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Stop a running job"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check permissions
        if not current_user.is_admin and job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Stop job
        success = await job_manager.stop_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to stop job"
            )
        
        return SuccessResponse(
            success=True,
            message=f"Job {job_id} stopped successfully",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop job"
        )


@router.post("/{job_id}/pause", response_model=SuccessResponse)
async def pause_job(
    job_id: int,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Pause a running job"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check permissions
        if not current_user.is_admin and job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Pause job
        success = await job_manager.pause_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to pause job"
            )
        
        return SuccessResponse(
            success=True,
            message=f"Job {job_id} paused successfully",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause job"
        )


@router.post("/{job_id}/resume", response_model=SuccessResponse)
async def resume_job(
    job_id: int,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Resume a paused job"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check permissions
        if not current_user.is_admin and job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Resume job
        success = await job_manager.resume_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to resume job"
            )
        
        return SuccessResponse(
            success=True,
            message=f"Job {job_id} resumed successfully",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume job"
        )


@router.post("/{job_id}/retry", response_model=SuccessResponse)
async def retry_job(
    job_id: int,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Retry a failed job"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check permissions
        if not current_user.is_admin and job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if job can be retried
        if not job.can_retry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job cannot be retried (max retries reached)"
            )
        
        # Retry job
        success = await job_manager.retry_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to retry job"
            )
        
        return SuccessResponse(
            success=True,
            message=f"Job {job_id} retried successfully",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry job"
        )


@router.get("/{job_id}/statistics", response_model=JobStatistics)
async def get_job_statistics(
    job_id: int,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user)
):
    """Get detailed statistics for a job"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
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
        
        # Get statistics from job manager
        job_manager = get_job_manager()
        stats = job_manager.get_job_statistics(job_id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job statistics not found"
            )
        
        return JobStatistics(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job statistics {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job statistics"
        )


@router.post("/{job_id}/schedule", response_model=SuccessResponse)
async def schedule_job(
    job_id: int,
    schedule_request: JobScheduleRequest,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Schedule a job with cron expression"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check permissions
        if not current_user.is_admin and job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Add schedule
        scheduler = job_manager.scheduler
        success = scheduler.add_schedule(
            job_id=job_id,
            cron_expression=schedule_request.cron_expression,
            timezone=schedule_request.timezone
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to schedule job"
            )
        
        return SuccessResponse(
            success=True,
            message=f"Job {job_id} scheduled successfully",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule job"
        )


@router.delete("/{job_id}/schedule", response_model=SuccessResponse)
async def remove_schedule(
    job_id: int,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Remove job schedule"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check permissions
        if not current_user.is_admin and job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Remove schedule
        scheduler = job_manager.scheduler
        schedules = scheduler.get_schedules_for_job(job_id)
        
        if not schedules:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No schedule found for this job"
            )
        
        success = scheduler.remove_schedule(schedules[0].id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove schedule"
            )
        
        return SuccessResponse(
            success=True,
            message=f"Schedule for job {job_id} removed successfully",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing schedule for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove schedule"
        )


@router.get("/{job_id}/clone", response_model=JobResponse)
async def clone_job(
    job_id: int,
    new_name: Optional[str] = None,
    db: Session = Depends(get_database),
    current_user = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Clone a job configuration"""
    try:
        # Get job from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
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
        
        # Clone job
        cloned_job_id = job_manager.clone_job(job_id, new_name)
        
        if not cloned_job_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to clone job"
            )
        
        return await get_job(cloned_job_id, db, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone job"
        )


# Admin-only endpoints
@router.get("/admin/all", response_model=List[JobSummary])
async def get_all_jobs_admin(
    status: Optional[JobStatus] = None,
    priority: Optional[JobPriority] = None,
    tags: Optional[List[str]] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|name|status|priority)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_database),
    current_user = Depends(get_current_admin_user)
):
    """Get all jobs (admin only)"""
    try:
        # Build query (no user filtering for admin)
        query = db.query(JobModel)
        
        # Apply filters
        if status:
            query = query.filter(JobModel.status == status.value)
        
        if priority:
            query = query.filter(JobModel.priority == priority.value)
        
        if tags:
            for tag in tags:
                query = query.filter(JobModel.tags.contains([tag]))
        
        # Apply sorting
        if sort_by == "created_at":
            query = query.order_by(
                JobModel.created_at.desc() if sort_order == "desc" else JobModel.created_at.asc()
            )
        elif sort_by == "name":
            query = query.order_by(
                JobModel.name.desc() if sort_order == "desc" else JobModel.name.asc()
            )
        elif sort_by == "status":
            query = query.order_by(
                JobModel.status.desc() if sort_order == "desc" else JobModel.status.asc()
            )
        elif sort_by == "priority":
            query = query.order_by(
                JobModel.priority.desc() if sort_order == "desc" else JobModel.priority.asc()
            )
        
        # Count total
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        jobs = query.offset(offset).limit(per_page).all()
        
        # Convert to response models
        job_summaries = []
        for job in jobs:
            job_summaries.append(JobSummary(
                id=job.id,
                name=job.name,
                status=JobStatus(job.status),
                priority=JobPriority(job.priority),
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                records_processed=job.records_processed,
                records_total=job.records_total,
                success_rate=job.success_rate,
                duration=job.duration,
                tags=job.tags or []
            ))
        
        return job_summaries
        
    except Exception as e:
        logger.error(f"Error getting all jobs (admin): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
        )


@router.delete("/admin/cleanup", response_model=SuccessResponse)
async def cleanup_completed_jobs(
    days: int = Query(30, ge=1, le=365),
    current_user = Depends(get_current_admin_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Clean up old completed jobs (admin only)"""
    try:
        deleted_count = job_manager.cleanup_completed_jobs(days)
        
        return SuccessResponse(
            success=True,
            message=f"Cleaned up {deleted_count} old jobs",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error cleaning up jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup jobs"
        )


@router.get("/admin/statistics")
async def get_system_statistics(
    current_user = Depends(get_current_admin_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get system-wide statistics (admin only)"""
    try:
        stats = job_manager.get_system_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting system statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system statistics"
        )
