from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.media import Media


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    full_name: Mapped[str]
    media: Mapped[List["Media"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
