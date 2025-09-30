import enum
from typing import Optional
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class FileType(enum.Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TEXT = "text"


class Media(Base):
    __tablename__ = "media"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    file_name: Mapped[str]
    file_type: Mapped[FileType] = mapped_column(Enum(FileType))
    mime_type: Mapped[str]
    storage_url: Mapped[str]
    size: Mapped[int]
    duration: Mapped[Optional[int]]
    width: Mapped[Optional[int]]
    height: Mapped[Optional[int]]


class MediaMetadata(Base):
    __tablename__ = "media_metadata"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    caption: Mapped[str]
    ocr_text: Mapped[Optional[str]]
    transcript: Mapped[Optional[str]]
    summary: Mapped[Optional[str]]
    topics: Mapped[Optional[ARRAY[Text]]] = mapped_column(ARRAY(Text))
    audio_tags: Mapped[Optional[ARRAY[Text]]] = mapped_column(ARRAY(Text))
    embeddings: Mapped[Optional[Vector]] = mapped_column(Vector())

    media_id: Mapped[str] = mapped_column(ForeignKey("media.id"))
