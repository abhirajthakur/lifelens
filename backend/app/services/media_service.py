from datetime import datetime
import logging
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.media import FileType, Media, MediaMetadata
from app.models.user import User
from app.services import ml_services


async def save_media(db: Session, user: User, file):
    contents = await file.read()

    media_id = uuid4()
    file_name = file.filename
    mime_type = file.content_type
    file_size = len(contents)

    # Determine file type without processing yet
    if mime_type.startswith("image/"):
        file_type = FileType.IMAGE
    elif mime_type.startswith("audio/"):
        file_type = FileType.AUDIO
    elif mime_type.startswith("video/"):
        file_type = FileType.VIDEO
    else:
        file_type = FileType.TEXT

    storage_url = f"https://fake-storage.local/{file_name}"

    # Create and save media record first
    media = Media(
        id=media_id,
        user_id=user.id,
        file_name=file_name,
        file_type=file_type,
        mime_type=mime_type,
        storage_url=storage_url,
        size=file_size,
    )

    db.add(media)
    db.commit()

    try:
        if file_type == FileType.IMAGE:
            # Only process images since that's the only function we have implemented
            ml_services.process_image(db, media_id, contents)
            # TODO: Add processing for other media types when functions are implemented
            # elif file_type == FileType.AUDIO:
            #     ml_services.process_audio(db, media_id, contents)
            # elif file_type == FileType.VIDEO:
            #     ml_services.process_video(db, media_id, contents)
            # elif file_type == FileType.TEXT:
            #     ml_services.process_text(db, media_id, contents)
    except Exception as e:
        # Log the error but don't fail the media save operation
        logging.warning(f"Failed to process media {media_id}: {e}")

    return {"message": "Media saved successfully", "media_id": str(media_id)}


def get_media(db: Session, media_id: str):
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return dict(media)


def filter_media_by_date(db: Session, start_date: datetime, end_date: datetime):
    media = (
        db.query(MediaMetadata)
        .filter(
            MediaMetadata.created_at >= start_date, MediaMetadata.created_at <= end_date
        )
        .all()
    )
    return media
