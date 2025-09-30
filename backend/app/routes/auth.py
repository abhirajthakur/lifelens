from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate
from app.services.auth_service import login_user
from app.services.user_service import create_user

router = APIRouter(prefix="/auth")


@router.post("/signup")
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    try:
        create_user(db, user_in)
        return {"message": "User created successfully"}
    except Exception as e:
        error_message = str(e)

        if "already exists" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during signup",
        )


@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        token = login_user(db, request.email, request.password)
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        error_message = str(e).lower()

        if "invalid credentials" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        )
