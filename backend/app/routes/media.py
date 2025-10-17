import base64
from typing import Annotated, cast
from uuid import uuid4

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
        task_ids = []

        for file in files:
            contents = await file.read()

            media_id = uuid4()
            file_name = file.filename or ""
            mime_type = file.content_type or ""
            file_size = len(contents)

            file_type = determine_file_type(mime_type, file_name)

            # TODO: Update this with actual storage URL
            storage_url = f"https://fake-storage.local/{media_id}/{file_name}"

            media = Media(
                id=media_id,
                user_id=current_user.id,
                file_name=file_name,
                file_type=file_type,
                mime_type=mime_type,
                storage_url=storage_url,
                size=file_size,
            )

            db.add(media)
            db.flush()

            contents_base64 = base64.b64encode(contents).decode("utf-8")

            task = process_media.delay(
                media_id_str=str(media_id),
                file_type=file_type.value,
                file_contents_base64=contents_base64,
            )

            uploaded_media.append(
                {
                    "media_id": str(media_id),
                    "file_name": file_name,
                    "file_type": file_type.value,
                    "file_size": file_size,
                    "task_id": task.id,
                }
            )

            task_ids.append(task.id)

        db.commit()

        return {
            "message": f"Successfully uploaded {len(files)} file(s)",
            "media": uploaded_media,
            "task_ids": task_ids,
            "status": "processing",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("")
def get_media(db: DBSession, current_user: CurrentUser):
    media_records = db.query(Media).join(User).filter(User.id == current_user.id).all()
    if not media_records:
        raise HTTPException(status_code=404, detail="Media not found")

    media_response = [
        {
            "id": media.id,
            "name": media.file_name,
            "file_type": media.mime_type,
            "size": media.size,
            "storage_url": media.storage_url,
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

        return {
            "task_id": task_id,
            "status": result.state,
            "result": result.result if result.ready() else None,
            "info": result.info,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking task status: {str(e)}"
        )
