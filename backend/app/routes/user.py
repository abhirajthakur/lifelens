from fastapi import APIRouter, HTTPException

from app.core.db import DBSession
from app.core.deps import CurrentUser

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/stats")
async def get_user_stats(db: DBSession, current_user: CurrentUser):
    try:
        from app.models.media import FileType, Media, MediaMetadata

        total_media = db.query(Media).filter(Media.user_id == current_user.id).count()

        image_count = (
            db.query(Media)
            .filter(Media.user_id == current_user.id, Media.file_type == FileType.IMAGE)
            .count()
        )

        audio_count = (
            db.query(Media)
            .filter(Media.user_id == current_user.id, Media.file_type == FileType.AUDIO)
            .count()
        )

        document_count = (
            db.query(Media)
            .filter(Media.user_id == current_user.id, Media.file_type == FileType.TEXT)
            .count()
        )

        processed_count = (
            db.query(MediaMetadata)
            .join(Media)
            .filter(Media.user_id == current_user.id)
            .count()
        )

        indexed_count = (
            db.query(MediaMetadata)
            .join(Media)
            .filter(
                Media.user_id == current_user.id, MediaMetadata.embeddings.isnot(None)
            )
            .count()
        )

        return {
            "total_media": total_media,
            "by_type": {
                "images": image_count,
                "audio": audio_count,
                "documents": document_count,
            },
            "processing_status": {
                "processed": processed_count,
                "indexed": indexed_count,
                "pending": total_media - processed_count,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")
