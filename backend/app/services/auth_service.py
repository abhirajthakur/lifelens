import logging
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    verify_password,
)
from app.models.user import User
from app.services import user_service


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = user_service.get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        logging.warning(f"Failed login attempt for user with email: {email}")
        return None
    logging.info(f"User with email: {email} logged in successfully")
    return user


def login_user(db: Session, email: str, password: str) -> str:
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
