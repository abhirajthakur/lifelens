from fastapi import APIRouter, HTTPException

from app.core.db import DBSession
from app.schemas.user import UserRead
from app.services.user_service import get_user_by_id

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: str, db: DBSession):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
