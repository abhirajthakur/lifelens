from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.media import FileType, Media, MediaMetadata
from app.models.user import User


async def save_media(db: Session, user: User, file):
    contents = await file.read()

    file_name = file.filename
    mime_type = file.content_type
    file_size = len(contents)

    if mime_type.startswith("image/"):
        file_type = FileType.IMAGE
    elif mime_type.startswith("audio/"):
        file_type = FileType.AUDIO
    else:
        file_type = FileType.TEXT

    storage_url = f"https://fake-storage.local/{file_name}"

    media_id = uuid4()

    media = Media(
        id=media_id,
        user_id=user.id,
        file_name=file_name,
        file_type=file_type,
        mime_type=mime_type,
        storage_url=storage_url,
        size=file_size,
        duration=None,
        width=None,
        height=None,
    )

    metadata = MediaMetadata(
        id=uuid4(),
        media_id=media_id,
        caption="",
        ocr_text=None,
        transcript=None,
        summary=None,
        topics=None,
        audio_tags=None,
        embeddings=None,
    )

    db.add(media)
    db.add(metadata)

    db.commit()

    return {"message": "Media saved successfully", "media_id": str(media_id)}
