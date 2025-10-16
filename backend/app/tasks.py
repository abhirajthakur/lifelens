import base64
import logging
from uuid import UUID

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core import config
from app.models.media import FileType
from app.services import ml_services

celery_app = Celery(
    "media_tasks", broker="redis://localhost:6379", backend="redis://localhost:6379"
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,
)

DATABASE_URL = config.DATABASE_URL
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    return SessionLocal()


@celery_app.task(
    name="process_media",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes between retries
    retry_jitter=True,
)
def process_media(self, media_id_str: str, file_type: str, file_contents_base64: str):
    db = None
    try:
        media_id = UUID(media_id_str)
        db = get_db_session()

        logging.info(f"Starting processing for media_id: {media_id}, type: {file_type}")

        success = False
        contents = base64.b64decode(file_contents_base64)

        if file_type == FileType.IMAGE.value or file_type == "image":
            success = ml_services.process_image(db, media_id, contents)
        elif file_type == FileType.AUDIO.value or file_type == "audio":
            success = ml_services.process_audio(db, media_id, contents)
        elif file_type == FileType.TEXT.value or file_type == "text":
            success = ml_services.process_text(db, media_id, contents)
        else:
            logging.warning(
                f"Unsupported file type: {file_type} for media_id: {media_id}"
            )
            return {"status": "skipped", "reason": "unsupported_type"}

        if success:
            logging.info(f"Successfully processed media_id: {media_id}")
            return {"status": "success", "media_id": media_id_str}
        else:
            logging.error(f"Processing failed for media_id: {media_id}")
            raise Exception(f"Processing failed for media_id: {media_id}")

    except Exception as e:
        logging.error(f"Error processing media {media_id_str}: {str(e)}", exc_info=True)

        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logging.error(f"Max retries exceeded for media_id: {media_id_str}")
            return {"status": "failed", "error": str(e), "media_id": media_id_str}

    finally:
        if db:
            db.close()


@celery_app.task(name="cleanup_failed_tasks")
def cleanup_failed_tasks():
    try:
        logging.info("Running cleanup of failed tasks")

        # Inspect Celery workers and get failed tasks
        inspect = celery_app.control.inspect()

        # Get registered tasks
        registered = inspect.registered()
        logging.info(f"Registered tasks: {registered}")

        # Additional cleanup logic can be added here
        # For example, marking media as failed in database

        return {"status": "completed"}

    except Exception as e:
        logging.error(f"Error in cleanup task: {e}")
        return {"status": "error", "error": str(e)}


celery_app.conf.beat_schedule = {
    "cleanup-failed-tasks": {
        "task": "cleanup_failed_tasks",
        "schedule": 3600.0,  # Run every hour
    },
}


@celery_app.task(name="get_task_status")
def get_task_status(task_id: str):
    try:
        result = celery_app.AsyncResult(task_id)

        return {
            "task_id": task_id,
            "status": result.state,
            "result": result.result if result.ready() else None,
            "info": result.info,
        }
    except Exception as e:
        logging.error(f"Error getting task status for {task_id}: {e}")
        return {"error": str(e)}
