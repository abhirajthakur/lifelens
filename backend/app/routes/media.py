from fastapi import APIRouter, File, UploadFile

from app.core.db import DBSession
from app.core.deps import CurrentUser
from app.services import media_service

router = APIRouter(prefix="/api/upload")


@router.post("")
async def upload_file(
    db: DBSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    await media_service.save_media(db, current_user, file)
    return {"filename": file.filename, "content-type": file.content_type}
