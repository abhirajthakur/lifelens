import base64
from typing import Annotated, cast

from celery import Task
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.db import DBSession
from app.core.deps import CurrentUser
from app.models.media import FileType, Media
from app.models.user import User
from app.tasks import process_media as _process_media

process_media = cast(Task, _process_media)

router = APIRouter(prefix="/api/media")


def determine_file_type(mime_type: str, file_name: str) -> FileType:
    if mime_type.startswith("image/"):
        return FileType.IMAGE
    elif mime_type.startswith("audio/"):
        return FileType.AUDIO
    else:
        ext = file_name.lower().split(".")[-1] if "." in file_name else ""
        if ext in ["pdf", "doc", "docx", "txt", "md", "csv", "xls", "xlsx"]:
            return FileType.TEXT
        return FileType.TEXT


@router.post("/upload")
async def upload_files(
    db: DBSession,
    current_user: CurrentUser,
    files: Annotated[
        list[UploadFile], File(description="Multiple files as UploadFile")
    ],
):
    try:
        uploaded_media = []

        for file in files:
            contents = await file.read()

            file_name = file.filename or ""
            mime_type = file.content_type or ""
            file_size = len(contents)

            file_type = determine_file_type(mime_type, file_name)

            media = Media(
                user_id=current_user.id,
                file_name=file_name,
                file_type=file_type,
                mime_type=mime_type,
                size=file_size,
            )

            db.add(media)
            db.flush()

            contents_base64 = base64.b64encode(contents).decode("utf-8")

            task = process_media.delay(
                media_id_str=str(media.id),
                file_type=file_type.value,
                file_contents_base64=contents_base64,
            )

            uploaded_media.append(
                {
                    "id": str(media.id),
                    "file_name": file_name,
                    "file_type": file_type.value,
                    "file_size": file_size,
                    "task_id": task.id,
                }
            )

        db.commit()

        return {
            "message": f"Successfully uploaded {len(files)} file(s)",
            "media": uploaded_media,
            "status": "processing",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/list")
def get_media(db: DBSession, current_user: CurrentUser):
    media_records = db.query(Media).join(User).filter(User.id == current_user.id).all()
    if not media_records:
        raise HTTPException(status_code=404, detail="Media not found")

    media_response = [
        {
            "id": media.id,
            "file_name": media.file_name,
            "file_type": media.mime_type,
            "file_size": media.size,
        }
        for media in media_records
    ]

    return {"media": media_response}


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: CurrentUser,
):
    try:
        from app.tasks import celery_app

        result = celery_app.AsyncResult(task_id)

        status_mapping = {
            "PENDING": "pending",
            "STARTED": "processing",
            "RETRY": "processing",
            "SUCCESS": "completed",
            "FAILURE": "failed",
            "REVOKED": "failed",
        }

        mapped_status = status_mapping.get(result.state, "processing")

        return {
            "status": mapped_status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking task status: {str(e)}"
        )
