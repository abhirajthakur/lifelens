from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services import media_service

router = APIRouter(prefix="/api/upload")


@router.post("")
async def upload_file(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
):
    await media_service.save_media(db, current_user, file)
    return {"filename": file.filename, "content-type": file.content_type}
