from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import User
from app.schemas.user import UserCreate


def create_user(db: Session, user_in: UserCreate) -> User:
    if get_user_by_email(db, user_in.email):
        raise ValueError(f"User with email {user_in.email} already exists")

    password_hash = get_password_hash(user_in.password)

    user = User(
        email=user_in.email,
        name=user_in.name,
        password_hash=password_hash,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return db.query(User).offset(skip).limit(limit).all()
