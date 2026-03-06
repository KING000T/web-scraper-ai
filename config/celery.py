"""
Celery Configuration

This module contains Celery configuration and task definitions.
"""

from celery import Celery
from kombu import Queue
import logging

from .settings import get_celery_config

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery("web_scraper")

# Configure Celery
celery_config = get_celery_config()
celery_app.conf.update(celery_config)

# Define task queues
celery_app.conf.task_queues = (
    Queue('scraping', celery_app.conf.task_routes['scrapers.tasks.*']),
    Queue('processing', celery_app.conf.task_routes['processors.tasks.*']),
    Queue('exporting', celery_app.conf.task_routes['exporters.tasks.*']),
)

# Task routing
celery_app.conf.task_routes = {
    'scrapers.tasks.*': {'queue': 'scraping'},
    'processors.tasks.*': {'queue': 'processing'},
    'exporters.tasks.*': {'queue': 'exporting'},
}

# Task annotations
celery_app.conf.task_annotations = {
    '*': {'rate_limit': '10/m'},
    'scrapers.tasks.*': {'rate_limit': '5/m'},
    'processors.tasks.*': {'rate_limit': '20/m'},
    'exporters.tasks.*': {'rate_limit': '10/m'},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-old-logs': {
        'task': 'jobs.tasks.cleanup_old_logs',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-temp-files': {
        'task': 'jobs.tasks.cleanup_temp_files',
        'schedule': 1800.0,  # Every 30 minutes
    },
    'backup-database': {
        'task': 'jobs.tasks.backup_database',
        'schedule': 86400.0,  # Every day
    },
}

# Worker configuration
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_acks_late = True
celery_app.conf.worker_max_tasks_per_child = 1000
celery_app.conf.worker_disable_rate_limits = False

# Result backend configuration
celery_app.conf.result_expires = 3600  # 1 hour
celery_app.conf.result_serializer = 'json'
celery_app.conf.result_compression = 'gzip'

# Error handling
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.task_acks_on_failure_or_timeout = False
celery_app.conf.task_ignore_result = False

# Security
celery_app.conf.accept_content = ['json']
celery_app.conf.result_serializer = 'json'
celery_app.conf.task_serializer = 'json'

# Monitoring
celery_app.conf.worker_send_task_events = True
celery_app.conf.task_send_sent_event = True
celery_app.conf.task_send_started_event = True
celery_app.conf.task_send_success_event = True
celery_app.conf.task_send_failure_event = True
celery_app.conf.task_send_retry_event = True
celery_app.conf.task_send_revoked_event = True

# Task utilities
def get_task_info(task_id: str):
    """Get task information"""
    result = celery_app.AsyncResult(task_id)
    return {
        'task_id': task_id,
        'status': result.status,
        'result': result.result,
        'traceback': result.traceback,
        'date_done': result.date_done,
        'meta': result.info if result.status == 'SUCCESS' else None
    }


def revoke_task(task_id: str, terminate: bool = False):
    """Revoke a task"""
    celery_app.control.revoke(task_id, terminate=terminate)
    return {'task_id': task_id, 'revoked': True, 'terminated': terminate}


def get_active_tasks():
    """Get list of active tasks"""
    inspect = celery_app.control.inspect()
    active_tasks = inspect.active()
    return active_tasks


def get_scheduled_tasks():
    """Get list of scheduled tasks"""
    inspect = celery_app.control.inspect()
    scheduled_tasks = inspect.scheduled()
    return scheduled_tasks


def get_reserved_tasks():
    """Get list of reserved tasks"""
    inspect = celery_app.control.inspect()
    reserved_tasks = inspect.reserved()
    return reserved_tasks


# Health check
def check_celery_health():
    """Check Celery health"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if not stats:
            return {'status': 'unhealthy', 'message': 'No workers available'}
        
        return {
            'status': 'healthy',
            'workers': len(stats),
            'stats': stats
        }
    except Exception as e:
        return {'status': 'unhealthy', 'message': str(e)}


# Task decorators
from celery import Task

class BaseTask(Task):
    """Base task class with error handling"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Task success callback"""
        logger.info(f"Task {task_id} completed successfully")
        super().on_success(retval, task_id, args, kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Task failure callback"""
        logger.error(f"Task {task_id} failed: {str(exc)}")
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Task retry callback"""
        logger.warning(f"Task {task_id} retrying: {str(exc)}")
        super().on_retry(exc, task_id, args, kwargs, einfo)


# Configure base task
celery_app.Task = BaseTask


# Import tasks (will be created later)
try:
    from jobs.tasks import *
except ImportError:
    logger.warning("Tasks not yet imported")


if __name__ == "__main__":
    # Start Celery worker
    celery_app.start()
